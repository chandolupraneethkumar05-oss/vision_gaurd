# VisionGuard 1-Click Startup Script for PowerShell
Write-Host "=======================================================================" -ForegroundColor DarkGreen
Write-Host "         Starting VisionGuard AI Urban Traffic Intelligence            " -ForegroundColor DarkGreen
Write-Host "=======================================================================" -ForegroundColor DarkGreen

$rootDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $rootDir

Write-Host "`n[1/2] Launching FastAPI Backend on http://127.0.0.1:8000..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location '$rootDir'; & '.\.venv\Scripts\python.exe' -m uvicorn visionguard.api.app:app --host 127.0.0.1 --port 8000"

Start-Sleep -Seconds 3

Write-Host "[2/2] Launching Vite Frontend on http://127.0.0.1:5173..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location '$rootDir\frontend'; npm run dev -- --host 127.0.0.1 --port 5173"

Start-Sleep -Seconds 2

Write-Host "`n=======================================================================" -ForegroundColor DarkGreen
Write-Host " VisionGuard is now active!" -ForegroundColor Green
Write-Host " - Main Dashboard:     http://localhost:8000" -ForegroundColor White
Write-Host " - Frontend Live Dev:  http://localhost:5173" -ForegroundColor White
Write-Host " - API Docs:           http://localhost:8000/docs" -ForegroundColor White
Write-Host "=======================================================================`n" -ForegroundColor DarkGreen

Start-Process "http://localhost:8000"
