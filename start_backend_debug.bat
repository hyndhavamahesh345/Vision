@echo off
setlocal

cd /d "%~dp0"
if not exist logs mkdir logs

echo Checking Python...
where python > logs\backend_debug.log 2>&1
if errorlevel 1 (
  echo ERROR: Python was not found. Install Python and enable Add to PATH. >> logs\backend_debug.log
  type logs\backend_debug.log
  pause
  exit /b 1
)

echo Python version: >> logs\backend_debug.log
python --version >> logs\backend_debug.log 2>&1

cd /d "%~dp0backend"

echo Checking backend imports... >> "%~dp0logs\backend_debug.log"
python -c "import fastapi, uvicorn, cv2, numpy, PIL, multipart; print('basic backend imports ok')" >> "%~dp0logs\backend_debug.log" 2>&1
if errorlevel 1 (
  echo ERROR: Backend packages are missing. Installing requirements... >> "%~dp0logs\backend_debug.log"
  python -m pip install -r requirements.txt >> "%~dp0logs\backend_debug.log" 2>&1
)

echo Starting backend on http://127.0.0.1:8001 >> "%~dp0logs\backend_debug.log"
python -m uvicorn main:app --host 127.0.0.1 --port 8001 >> "%~dp0logs\backend_debug.log" 2>&1

echo.
echo Backend stopped or failed. Error log:
echo %~dp0logs\backend_debug.log
echo.
type "%~dp0logs\backend_debug.log"
pause
