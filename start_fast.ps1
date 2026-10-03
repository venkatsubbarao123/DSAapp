# ==============================================================================
# DSAapp - FAST local development launcher (Windows PowerShell)
#
#   .\start_fast.ps1
#
# Uses the LOCAL Docker Postgres + Redis instead of the remote Neon cloud
# database, which removes 5-30s network round-trips and makes every page load
# in milliseconds. Starts Postgres, Redis, the FastAPI backend and the Vite
# frontend, then waits until both are actually serving traffic.
# ==============================================================================

$ErrorActionPreference = 'Stop'
$Root    = Split-Path -Parent $MyInvocation.MyCommand.Path
$Logs    = Join-Path $Root 'logs'
$Backend = Join-Path $Root 'backend'
$PyExe   = Join-Path $Backend '.venv\Scripts\python.exe'

function Step($m) { Write-Host "`n==> $m" -ForegroundColor Cyan }
function Ok($m)   { Write-Host "    [OK] $m" -ForegroundColor Green }
function Warn($m) { Write-Host "    [!]  $m" -ForegroundColor Yellow }
function Die($m)  { Write-Host "    [X]  $m" -ForegroundColor Red; exit 1 }

New-Item -ItemType Directory -Force -Path $Logs | Out-Null

# ---------------------------------------------------------------- 1. Docker
Step "Checking Docker infrastructure"
$dockerUp = $false
try { docker info --format '{{.ServerVersion}}' 2>$null | Out-Null; $dockerUp = $true } catch { }
if (-not $dockerUp) {
    Warn "Docker daemon is not reachable."
    Warn "Start Docker Desktop, then run this script again."
    Warn "The Online Judge needs Docker; everything else works without it."
} else {
    Ok "Docker daemon is running"

    foreach ($svc in @(@{n='postgres:16-alpine'; c='dsaapp-postgres'; p='5432'},
                       @{n='redis:7-alpine';    c='dsaapp-redis';    p='6379'})) {
        $running = docker ps --filter "ancestor=$($svc.n)" --filter "status=running" -q 2>$null
        if ($running) {
            Ok "$($svc.n) is running on port $($svc.p)"
        } else {
            Warn "Starting $($svc.n)..."
            docker run -d --name $svc.c --restart unless-stopped `
                -p "$($svc.p):$($svc.p)" `
                -e POSTGRES_USER=dsaapp_user `
                -e POSTGRES_PASSWORD=dsaapp_secure_password `
                -e POSTGRES_DB=dsaapp_prod $svc.n 2>$null | Out-Null
            Start-Sleep -Seconds 5
            Ok "$($svc.n) started"
        }
    }
}

# ---------------------------------------------------------------- 2. Python
Step "Checking backend environment"
if (-not (Test-Path $PyExe)) {
    Die "Virtual environment missing. Run: python -m venv backend\.venv"
}
& $PyExe -c "import redis" 2>$null
if ($LASTEXITCODE -ne 0) {
    Warn "Installing redis-py (enables caching + judge queue)..."
    & $PyExe -m pip install "redis>=5.0.0" --quiet
}
Ok "Python environment ready"

# ---------------------------------------------------------------- 3. Ports
Step "Freeing ports 8000 and 5173"
foreach ($port in @(8000, 5173)) {
    $conns = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue
    foreach ($c in $conns) {
        Stop-Process -Id $c.OwningProcess -Force -ErrorAction SilentlyContinue
        Ok "Released port $port (PID $($c.OwningProcess))"
    }
}
Start-Sleep -Seconds 2

# ---------------------------------------------------------------- 4. Backend
Step "Starting FastAPI backend (port 8000)"
$backendProc = Start-Process -FilePath $PyExe `
    -ArgumentList '-m', 'uvicorn', 'backend.app.main:app', '--host', '127.0.0.1', '--port', '8000' `
    -WorkingDirectory $Root `
    -RedirectStandardOutput (Join-Path $Logs 'backend_out.log') `
    -RedirectStandardError  (Join-Path $Logs 'backend_err.log') `
    -WindowStyle Hidden -PassThru
Ok "Backend PID $($backendProc.Id) - waiting for it to accept requests..."

$ready = $false
for ($i = 0; $i -lt 60; $i++) {
    Start-Sleep -Seconds 1
    try {
        $h = Invoke-RestMethod 'http://127.0.0.1:8000/health' -TimeoutSec 3
        $ready = $true
        Ok ("Health: {0} | db: {1} | redis: {2}" -f `
            $h.data.status, $h.data.database, $h.data.redis)
        break
    } catch { }
}
if (-not $ready) { Die "Backend did not become healthy. Check logs\backend_err.log" }

# ---------------------------------------------------------------- 5. Frontend
Step "Starting Vite frontend (port 5173)"
Push-Location (Join-Path $Root 'frontend')
if (-not (Test-Path 'node_modules')) {
    Warn "node_modules missing - running npm install (this takes a minute)..."
    npm install --silent
}
$frontProc = Start-Process -FilePath 'npm.cmd' `
    -ArgumentList 'run', 'dev', '--', '--host', '127.0.0.1', '--port', '5173' `
    -WorkingDirectory (Join-Path $Root 'frontend') `
    -RedirectStandardOutput (Join-Path $Logs 'frontend_out.log') `
    -RedirectStandardError  (Join-Path $Logs 'frontend_err.log') `
    -WindowStyle Hidden -PassThru
Pop-Location
Ok "Frontend PID $($frontProc.Id) - waiting for Vite..."

$up = $false
for ($i = 0; $i -lt 60; $i++) {
    Start-Sleep -Seconds 1
    try {
        $f = Invoke-WebRequest 'http://127.0.0.1:5173/' -UseBasicParsing -TimeoutSec 3
        if ($f.StatusCode -eq 200) { $up = $true; break }
    } catch { }
}
if ($up) { Ok "Frontend is serving" } else { Warn "Frontend not responding yet - it may still be compiling" }

# ---------------------------------------------------------------- 6. Done
Write-Host "`n================================================================" -ForegroundColor Cyan
Write-Host "  DSAapp is running FAST" -ForegroundColor Green
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host "  App      : http://localhost:5173"
Write-Host "  API docs : http://localhost:8000/docs"
Write-Host "  Health   : http://localhost:8000/health"
Write-Host ""
Write-Host "  Backend PID $($backendProc.Id)   Frontend PID $($frontProc.Id)"
Write-Host ""
Write-Host "  Logs: $Logs"
Write-Host "  Stop: .\stop_fast.ps1"
Write-Host ""

Start-Process 'http://localhost:5173'
