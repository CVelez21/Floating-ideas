#!/usr/bin/env bash
# ============================
# run.sh — Double-click launcher (macOS/Linux)
# Ensures .venv exists, installs requirements if missing,
# then runs run.py using that venv.
# ============================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Pick venv path
VENV_DIR="$SCRIPT_DIR/.venv"
PYTHON_BIN="python3"

# Create venv if it doesn't exist
if [ ! -d "$VENV_DIR" ]; then
  echo "[setup] No venv found, creating at $VENV_DIR"
  $PYTHON_BIN -m venv "$VENV_DIR"
  echo "[setup] Upgrading pip..."
  "$VENV_DIR/bin/python" -m pip install --upgrade pip
  echo "[setup] Installing requirements..."
  if [ -f requirements.txt ]; then
    "$VENV_DIR/bin/python" -m pip install -r requirements.txt
  fi
fi

# Always use venv python
PY="$VENV_DIR/bin/python"
echo "[launcher] using: $($PY -c 'import sys; print(sys.executable)')"

# Run launcher
exec "$PY" run.py