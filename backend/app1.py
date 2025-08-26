# ============================
# backend/app.py
# Floating Ideas — Single-Event Backend
# - FastAPI server with PIN-protected submissions
# - CSV + JSON persistence (no DB)
# - Header management for the wall title
# - Minimal HTML form served at '/'
# - WebSocket broadcasting for instant wall updates
# ============================

# ----------------------------
# Imports (standard library)
# ----------------------------
# Filesystem paths and timestamps
from pathlib import Path
from datetime import datetime
# OS env, CSV/JSON, asyncio for write lock & websockets broadcast
import os
import csv
import json
import asyncio
from typing import List, Dict, Any, Set

# ----------------------------
# Imports (third-party)
# ----------------------------
# FastAPI + Starlette primitives
from fastapi import FastAPI, Form, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse
from fastapi.middleware.cors import CORSMiddleware


# ----------------------------
# Constants & Paths
# ----------------------------
# Repository root (…/floating-ideas)
BASE_DIR: Path = Path(__file__).resolve().parent.parent
# Data directory for event outputs
DATA_DIR: Path = BASE_DIR / "data"
# File paths for persistence
CSV_PATH: Path = DATA_DIR / "ideas.csv"
JSON_PATH: Path = DATA_DIR / "ideas.json"
HEADER_PATH: Path = DATA_DIR / "header.txt"
# Default header/question shown on the wall
DEFAULT_HEADER: str = "What ways can we use AI?"
# Event PIN (set in shell: export EVENT_PIN=1234)
EVENT_PIN: str = os.environ.get("EVENT_PIN", "").strip()


# ----------------------------
# Data Model (lightweight class)
# ----------------------------
class Idea:
    """
    @brief  In-memory model for an idea row.

    @field  id          Auto-incrementing integer identifier.
    @field  author      Name of the submitter.
    @field  text        Idea content text.
    @field  created_at  ISO 8601 timestamp (seconds precision).
    """

    id: int
    author: str
    text: str
    created_at: str

    def to_dict(self) -> Dict[str, Any]:
        """
        @brief  Convert Idea to a plain dict for JSON responses and persistence.
        @return Dict with keys: id, author, text, created_at.
        """
        return {
            "id": self.id,
            "author": self.author,
            "text": self.text,
            "created_at": self.created_at,
        }


# ----------------------------
# Runtime State
# ----------------------------
# In-memory cache of ideas to avoid constant disk IO
IDEAS_CACHE: List[Idea] = []
# Connected websocket clients
ACTIVE_SOCKETS: Set[WebSocket] = set()
# Single writer lock to serialize file updates
WRITE_LOCK: asyncio.Lock = asyncio.Lock()


# ----------------------------
# File Utilities
# ----------------------------
def ensure_data_files() -> None:
    """
    @brief  Ensure the data folder and files exist with sensible defaults.
    """
    # Ensure data directory exists
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    # Initialize CSV with header row if missing
    if not CSV_PATH.exists():
        with CSV_PATH.open("w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["id", "author", "text", "created_at"])
    # Initialize JSON with empty list if missing
    if not JSON_PATH.exists():
        JSON_PATH.write_text("[]", encoding="utf-8")
    # Initialize header text if missing
    if not HEADER_PATH.exists():
        HEADER_PATH.write_text(DEFAULT_HEADER, encoding="utf-8")


def load_all_ideas_from_disk() -> List[Idea]:
    """
    @brief  Load all ideas from ideas.json into memory at startup.
    @return List[Idea] parsed from JSON file.
    """
    raw = JSON_PATH.read_text(encoding="utf-8")
    data = json.loads(raw)
    items: List[Idea] = []
    for o in data:
        it = Idea()
        it.id = int(o["id"])
        it.author = str(o["author"])
        it.text = str(o["text"])
        it.created_at = str(o["created_at"])
        items.append(it)
    return items


def persist_full_json(ideas: List[Idea]) -> None:
    """
    @brief  Overwrite ideas.json with the full list (simple & robust for small volumes).
    @param  ideas  In-memory ideas to persist.
    """
    payload = [i.to_dict() for i in ideas]
    JSON_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def append_csv_row(idea: Idea) -> None:
    """
    @brief  Append one row to ideas.csv (for easy post-event analysis).
    @param  idea  The newly created idea.
    """
    with CSV_PATH.open("a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([idea.id, idea.author, idea.text, idea.created_at])


def get_next_id(ideas: List[Idea]) -> int:
    """
    @brief  Compute next auto-increment ID from in-memory list.
    @param  ideas  Current cache.
    @return Next integer ID (starts at 1).
    """
    return (max((i.id for i in ideas), default=0) + 1)


def read_header_text() -> str:
    """
    @brief  Read current header text from disk (fallback to default if blank).
    @return Header string to display on the wall.
    """
    txt = HEADER_PATH.read_text(encoding="utf-8").strip()
    return txt or DEFAULT_HEADER


def write_header_text(value: str) -> None:
    """
    @brief  Write new header text to disk.
    @param  value  New header string.
    """
    HEADER_PATH.write_text(value.strip(), encoding="utf-8")


async def broadcast(payload: Dict[str, Any]) -> None:
    """
    @brief  Broadcast a JSON payload to all connected WebSocket clients.
    @param  payload  JSON-serializable object.
    """
    message = json.dumps(payload)
    # Take a snapshot to avoid set mutation during iteration
    targets = list(ACTIVE_SOCKETS)
    for ws in targets:
        try:
            await ws.send_text(message)
        except Exception:
            # Drop broken socket silently to keep the rest healthy
            ACTIVE_SOCKETS.discard(ws)


# ----------------------------
# FastAPI App & Startup
# ----------------------------
app = FastAPI(title="Floating Ideas — Event Backend")

# Open CORS for local-network staff devices
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Prepare files and warm cache at import time
ensure_data_files()
IDEAS_CACHE = load_all_ideas_from_disk()


# ----------------------------
# Routes — HTML Intake
# ----------------------------
@app.get("/", response_class=HTMLResponse)
def intake_form() -> HTMLResponse:
    """
    @brief  Serve the mobile-friendly HTML intake form (with PIN field).
    @return HTMLResponse with contents of backend/submit.html.
    """
    html_path: Path = Path(__file__).resolve().parent / "submit.html"
    html_text: str = html_path.read_text(encoding="utf-8")
    return HTMLResponse(content=html_text)


# ----------------------------
# Routes — Ideas CRUD
# ----------------------------
@app.get("/ideas")
def get_ideas() -> List[Dict[str, Any]]:
    """
    @brief  Return all ideas as JSON (used by wall & Streamlit intake).
    @return List of idea dicts.
    """
    return [i.to_dict() for i in IDEAS_CACHE]


@app.post("/ideas")
async def post_idea(
    author: str = Form(...),
    text: str = Form(...),
    pin: str = Form(...),
) -> JSONResponse:
    """
    @brief  Create a new idea if PIN is valid; persist to CSV/JSON; broadcast via WS.
    @param  author  Submitter name (form field).
    @param  text    Idea text (form field).
    @param  pin     Event PIN (form field).
    @return JSONResponse: { ok: bool, idea?: dict, error?: str }.
    """
    # Validate server-side PIN config
    if not EVENT_PIN:
        return JSONResponse({"ok": False, "error": "Server missing EVENT_PIN."}, status_code=500)

    # Normalize inputs
    author = author.strip()
    text = text.strip()
    pin = pin.strip()

    # Validate PIN match
    if pin != EVENT_PIN:
        return JSONResponse({"ok": False, "error": "Invalid PIN."}, status_code=401)

    # Validate required fields
    if not author or not text:
        return JSONResponse({"ok": False, "error": "Missing name or idea."}, status_code=400)

    # Serialize writes (CSV append + JSON overwrite)
    async with WRITE_LOCK:
        new_id = get_next_id(IDEAS_CACHE)

        new = Idea()
        new.id = new_id
        new.author = author
        new.text = text
        new.created_at = datetime.now().isoformat(timespec="seconds")

        IDEAS_CACHE.append(new)
        append_csv_row(new)
        persist_full_json(IDEAS_CACHE)

    # Notify live clients
    await broadcast({"type": "idea.new", "data": new.to_dict()})

    return JSONResponse({"ok": True, "idea": new.to_dict()})


# ----------------------------
# Routes — Header Management
# ----------------------------
@app.get("/header")
def get_header() -> Dict[str, str]:
    """
    @brief  Read the current wall header text.
    @return { "header": str }
    """
    return {"header": read_header_text()}


@app.post("/header")
async def set_header(text: str = Form(...), pin: str = Form(...)) -> JSONResponse:
    """
    @brief  Set a new header if PIN is valid; broadcast change to live clients.
    @param  text  New header text (form field).
    @param  pin   Event PIN (form field).
    @return { ok: bool } or { ok: false, error: str }.
    """
    if not EVENT_PIN:
        return JSONResponse({"ok": False, "error": "Server missing EVENT_PIN."}, status_code=500)

    t = text.strip()
    p = pin.strip()

    if p != EVENT_PIN:
        return JSONResponse({"ok": False, "error": "Invalid PIN."}, status_code=401)

    write_header_text(t or DEFAULT_HEADER)
    await broadcast({"type": "header.set", "data": read_header_text()})
    return JSONResponse({"ok": True})


# ----------------------------
# Routes — Exports
# ----------------------------
@app.get("/export.csv")
def export_csv() -> PlainTextResponse:
    """
    @brief  Download CSV snapshot of all ideas (simple archival).
    @return text/csv payload.
    """
    data = CSV_PATH.read_text(encoding="utf-8")
    return PlainTextResponse(data, media_type="text/csv")


@app.get("/export.json")
def export_json() -> JSONResponse:
    """
    @brief  Download JSON snapshot of all ideas.
    @return JSON array of idea objects.
    """
    return JSONResponse([i.to_dict() for i in IDEAS_CACHE])


# ----------------------------
# WebSocket — /ws
# ----------------------------
@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket) -> None:
    """
    @brief  WebSocket endpoint for live updates to the wall.
    @detail On connect: send hello {header, ideas}. Then keep open to push:
            - {type: 'idea.new', data: idea}
            - {type: 'header.set', data: header}
    """
    await ws.accept()
    ACTIVE_SOCKETS.add(ws)

    try:
        # Send initial state to the new client
        await ws.send_text(json.dumps({
            "type": "hello",
            "data": {
                "header": read_header_text(),
                "ideas": [i.to_dict() for i in IDEAS_CACHE],
            }
        }))

        # Keep connection alive; we don't expect client messages,
        # but awaiting receive lets us detect clean disconnects.
        while True:
            await ws.receive_text()

    except WebSocketDisconnect:
        ACTIVE_SOCKETS.discard(ws)
    except Exception:
        # Any other error: drop socket and continue serving others
        ACTIVE_SOCKETS.discard(ws)