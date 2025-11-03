@echo off
REM ============================================
REM Build License Generator EXE
REM ============================================

echo.
echo ============================================
echo   BUILDING LICENSE GENERATOR EXE
echo ============================================
echo.

REM Check if PyInstaller is installed
python -c "import PyInstaller" 2>nul
if errorlevel 1 (
    echo [!] PyInstaller not found. Installing...
    pip install pyinstaller
    if errorlevel 1 (
        echo [ERROR] Failed to install PyInstaller!
        pause
        exit /b 1
    )
)

REM Create build directory
if not exist "build" mkdir build
if not exist "dist" mkdir dist

echo.
echo [*] Building executable...
echo.

REM Build with PyInstaller
pyinstaller ^
    --onefile ^
    --windowed ^
    --name "LicenseGenerator" ^
    --icon=NONE ^
    --add-data "rsa_keys;rsa_keys" ^
    --clean ^
    license_generator_gui.py

if errorlevel 1 (
    echo.
    echo [ERROR] Build failed!
    pause
    exit /b 1
)

echo.
echo ============================================
echo   BUILD SUCCESSFUL!
echo ============================================
echo.
echo Executable: dist\LicenseGenerator.exe
echo.
echo To use:
echo   1. Copy dist\LicenseGenerator.exe to anywhere
echo   2. Make sure rsa_keys folder is in same directory
echo   3. Double-click to run
echo.

REM Copy rsa_keys to dist folder
echo [*] Copying RSA keys to dist folder...
xcopy /E /I /Y rsa_keys dist\rsa_keys

echo.
echo [DONE] Ready to distribute!
echo.
pause
