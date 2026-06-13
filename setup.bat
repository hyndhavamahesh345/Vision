@echo off
echo ========================================
echo AI Property Inventory - Setup Script
echo ========================================
echo.

REM Backend setup
echo Installing backend dependencies...
cd backend
pip install -r requirements.txt
cd ..

REM Frontend setup
echo Installing frontend dependencies...
cd frontend
npm install
cd ..

echo.
echo ========================================
echo Setup Complete!
echo ========================================
echo.
echo Next steps:
echo 1. Add your Gemini API key to backend/.env
echo 2. Start backend: cd backend && uvicorn main:app --reload --port 8001
echo 3. Start frontend: cd frontend && npm run dev
echo 4. Open http://localhost:3000
echo.
pause
