# Run every automated test on Windows: contract, backend (Postgres + Anvil), frontend, and browser e2e.
$ErrorActionPreference = "Continue"
Set-Location (Split-Path $PSScriptRoot -Parent)
$root = (Get-Location).Path
$fail = 0

Write-Host "== Contract (forge) ==" -ForegroundColor Cyan
docker run --rm -v "${root}\chain:/work" -w /work --entrypoint sh ghcr.io/foundry-rs/foundry:stable -c "forge test"
if ($LASTEXITCODE -ne 0) { $fail++ }

Write-Host "== Backend (pytest) ==" -ForegroundColor Cyan
docker compose run --rm --no-deps web python -m pytest -q -p no:cacheprovider
if ($LASTEXITCODE -ne 0) { $fail++ }

Write-Host "== Frontend (vitest) ==" -ForegroundColor Cyan
Push-Location frontend; npm test; if ($LASTEXITCODE -ne 0) { $fail++ }; Pop-Location

Write-Host "== Browser end-to-end ==" -ForegroundColor Cyan
python scripts\e2e_smoke.py
if ($LASTEXITCODE -ne 0) { $fail++ }

if ($fail -gt 0) { Write-Host "$fail suite(s) failed" -ForegroundColor Red; exit 1 }
Write-Host "All suites passed" -ForegroundColor Green
