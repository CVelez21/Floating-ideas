# ============================
# wall/api_client.py
# Backend client: initial REST fetch + WebSocket live updates + poll fallback
# ============================

# ----------------------------
# Imports
# ----------------------------
# Import typing for hints
from typing import List, Dict, Any, Callable
# Import os/json for env + parsing
import os, json, time, threading, asyncio
# Import requests for REST
import requests
# Import websockets for WS client
import websockets


class WallState:
    """
    @brief  Shared state for the wall (header + ideas) with callbacks on updates.

    @field  header        Current header string.
    @field  ideas         Current list of idea dicts.
    @field  on_refresh    Callback invoked after any refresh (header/ideas).
    """
    def __init__(self, on_refresh: Callable[[], None]) -> None:
        """
        @brief  Initialize shared state with a callback invoked on updates.
        @param  on_refresh  Function to call when header/ideas change.
        """
        self.header: str = "What ways can we use AI?"
        self.ideas: List[Dict[str, Any]] = []
        self.on_refresh = on_refresh


class APIClient:
    """
    @brief  Talks to the backend: initial REST fetch, WS live updates, poll fallback.

    @field  base_url    Backend base URL (http://host:8000).
    @field  state       Shared WallState to update.
    @field  running     Control flag for threads.
    """
    def __init__(self, state: WallState, base_url: str | None = None) -> None:
        """
        @brief  Construct an API client bound to a WallState.
        @param  state     Shared state object.
        @param  base_url  Backend base URL (read from IDEAS_API if None).
        """
        self.base_url = (base_url or os.environ.get("IDEAS_API", "http://127.0.0.1:8000")).rstrip("/")
        self.state = state
        self.running = True

    def fetch_initial(self) -> None:
        """
        @brief  Fetch header + ideas once via REST and notify.
        """
        # Fetch header
        try:
            self.state.header = requests.get(f"{self.base_url}/header", timeout=5).json().get("header", self.state.header)
        except Exception:
            pass
        # Fetch ideas
        try:
            items = requests.get(f"{self.base_url}/ideas", timeout=5).json()
            if isinstance(items, list):
                self.state.ideas = items
        except Exception:
            pass
        # Notify render loop to rebuild
        self.state.on_refresh()

    def start_websocket(self) -> threading.Thread:
        """
        @brief  Start the WebSocket listener in a daemon thread.
        @return Thread object (already started).
        """
        # Target coroutine runner
        def runner():
            asyncio.run(self._ws_loop())
        t = threading.Thread(target=runner, daemon=True)
        t.start()
        return t

    async def _ws_loop(self) -> None:
        """
        @brief  Maintain WebSocket connection; apply broadcasts to state.
        """
        ws_url = self.base_url.replace("http", "ws") + "/ws"
        while self.running:
            try:
                async with websockets.connect(ws_url, ping_interval=20) as ws:
                    async for msg in ws:
                        payload = json.loads(msg)
                        t = payload.get("type")
                        if t == "hello":
                            self.state.header = payload["data"].get("header", self.state.header)
                            self.state.ideas = payload["data"].get("ideas", self.state.ideas)
                            self.state.on_refresh()
                        elif t == "idea.new":
                            self.state.ideas.append(payload["data"])
                            self.state.on_refresh()
                        elif t == "header.set":
                            self.state.header = payload["data"]
                            self.state.on_refresh()
            except Exception:
                # Backoff on disconnect or failure
                await asyncio.sleep(2.0)

    def start_poll_fallback(self, interval_sec: float = 15.0) -> threading.Thread:
        """
        @brief  Start a simple REST poller to refresh ideas periodically.
        @param  interval_sec  Poll period in seconds.
        @return Thread object (already started).
        """
        def loop():
            while self.running:
                try:
                    items = requests.get(f"{self.base_url}/ideas", timeout=5).json()
                    if isinstance(items, list) and len(items) != len(self.state.ideas):
                        self.state.ideas = items
                        self.state.on_refresh()
                except Exception:
                    pass
                time.sleep(interval_sec)
        t = threading.Thread(target=loop, daemon=True)
        t.start()
        return t