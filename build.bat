@echo off
REM Build DMXMaster - Wrapper script
REM Calls the actual build script in scripts folder

cd /d "%~dp0"
call scripts\build.bat
