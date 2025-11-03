@echo off
REM =========================================
REM RSA Key Generator - Standalone Tool
REM =========================================
echo.
echo ========================================
echo   RSA-2048 Key Pair Generator
echo ========================================
echo.

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not installed!
    echo Download from: https://www.python.org/downloads/
    pause
    exit /b 1
)

REM Check cryptography
python -c "import cryptography" >nul 2>&1
if errorlevel 1 (
    echo Installing cryptography library...
    python -m pip install cryptography --quiet
)

REM Run generator
echo Running RSA Key Generator...
echo.
python "%~dp0generate_rsa_keys.py"

echo.
pause
