@echo off
echo ================================================
echo Building DMX Master with Simple PyInstaller
echo ================================================
echo.

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

echo.
echo Building executable with detailed hidden imports...
pyinstaller --onefile ^
    --windowed ^
    --name DMXMaster ^
    --icon assets\DMXMaster.ico ^
    --add-data "assets;assets" ^
    --add-data "src;src" ^
    --add-data "config;config" ^
    --add-data "data;data" ^
    --hidden-import PyQt6 ^
    --hidden-import PyQt6.QtCore ^
    --hidden-import PyQt6.QtGui ^
    --hidden-import PyQt6.QtWidgets ^
    --hidden-import PyQt6.QtNetwork ^
    --hidden-import PyQt6.sip ^
    --hidden-import cryptography ^
    --hidden-import cryptography.fernet ^
    --hidden-import cryptography.hazmat ^
    --hidden-import cryptography.hazmat.primitives ^
    --hidden-import cryptography.hazmat.primitives.asymmetric ^
    --hidden-import cryptography.hazmat.primitives.asymmetric.rsa ^
    --hidden-import cryptography.hazmat.primitives.asymmetric.padding ^
    --hidden-import cryptography.hazmat.primitives.hashes ^
    --hidden-import cryptography.hazmat.primitives.serialization ^
    --hidden-import cryptography.hazmat.primitives.ciphers ^
    --hidden-import cryptography.hazmat.primitives.ciphers.aead ^
    --hidden-import cryptography.hazmat.primitives.kdf ^
    --hidden-import cryptography.hazmat.primitives.kdf.pbkdf2 ^
    --hidden-import cryptography.hazmat.backends ^
    --hidden-import cryptography.hazmat.backends.openssl ^
    --hidden-import flask ^
    --hidden-import flask_cors ^
    --hidden-import werkzeug ^
    --hidden-import werkzeug.serving ^
    --hidden-import jinja2 ^
    --hidden-import click ^
    --hidden-import pygame ^
    --hidden-import pygame.mixer ^
    --hidden-import tzdata ^
    --hidden-import tzdata.zoneinfo ^
    --collect-all PyQt6 ^
    --collect-all pygame ^
    --collect-all cryptography ^
    --clean ^
    main.py

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

dir dist\DMXMaster.exe

pause
