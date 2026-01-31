@echo off
setlocal

echo ========================================
echo Checking for Calibre processes...
echo ========================================
echo.
echo 1. Checking with tasklist:
tasklist | findstr /i "calibre" || echo No Calibre processes found.

echo.
echo 2. Checking with wmic:
wmic process where "name like '%%calibre%%'" get name 2>nul | findstr /v "Name" || echo No Calibre processes found.

echo.
echo 3. Checking all processes (showing first 50):
tasklist | head -n 50
echo.
echo ========================================