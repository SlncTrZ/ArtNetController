@echo off
echo ================================================
echo DMX Master - Build Installer
echo ================================================
echo.

REM Check if Inno Setup is installed
set "INNO_PATH=C:\Program Files (x86)\Inno Setup 6\ISCC.exe"

if not exist "%INNO_PATH%" (
    echo ERROR: Inno Setup not found!
    echo.
    echo Please download and install Inno Setup from:
    echo https://jrsoftware.org/isdl.php
    echo.
    echo Default installation path should be:
    echo C:\Program Files ^(x86^)\Inno Setup 6\ISCC.exe
    echo.
    pause
    exit /b 1
)

REM Check if executable exists
if not exist "dist\DMXMaster.exe" (
    echo ERROR: DMXMaster.exe not found!
    echo.
    echo Please build the executable first by running:
    echo   build.bat
    echo.
    pause
    exit /b 1
)

REM Create output directory
if not exist "installer_output" mkdir installer_output

REM Build installer
echo Building installer with Inno Setup...
echo.
"%INNO_PATH%" DMXMaster_Setup.iss

if errorlevel 1 (
    echo.
    echo ================================================
    echo INSTALLER BUILD FAILED!
    echo ================================================
    pause
    exit /b 1
)

echo.
echo ================================================
echo INSTALLER BUILD SUCCESSFUL!
echo ================================================
echo.
echo Installer location:
dir /B installer_output\DMXMaster_Setup_*.exe
echo.
echo This installer includes:
echo   - Auto-update detection
echo   - User data preservation
echo   - Desktop shortcut option
echo   - Uninstaller with data keep option
echo   - Professional installation wizard
echo.
echo You can now distribute this installer!
echo.

pause
