@echo off
title VisionGuard AI Traffic Intelligence Launcher
echo =======================================================================
echo          Starting VisionGuard AI Urban Traffic Intelligence
echo =======================================================================
echo.

cd /d "%~dp0"

echo [1/2] Activating Python environment and launching FastAPI backend...
start "VisionGuard Backend (Port 8000)" cmd /k ".venv\Scripts\python.exe -m uvicorn visionguard.api.app:app --host 127.0.0.1 --port 8000"

timeout /t 3 /nobreak >nul

echo [2/2] Launching Vite Frontend Dev Server (Port 5173)...
start "VisionGuard Frontend (Port 5173)" cmd /k "cd frontend && npm run dev -- --host 127.0.0.1 --port 5173"

timeout /t 2 /nobreak >nul

echo.
echo =======================================================================
echo  VisionGuard is now running!
echo.
echo  - Main Dashboard (Combined):  http://localhost:8000
echo  - Frontend Dev Server:        http://localhost:5173
echo  - Interactive Swagger Docs:   http://localhost:8000/docs
echo =======================================================================
echo.
echo Opening browser...
start http://localhost:8000
