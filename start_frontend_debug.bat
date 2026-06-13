@echo off
setlocal

cd /d "%~dp0"
if not exist logs mkdir logs

echo Checking Node.js and npm...
where node > logs\frontend_debug.log 2>&1
if errorlevel 1 (
  echo ERROR: Node.js was not found. Install Node.js LTS from https://nodejs.org/ >> logs\frontend_debug.log
  type logs\frontend_debug.log
  pause
  exit /b 1
)

where npm >> logs\frontend_debug.log 2>&1
if errorlevel 1 (
  echo ERROR: npm was not found. Reinstall Node.js LTS and include npm. >> logs\frontend_debug.log
  type logs\frontend_debug.log
  pause
  exit /b 1
)

echo Node version: >> logs\frontend_debug.log
node --version >> logs\frontend_debug.log 2>&1
echo npm version: >> logs\frontend_debug.log
npm --version >> logs\frontend_debug.log 2>&1

cd /d "%~dp0frontend"

if not exist package.json (
  echo ERROR: frontend\package.json was not found. >> "%~dp0logs\frontend_debug.log"
  type "%~dp0logs\frontend_debug.log"
  pause
  exit /b 1
)

if not exist node_modules (
  echo Installing frontend packages... >> "%~dp0logs\frontend_debug.log"
  call npm install >> "%~dp0logs\frontend_debug.log" 2>&1
  if errorlevel 1 (
    echo ERROR: npm install failed. >> "%~dp0logs\frontend_debug.log"
    type "%~dp0logs\frontend_debug.log"
    pause
    exit /b 1
  )
)

echo Starting frontend on http://127.0.0.1:5173 >> "%~dp0logs\frontend_debug.log"
call npm run dev >> "%~dp0logs\frontend_debug.log" 2>&1

echo.
echo Frontend stopped or failed. Error log:
echo %~dp0logs\frontend_debug.log
echo.
type "%~dp0logs\frontend_debug.log"
pause
