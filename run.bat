@echo off
REM ============================
REM run.bat — Double-click launcher (Windows)
REM - cd to this script's directory
REM - call Python on run.py
REM ============================

setlocal enabledelayedexpansion

REM Move to the folder this .bat lives in
cd /d "%~dp0"

REM Prefer the Python launcher 'py -3', fallback to 'python'
where py >NUL 2>&1
if %errorlevel%==0 (
  set "PY=py -3"
) else (
  where python >NUL 2>&1
  if %errorlevel%==0 (
    set "PY=python"
  ) else (
    echo Python 3 is not installed or not in PATH.
    echo Please install Python 3, then double-click this file again.
    pause
    exit /b 1
  )
)

%PY% run.py

echo.
echo (Press any key to close this window)
pause >NUL
