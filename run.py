#!/usr/bin/env python3
# ============================
# run.py
# One-command launcher for Floating Ideas
# - Loads .env (if present) and/or environment variables
# - Ensures EVENT_PIN is set (prompt if not)
# - Installs requirements (unless SKIP_PIP=1)
# - Detects LAN IP, sets IDEAS_API
# - Generates intake QR code PNG (if 'qrcode' installed)
# - Starts: FastAPI backend, Streamlit intake (optional), Pygame wall (optional)
# - Clean shutdown on Ctrl+C
# ============================

import os
import sys
import socket
import subprocess
import time
from pathlib import Path

# Optional: QR code support
try:
    import qrcode
    QR_AVAILABLE = True
except Exception:
    QR_AVAILABLE = False


def load_dotenv(dotenv_path: Path) -> None:
    """
    Minimal .env loader (KEY=VALUE lines; ignores comments and blanks).
    Does not override existing environment variables.
    """
    if not dotenv_path.exists():
        return
    try:
        for raw in dotenv_path.read_text(encoding="utf-8").splitlines():
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            if "=" not in line:
                continue
            key, val = line.split("=", 1)
            key = key.strip()
            v = val.strip().strip('"').strip("'")
            if key and key not in os.environ:
                os.environ[key] = v
    except Exception:
        # Silently continue if .env can't be parsed
        pass


def find_free_port(start_port: int) -> int:
    """
    Find the first available TCP port at or above start_port.
    """
    port = start_port
    while True:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                s.bind(("", port))
                return port
            except OSError:
                port += 1


def get_lan_ip() -> str:
    """
    Determine LAN IP via UDP connect trick; fall back to localhost.
    """
    ip = "127.0.0.1"
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
    except Exception:
        pass
    finally:
        try:
            s.close()
        except Exception:
            pass
    return ip


def ensure_reqs(repo_root: Path, env: dict) -> None:
    """
    Install requirements.txt if modules appear missing (unless SKIP_PIP=1).
    """
    if env.get("SKIP_PIP", "0") in ("1", "true", "True"):
        return

    missing = []

    def _chk(mod: str) -> bool:
        try:
            __import__(mod)
            return False
        except Exception:
            return True

    core_mods = ["fastapi", "uvicorn", "requests", "pygame", "websockets", "streamlit"]
    for m in core_mods:
        if _chk(m):
            missing.append(m)

    if not missing and (not env.get("FORCE_PIP")):
        return

    req = repo_root / "requirements.txt"
    if req.exists():
        cmd = [sys.executable, "-m", "pip", "install", "-r", str(req)]
    else:
        cmd = [
            sys.executable, "-m", "pip", "install",
            *core_mods, "qrcode", "pillow", "python-multipart", "pydantic"
        ]

    print("[setup] Installing dependencies via pip...")
    try:
        subprocess.check_call(cmd)
    except subprocess.CalledProcessError as e:
        print(f"[setup] pip install encountered an error (continuing): {e}")


def ensure_data_dir(repo_root: Path) -> None:
    (repo_root / "data").mkdir(parents=True, exist_ok=True)


def make_qr_png(url: str, out_path: Path) -> None:
    """
    Generate QR code PNG for the provided URL, if qrcode is installed.
    """
    if not QR_AVAILABLE:
        return
    try:
        img = qrcode.make(url)
        img.save(out_path)
    except Exception:
        pass


def main() -> None:
    """
    Launch backend, Streamlit, and wall after preparing environment.
    """
    repo_root = Path(__file__).resolve().parent
    os.chdir(repo_root)

    # Load .env (if present) before reading env
    load_dotenv(repo_root / ".env")

    # Ensure dependencies
    ensure_reqs(repo_root, os.environ.copy())

    # Detect IP and choose ports (use env or defaults)
    lan_ip = get_lan_ip()
    backend_port = int(os.environ.get("BACKEND_PORT", "8000"))
    streamlit_port = int(os.environ.get("STREAMLIT_PORT", "8501"))

    # Compose base URL and set IDEAS_API for children
    base_url = f"http://{lan_ip}:{backend_port}"
    env = os.environ.copy()
    env["IDEAS_API"] = env.get("IDEAS_API", base_url)

    # Ensure EVENT_PIN (env/.env preferred; else prompt with default 1234)
    pin = env.get("EVENT_PIN", "").strip()
    if not pin:
        try:
            print("EVENT_PIN not set. Enter a numeric PIN (press Enter for 1234): ", end="", flush=True)
            user_in = input().strip()
            pin = user_in or "1234"
        except Exception:
            pin = "1234"
        env["EVENT_PIN"] = pin

    # Allow disabling components
    run_streamlit = env.get("RUN_STREAMLIT", "1") not in ("0", "false", "False")
    run_wall = env.get("RUN_WALL", "1") not in ("0", "false", "False")

    # Ensure data directory exists
    ensure_data_dir(repo_root)

    # Generate QR code for the intake URL
    # ----------------------------
    # QR target selection (env: QR_TARGET=html|streamlit)
    # ----------------------------
    qr_path = repo_root / "submit-ideas-qr.png"
    qr_target = os.environ.get("QR_TARGET", "html").lower()
    if qr_target == "streamlit":
        qr_url = f"http://{lan_ip}:{streamlit_port}/"
    else:
        qr_url = f"{base_url}/"

    # Generate QR code for the selected target
    make_qr_png(qr_url, qr_path)

    # Commands
    py = sys.executable or "python"
    backend_cmd = [py, "-m", "uvicorn", "backend.app:app", "--host", "0.0.0.0", "--port", str(backend_port)]
    streamlit_cmd = [
        py, "-m", "streamlit", "run", "streamlit_app/submit.py",
        "--server.port", str(streamlit_port),
        "--server.headless", "true",
    ]
    wall_cmd = [py, "-m", "wall.main"]

    procs = []

    try:
        # Start backend
        print(f"[backend] starting on {base_url} (EVENT_PIN={env['EVENT_PIN']})")
        procs.append(subprocess.Popen(backend_cmd, env=env))

        # Give it a moment to bind
        time.sleep(1.2)

        # Start Streamlit (optional)
        if run_streamlit:
            print(f"[streamlit] starting at http://{lan_ip}:{streamlit_port}/")
            procs.append(subprocess.Popen(streamlit_cmd, env=env))

        # Start wall (optional)
        if run_wall:
            print("[wall] starting...")
            procs.append(subprocess.Popen(wall_cmd, env=env))

        # Friendly banner
        print("\n================= Floating Ideas — Ready =================")
        print(f" Submit (HTML):      {base_url}/")
        if run_streamlit:
            print(f" Submit (Streamlit): http://{lan_ip}:{streamlit_port}/")
        print(f" Export CSV:         {base_url}/export.csv")
        print(f" Export JSON:        {base_url}/export.json")
        print(f" WebSocket:          {base_url.replace('http','ws')}/ws")
        print(f" IDEAS_API:          {env['IDEAS_API']}")
        print(f" EVENT_PIN:          {env['EVENT_PIN']}")
        if qr_path.exists():
            print(f" QR code saved:      {qr_path}")
            print(f" QR points to:       {qr_url}")
        else:
            print(" QR code:            (install 'qrcode' to auto-generate)")
        print(" Ctrl+C to stop everything cleanly.")
        print("==========================================================\n")

        # Wait until children exit
        while True:
            alive = False
            for p in procs:
                if p.poll() is None:
                    alive = True
            if not alive:
                break
            time.sleep(0.5)

    except KeyboardInterrupt:
        print("\n[shutdown] Ctrl+C received, terminating...")
    finally:
        # Terminate all children
        for p in procs:
            try:
                if p and p.poll() is None:
                    p.terminate()
            except Exception:
                pass
        time.sleep(0.8)
        for p in procs:
            try:
                if p and p.poll() is None:
                    p.kill()
            except Exception:
                pass
        print("[shutdown] all processes stopped.")


if __name__ == "__main__":
    main()