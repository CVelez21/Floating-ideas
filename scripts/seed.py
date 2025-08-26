# ============================
# scripts/seed.py
# Seed the backend with sample ideas via HTTP POST
# ============================

# Imports: os/env, requests for HTTP, time for pacing
import os
import time
import requests


API_BASE = os.environ.get("IDEAS_API", "http://127.0.0.1:8000")
EVENT_PIN = os.environ.get("EVENT_PIN", "1234")

SAMPLES = [
    ("Avery",  "Use AI to auto-summarize customer interviews."),
    ("Jordan", "Generate slide outlines from meeting notes automatically."),
    ("Kai",    "AI assistant for onboarding new hires with tailored checklists."),
    ("Riley",  "Real-time anomaly detection for sales dashboards."),
]


def post(author: str, text: str) -> None:
    """
    @brief  Submit one idea to POST /ideas using env EVENT_PIN.
    """
    payload = {"author": author, "text": text, "pin": EVENT_PIN}
    r = requests.post(f"{API_BASE}/ideas", data=payload, timeout=5)
    try:
        j = r.json()
    except Exception:
        j = {"ok": False, "error": f"HTTP {r.status_code}"}
    status = "ok" if j.get("ok") else f"err: {j.get('error')}"
    print(f"[seed] {author}: {status}")


def main() -> None:
    """
    @brief  Iterate SAMPLES and submit each with a short delay.
    """
    for a, t in SAMPLES:
        post(a, t)
        time.sleep(0.2)


if __name__ == "__main__":
    main()