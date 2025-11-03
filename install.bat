@echo off
REM Install script for Art-Net Controller on Windows

echo Installing Art-Net Controller...

REM Create virtual environment
python -m venv venv

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Upgrade pip
python -m pip install --upgrade pip

REM Install requirements
pip install -r requirements.txt

echo Installation complete!
echo.
echo To run the application:
echo 1. Activate virtual environment:
echo    venv\Scripts\activate.bat
echo 2. Run the application:
echo    python run.py
echo.
echo Or simply:
echo    python main.py

pause