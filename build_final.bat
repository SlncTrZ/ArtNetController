@echo off
echo ================================================
echo Building DMX Master - Final Version
echo ================================================
echo.

REM Activate venv if needed
REM call venv\Scripts\activate.bat

echo Cleaning previous build...
if exist "build" rmdir /s /q build
if exist "dist" rmdir /s /q dist
if exist "DMXMaster.spec" del DMXMaster.spec

echo.
echo Building executable with all required modules...
echo.

pyinstaller --clean --onefile --windowed ^
    --name DMXMaster ^
    --icon assets\DMXMaster.ico ^
    --add-data "assets;assets" ^
    --add-data "src;src" ^
    --add-data "config;config" ^
    --add-data "data;data" ^
    --hidden-import logging.handlers ^
    --hidden-import platform ^
    --hidden-import socket ^
    --hidden-import subprocess ^
    --hidden-import threading ^
    --hidden-import time ^
    --hidden-import json ^
    --hidden-import os ^
    --hidden-import sys ^
    --hidden-import hashlib ^
    --hidden-import uuid ^
    --hidden-import base64 ^
    --hidden-import shutil ^
    --hidden-import pathlib ^
    --hidden-import datetime ^
    --hidden-import typing ^
    --hidden-import struct ^
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

dir dist\DMXMaster.exe

echo.
echo Testing executable...
echo Running DMXMaster.exe in background...
start "" "dist\DMXMaster.exe"

timeout /t 5 /nobreak >nul

echo.
echo If app opened successfully, press any key to continue...
echo If app failed, check error and rebuild.
echo.

pause
