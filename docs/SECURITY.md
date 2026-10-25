# Security controls

| Area | Control | Where |
|---|---|---|
| Student access | Magic link to `@btu.edu.ge` only; 256-bit token, stored as SHA-256, 15-minute TTL, single use (atomic update), older links invalidated | `apps/accounts/models.py` |
| Token leakage | Token travels in the URL fragment (`#token=`), never sent to servers or logs; removed from history on load | `frontend/.../auth/callback` |
| Enumeration | Sign-in request always returns the same 202 message; unknown emails get no token | `apps/api/views_auth.py` |
| Sessions | DB sessions, 12 h, HttpOnly, SameSite=Lax, Secure in production, key cycled at login | `config/settings.py` |
| CSRF | Django CSRF middleware + `X-CSRFToken` header from the frontend; trusted origins explicit | settings, `frontend/src/lib/api.ts` |
| Roles | `admin` and `staff` groups; DRF permissions are the real gate; first admin from `ADMIN_BOOTSTRAP_EMAILS` | `apps/api/permissions.py` |
| Object access | Students can download only their own versions; staff downloads are audited | `views_auth.py`, `views_admin.py` |
| Rate limits | verify 30/min/IP, sign-in 10/h/IP and 3/15 min/email, consume 20/h, admin actions 60/min; nginx `limit_req` in production | `apps/api/throttles.py`, `docker/nginx/nginx.conf` |
| Headers | Nonce-based CSP with `strict-dynamic`, `frame-ancestors 'none'`, X-Frame-Options DENY, nosniff, Referrer-Policy, Permissions-Policy, COOP; API responses `default-src 'none'` + `no-store` | `frontend/src/middleware.ts`, `next.config.ts`, `apps/core/middleware.py` |
| Transport | HSTS, TLS 1.2+, HTTPS redirect when `BEHIND_TLS_PROXY=true` | nginx, settings |
| Files | PDFs are never served statically; only through authorised views with `Cache-Control: private, no-store` | `MEDIA_URL` unused |
| Privacy | PDF verification hashes the file in the browser; only hashes on chain; IPs stored as salted hashes | `FileDrop.tsx`, `apps/core/hashing.py` |
| Audit | Append-only `AuditLog` for issuance, anchoring, revocation, sync, sign-in, downloads, lookups | `apps/audit/models.py` |
| Keys | Owner key (cold, can authorise/rotate issuers) separate from issuer key (hot, in the worker); ownership transfer is two-step | `PassportRegistry.sol` |
| Integrity rules | Names, Passport ID and first-issue date frozen; chain enforces version order and unique document hashes | models, contract |
| Containers | Non-root users in web, worker and frontend images | Dockerfiles |

Production checklist: set a long random `SECRET_KEY`, `DJANGO_DEBUG=false`, real SMTP, HTTPS
`PUBLIC_BASE_URL`, `BEHIND_TLS_PROXY=true`, `SECURE_COOKIES=true`, new owner/issuer keys (never the
Anvil test keys), and restrict who can read `.env`.
