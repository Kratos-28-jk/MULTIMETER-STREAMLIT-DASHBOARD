@echo off
REM Automated Deployment Script for SECURE ELITE 440 Dashboard
REM This script helps you deploy to GitHub and Streamlit Cloud

echo ========================================
echo  SECURE ELITE 440 Dashboard
echo  Automated Deployment Helper
echo ========================================
echo.

REM Check if Git is installed
git --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Git is not installed!
    echo Please install Git from: https://git-scm.com/downloads
    pause
    exit /b 1
)

echo Step 1: Checking current status...
git status

echo.
echo ========================================
echo Step 2: Adding files to Git...
echo ========================================
git add .

echo.
echo Step 3: Committing changes...
set /p commit_msg="Enter commit message (or press Enter for default): "
if "%commit_msg%"=="" set commit_msg=Update dashboard

git commit -m "%commit_msg%"

echo.
echo ========================================
echo Step 4: Pushing to GitHub...
echo ========================================
echo.
echo Make sure you have:
echo 1. Created a repository on GitHub
echo 2. Added the remote: git remote add origin https://github.com/USERNAME/REPO.git
echo.
set /p push_confirm="Push to GitHub? (y/n): "

if /i "%push_confirm%"=="y" (
    git push
    if errorlevel 1 (
        echo.
        echo Push failed! Make sure you have:
        echo 1. Set up remote: git remote add origin YOUR_REPO_URL
        echo 2. Authenticated with GitHub
        echo.
        echo To set up remote, run:
        echo git remote add origin https://github.com/USERNAME/REPO.git
        pause
        exit /b 1
    )
    echo.
    echo ========================================
    echo  SUCCESS! Code pushed to GitHub
    echo ========================================
    echo.
    echo Next steps:
    echo 1. Go to https://share.streamlit.io
    echo 2. Click "New app"
    echo 3. Select your repository
    echo 4. Set main file to: app.py
    echo 5. Click Deploy!
    echo.
    echo Your app will be live in 2-5 minutes!
    echo ========================================
) else (
    echo Push cancelled.
)

echo.
pause