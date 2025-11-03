@echo off
REM ============================================
REM Package License Generator for Distribution
REM ============================================

echo.
echo ============================================
echo   PACKAGING LICENSE GENERATOR
echo ============================================
echo.

cd /d "%~dp0"

REM Check if exe exists
if not exist "dist\LicenseGenerator.exe" (
    echo [ERROR] LicenseGenerator.exe not found!
    echo Please run build_license_generator.bat first
    pause
    exit /b 1
)

REM Create package folder
set PACKAGE_NAME=LicenseGenerator_v1.0.0
if exist "%PACKAGE_NAME%" (
    echo [*] Cleaning old package...
    rmdir /s /q "%PACKAGE_NAME%"
)

mkdir "%PACKAGE_NAME%"

echo [*] Copying files...
copy "dist\LicenseGenerator.exe" "%PACKAGE_NAME%\" >nul
copy "dist\README.txt" "%PACKAGE_NAME%\" >nul

echo [*] Creating generated_licenses folder...
mkdir "%PACKAGE_NAME%\generated_licenses"
echo # License files will be saved here > "%PACKAGE_NAME%\generated_licenses\.gitkeep"

echo [*] Creating ZIP archive...
powershell -Command "Compress-Archive -Path '%PACKAGE_NAME%\*' -DestinationPath '%PACKAGE_NAME%.zip' -Force"

if exist "%PACKAGE_NAME%.zip" (
    echo.
    echo ============================================
    echo   PACKAGE CREATED SUCCESSFULLY!
    echo ============================================
    echo.
    echo Package: %PACKAGE_NAME%.zip
    echo Size: 
    powershell -Command "(Get-Item '%PACKAGE_NAME%.zip').Length / 1MB | ForEach-Object { '{0:N2} MB' -f $_ }"
    echo.
    echo Contents:
    echo   - LicenseGenerator.exe
    echo   - README.txt
    echo   - generated_licenses\
    echo.
    echo Ready to distribute!
    echo.
) else (
    echo [ERROR] Failed to create ZIP
)

pause
