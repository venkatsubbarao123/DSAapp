# ==============================================================================
# DSAapp - stop the local development stack.
#
#   .\stop_fast.ps1              stop backend + frontend (keep Docker data)
#   .\stop_fast.ps1 -WithDocker  also stop the Postgres + Redis containers
# =============================================================================

param([switch]$WithDocker)

Write-Host "`n==> Stopping application servers" -ForegroundColor Cyan

foreach ($port in @(8000, 5173)) {
    $conns = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue
    foreach ($c in $conns) {
        Stop-Process -Id $c.OwningProcess -Force -ErrorAction SilentlyContinue
        Write-Host "    [OK] Stopped process on port $port (PID $($c.OwningProcess))" -ForegroundColor Green
    }
}

# Vite spawns a child node process; clear any stragglers.
Get-CimInstance Win32_Process -Filter "Name='node.exe'" -ErrorAction SilentlyContinue |
    Where-Object { $_.CommandLine -like '*vite*' } |
    ForEach-Object {
        Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue
        Write-Host "    [OK] Stopped Vite node process (PID $($_.ProcessId))" -ForegroundColor Green
    }

if ($WithDocker) {
    Write-Host "`n==> Stopping Docker services" -ForegroundColor Cyan
    foreach ($c in @('dsaapp-postgres', 'dsaapp-redis')) {
        docker stop $c 2>$null | Out-Null
        if ($LASTEXITCODE -eq 0) {
            Write-Host "    [OK] Stopped container $c" -ForegroundColor Green
        } else {
            Write-Host "    [!]  Container $c was not running" -ForegroundColor Yellow
        }
    }
}

Write-Host "`nDone. Run .\start_fast.ps1 to start again.`n" -ForegroundColor Cyan
