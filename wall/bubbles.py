# ============================
# wall/bubbles.py
# IdeaBubble sprite: motion + caching of rendered card
# ============================

# ----------------------------
# Imports
# ----------------------------
# Import typing for hints
from typing import Dict, Any, Optional, List
# Import standard libs for math/time/random
import math, time, random
# Import pygame for rects/surfaces
import pygame

# Import theme constants
from .theme import MARGIN_X, DRIFT_PX_S, DRIFT_VAR, BOB_PX
# Import rendering component
from .components import render_text_block


class IdeaBubble:
    """
    @brief  Visual sprite carrying position/drift and cached surface.

    @field  idea         Underlying idea dict {id, text, author, ...}.
    @field  x,y          Current position.
    @field  dx,dy        Drift velocity in px/s.
    @field  phase,freq   Bobbing parameters.
    @field  scale        Render scale (1.0 default; >1.0 when spotlighted).
    @field  rect         Last drawn rect (optional layout logic).
    """

    def __init__(self, idea: Dict[str, Any], fonts: Dict[str, pygame.font.Font], win_w: int, win_h: int) -> None:
        """
        @brief  Initialize bubble with seeded drift and cached render metadata.
        @param  idea    Idea dict (must include 'id','text','author').
        @param  fonts   Font dict for rendering.
        @param  win_w   Window width at creation time.
        @param  win_h   Window height at creation time.
        """
        # Seed RNG from id for stable drift per idea
        rng = random.Random(int(idea.get("id", 0)) * 1337)

        # Seed initial Y placement into gentle lanes for pleasant spacing (no header/footer deps)
        lanes = 5                       # number of vertical lanes (feel free to tweak)
        PAD_TOP = 100                   # keep text away from the very top
        PAD_BOTTOM = 100                # keep text away from the very bottom
        usable_h = max(260, win_h - (PAD_TOP + PAD_BOTTOM))
        lane_h = max(120, usable_h // lanes)

        lane_index = int(idea.get("id", 0)) % lanes
        y_base = PAD_TOP + lane_index * lane_h

        # Place within margins
        self.x: float = rng.uniform(MARGIN_X, max(MARGIN_X, win_w - MARGIN_X))
        self.y: float = rng.uniform(y_base - 40, y_base + 40)

        # Drift vector
        angle = rng.uniform(-math.pi / 4, math.pi / 4)
        speed = DRIFT_PX_S * (1.0 + rng.uniform(-DRIFT_VAR, DRIFT_VAR))
        self.dx: float = math.cos(angle) * speed
        self.dy: float = math.sin(angle) * speed

        # Bobbing params
        self.phase: float = rng.uniform(0, 2 * math.pi)
        self.freq: float = rng.uniform(0.20, 0.45)

        # Store idea + draw state
        self.idea: Dict[str, Any] = idea
        self.scale: float = 1.0
        self.rect: pygame.Rect = pygame.Rect(0, 0, 0, 0)

        # Cache metadata (content/scale)
        self._fonts = fonts
        self._win_w = win_w  # wrap width depends on window size
        self._cache_text: str = ""
        self._cache_author: str = ""
        self._cache_scale: float = 0.0
        self._cache_surface: Optional[pygame.Surface] = None

    def update(self, dt: float, win_w: int, win_h: int) -> None:
        """
        @brief  Advance position with drift + bob; softly reflect at margins.
        @param  dt     Delta time in seconds.
        @param  win_w  Current window width (for edge constraints).
        @param  win_h  Current window height (for edge constraints).
        """
        # Move by drift
        self.x += self.dx * dt
        self.y += self.dy * dt

        # Add gentle vertical bob
        self.y += math.sin(self.phase + time.time() * self.freq) * (BOB_PX * dt)

        # Softly reflect at X edges
        if self.x < MARGIN_X:
            self.x = MARGIN_X
            self.dx = abs(self.dx)
        if self.x > win_w - MARGIN_X:
            self.x = win_w - MARGIN_X
            self.dx = -abs(self.dx)

        # Softly reflect at outer Y edges (no middle bands)
        PAD = 40  # small vertical padding from the very top/bottom
        if self.y < PAD:
            self.y = PAD
            self.dy = abs(self.dy)
        if self.y > win_h - PAD:
            self.y = win_h - PAD
            self.dy = -abs(self.dy)

        # Update cached wrap width if window changed meaningfully
        self._win_w = win_w

    def surface(self) -> pygame.Surface:
        """
        @brief  Return cached idea card; rebuild if content or scale changed.
        @return RGBA surface for blit.
        """
        t = str(self.idea.get("text", ""))
        a = str(self.idea.get("author", ""))

        # Serve cached if content/scale unchanged
        if (
            self._cache_surface is not None
            and t == self._cache_text
            and a == self._cache_author
            and abs(self.scale - self._cache_scale) < 1e-3
        ):
            return self._cache_surface

        # Rebuild card and update cache
        s = render_text_block(t, a, self.scale, self._fonts, self._win_w)
        self._cache_surface = s
        self._cache_text = t
        self._cache_author = a
        self._cache_scale = self.scale
        return s