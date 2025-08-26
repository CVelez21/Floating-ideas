# ============================
# streamlit_app/submit.py
# Floating Ideas — Staff Intake with PIN Gate (PIN once per tab)
# ============================

# ----------------------------
# Imports
# ----------------------------
import os  # env vars (IDEAS_API)
import requests  # HTTP client for backend
import streamlit as st  # UI

# ----------------------------
# Config helpers
# ----------------------------
def get_api_base() -> str:
    """
    @brief  Resolve backend base URL from env or default.
    @return Base URL string (e.g., 'http://127.0.0.1:8000').
    """
    base = os.environ.get("IDEAS_API", "http://127.0.0.1:8000").rstrip("/")
    return base

API_BASE = get_api_base()

# ----------------------------
# Backend API helpers
# ----------------------------
def post_idea(author: str, text: str, pin: str) -> dict:
    """
    @brief  POST a new idea to the backend.
    @param  author  Name string.
    @param  text    Idea text.
    @param  pin     Event PIN (required by backend).
    @return Dict with 'ok' or 'error' keys.
    """
    # Build payload
    data = {"author": author, "text": text, "pin": pin}

    try:
        resp = requests.post(f"{API_BASE}/ideas", data=data, timeout=10)
        if resp.ok:
            # Expecting {"ok": true} or {"ok": false, "error": "..."}
            try:
                j = resp.json()
                return j if isinstance(j, dict) else {"ok": True}
            except Exception:
                return {"ok": True}
        return {"ok": False, "error": f"HTTP {resp.status_code}"}
    except Exception as e:
        return {"ok": False, "error": f"Network error: {e}"}

def get_count() -> int:
    """
    @brief  Fetch current idea count from backend.
    @return Count int, or -1 on failure.
    """
    try:
        resp = requests.get(f"{API_BASE}/ideas", timeout=10)
        if resp.ok:
            j = resp.json()
            return len(j) if isinstance(j, list) else -1
    except Exception:
        pass
    return -1

# ----------------------------
# Streamlit page configuration
# ----------------------------
st.set_page_config(page_title="Submit an Idea", page_icon="💡", layout="centered")

# ----------------------------
# PIN Gate (login-like)
# ----------------------------
if "event_pin_ok" not in st.session_state:
    st.session_state["event_pin_ok"] = False

if not st.session_state["event_pin_ok"]:
    st.title("Enter Event PIN")

    # PIN input
    pin_input = st.text_input("Event PIN", type="password")

    # Button to submit the PIN
    if st.button("Enter"):
        if pin_input.strip():
            # Store PIN and allow access (backend still validates on POST)
            st.session_state["event_pin"] = pin_input.strip()
            st.session_state["event_pin_ok"] = True
            st.rerun()
        else:
            st.error("Please enter a PIN.")

    # Show API for debugging
    with st.expander("Connection details", expanded=False):
        st.caption(f"Backend: {API_BASE}")
    st.stop()

# ----------------------------
# Main idea submission form (visible after PIN gate)
# ----------------------------
st.title("Submit an Idea")

with st.form("idea_form", clear_on_submit=False):
    # Author + idea fields
    author = st.text_input("Your name", placeholder="e.g., Jordan")
    text = st.text_area("Your idea", placeholder="Share your idea", height=120)

    # Submit button
    submit = st.form_submit_button("Submit")

    if submit:
        # Resolve PIN from session
        pin = st.session_state.get("event_pin", "").strip()

        # Basic validation
        if not pin:
            st.error("PIN missing. Refresh and enter the PIN again.")
        elif not author.strip() or not text.strip():
            st.error("Please fill in your name and idea.")
        else:
            # Post to backend
            result = post_idea(author.strip(), text.strip(), pin)
            if result.get("ok"):
                st.success("Idea submitted — thank you!")
                # Keep author for rapid entries, clear idea text
                st.session_state["idea_form-text"] = ""
            else:
                st.error(result.get("error", "Unknown error"))

# ----------------------------
# Footer: live idea count
# ----------------------------
count = get_count()
if count >= 0:
    st.caption(f"Ideas so far: **{count}**")
else:
    st.caption("Ideas so far: —")