@echo off
setlocal

cd /d "%~dp0"

where python >nul 2>nul
if errorlevel 1 (
  echo Python was not found on PATH. Install Python or open this from a Python-enabled terminal.
  pause
  exit /b 1
)

where npm >nul 2>nul
if errorlevel 1 (
  echo npm was not found on PATH. Install Node.js first.
  pause
  exit /b 1
)

if not exist "%~dp0frontend\node_modules" (
  echo Installing frontend packages...
  cd /d "%~dp0frontend"
  call npm install
  if errorlevel 1 (
    echo Frontend install failed.
    pause
    exit /b 1
  )
  cd /d "%~dp0"
)

echo Starting VisionVault backend on http://127.0.0.1:8001
start "VisionVault Backend" cmd /k "cd /d ""%~dp0backend"" && python -m uvicorn main:app --host 127.0.0.1 --port 8001"

echo Starting VisionVault frontend on http://127.0.0.1:5173
start "VisionVault Frontend" cmd /k "cd /d ""%~dp0frontend"" && npm run dev"

echo.
echo Open this preview link after both windows finish loading:
echo http://127.0.0.1:5173
echo.
pause
