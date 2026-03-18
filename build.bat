@echo off
setlocal

echo ============================================================
echo  Password Manager - Build Script
echo ============================================================
echo.

:: ── Step 1: PyInstaller ─────────────────────────────────────
echo [1/2] Building executable with PyInstaller...
echo.
pyinstaller pwapp.spec --clean --noconfirm

if errorlevel 1 (
    echo.
    echo ERROR: PyInstaller failed. Aborting.
    pause
    exit /b 1
)

echo.
echo PyInstaller build successful.
echo Output: dist\PasswordManager.exe
echo.

:: ── Step 2: Inno Setup ──────────────────────────────────────
echo [2/2] Building installer with Inno Setup...
echo.

:: Common Inno Setup compiler paths
set ISCC=""
if exist "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" (
    set ISCC="C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
) else if exist "C:\Program Files\Inno Setup 6\ISCC.exe" (
    set ISCC="C:\Program Files\Inno Setup 6\ISCC.exe"
) else if exist "C:\Program Files (x86)\Inno Setup 5\ISCC.exe" (
    set ISCC="C:\Program Files (x86)\Inno Setup 5\ISCC.exe"
)

if %ISCC%=="" (
    echo ERROR: Inno Setup compiler (ISCC.exe) not found.
    echo Please install Inno Setup from https://jrsoftware.org/isinfo.php
    echo or add ISCC.exe to your PATH.
    pause
    exit /b 1
)

%ISCC% installer.iss

if errorlevel 1 (
    echo.
    echo ERROR: Inno Setup compilation failed.
    pause
    exit /b 1
)

echo.
echo ============================================================
echo  Done!
echo  Installer: installer_output\PasswordManagerSetup_1.0.0.exe
echo ============================================================
echo.
pause
