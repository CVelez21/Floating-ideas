# ============================
# scripts/make_qr.py
# Generate a QR code PNG for the intake URL
# ============================

# Imports: qrcode for QR, os for env, pathlib for paths
import os
from pathlib import Path

# Imports: qrcode makes it easy to render a PNG
import qrcode


def build_intake_url() -> str:
    """
    @brief  Compute the intake URL for QR generation.
    @return Full URL string to the backend form (e.g., http://192.168.1.23:8000/).
    """
    # Read from env if set, else fallback to localhost
    base = os.environ.get("IDEAS_API", "http://127.0.0.1:8000").rstrip("/")
    # Root path serves the HTML form
    return f"{base}/"


def main() -> None:
    """
    @brief  Render the QR PNG to ./submit-ideas-qr.png and print the path.
    """
    # Determine output path in repo root
    out_path = Path(__file__).resolve().parent.parent / "submit-ideas-qr.png"

    # Build the target URL
    url = build_intake_url()

    # Create QR image from URL
    img = qrcode.make(url)

    # Save PNG file
    img.save(out_path)

    # Notify user on stdout
    print(f"[ok] QR saved to: {out_path}")
    print(f"     Points to:     {url}")


if __name__ == "__main__":
    main()