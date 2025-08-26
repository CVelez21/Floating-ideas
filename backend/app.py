# ============================
# backend/app.py
# FastAPI backend for Floating Ideas (single-event)
# - PIN-protected submissions
# - CSV + JSON persistence
# - Header management
# - Minimal HTML form at '/'
# - WebSocket broadcast for live updates
# ============================

# ----------------------------
# Imports
# ----------------------------
# Import typing tools for explicit type hints
from typing import List, Dict, Any, Set

# Import standard library modules for filesystem and time
from pathlib import Path
from datetime import datetime
import os
import csv
import json
import asyncio

# Import FastAPI and Starlette components
from fastapi import FastAPI, Form, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse
from fastapi.middleware.cors import CORSMiddleware


# ----------------------------
# Constants & Paths
# ----------------------------
# Define base directory as repository root (one level above /backend)
BASE_DIR: Path = Path(__file__).resolve().parent.parent

# Define data directory path where CSV/JSON/header files will live
DATA_DIR: Path = BASE_DIR / "data"

# Define individual file paths for data persistence
CSV_PATH: Path = DATA_DIR / "ideas.csv"
JSON_PATH: Path = DATA_DIR / "ideas.json"
HEADER_PATH: Path = DATA_DIR / "header.txt"

# Define default header question text
DEFAULT_HEADER: str = "What ways can we use AI?"

# Read the required event PIN from environment (set EVENT_PIN=1234 before running)
EVENT_PIN: str = os.environ.get("EVENT_PIN", "").strip()


# ----------------------------
# Data Models (Pydantic-like typing, simple dicts persisted to files)
# ----------------------------
class Idea:
    """
    @brief  In-memory representation of an idea row.
    @field  id          Auto-increment integer identifier.
    @field  author      Name of the submitter.
    @field  text        The idea text.
    @field  created_at  ISO timestamp (seconds precision).
    """
    id: int
    author: str
    text: str
    created_at: str

    # Comment-before-line: Provide a helper to convert Idea to plain dict for JSON/response.
    def to_dict(self) -> Dict[str, Any]:
        # Convert the Idea instance to a serializable dictionary
        return {"id": self.id, "author": self.author, "text": self.text, "created_at": self.created_at}


# ----------------------------
# Globals (in-memory cache)
# ----------------------------
# Comment-before-line: Maintain a lightweight cache of ideas to minimize file I/O frequency.
IDEAS_CACHE: List[Idea] = []

# Comment-before-line: Keep a set of active WebSocket connections for broadcasting updates in real time.
ACTIVE_SOCKETS: Set[WebSocket] = set()

# Comment-before-line: Create a single asyncio lock to serialize file writes.
WRITE_LOCK: asyncio.Lock = asyncio.Lock()


# ----------------------------
# Utility Functions (declarations + definitions)
# ----------------------------
def ensure_data_files() -> None:
    """
    @brief  Ensure data directory and files exist with correct initial content.
    """
    # Create the data directory if it doesn't exist
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    # Initialize CSV with header row if missing
    if not CSV_PATH.exists():
        with CSV_PATH.open("w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["id", "author", "text", "created_at"])

    # Initialize JSON file with empty list if missing
    if not JSON_PATH.exists():
        JSON_PATH.write_text("[]", encoding="utf-8")

    # Initialize header text file if missing
    if not HEADER_PATH.exists():
        HEADER_PATH.write_text(DEFAULT_HEADER, encoding="utf-8")


def load_all_ideas_from_disk() -> List[Idea]:
    """
    @brief  Load all ideas from JSON to memory (source of truth).
    @return List of Idea objects loaded from ideas.json.
    """
    # Read JSON text from disk
    raw = JSON_PATH.read_text(encoding="utf-8")
    # Parse JSON content into Python objects
    data = json.loads(raw)
    # Convert dicts to Idea instances
    items: List[Idea] = []
    for o in data:
        it = Idea()
        it.id = int(o["id"])
        it.author = str(o["author"])
        it.text = str(o["text"])
        it.created_at = str(o["created_at"])
        items.append(it)
    # Return parsed ideas
    return items


def persist_full_json(ideas: List[Idea]) -> None:
    """
    @brief  Write the full list of ideas back to JSON atomically.
    @param  ideas  The in-memory list to persist.
    """
    # Convert Idea objects to dictionaries
    payload = [i.to_dict() for i in ideas]
    # Write JSON with pretty indent for readability
    JSON_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def append_csv_row(idea: Idea) -> None:
    """
    @brief  Append a single idea to the CSV file.
    @param  idea  The Idea to append.
    """
    # Open CSV in append mode and write the new row
    with CSV_PATH.open("a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([idea.id, idea.author, idea.text, idea.created_at])


def get_next_id(ideas: List[Idea]) -> int:
    """
    @brief  Compute the next auto-increment ID based on the current cache.
    @param  ideas  The in-memory list of ideas.
    @return Next integer ID.
    """
    # If there are no ideas, start at 1, else current max id + 1
    return (max((i.id for i in ideas), default=0) + 1)


def read_header_text() -> str:
    """
    @brief  Read the header text from disk.
    @return Current header string (falls back to default).
    """
    # Return content of header file (or default if empty)
    txt = HEADER_PATH.read_text(encoding="utf-8").strip()
    return txt or DEFAULT_HEADER


def write_header_text(value: str) -> None:
    """
    @brief  Overwrite the header text on disk.
    @param  value  The new header string to persist.
    """
    # Write the provided header string to the header file
    HEADER_PATH.write_text(value.strip(), encoding="utf-8")


async def broadcast(payload: Dict[str, Any]) -> None:
    """
    @brief  Broadcast a JSON message to all connected WebSocket clients.
    @param  payload  The JSON-serializable message to send.
    """
    # Convert payload to JSON string once for efficiency
    message = json.dumps(payload)
    # Iterate a snapshot of sockets to avoid mutation during iteration
    targets = list(ACTIVE_SOCKETS)
    # Send the message to each active client; drop broken sockets
    for ws in targets:
        try:
            await ws.send_text(message)
        except Exception:
            # If sending fails, remove the socket from active set
            try:
                ACTIVE_SOCKETS.remove(ws)
            except KeyError:
                pass


# ----------------------------
# FastAPI App Initialization
# ----------------------------
# Create FastAPI application instance
app = FastAPI(title="Floating Ideas — Event Backend")

# Enable permissive CORS so staff devices on local Wi‑Fi can post ideas
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],          # Allow all origins for a single-event LAN usage
    allow_credentials=True,       # Allow cookies/credentials if needed later
    allow_methods=["*"],          # Allow all HTTP methods
    allow_headers=["*"],          # Allow all headers
)

# Ensure data files exist and warm the cache at startup
ensure_data_files()
IDEAS_CACHE = load_all_ideas_from_disk()


# ----------------------------
# Routes: HTML Intake (minimal form)
# ----------------------------
@app.get("/", response_class=HTMLResponse)
def intake_form() -> HTMLResponse:
    """
    @brief  Serve the minimal mobile-friendly HTML intake form.
    @return HTMLResponse containing the contents of backend/submit.html.
    """
    # Compute path to embedded HTML file
    html_path: Path = Path(__file__).resolve().parent / "submit.html"
    # Read the file text (assumes you will add submit.html next)
    html_text: str = html_path.read_text(encoding="utf-8")
    # Return as HTML
    return HTMLResponse(content=html_text)


# ----------------------------
# Routes: Ideas CRUD (file-based)
# ----------------------------
@app.get("/ideas")
def get_ideas() -> List[Dict[str, Any]]:
    """
    @brief  Return all ideas as a JSON list (used by wall and Streamlit).
    @return List of idea dicts.
    """
    # Convert the in-memory cache to plain dicts for response
    return [i.to_dict() for i in IDEAS_CACHE]


@app.post("/ideas")
async def post_idea(
    author: str = Form(...),
    text: str = Form(...),
    pin: str = Form(...),
) -> JSONResponse:
    """
    @brief  Create a new idea after validating the event PIN.
    @param  author  Submitter's name (form field).
    @param  text    Idea text (form field).
    @param  pin     Event PIN (form field).
    @return JSONResponse with ok flag and idea data or error.
    """
    # Trim inputs for cleanliness
    author = author.strip()
    text = text.strip()
    pin = pin.strip()

    # Reject if PIN is not configured or does not match
    if not EVENT_PIN:
        return JSONResponse({"ok": False, "error": "Server missing EVENT_PIN."}, status_code=500)
    if pin != EVENT_PIN:
        return JSONResponse({"ok": False, "error": "Invalid PIN."}, status_code=401)

    # Reject empty fields to keep data quality
    if not author or not text:
        return JSONResponse({"ok": False, "error": "Missing name or idea."}, status_code=400)

    # Lock writes to prevent simultaneous file modifications
    async with WRITE_LOCK:
        # Compute new ID for the idea
        next_id = get_next_id(IDEAS_CACHE)
        # Create the Idea object with timestamp
        new = Idea()
        new.id = next_id
        new.author = author
        new.text = text
        new.created_at = datetime.now().isoformat(timespec="seconds")

        # Append to in-memory cache
        IDEAS_CACHE.append(new)

        # Persist to CSV (append only)
        append_csv_row(new)

        # Persist full JSON (overwrite with new list)
        persist_full_json(IDEAS_CACHE)

    # Broadcast to WebSocket clients that a new idea arrived
    await broadcast({"type": "idea.new", "data": new.to_dict()})

    # Return success with the created idea
    return JSONResponse({"ok": True, "idea": new.to_dict()})


# ----------------------------
# Routes: Header management
# ----------------------------
@app.get("/header")
def get_header() -> Dict[str, str]:
    """
    @brief  Return current header text for the big screen.
    @return Dict with 'header' key.
    """
    # Read header from disk and return it
    return {"header": read_header_text()}


@app.post("/header")
async def set_header(text: str = Form(...), pin: str = Form(...)) -> JSONResponse:
    """
    @brief  Update the header text if the correct PIN is provided.
    @param  text  New header text (form field).
    @param  pin   Event PIN (form field).
    @return JSONResponse with ok flag or error.
    """
    # Trim inputs first
    t = text.strip()
    p = pin.strip()

    # Validate that ENV pin is set and matches
    if not EVENT_PIN:
        return JSONResponse({"ok": False, "error": "Server missing EVENT_PIN."}, status_code=500)
    if p != EVENT_PIN:
        return JSONResponse({"ok": False, "error": "Invalid PIN."}, status_code=401)

    # Write header text to disk
    write_header_text(t or DEFAULT_HEADER)

    # Broadcast header change to all WebSocket clients
    await broadcast({"type": "header.set", "data": read_header_text()})

    # Return success
    return JSONResponse({"ok": True})


# ----------------------------
# Routes: Exports
# ----------------------------
@app.get("/export.csv")
def export_csv() -> PlainTextResponse:
    """
    @brief  Return the raw CSV file as text for download/archival.
    @return PlainTextResponse with 'text/csv' media type.
    """
    # Read CSV contents and return as text/csv
    data = CSV_PATH.read_text(encoding="utf-8")
    return PlainTextResponse(data, media_type="text/csv")


@app.get("/export.json")
def export_json() -> JSONResponse:
    """
    @brief  Return the full JSON payload of ideas for download/archival.
    @return JSONResponse with array of idea dicts.
    """
    # Convert cache to JSON response directly
    return JSONResponse([i.to_dict() for i in IDEAS_CACHE])


# ----------------------------
# WebSocket: /ws
# ----------------------------
@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket) -> None:
    """
    @brief  Maintain a WebSocket connection for live updates.
    @detail On connect: send hello with current header + full ideas.
            On idea/new or header/set: broadcast incremental messages.
    """
    # Accept the WebSocket handshake
    await ws.accept()

    # Add this socket to the active set
    ACTIVE_SOCKETS.add(ws)

    try:
        # Send an initial hello payload with current state
        await ws.send_text(json.dumps({
            "type": "hello",
            "data": {
                "header": read_header_text(),
                "ideas": [i.to_dict() for i in IDEAS_CACHE],
            }
        }))

        # Keep the connection open; we don't expect client messages,
        # but we await receive to detect disconnects cleanly.
        while True:
            # Wait for any message (ping/pong or text) to keep the loop alive
            await ws.receive_text()

    except WebSocketDisconnect:
        # On disconnect, remove from active sockets
        ACTIVE_SOCKETS.discard(ws)
    except Exception:
        # On any error, ensure removal and swallow exception to keep server healthy
        ACTIVE_SOCKETS.discard(ws)