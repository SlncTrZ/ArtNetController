@echo off
echo ================================================
echo DMX Master - Creating Deployment Package
echo ================================================
echo.

set DEPLOY_DIR=DMXMaster_Deploy
set TIMESTAMP=%DATE:~10,4%%DATE:~4,2%%DATE:~7,2%

REM Clean old deploy folder
if exist %DEPLOY_DIR% (
    echo Cleaning old deployment folder...
    rmdir /s /q %DEPLOY_DIR%
)

REM Create deployment structure
echo Creating deployment structure...
mkdir %DEPLOY_DIR%
mkdir %DEPLOY_DIR%\assets
mkdir %DEPLOY_DIR%\data
mkdir %DEPLOY_DIR%\data\shows
mkdir %DEPLOY_DIR%\data\audio

REM Copy executable
echo.
echo Copying executable...
copy dist\DMXMaster.exe %DEPLOY_DIR%\DMXMaster.exe

REM Copy assets
echo Copying assets...
xcopy /E /I /Y assets %DEPLOY_DIR%\assets

REM Copy data (shows and audio)
echo Copying data files...
if exist data\shows (
    xcopy /E /I /Y data\shows %DEPLOY_DIR%\data\shows
)
if exist data\audio (
    xcopy /E /I /Y data\audio %DEPLOY_DIR%\data\audio
)

REM Copy documentation
echo Copying documentation...
copy DEPLOYMENT.md %DEPLOY_DIR%\README.txt

REM Create run shortcut info
echo Creating quick start file...
(
echo ================================
echo DMX MASTER - QUICK START
echo ================================
echo.
echo 1. Double-click DMXMaster.exe to start
echo.
echo 2. First run will create config and logs folders
echo.
echo 3. Default timezone: UTC ^(change in Settings menu^)
echo.
echo 4. Trial period: 7 days
echo.
echo 5. For license activation:
echo    - Help ^> License Activation
echo    - Copy Device ID
echo    - Send to: truongcongdinh97tcd@gmail.com
echo.
echo ================================
echo SUPPORT
echo ================================
echo Email: truongcongdinh97tcd@gmail.com
echo.
echo Press any key to close...
pause ^> nul
) > %DEPLOY_DIR%\QUICK_START.txt

REM Create zip archive
echo.
echo Creating ZIP archive...
powershell Compress-Archive -Path %DEPLOY_DIR% -DestinationPath DMXMaster_%TIMESTAMP%.zip -Force

echo.
echo ================================================
echo DEPLOYMENT PACKAGE CREATED!
echo ================================================
echo.
echo Package location:
echo   - Folder: %DEPLOY_DIR%\
echo   - ZIP: DMXMaster_%TIMESTAMP%.zip
echo.
echo Ready to deploy to another computer!
echo.
echo Contents:
dir /B %DEPLOY_DIR%
echo.

pause
