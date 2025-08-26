@echo off
setlocal ENABLEDELAYEDEXPANSION

REM =====================================================
REM  run.bat — Double-click Windows launcher
REM  Professional Ideas Visualizer
REM  Mirrors run.sh (create .venv, install deps, run.py)
REM =====================================================

chcp 65001 >NUL
title Professional Ideas Visualizer — Launcher
cd /d "%~dp0"

echo ============================================================
echo  ✨ PROFESSIONAL FLOATING IDEAS VISUALIZER — Windows Launcher
echo ============================================================

set "VENV_DIR=.venv"
set "VENV_PY=%VENV_DIR%\Scripts\python.exe"

REM ---- Find a system Python (prefer py launcher) ----
set "PY_CMD="
where py >NUL 2>&1 && (set "PY_CMD=py -3")
if not defined PY_CMD (
  where python >NUL 2>&1 && (set "PY_CMD=python")
)

if not defined PY_CMD (
  echo [error] Python 3 not found in PATH.
  echo         Please install Python 3 from https://www.python.org/ and try again.
  echo.
  pause
  exit /b 1
)

REM ---- Create venv if missing ----
if not exist "%VENV_PY%" (
  echo [setup] Creating virtual environment: %VENV_DIR%
  %PY_CMD% -m venv "%VENV_DIR%"
  if errorlevel 1 (
    echo [error] Failed to create virtual environment.
    echo.
    pause
    exit /b 1
  )

  echo [setup] Upgrading pip, setuptools, wheel ...
  "%VENV_PY%" -m pip install --upgrade pip setuptools wheel

  if exist requirements.txt (
    echo [setup] Installing requirements from requirements.txt ...
    "%VENV_PY%" -m pip install -r requirements.txt
    if errorlevel 1 (
      echo [error] pip install failed. Check your internet connection and requirements.
      echo.
      pause
      exit /b 1
    )
  ) else (
    echo [setup] No requirements.txt found — skipping dependency install.
  )
) else (
  echo [setup] Using existing virtual environment: %VENV_DIR%
)

echo [launcher] Interpreter: %VENV_PY%
echo [launcher] Starting run.py ...
echo ------------------------------------------------------------

"%VENV_PY%" run.py
set "EXITCODE=%ERRORLEVEL%"

echo ------------------------------------------------------------
if "%EXITCODE%"=="0" (
  echo [done] run.py exited successfully.
) else (
  echo [done] run.py exited with code %EXITCODE%.
)

echo.
echo (Press any key to close this window)
pause >NUL
endlocal