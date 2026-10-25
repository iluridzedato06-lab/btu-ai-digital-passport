# Architecture

```
 Google Sheet ──read/write──▶ worker (Django command run_worker)
 (or local .xlsx)               │  1. validate rows, upsert Students / Skills / Awards
                                │  2. per changed student: issue_version()
                                │       code → snapshot → EIP-712 sig → WeasyPrint PDF → SHA-256
                                │  3. anchor pending versions ──tx──▶ PassportRegistry (EVM)
                                │  4. write sys_* status back to the sheet
                                ▼
                            Postgres ◀── web (Django + DRF, gunicorn) ◀── Next.js (ka / en) ◀── browser
                                              │ reads chain for every public verification
                                              └──────────────────────────────▶ PassportRegistry
```

| Service | Image | Role |
|---|---|---|
| `web` | `backend/Dockerfile` | REST API, migrations, Django admin |
| `worker` | same image | Sheet sync loop, anchoring with retries, housekeeping |
| `frontend` | `frontend/Dockerfile` | Public site, student portal, passport office; proxies `/api` |
| `postgres` | postgres:16 | Data |
| `anvil` | foundry | Local EVM chain with persisted state (dev only) |
| `mailpit` | mailpit | Catches email locally |
| `nginx` | profile `prod` | TLS, rate limits, routing |

## Key decisions

- **Snapshot-first rendering.** Each version stores a frozen JSON snapshot; the PDF is rendered only
  from it, so re-rendering is byte-identical and the history is self-describing.
- **One version per student per pass.** Batching keeps transactions and versions low.
- **Strict on-chain ordering.** `anchorVersion` only accepts `latest + 1`, so the chain alone
  answers "which version is latest".
- **No queue server.** A single worker with a Postgres advisory lock is enough for 5,000+
  passports/year; a second replica is safe because of the lock.
- **Retries and reconciliation.** Failed anchors back off exponentially; if a transaction landed but
  the receipt was lost, the worker reconciles from the chain instead of re-sending.

## Scale estimate (5,000 passports/year, ~4 updates each)

| Item | Load |
|---|---|
| Versions per year | ~20,000 |
| PDF render | ~0.7 s each → ~4 CPU-hours/year |
| Chain transactions | ~20,000/year; on Polygon a few cents each |
| Sheet API | 3 reads + ≤1 batch write per pass, far under the 60/min quota |
| Storage | ~100 KB per PDF → ~2 GB/year |
