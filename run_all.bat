@echo off
echo =========================================
echo       Starting ISCOR AI Services...
echo =========================================

:: 1. Setup Backend
set VENV_PATH=
if exist ".venv\Scripts\activate.bat" (
    set VENV_PATH=".venv\Scripts\activate.bat"
) else if exist ".venv-1\Scripts\activate.bat" (
    set VENV_PATH=".venv-1\Scripts\activate.bat"
)

if "%VENV_PATH%"=="" (
    echo [INFO] No virtual environment found. Creating .venv...
    python -m venv .venv
    set VENV_PATH=".venv\Scripts\activate.bat"
)

echo [INFO] Activating virtual environment at %VENV_PATH%...
call %VENV_PATH%

echo [INFO] Checking backend dependencies...
if not exist ".venv\Scripts\uvicorn.exe" if not exist ".venv-1\Scripts\uvicorn.exe" (
    echo [INFO] uvicorn not found, installing requirements.txt...
    pip install -r requirements.txt
)

echo [1/2] Starting FastAPI Backend on port 8000...
start "FastAPI Backend" cmd /k "call %VENV_PATH% && python -m uvicorn integration.api:app --port 8000 --reload"

:: 2. Setup Frontend
echo [INFO] Checking frontend dependencies...
cd frontend
if not exist "node_modules\" (
    echo [INFO] First time setup: Installing frontend dependencies...
    call npm install
)
cd ..

echo [2/2] Starting Vite Frontend...
start "Vite Frontend" cmd /k "cd frontend && npm run dev"

echo.
echo =========================================
echo All services have been launched in separate windows!
echo =========================================
pause
