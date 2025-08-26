# ================================
# backend/app.py
# FastAPI backend — now with:
# 1) PIN-protected submissions (ENV: EVENT_PIN)
# 2) WebSocket broadcast on new ideas (/ws)
# 3) CSV/JSON persistence and simple header config
# ================================

import os
import csv
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Set

from fastapi import FastAPI, Form, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse
from fastapi.middleware.cors import CORSMiddleware

# --- Paths & Constants ---
DATA_DIR = Path(__file__).parent.parent / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)
CSV_PATH = DATA_DIR / "ideas.csv"
JSON_PATH = DATA_DIR / "ideas.json"
HEADER_TEXT_PATH = DATA_DIR / "header.txt"
DEFAULT_HEADER = "What ways can we use AI?"
EVENT_PIN = os.environ.get("EVENT_PIN", "")  # empty = no PIN required

# Initialize files if missing
if not CSV_PATH.exists():
    with CSV_PATH.open("w", newline="") as f:
        csv.writer(f).writerow(["id", "author", "text", "created_at"])  # header row
if not JSON_PATH.exists():
    JSON_PATH.write_text("[]", encoding="utf-8")
if not HEADER_TEXT_PATH.exists():
    HEADER_TEXT_PATH.write_text(DEFAULT_HEADER, encoding="utf-8")

# --- App ---
app = FastAPI(title="Ideas Wall (Single Event)")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- In-memory cache ---
_cache: List[Dict[str, Any]] = []


def load_all() -> List[Dict[str, Any]]:
    try:
        return json.loads(JSON_PATH.read_text(encoding="utf-8"))
    except Exception:
        return []


def save_all(items: List[Dict[str, Any]]):
    JSON_PATH.write_text(json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8")


def append_csv(row: List[str]):
    with CSV_PATH.open("a", newline="") as f:
        csv.writer(f).writerow(row)

# --- WebSocket manager ---
class WSManager:
    def __init__(self):
        self.active: Set[WebSocket] = set()

    async def connect(self, ws: WebSocket):
        await ws.accept()
        self.active.add(ws)

    def disconnect(self, ws: WebSocket):
        self.active.discard(ws)

    async def broadcast_json(self, payload: Any):
        dead = []
        for ws in list(self.active):
            try:
                await ws.send_json(payload)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(ws)

ws_manager = WSManager()

# --- Routes ---
@app.get("/", response_class=HTMLResponse)
async def intake_form():
    html = (Path(__file__).parent / "submit.html").read_text(encoding="utf-8")
    return HTMLResponse(content=html)

@app.get("/ideas")
async def get_ideas():
    return load_all()

@app.post("/ideas")
async def post_idea(author: str = Form(...), text: str = Form(...), pin: str = Form("")):
    if EVENT_PIN and pin != EVENT_PIN:
        return JSONResponse({"ok": False, "error": "Invalid PIN."}, status_code=401)
    author = author.strip()
    text = text.strip()
    if not author or not text:
        return JSONResponse({"ok": False, "error": "Missing name or idea."}, status_code=400)
    items = load_all()
    new = {
        "id": (items[-1]["id"] + 1) if items else 1,
        "author": author,
        "text": text,
        "created_at": datetime.now().isoformat(timespec="seconds"),
    }
    items.append(new)
    save_all(items)
    append_csv([new["id"], new["author"], new["text"], new["created_at"]])
    await ws_manager.broadcast_json({"type": "idea.new", "data": new})
    return {"ok": True, "idea": new}

@app.get("/export.csv")
async def export_csv():
    return PlainTextResponse(CSV_PATH.read_text(encoding="utf-8"), media_type="text/csv")

@app.get("/export.json")
async def export_json():
    return JSONResponse(load_all())

@app.get("/header")
async def get_header():
    return {"header": HEADER_TEXT_PATH.read_text(encoding="utf-8").strip()}

@app.post("/header")
async def set_header(text: str = Form(...)):
    HEADER_TEXT_PATH.write_text(text.strip(), encoding="utf-8")
    await ws_manager.broadcast_json({"type": "header.set", "data": text.strip()})
    return {"ok": True}

@app.websocket("/ws")
async def ws_endpoint(ws: WebSocket):
    await ws_manager.connect(ws)
    try:
        # Send initial state on connect
        await ws.send_json({"type": "hello", "data": {
            "header": HEADER_TEXT_PATH.read_text(encoding="utf-8").strip(),
            "ideas": load_all()
        }})
        while True:
            # We don't expect client messages; keep alive
            await ws.receive_text()
    except WebSocketDisconnect:
        ws_manager.disconnect(ws)
    except Exception:
        ws_manager.disconnect(ws)

# ================================

import os
import csv
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Set

from fastapi import FastAPI, Form, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse
from fastapi.middleware.cors import CORSMiddleware

# --- Paths & Constants ---
DATA_DIR = Path(__file__).parent.parent / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)
CSV_PATH = DATA_DIR / "ideas.csv"
JSON_PATH = DATA_DIR / "ideas.json"
HEADER_TEXT_PATH = DATA_DIR / "header.txt"
DEFAULT_HEADER = "What ways can we use AI?"
EVENT_PIN = os.environ.get("EVENT_PIN", "")  # empty = no PIN required

# Initialize files if missing
if not CSV_PATH.exists():
    with CSV_PATH.open("w", newline="") as f:
        csv.writer(f).writerow(["id", "author", "text", "created_at"])  # header row
if not JSON_PATH.exists():
    JSON_PATH.write_text("[]", encoding="utf-8")
if not HEADER_TEXT_PATH.exists():
    HEADER_TEXT_PATH.write_text(DEFAULT_HEADER, encoding="utf-8")

# --- App ---
app = FastAPI(title="Ideas Wall (Single Event)")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- In-memory cache ---
_cache: List[Dict[str, Any]] = []


def load_all() -> List[Dict[str, Any]]:
    try:
        return json.loads(JSON_PATH.read_text(encoding="utf-8"))
    except Exception:
        return []


def save_all(items: List[Dict[str, Any]]):
    JSON_PATH.write_text(json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8")


def append_csv(row: List[str]):
    with CSV_PATH.open("a", newline="") as f:
        csv.writer(f).writerow(row)

# --- WebSocket manager ---
class WSManager:
    def __init__(self):
        self.active: Set[WebSocket] = set()

    async def connect(self, ws: WebSocket):
        await ws.accept()
        self.active.add(ws)

    def disconnect(self, ws: WebSocket):
        self.active.discard(ws)

    async def broadcast_json(self, payload: Any):
        dead = []
        for ws in list(self.active):
            try:
                await ws.send_json(payload)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(ws)

ws_manager = WSManager()

# --- Routes ---
@app.get("/", response_class=HTMLResponse)
async def intake_form():
    html = (Path(__file__).parent / "submit.html").read_text(encoding="utf-8")
    return HTMLResponse(content=html)

@app.get("/ideas")
async def get_ideas():
    return load_all()

@app.post("/ideas")
async def post_idea(author: str = Form(...), text: str = Form(...), pin: str = Form("")):
    if EVENT_PIN and pin != EVENT_PIN:
        return JSONResponse({"ok": False, "error": "Invalid PIN."}, status_code=401)
    author = author.strip()
    text = text.strip()
    if not author or not text:
        return JSONResponse({"ok": False, "error": "Missing name or idea."}, status_code=400)
    items = load_all()
    new = {
        "id": (items[-1]["id"] + 1) if items else 1,
        "author": author,
        "text": text,
        "created_at": datetime.now().isoformat(timespec="seconds"),
    }
    items.append(new)
    save_all(items)
    append_csv([new["id"], new["author"], new["text"], new["created_at"]])
    await ws_manager.broadcast_json({"type": "idea.new", "data": new})
    return {"ok": True, "idea": new}

@app.get("/export.csv")
async def export_csv():
    return PlainTextResponse(CSV_PATH.read_text(encoding="utf-8"), media_type="text/csv")

@app.get("/export.json")
async def export_json():
    return JSONResponse(load_all())

@app.get("/header")
async def get_header():
    return {"header": HEADER_TEXT_PATH.read_text(encoding="utf-8").strip()}

@app.post("/header")
async def set_header(text: str = Form(...)):
    HEADER_TEXT_PATH.write_text(text.strip(), encoding="utf-8")
    await ws_manager.broadcast_json({"type": "header.set", "data": text.strip()})
    return {"ok": True}

@app.websocket("/ws")
async def ws_endpoint(ws: WebSocket):
    await ws_manager.connect(ws)
    try:
        # Send initial state on connect
        await ws.send_json({"type": "hello", "data": {
            "header": HEADER_TEXT_PATH.read_text(encoding="utf-8").strip(),
            "ideas": load_all()
        }})
        while True:
            # We don't expect client messages; keep alive
            await ws.receive_text()
    except WebSocketDisconnect:
        ws_manager.disconnect(ws)
    except Exception:
        ws_manager.disconnect(ws)

# ================================

import os
import csv
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Set

from fastapi import FastAPI, Form, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse
from fastapi.middleware.cors import CORSMiddleware

# --- Paths & Constants ---
DATA_DIR = Path(__file__).parent.parent / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)
CSV_PATH = DATA_DIR / "ideas.csv"
JSON_PATH = DATA_DIR / "ideas.json"
HEADER_TEXT_PATH = DATA_DIR / "header.txt"
DEFAULT_HEADER = "What ways can we use AI?"
EVENT_PIN = os.environ.get("EVENT_PIN", "")  # empty = no PIN required

# Initialize files if missing
if not CSV_PATH.exists():
    with CSV_PATH.open("w", newline="") as f:
        csv.writer(f).writerow(["id", "author", "text", "created_at"])  # header row
if not JSON_PATH.exists():
    JSON_PATH.write_text("[]", encoding="utf-8")
if not HEADER_TEXT_PATH.exists():
    HEADER_TEXT_PATH.write_text(DEFAULT_HEADER, encoding="utf-8")

# --- App ---
app = FastAPI(title="Ideas Wall (Single Event)")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- In-memory cache ---
_cache: List[Dict[str, Any]] = []


def load_all() -> List[Dict[str, Any]]:
    try:
        return json.loads(JSON_PATH.read_text(encoding="utf-8"))
    except Exception:
        return []


def save_all(items: List[Dict[str, Any]]):
    JSON_PATH.write_text(json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8")


def append_csv(row: List[str]):
    with CSV_PATH.open("a", newline="") as f:
        csv.writer(f).writerow(row)

# --- WebSocket manager ---
class WSManager:
    def __init__(self):
        self.active: Set[WebSocket] = set()

    async def connect(self, ws: WebSocket):
        await ws.accept()
        self.active.add(ws)

    def disconnect(self, ws: WebSocket):
        self.active.discard(ws)

    async def broadcast_json(self, payload: Any):
        dead = []
        for ws in list(self.active):
            try:
                await ws.send_json(payload)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(ws)

ws_manager = WSManager()

# --- Routes ---
@app.get("/", response_class=HTMLResponse)
async def intake_form():
    html = (Path(__file__).parent / "submit.html").read_text(encoding="utf-8")
    return HTMLResponse(content=html)

@app.get("/ideas")
async def get_ideas():
    return load_all()

@app.post("/ideas")
async def post_idea(author: str = Form(...), text: str = Form(...), pin: str = Form("")):
    if EVENT_PIN and pin != EVENT_PIN:
        return JSONResponse({"ok": False, "error": "Invalid PIN."}, status_code=401)
    author = author.strip()
    text = text.strip()
    if not author or not text:
        return JSONResponse({"ok": False, "error": "Missing name or idea."}, status_code=400)
    items = load_all()
    new = {
        "id": (items[-1]["id"] + 1) if items else 1,
        "author": author,
        "text": text,
        "created_at": datetime.now().isoformat(timespec="seconds"),
    }
    items.append(new)
    save_all(items)
    append_csv([new["id"], new["author"], new["text"], new["created_at"]])
    await ws_manager.broadcast_json({"type": "idea.new", "data": new})
    return {"ok": True, "idea": new}

@app.get("/export.csv")
async def export_csv():
    return PlainTextResponse(CSV_PATH.read_text(encoding="utf-8"), media_type="text/csv")

@app.get("/export.json")
async def export_json():
    return JSONResponse(load_all())

@app.get("/header")
async def get_header():
    return {"header": HEADER_TEXT_PATH.read_text(encoding="utf-8").strip()}

@app.post("/header")
async def set_header(text: str = Form(...)):
    HEADER_TEXT_PATH.write_text(text.strip(), encoding="utf-8")
    await ws_manager.broadcast_json({"type": "header.set", "data": text.strip()})
    return {"ok": True}

@app.websocket("/ws")
async def ws_endpoint(ws: WebSocket):
    await ws_manager.connect(ws)
    try:
        # Send initial state on connect
        await ws.send_json({"type": "hello", "data": {
            "header": HEADER_TEXT_PATH.read_text(encoding="utf-8").strip(),
            "ideas": load_all()
        }})
        while True:
            # We don't expect client messages; keep alive
            await ws.receive_text()
    except WebSocketDisconnect:
        ws_manager.disconnect(ws)
    except Exception:
        ws_manager.disconnect(ws)

# ================================

import os
import csv
import json
from datetime import datetime
from pathlib import Path
from typing import List

from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

DATA_DIR = Path(__file__).parent.parent / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)
CSV_PATH = DATA_DIR / "ideas.csv"
JSON_PATH = DATA_DIR / "ideas.json"
HEADER_TEXT_PATH = DATA_DIR / "header.txt"
DEFAULT_HEADER = "What ways can we use AI?"

# Initialize files if missing
if not CSV_PATH.exists():
    with CSV_PATH.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["id", "author", "text", "created_at"])  # header row

if not JSON_PATH.exists():
    with JSON_PATH.open("w") as f:
        json.dump([], f)

if not HEADER_TEXT_PATH.exists():
    HEADER_TEXT_PATH.write_text(DEFAULT_HEADER, encoding="utf-8")

app = FastAPI(title="Ideas Wall (Single Event)")

# Allow local devices on same network to POST
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"];
    allow_headers=["*"],
)

class IdeaIn(BaseModel):
    author: str = Field(min_length=1, max_length=80)
    text: str = Field(min_length=3, max_length=500)

class IdeaOut(IdeaIn):
    id: int
    created_at: str

# Simple in-memory cache for quick reads (source of truth is files)
_cache: List[IdeaOut] = []


def load_all() -> List[IdeaOut]:
    global _cache
    try:
        raw = json.loads(JSON_PATH.read_text(encoding="utf-8"))
        _cache = [IdeaOut(**o) for o in raw]
    except Exception:
        _cache = []
    return _cache


def append_idea(i: IdeaOut) -> None:
    # Append to CSV
    with CSV_PATH.open("a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([i.id, i.author, i.text, i.created_at])
    # Append to JSON (read-modify-write for simplicity)
    items = load_all()
    items.append(i)
    with JSON_PATH.open("w") as f:
        json.dump([o.dict() for o in items], f, ensure_ascii=False, indent=2)


@app.get("/", response_class=HTMLResponse)
async def intake_form():
    # Serve minimal intake form (no JS build toolchain) from embedded string
    return HTMLResponse(content=(Path(__file__).parent / "submit.html").read_text(encoding="utf-8"))


@app.get("/ideas")
async def get_ideas():
    items = load_all()
    return [o.dict() for o in items]


@app.post("/ideas")
async def post_idea(author: str = Form(...), text: str = Form(...)):
    author = author.strip()
    text = text.strip()
    if not author or not text:
        return JSONResponse({"ok": False, "error": "Missing name or idea."}, status_code=400)
    items = load_all()
    new = IdeaOut(
        id=(items[-1].id + 1) if items else 1,
        author=author,
        text=text,
        created_at=datetime.now().isoformat(timespec="seconds")
    )
    append_idea(new)
    return {"ok": True, "idea": new.dict()}


@app.get("/export.csv")
async def export_csv():
    return PlainTextResponse(CSV_PATH.read_text(encoding="utf-8"), media_type="text/csv")


@app.get("/export.json")
async def export_json():
    return JSONResponse(json.loads(JSON_PATH.read_text(encoding="utf-8")))


@app.get("/header")
async def get_header():
    return {"header": HEADER_TEXT_PATH.read_text(encoding="utf-8").strip()}


@app.post("/header")
async def set_header(text: str = Form(...)):
    HEADER_TEXT_PATH.write_text(text.strip(), encoding="utf-8")
    return {"ok": True}


# ================================
# backend/submit.html
# Minimal mobile-friendly intake form (now includes a PIN field)
# ================================

# <!doctype html>
# <html lang="en">
# <head>
#   <meta charset="utf-8" />
#   <meta name="viewport" content="width=device-width, initial-scale=1" />
#   <title>Submit an Idea</title>
#   <style>
#     body { font-family: system-ui, -apple-system, Segoe UI, Roboto, sans-serif; margin: 20px; }
#     .card { max-width: 520px; margin: 0 auto; padding: 18px; border-radius: 14px; box-shadow: 0 8px 30px rgba(0,0,0,.08); }
#     h1 { font-size: 22px; margin: 0 0 14px; }
#     label { display:block; font-weight:600; margin: 12px 0 6px; }
#     input, textarea { width:100%; padding:10px; border:1px solid #ddd; border-radius:10px; font-size:16px; }
#     button { margin-top:14px; width:100%; padding:12px; border:0; border-radius:12px; font-size:16px; font-weight:700; }
#     .ok { background:#0ea5e9; color:white; }
#     .msg { text-align:center; margin-top:10px; font-weight:600; }
#   </style>
# </head>
# <body>
#   <div class="card">
#     <h1>Submit an Idea</h1>
#     <form id="f">
#       <label for="author">Your name</label>
#       <input id="author" name="author" placeholder="e.g., Jordan" required />
#       <label for="text">Your idea</label>
#       <textarea id="text" name="text" rows="4" placeholder="Share your idea" required></textarea>
#       <label for="pin">Event PIN</label>
#       <input id="pin" name="pin" type="password" inputmode="numeric" placeholder="4-6 digits" required />
#       <button class="ok" type="submit">Submit</button>
#       <div class="msg" id="m"></div>
#     </form>
#   </div>
# <script>
# const form = document.getElementById('f');
# const msg = document.getElementById('m');
# form.addEventListener('submit', async (e) => {
#   e.preventDefault();
#   const data = new FormData(form);
#   try {
#     const res = await fetch('/ideas', { method: 'POST', body: data });
#     const j = await res.json();
#     if (j.ok) {
#       msg.textContent = 'Idea submitted — thank you!';
#       msg.style.color = '#16a34a';
#       form.reset();
#     } else {
#       msg.textContent = j.error || 'Submission failed.';
#       msg.style.color = '#ef4444';
#     }
#   } catch (err) {
#     msg.textContent = 'Network error.';
#     msg.style.color = '#ef4444';
#   }
# });
# </script>
# </body>
# </html>

# ================================

# <!doctype html>
# <html lang="en">
# <head>
#   <meta charset="utf-8" />
#   <meta name="viewport" content="width=device-width, initial-scale=1" />
#   <title>Submit an Idea</title>
#   <style>
#     body { font-family: system-ui, -apple-system, Segoe UI, Roboto, sans-serif; margin: 20px; }
#     .card { max-width: 520px; margin: 0 auto; padding: 18px; border-radius: 14px; box-shadow: 0 8px 30px rgba(0,0,0,.08); }
#     h1 { font-size: 22px; margin: 0 0 14px; }
#     label { display:block; font-weight:600; margin: 12px 0 6px; }
#     input, textarea { width:100%; padding:10px; border:1px solid #ddd; border-radius:10px; font-size:16px; }
#     button { margin-top:14px; width:100%; padding:12px; border:0; border-radius:12px; font-size:16px; font-weight:700; }
#     .ok { background:#0ea5e9; color:white; }
#     .msg { text-align:center; margin-top:10px; font-weight:600; }
#   </style>
# </head>
# <body>
#   <div class="card">
#     <h1>Submit an Idea</h1>
#     <form id="f">
#       <label for="author">Your name</label>
#       <input id="author" name="author" placeholder="e.g., Jordan" required />
#       <label for="text">Your idea</label>
#       <textarea id="text" name="text" rows="4" placeholder="Share your idea" required></textarea>
#       <label for="pin">Event PIN</label>
#       <input id="pin" name="pin" type="password" inputmode="numeric" placeholder="4-6 digits" required />
#       <button class="ok" type="submit">Submit</button>
#       <div class="msg" id="m"></div>
#     </form>
#   </div>
# <script>
# const form = document.getElementById('f');
# const msg = document.getElementById('m');
# form.addEventListener('submit', async (e) => {
#   e.preventDefault();
#   const data = new FormData(form);
#   try {
#     const res = await fetch('/ideas', { method: 'POST', body: data });
#     const j = await res.json();
#     if (j.ok) {
#       msg.textContent = 'Idea submitted — thank you!';
#       msg.style.color = '#16a34a';
#       form.reset();
#     } else {
#       msg.textContent = j.error || 'Submission failed.';
#       msg.style.color = '#ef4444';
#     }
#   } catch (err) {
#     msg.textContent = 'Network error.';
#     msg.style.color = '#ef4444';
#   }
# });
# </script>
# </body>
# </html>

# ================================

# <!doctype html>
# <html lang="en">
# <head>
#   <meta charset="utf-8" />
#   <meta name="viewport" content="width=device-width, initial-scale=1" />
#   <title>Submit an Idea</title>
#   <style>
#     body { font-family: system-ui, -apple-system, Segoe UI, Roboto, sans-serif; margin: 20px; }
#     .card { max-width: 520px; margin: 0 auto; padding: 18px; border-radius: 14px; box-shadow: 0 8px 30px rgba(0,0,0,.08); }
#     h1 { font-size: 22px; margin: 0 0 14px; }
#     label { display:block; font-weight:600; margin: 12px 0 6px; }
#     input, textarea { width:100%; padding:10px; border:1px solid #ddd; border-radius:10px; font-size:16px; }
#     button { margin-top:14px; width:100%; padding:12px; border:0; border-radius:12px; font-size:16px; font-weight:700; }
#     .ok { background:#0ea5e9; color:white; }
#     .msg { text-align:center; margin-top:10px; font-weight:600; }
#   </style>
# </head>
# <body>
#   <div class="card">
#     <h1>Submit an Idea</h1>
#     <form id="f">
#       <label for="author">Your name</label>
#       <input id="author" name="author" placeholder="e.g., Jordan" required />
#       <label for="text">Your idea</label>
#       <textarea id="text" name="text" rows="4" placeholder="Share your idea" required></textarea>
#       <label for="pin">Event PIN</label>
#       <input id="pin" name="pin" type="password" inputmode="numeric" placeholder="4-6 digits" required />
#       <button class="ok" type="submit">Submit</button>
#       <div class="msg" id="m"></div>
#     </form>
#   </div>
# <script>
# const form = document.getElementById('f');
# const msg = document.getElementById('m');
# form.addEventListener('submit', async (e) => {
#   e.preventDefault();
#   const data = new FormData(form);
#   try {
#     const res = await fetch('/ideas', { method: 'POST', body: data });
#     const j = await res.json();
#     if (j.ok) {
#       msg.textContent = 'Idea submitted — thank you!';
#       msg.style.color = '#16a34a';
#       form.reset();
#     } else {
#       msg.textContent = j.error || 'Submission failed.';
#       msg.style.color = '#ef4444';
#     }
#   } catch (err) {
#     msg.textContent = 'Network error.';
#     msg.style.color = '#ef4444';
#   }
# });
# </script>
# </body>
# </html>

# ================================

# (Saved next to app.py)

# <!doctype html>
# <html lang="en">
# <head>
#   <meta charset="utf-8" />
#   <meta name="viewport" content="width=device-width, initial-scale=1" />
#   <title>Submit an Idea</title>
#   <style>
#     body { font-family: system-ui, -apple-system, Segoe UI, Roboto, sans-serif; margin: 20px; }
#     .card { max-width: 520px; margin: 0 auto; padding: 18px; border-radius: 14px; box-shadow: 0 8px 30px rgba(0,0,0,.08); }
#     h1 { font-size: 22px; margin: 0 0 14px; }
#     label { display:block; font-weight:600; margin: 12px 0 6px; }
#     input, textarea { width:100%; padding:10px; border:1px solid #ddd; border-radius:10px; font-size:16px; }
#     button { margin-top:14px; width:100%; padding:12px; border:0; border-radius:12px; font-size:16px; font-weight:700; }
#     .ok { background:#0ea5e9; color:white; }
#     .err{ background:#ef4444; color:white; }
#     .msg { text-align:center; margin-top:10px; font-weight:600; }
#   </style>
# </head>
# <body>
#   <div class="card">
#     <h1>Submit an Idea</h1>
#     <form id="f">
#       <label for="author">Your name</label>
#       <input id="author" name="author" placeholder="e.g., Jordan" required />
#       <label for="text">Your idea</label>
#       <textarea id="text" name="text" rows="4" placeholder="Share your idea" required></textarea>
#       <button class="ok" type="submit">Submit</button>
#       <div class="msg" id="m"></div>
#     </form>
#   </div>
# <script>
# const form = document.getElementById('f');
# const msg = document.getElementById('m');
# form.addEventListener('submit', async (e) => {
#   e.preventDefault();
#   const data = new FormData(form);
#   try {
#     const res = await fetch('/ideas', { method: 'POST', body: data });
#     const j = await res.json();
#     if (j.ok) {
#       msg.textContent = 'Idea submitted — thank you!';
#       msg.style.color = '#16a34a';
#       form.reset();
#     } else {
#       msg.textContent = j.error || 'Submission failed.';
#       msg.style.color = '#ef4444';
#     }
#   } catch (err) {
#     msg.textContent = 'Network error.';
#     msg.style.color = '#ef4444';
#   }
# });
# </script>
# </body>
# </html>


# ================================
# wall/main.py
# Pygame Display Wall — Showcase Edition (clean, calm, professional)
# - Smooth drift (no arcade bounce) using gentle sinusoidal vectors
# - Elegant typography with word-wrap, margins, and consistent spacing
# - Spotlight effect with subtle glow + scale (accessible, non-distracting)
# - Collision light-resolve to reduce overlaps (good for small idea counts)
# - Responsive to window resize; header centered; idea count footer
# ================================

import os
import math
import time
import random
import typing as t
import threading

# Importing requests to communicate with the backend API
import requests

# Importing pygame for rendering the showcase wall
import pygame

# ---------------------------------
# Configuration Variables
# ---------------------------------
# Defining the backend API base URL (overridable by environment variable)
API_BASE: str = os.environ.get("IDEAS_API", "http://127.0.0.1:8000")

# Defining the initial window size for a 16:9 screen
WIDTH: int = 1920
HEIGHT: int = 1080

# Defining frames per second target for smooth motion
FPS: int = 60

# Defining the spotlight cycle duration in seconds
SPOTLIGHT_PERIOD: float = 7.0

# Defining how often to poll the backend for new ideas
POLL_SEC: float = 5.0

# Defining the visual theme colors (calm, professional palette)
BG_TOP: t.Tuple[int,int,int] = (9, 13, 24)        # Dark navy
BG_BOTTOM: t.Tuple[int,int,int] = (21, 29, 45)    # Slightly lighter navy
ACCENT: t.Tuple[int,int,int] = (93, 196, 255)     # Soft cyan
TEXT_MAIN: t.Tuple[int,int,int] = (235, 242, 255) # Near-white
TEXT_SUB: t.Tuple[int,int,int] = (168, 179, 196)  # Muted grey-blue
SPOT_GLOW: t.Tuple[int,int,int] = (93, 196, 255)  # Same as accent for consistency

# Defining layout margins and spacing
MARGIN_X: int = 80
HEADER_Y: int = 90
FOOTER_Y_MARGIN: int = 60
MAX_TEXT_WIDTH_RATIO: float = 0.42   # Each idea wraps to ~42% of screen width

# Defining motion parameters (gentle drift)
DRIFT_SPEED: float = 12.0            # Pixels per second base
DRIFT_VARIANCE: float = 0.6          # Scales per-idea drift differences
BOB_AMPLITUDE: float = 8.0           # Minor vertical bob in pixels

# Defining spotlight visual parameters
SPOT_SCALE_MAX: float = 1.28         # Max scale during spotlight
SPOT_GLOW_RADIUS: int = 8            # Pixel glow radius
SPOT_GLOW_ALPHA: int = 60            # Transparency for the glow

# Defining overlap resolution parameters (very light touch)
RESOLVE_STEPS: int = 1               # Small n^2 pushes each frame (low counts only)
RESOLVE_PUSH: float = 0.25           # Pixels per step
RESOLVE_MIN_DIST: int = 28           # Approx min vertical separation between baselines

# ---------------------------------
# Runtime State
# ---------------------------------
# Initializing pygame and the window (resizable for venue screens)
pygame.init()
window = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
clock = pygame.time.Clock()

# Selecting professional fonts (fallback to Arial if unavailable)
HEADER_FONT = pygame.font.SysFont("Helvetica Neue, Helvetica, Arial", 64, bold=True)
IDEA_FONT_BASE = pygame.font.SysFont("Helvetica Neue, Helvetica, Arial", 28)
AUTHOR_FONT = pygame.font.SysFont("Helvetica Neue, Helvetica, Arial", 22)
FOOTER_FONT = pygame.font.SysFont("Helvetica Neue, Helvetica, Arial", 20)

# Setting header text default
DEFAULT_HEADER: str = "What ways can we use AI?"

# Storing header and ideas fetched from backend
header_text: str = DEFAULT_HEADER
ideas: t.List[t.Dict[str, t.Any]] = []

# ---------------------------------
# Helper Functions (Declarations)
# ---------------------------------
# Declaring a function to draw a vertical gradient background
def draw_gradient_background(surface: pygame.Surface, top: t.Tuple[int,int,int], bottom: t.Tuple[int,int,int]) -> None: ...

# Declaring a function to wrap a text string into multiple lines
def wrap_text(text: str, font: pygame.font.Font, max_width: int) -> t.List[pygame.Surface]: ...

# Declaring a function to softly resolve overlaps between idea boxes
def resolve_overlaps(rects: t.List[pygame.Rect]) -> None: ...

# Declaring a function to fetch header and ideas in a background thread
def fetch_loop() -> None: ...

# Declaring a function to render a subtle glow under spotlight text
def blit_glow(surface: pygame.Surface, text_surface: pygame.Surface, pos: t.Tuple[int,int]) -> None: ...

# Declaring a function to create a nicely padded idea surface (text + author)
def render_idea_block(text: str, author: str, scale: float) -> pygame.Surface: ...

# Declaring a function to update drifted positions based on time
def update_positions(dt: float) -> None: ...

# ---------------------------------
# Idea Bubble Class (Data + Motion)
# ---------------------------------
class IdeaBubble:
    # Declaring the initializer with typed fields
    def __init__(self, idea: t.Dict[str, t.Any]):
        # Storing the idea dict
        self.idea: t.Dict[str, t.Any] = idea
        # Computing per-idea horizontal band based on index for pleasant distribution
        idx = (idea.get('id', 0) or 0)
        bands = max(3, 6)
        band = idx % bands
        band_height = (HEIGHT - HEADER_Y - FOOTER_Y_MARGIN - 160) / bands
        y_base = HEADER_Y + 120 + band * band_height
        # Choosing an initial position with margins
        self.x: float = random.uniform(MARGIN_X, WIDTH - MARGIN_X)
        self.y: float = random.uniform(y_base - 40, y_base + 40)
        # Assigning a stable drift direction based on seeded random
        rng = random.Random(idx * 1337)
        angle = rng.uniform(-math.pi/4, math.pi/4)
        speed = DRIFT_SPEED * (1.0 + rng.uniform(-DRIFT_VARIANCE, DRIFT_VARIANCE))
        self.dx: float = math.cos(angle) * speed
        self.dy: float = math.sin(angle) * speed
        # Assigning a gentle bobbing phase/frequency
        self.phase: float = rng.uniform(0, 2 * math.pi)
        self.freq: float = rng.uniform(0.2, 0.45)
        # Initializing the render scale (modified by spotlight)
        self.scale: float = 1.0
        # Caching last-rendered surface for performance
        self.cache_text: str = ""
        self.cache_author: str = ""
        self.cache_scale: float = 0.0
        self.cache_surface: t.Optional[pygame.Surface] = None
        self.rect: pygame.Rect = pygame.Rect(0,0,0,0)

    # Declaring a method to update the bubble's position
    def update(self, dt: float) -> None:
        # Advancing position with gentle drift
        self.x += self.dx * dt
        self.y += self.dy * dt
        # Adding a subtle vertical bob using a sine wave
        self.y += math.sin(self.phase + time.time() * self.freq) * (BOB_AMPLITUDE * dt)
        # Constraining within margins softly by reflecting drift when near edges
        if self.x < MARGIN_X:
            self.x = MARGIN_X
            self.dx = abs(self.dx)
        if self.x > WIDTH - MARGIN_X:
            self.x = WIDTH - MARGIN_X
            self.dx = -abs(self.dx)
        if self.y < HEADER_Y + 80:
            self.y = HEADER_Y + 80
            self.dy = abs(self.dy)
        if self.y > HEIGHT - FOOTER_Y_MARGIN - 80:
            self.y = HEIGHT - FOOTER_Y_MARGIN - 80
            self.dy = -abs(self.dy)

    # Declaring a method to get the rendered block (with caching)
    def get_surface(self) -> pygame.Surface:
        # Reading the current idea text and author
        t_text = self.idea.get('text', '')
        t_author = self.idea.get('author', '')
        # Returning cached surface if text/author/scale unchanged
        if self.cache_surface and t_text == self.cache_text and t_author == self.cache_author and abs(self.scale - self.cache_scale) < 1e-3:
            return self.cache_surface
        # Rendering a new block surface when needed
        surf = render_idea_block(t_text, t_author, self.scale)
        # Updating cache values for next time
        self.cache_surface = surf
        self.cache_text = t_text
        self.cache_author = t_author
        self.cache_scale = self.scale
        return surf

# Creating the bubbles container
bubbles: t.List[IdeaBubble] = []

# Declaring spotlight state variables
spot_index: int = 0
spot_t: float = 0.0

# ---------------------------------
# Background Fetch Thread
# ---------------------------------
# Creating a thread target for polling header and ideas from the backend

def fetch_loop() -> None:
    # Declaring last seen id set for lightweight change detection
    last_ids: t.Set[int] = set()
    # Starting an infinite loop for periodic polling
    while True:
        try:
            # Fetching the header text from backend
            ht = requests.get(f"{API_BASE}/header", timeout=5).json().get("header", DEFAULT_HEADER)
            # Updating global header text
            globals()['header_text'] = ht
            # Fetching the ideas list from backend
            items = requests.get(f"{API_BASE}/ideas", timeout=5).json()
            # Converting ids to a set for comparison
            cur_ids = {int(i['id']) for i in items} if items else set()
            # Rebuilding bubbles only if the set of ideas changed (simple + robust)
            if cur_ids != last_ids:
                globals()['ideas'] = items
                globals()['bubbles'] = [IdeaBubble(i) for i in items]
                last_ids = cur_ids
        except Exception:
            # Silently ignoring transient network errors to keep the wall running
            pass
        # Sleeping before the next poll
        time.sleep(POLL_SEC)

# Spawning the fetcher background thread as daemon
fetcher = threading.Thread(target=fetch_loop, daemon=True)
fetcher.start()

# ---------------------------------
# Helper Implementations
# ---------------------------------
# Implementing the gradient background drawing helper

def draw_gradient_background(surface: pygame.Surface, top: t.Tuple[int,int,int], bottom: t.Tuple[int,int,int]) -> None:
    # Getting surface width and height
    w, h = surface.get_size()
    # Iterating over vertical lines to draw the gradient
    for y in range(h):
        # Computing interpolation factor for the current row
        tval = y / max(1, h - 1)
        # Interpolating RGB components between top and bottom colors
        r = int(top[0] + (bottom[0] - top[0]) * tval)
        g = int(top[1] + (bottom[1] - top[1]) * tval)
        b = int(top[2] + (bottom[2] - top[2]) * tval)
        # Drawing a horizontal line for this gradient step
        pygame.draw.line(surface, (r, g, b), (0, y), (w, y))

# Implementing the text wrapping helper

def wrap_text(text: str, font: pygame.font.Font, max_width: int) -> t.List[pygame.Surface]:
    # Splitting input text into words
    words = text.split()
    # Preparing containers for lines and current line words
    lines: t.List[str] = []
    current: t.List[str] = []
    # Iterating over each word to assemble wrapped lines
    for w in words:
        # Considering the candidate line with this word
        candidate = (" ".join(current + [w])).strip()
        # Measuring the candidate width
        width, _ = font.size(candidate)
        # Deciding to wrap if the candidate exceeds max width
        if width > max_width and current:
            # Pushing the current line to lines
            lines.append(" ".join(current))
            # Starting a new line with the current word
            current = [w]
        else:
            # Continuing the current line with the word
            current.append(w)
    # Appending any trailing line
    if current:
        lines.append(" ".join(current))
    # Rendering each line to a surface and returning the list
    return [font.render(line, True, TEXT_MAIN) for line in lines]

# Implementing a tiny overlap resolver to reduce overdraw

def resolve_overlaps(rects: t.List[pygame.Rect]) -> None:
    # Repeating a small number of relaxation steps
    for _ in range(RESOLVE_STEPS):
        # Iterating over all rect pairs (n^2, OK for small sets)
        for i in range(len(rects)):
            for j in range(i + 1, len(rects)):
                # Accessing the two rects
                a = rects[i]
                b = rects[j]
                # Checking intersection
                if a.colliderect(b):
                    # Computing a small separating vector
                    dx = (a.centerx - b.centerx)
                    dy = (a.centery - b.centery)
                    # Avoiding zero-length vector
                    if dx == 0 and dy == 0:
                        dx = 1
                    # Normalizing the vector length
                    dist = math.hypot(dx, dy)
                    nx = dx / dist
                    ny = dy / dist
                    # Applying opposing pushes to each rect
                    a.move_ip(nx * RESOLVE_PUSH, ny * RESOLVE_PUSH)
                    b.move_ip(-nx * RESOLVE_PUSH, -ny * RESOLVE_PUSH)

# Implementing a glow blit for spotlight emphasis

def blit_glow(surface: pygame.Surface, text_surface: pygame.Surface, pos: t.Tuple[int,int]) -> None:
    # Creating a temporary surface with alpha channel for glow
    glow = pygame.Surface((text_surface.get_width() + SPOT_GLOW_RADIUS * 4,
                           text_surface.get_height() + SPOT_GLOW_RADIUS * 4), pygame.SRCALPHA)
    # Filling glow color with configured alpha
    glow_color = (*SPOT_GLOW, SPOT_GLOW_ALPHA)
    # Drawing multiple blurred-like offsets to simulate a soft glow
    for r in range(1, SPOT_GLOW_RADIUS + 1):
        # Computing offset magnitude
        offset = r
        # Drawing the original text in glow color slightly offset
        glow.blit(text_surface, (offset + 2, offset + 2))
    # Tinting the glow surface with the glow color using fill and BLEND_RGBA_MULT
    tint = pygame.Surface(glow.get_size(), pygame.SRCALPHA)
    tint.fill(glow_color)
    glow.blit(tint, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
    # Blitting the glow under the text at the given position minus padding
    surface.blit(glow, (pos[0] - SPOT_GLOW_RADIUS * 2, pos[1] - SPOT_GLOW_RADIUS * 2))

# Implementing a padded idea block renderer

def render_idea_block(text: str, author: str, scale: float) -> pygame.Surface:
    # Computing the max text width based on current window width
    max_w = int(WIDTH * MAX_TEXT_WIDTH_RATIO)
    # Wrapping the idea text into lines
    lines = wrap_text(text, IDEA_FONT_BASE, max_w)
    # Rendering the author line prefixed with an en dash
    author_surf = AUTHOR_FONT.render(f"— {author}", True, TEXT_SUB)
    # Computing block padding and spacing
    pad = 12
    gap = 8
    # Computing total height by summing line heights and gaps
    total_h = sum(l.get_height() for l in lines) + (len(lines) - 1) * 4 + gap + author_surf.get_height()
    # Computing total width as max among line widths and author width
    total_w = max([author_surf.get_width()] + [l.get_width() for l in lines])
    # Creating the block surface with per-pixel alpha for transparency
    block = pygame.Surface((int(total_w * scale) + pad * 2, int(total_h * scale) + pad * 2), pygame.SRCALPHA)
    # Optionally drawing a subtle translucent card background for readability
    card = pygame.Surface((int(total_w * scale) + pad * 2, int(total_h * scale) + pad * 2), pygame.SRCALPHA)
    card.fill((255, 255, 255, 16))
    block.blit(card, (0, 0))
    # Creating a sub-surface for scaled blits
    content = pygame.Surface((total_w, total_h), pygame.SRCALPHA)
    # Computing y cursor for stacking lines
    y = 0
    # Blitting each wrapped line onto the content surface
    for ls in lines:
        content.blit(ls, (0, y))
        y += ls.get_height() + 4
    # Adding a gap before the author line
    y += max(0, gap - 4)
    # Blitting the author
    content.blit(author_surf, (0, y))
    # Scaling the content by the spotlight scale factor
    scaled = pygame.transform.smoothscale(content, (int(total_w * scale), int(total_h * scale)))
    # Blitting the scaled content with padding
    block.blit(scaled, (pad, pad))
    # Returning the final block surface
    return block

# Implementing a position update helper (separate from class for clarity)

def update_positions(dt: float) -> None:
    # Iterating all bubbles to advance their motion
    for b in bubbles:
        b.update(dt)

# ---------------------------------
# Main Loop
# ---------------------------------
# Initializing spotlight tracking variables
spot_index = 0
spot_t = 0.0

# Recording the last time for delta-time computation
last_time = time.time()

# Starting the application loop
running = True
while running:
    # Handling events from pygame
    for event in pygame.event.get():
        # Handling quit event to close the application
        if event.type == pygame.QUIT:
            running = False
        # Handling window resize to keep layout responsive
        if event.type == pygame.VIDEORESIZE:
            WIDTH, HEIGHT = event.w, event.h
            window = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)

    # Computing delta time since last frame
    now = time.time()
    dt = now - last_time
    last_time = now

    # Drawing a smooth vertical gradient background
    draw_gradient_background(window, BG_TOP, BG_BOTTOM)

    # Rendering and centering the header at the top
    header_str = header_text or DEFAULT_HEADER
    header_surf = HEADER_FONT.render(header_str, True, ACCENT)
    header_rect = header_surf.get_rect(center=(WIDTH // 2, HEADER_Y))
    window.blit(header_surf, header_rect)

    # Updating the spotlight timing and index when enough time has elapsed
    if bubbles:
        spot_t += dt
        if spot_t >= SPOTLIGHT_PERIOD:
            spot_t = 0.0
            spot_index = (spot_index + 1) % len(bubbles)
        # Computing a sine-eased scale for the current spotlight
        phase = spot_t / SPOTLIGHT_PERIOD
        scale_now = 1.0 + (SPOT_SCALE_MAX - 1.0) * math.sin(math.pi * phase)
    else:
        scale_now = 1.0

    # Updating idea positions based on drift
    update_positions(dt)

    # Preparing a list to collect rects for light overlap resolution
    rects: t.List[pygame.Rect] = []

    # Iterating through bubbles to render each idea block
    for idx, b in enumerate(bubbles):
        # Applying spotlight scale for the active idea, 1.0 otherwise
        b.scale = scale_now if idx == spot_index else 1.0
        # Retrieving the rendered surface (cached when possible)
        surf = b.get_surface()
        # Computing top-left drawing coordinates with current x/y
        x = int(b.x)
        y = int(b.y)
        # Optionally blitting a soft glow for spotlighted idea
        if idx == spot_index:
            blit_glow(window, surf, (x, y))
        # Blitting the idea block onto the window
        window.blit(surf, (x, y))
        # Recording the rect for overlap post-pass
        r = pygame.Rect(x, y, surf.get_width(), surf.get_height())
        rects.append(r)

    # Performing a tiny overlap relaxation pass to reduce collisions
    resolve_overlaps(rects)

    # Drawing a professional footer with idea count and timestamp
    count = len(bubbles)
    footer_text = f"Ideas submitted: {count}"
    foot = FOOTER_FONT.render(footer_text, True, TEXT_SUB)
    foot_rect = foot.get_rect(center=(WIDTH // 2, HEIGHT - FOOTER_Y_MARGIN))
    window.blit(foot, foot_rect)

    # Flipping buffers to display the current frame
    pygame.display.flip()

    # Waiting to maintain target FPS
    clock.tick(FPS)

# Quitting pygame cleanly when loop exits
pygame.quit()
