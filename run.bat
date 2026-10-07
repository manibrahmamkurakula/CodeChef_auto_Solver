@echo off
title CodeChef Universal Auto Solver
echo ========================================================
echo         CodeChef Universal Course Auto-Solver
echo ========================================================
echo.
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not in PATH.
    echo Download Python from https://www.python.org/
    pause
    exit /b
)
if not exist auto_solve.py (
    echo Downloading auto_solve.py...
    curl -s -L -o auto_solve.py https://raw.githubusercontent.com/manibrahmamkurakula/CodeChef_auto_Solver/main/auto_solve.py
)
if not exist solutions_database.json (
    echo Downloading solutions_database.json...
    curl -s -L -o solutions_database.json https://raw.githubusercontent.com/manibrahmamkurakula/CodeChef_auto_Solver/main/solutions_database.json
)
echo Installing dependencies...
pip install playwright python-dotenv --quiet
playwright install chromium
echo Starting solver...
python auto_solve.py
pause
