@echo off
setlocal EnableDelayedExpansion
title SecureStream — Encrypted Camera Server

:: =========================================================
::  SecureStream start script
::  Launches the AES-128-GCM encrypted camera streaming app.
::  Run this file from any location — it adjusts the CWD.
:: =========================================================

:: Move to the directory containing this script
cd /d "%~dp0"

echo.
echo  ================================================================
echo   SecureStream  ^|  AES-128-GCM Encrypted Camera Server
echo  ================================================================
echo.

:: ----------------------------------------------------------
::  1. Verify Python is on PATH
:: ----------------------------------------------------------
where python >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo  [ERROR] Python was not found on your PATH.
    echo          Install Python 3.9+ from https://python.org and ensure
    echo          "Add Python to PATH" is checked during installation.
    echo.
    pause
    exit /b 1
)

for /f "tokens=*" %%v in ('python --version 2^>^&1') do set PY_VER=%%v
echo  [OK] Found %PY_VER%

:: ----------------------------------------------------------
::  2. Check required packages
:: ----------------------------------------------------------
echo  [..] Checking dependencies...
python -c "import flask, cv2, cryptography" >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo  [..] Installing missing packages...
    pip install flask opencv-python cryptography qrcode pillow --quiet
    if %ERRORLEVEL% neq 0 (
        echo  [ERROR] Package installation failed. Check your internet connection
        echo          or run:  pip install flask opencv-python cryptography
        echo.
        pause
        exit /b 1
    )
    echo  [OK] Packages installed.
) else (
    echo  [OK] All dependencies satisfied.
)

:: ----------------------------------------------------------
::  3. Navigate to the Flask app directory
:: ----------------------------------------------------------
cd /d "%~dp0UI_based_webcam"

:: ----------------------------------------------------------
::  4. Generate TLS certificate if missing
:: ----------------------------------------------------------
if not exist "server_certificate.crt" (
    echo.
    echo  [..] SSL certificate not found. Generating a self-signed certificate...
    python setup_certs.py
    if %ERRORLEVEL% neq 0 (
        echo  [ERROR] Certificate generation failed. See output above.
        echo.
        pause
        exit /b 1
    )
) else (
    echo  [OK] SSL certificate present.
)

if not exist "key.pem" (
    echo.
    echo  [..] Private key not found. Re-generating certificate...
    python setup_certs.py
)

:: ----------------------------------------------------------
::  5. Create default password file if missing
:: ----------------------------------------------------------
if not exist "streampassword.txt" (
    echo  [..] Creating default password file (admin123)...
    echo admin123> streampassword.txt
    echo  [OK] Default password set: admin123
    echo       Change it immediately after first login via the Reset page.
)

:: ----------------------------------------------------------
::  6. Launch the Flask server
:: ----------------------------------------------------------
echo.
echo  ================================================================
echo   Starting server...
echo   Open your browser and navigate to https://localhost:5000
echo   Default password: admin123
echo  ================================================================
echo.

python stream.py

:: If the server exits for any reason, keep the window open
echo.
echo  [SERVER STOPPED]
pause
