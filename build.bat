@echo off
REM =========================================
REM Build Script for ArtNet Controller
REM Compiles license module with Cython
REM =========================================

echo.
echo ========================================
echo   ArtNet Controller - Build Script
echo ========================================
echo.

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found!
    echo Please install Python 3.8+ and add to PATH
    pause
    exit /b 1
)

echo [1/5] Checking dependencies...
pip install --quiet cython cryptography numpy pyinstaller

echo [2/5] Compiling license module with Cython...
python setup_cython.py build_ext --inplace

if errorlevel 1 (
    echo ERROR: Cython compilation failed!
    pause
    exit /b 1
)

echo [3/5] Verifying compiled binary...
if exist "src\utils\license.cp*.pyd" (
    echo   SUCCESS: license.pyd compiled
) else (
    echo   ERROR: Compiled binary not found!
    pause
    exit /b 1
)

echo [4/5] Backing up original source...
if exist "src\utils\license.py" (
    copy "src\utils\license.py" "src\utils\license.py.original" >nul
    echo   Backup created: license.py.original
)

echo [5/5] Cleaning build artifacts...
rmdir /s /q build 2>nul
del /q src\utils\license.c 2>nul

echo.
echo ========================================
echo   BUILD SUCCESSFUL!
echo ========================================
echo.
echo Compiled files:
dir /b src\utils\license*.pyd 2>nul
echo.
echo IMPORTANT:
echo   - license.pyd contains the protected code
echo   - You can now delete license.py before distribution
echo   - Keep license.py.original for development
echo.
echo Next steps:
echo   1. Test the application with compiled module
echo   2. Create distribution package (see SECURITY_ARCHITECTURE.md)
echo   3. Delete original license.py before shipping
echo.
pause
