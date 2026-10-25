# Start the whole stack on Windows (Docker Desktop must be running).
#   .\scripts\up.ps1           build + start
#   .\scripts\up.ps1 -Reset    wipe database, chain and local sheet first
param([switch]$Reset)
$ErrorActionPreference = "Stop"
Set-Location (Split-Path $PSScriptRoot -Parent)

if (-not (Test-Path .env)) { Copy-Item .env.example .env; Write-Host "Created .env from .env.example" }
if ($Reset) {
  docker compose down -v
  Remove-Item -ErrorAction SilentlyContinue data\local_sheet\passport_sheet.xlsx, chain\deployments\31337.json
}
docker compose up -d --build
if ($LASTEXITCODE -ne 0) { throw "docker compose failed" }

Write-Host "Waiting for the first sync..."
for ($i = 0; $i -lt 60; $i++) {
  try {
    $h = Invoke-RestMethod http://localhost:8000/api/health -TimeoutSec 3
    if ($h.worker_last_seen -and $h.contract) { break }
  } catch {}
  Start-Sleep -Seconds 2
}
Start-Sleep -Seconds 5
docker compose exec -T web python manage.py demo_summary
Write-Host ""
Write-Host "Site (Georgian): http://localhost:3000/ka"
Write-Host "Site (English):  http://localhost:3000/en"
Write-Host "Mail inbox:      http://localhost:8025   (magic sign-in links land here)"
Write-Host "Admin sign-in:   passport.admin@btu.edu.ge"
