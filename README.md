# BTU AI Skills Digital Passport

A working MVP for Business and Technology University: one permanent, incrementally updated,
blockchain-verified **AI Skills Digital Passport** per student, generated automatically from a
Google Sheet, viewable by students with their BTU email, and verifiable by anyone without an account.

Bilingual website (Georgian `/ka`, English `/en`), 4-page PDF rebuilt from BTU's design, Solidity
registry on an EVM chain (local Anvil by default, Polygon Amoy via `.env`).

## Run it

Requirements: Docker Desktop (or Docker Engine + Compose v2). Nothing else.

```bash
cp .env.example .env          # safe local defaults
docker compose up -d --build  # or: make up   |   Windows: .\scripts\up.ps1
```

| What | URL |
|---|---|
| Website (Georgian / English) | http://localhost:3000/ka · http://localhost:3000/en |
| Mail inbox (sign-in links land here locally) | http://localhost:8025 |
| API health | http://localhost:8000/api/health |
| Issuer identity record | http://localhost:3000/.well-known/btu-issuer.json |
| Django back office (fallback) | http://localhost:3000/django-admin/ |

On first start the worker deploys the registry contract to the local chain, creates the local sheet
with three showcase students, issues their passports and anchors them. After ~30 seconds:

```bash
docker compose exec web python manage.py demo_summary    # passports + verification links
```

### Five-minute demo

1. **Verify as an employer.** Open a verification link from `demo_summary`. No login. You see the
   holder, the stamps, *document authenticity* and *issuer authenticity* checks, and the chain record.
2. **Tamper test.** On the same page drop the PDF (download it as the student, below). It matches.
   Change one character in the PDF and drop it again: verification fails.
3. **Student access.** Go to *Student sign-in*, enter `demo.nino.beridze@btu.edu.ge`, open the
   link from Mailpit (http://localhost:8025). View and download the passport.
4. **Passport update.** Sign in as `passport.admin@btu.edu.ge` → *Passport office*. Simulate the office
   confirming a new skill in the sheet:
   `docker compose exec web python manage.py demo_confirm AW-DEMO-0013`, then press *Sync now*.
   Giorgi's passport gets **v2** with the same Passport ID; his v1 code now reports *superseded*.
5. **Revoke** a version from the version page; its code immediately reports *revoked*.

Edit `data/local_sheet/passport_sheet.xlsx` directly (close it before the next sync) to try your own
students and skills; the worker picks changes up every 30 seconds.

## How it meets the brief

| Requirement | Implementation |
|---|---|
| 1. One passport, permanent ID | `Passport` is 1:1 with `Student`; ID `BTU-AI-YYYY-NNNNN`; name, surname, ID and first-issue date are frozen at creation |
| 2. Google Sheets as source | Adapter reads Students / SkillCatalog / Awards tabs every `SYNC_INTERVAL_SECONDS`, validates, writes status back into grey `sys_*` columns |
| 3. Automatic PDF generation | WeasyPrint renders the 4-page BTU design from a frozen snapshot; no manual step |
| 4. Adding skills | Each confirmed Awards row adds skill, stamp, date, description; all earlier stamps are kept |
| 5. Blockchain verification | SHA-256 of the exact PDF bytes is anchored in `PassportRegistry`; any byte change fails |
| 6. Issuer identity | Only addresses the BTU-owned contract authorises can anchor; the address is published at `/.well-known/btu-issuer.json`; each PDF also carries an EIP-712 issuer signature |
| 7. Verification code | 12-character code (`XXXX-XXXX-XXXX`, 60 bits) + QR on the cover; public page, no login |
| 8. Versions | New version per change, same Passport ID; chain enforces strict version order; latest valid version is reported on every check |
| 9. Student access | Magic link to `@btu.edu.ge` email; single-use, 15-minute, hashed at rest |
| 10. Scale | Stateless web + one worker; sheet read in 3 API calls per pass; ~1 s render + 1 tx per version; 5,000/year is far below limits |

## Repository

```
backend/    Django 5.2 + DRF: models, sheet sync, PDF renderer, chain client, API, worker
frontend/   Next.js 15 + next-intl: public site (ka/en), verification, student portal, passport office
chain/      PassportRegistry.sol, Foundry tests, committed ABI/bytecode, deployments
data/       sheet_template/ (official template + test sheet + CSVs), showcase/, local_sheet/
docs/       SHEET_SCHEMA, VERIFICATION, SECURITY, ARCHITECTURE, GOOGLE_SHEETS, DEPLOYMENT
scripts/    e2e_smoke.py, up.ps1, test.ps1, asset generator
```

## Tests

```bash
make test        # forge + pytest (Postgres + Anvil) + vitest      | Windows: .\scripts\test.ps1
make e2e         # real browser: sign-in, download, hash match, tamper, update, supersede, revoke
```

## Switching to Polygon Amoy or real Google Sheets

See [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) and [docs/GOOGLE_SHEETS.md](docs/GOOGLE_SHEETS.md).
Both are configuration only; no code changes.
