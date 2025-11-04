@echo off
echo ================================================
echo Building DMX Master Executable
echo ================================================
echo.

REM Activate virtual environment if exists
if exist venv\Scripts\activate.bat (
    echo Activating virtual environment...
    call venv\Scripts\activate.bat
)

REM Check if PyInstaller is installed
python -c "import PyInstaller" 2>nul
if errorlevel 1 (
    echo PyInstaller not found. Installing...
    pip install pyinstaller
)

REM Clean previous build
echo.
echo Cleaning previous build...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

REM Build with spec file
echo.
echo Building executable...
pyinstaller --clean DMXMaster_Complete.spec

if errorlevel 1 (
    echo.
    echo ================================================
    echo BUILD FAILED!
    echo ================================================
    pause
    exit /b 1
)

echo.
echo ================================================
echo BUILD SUCCESSFUL!
echo ================================================
echo.
echo Executable location: dist\DMXMaster.exe
echo.
echo You can now run the application by double-clicking:
echo   dist\DMXMaster.exe
echo.

pause
