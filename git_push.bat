@echo off
REM =========================================
REM Git Setup & Push to GitHub (Windows)
REM Repository: https://github.com/truongcongdinh97/DMX-Master
REM =========================================

echo.
echo ========================================
echo   Git Setup for DMX-Master Project
echo ========================================
echo.

REM Check Git installation
git --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Git not installed!
    echo Download from: https://git-scm.com/downloads
    pause
    exit /b 1
)

REM Step 1: Initialize Git (if not already)
if not exist ".git" (
    echo [1/6] Initializing Git repository...
    git init
    echo   SUCCESS: Git initialized
) else (
    echo [1/6] Git repository already exists
)

REM Step 2: Configure Git user
echo [2/6] Configuring Git user...
git config user.name "Truong Cong Dinh"
git config user.email "truongcongdinh97@gmail.com"
echo   SUCCESS: Git user configured

REM Step 3: Add remote (if not already)
git remote | findstr "origin" >nul
if errorlevel 1 (
    echo [3/6] Adding GitHub remote...
    git remote add origin https://github.com/truongcongdinh97/DMX-Master.git
    echo   SUCCESS: Remote added
) else (
    echo [3/6] Remote already exists
    git remote -v
)

REM Step 4: Stage all files (respecting .gitignore)
echo [4/6] Staging files...
git add .
echo   SUCCESS: Files staged

REM Step 5: Show what will be committed
echo.
echo Files to be committed:
git status --short
echo.

REM Step 6: Commit
echo [5/6] Creating commit...
set /p commit_msg="Enter commit message (or press Enter for default): "
if "%commit_msg%"=="" set commit_msg=🚀 Upload DMX-Master project with advanced license system

git commit -m "%commit_msg%"
echo   SUCCESS: Committed

REM Step 7: Push to GitHub
echo [6/6] Pushing to GitHub...
echo.
echo WARNING: You will be prompted for GitHub credentials
echo    Use Personal Access Token instead of password
echo    Generate at: https://github.com/settings/tokens
echo.
pause

git push -u origin main

if errorlevel 1 (
    echo.
    echo ========================================
    echo   PUSH FAILED!
    echo ========================================
    echo.
    echo Common issues:
    echo 1. Wrong credentials
    echo 2. Need to create Personal Access Token
    echo 3. Repository doesn't exist on GitHub
    echo.
    echo Solutions:
    echo 1. Go to https://github.com/settings/tokens
    echo 2. Generate new token (classic^)
    echo 3. Select 'repo' scope
    echo 4. Copy token and use as password
    echo.
    pause
    exit /b 1
)

echo.
echo ========================================
echo   SUCCESS!
echo ========================================
echo.
echo Project uploaded to:
echo https://github.com/truongcongdinh97/DMX-Master
echo.
pause
