# ============================
# wall/spots.py
# Soft, drifting background spots (radial blobs) for ambient motion
# ============================

# ----------------------------
# Imports
# ----------------------------
import random
import pygame
from typing import List, Tuple


class Spot:
    """
    @brief  Single radial spot that drifts and softly reflects at edges.

    @field  x,y       Current position (center).
    @field  dx,dy     Velocity in px/s.
    @field  radius    Base radius in px.
    @field  alpha     Max alpha used for inner rings.
    @field  color     Base RGB color (pastel).
    """

    def __init__(self, w: int, h: int) -> None:
        """
        @brief  Initialize a spot at a random location with gentle velocity.
        @param  w  Canvas width in px.
        @param  h  Canvas height in px.
        """
        # Local RNG for variety
        r = random.Random()

        # Random placement and drift
        self.x: float = r.uniform(0, w)
        self.y: float = r.uniform(0, h)
        self.dx: float = r.uniform(-10.0, 10.0)
        self.dy: float = r.uniform(-10.0, 10.0)

        # Visual properties (subtle)
        self.radius: float = r.uniform(90.0, 220.0)
        self.alpha: int = int(r.uniform(20, 50))
        self.color: Tuple[int, int, int] = r.choice([
            (255, 255, 255),
            (195, 210, 255),
            (165, 190, 255),
            (140, 175, 240),
        ])

    def update(self, dt: float, w: int, h: int) -> None:
        """
        @brief  Advance position and softly reflect at screen edges.
        @param  dt  Delta time in seconds.
        @param  w   Canvas width.
        @param  h   Canvas height.
        """
        # Move
        self.x += self.dx * dt
        self.y += self.dy * dt

        # Reflect with loose bounds so spots re-enter smoothly
        if self.x < -self.radius or self.x > w + self.radius:
            self.dx *= -1.0
        if self.y < -self.radius or self.y > h + self.radius:
            self.dy *= -1.0

    def draw(self, dest: pygame.Surface) -> None:
        """
        @brief  Draw a soft radial fade using layered circles.
        @param  dest  Destination surface.
        """
        # Create a per-spot surface with alpha for blending
        size = int(self.radius * 2)
        surf = pygame.Surface((size, size), pygame.SRCALPHA)
        cx = cy = int(self.radius)

        # Draw concentric rings from center outward (alpha fades)
        step = 4  # ring thickness; smaller = smoother but more cost
        for r in range(int(self.radius), 0, -step):
            a = int(self.alpha * (r / self.radius))
            pygame.draw.circle(surf, (*self.color, a), (cx, cy), r)

        # Blit centered at (x, y)
        dest.blit(surf, (int(self.x - self.radius), int(self.y - self.radius)))


class SpotsLayer:
    """
    @brief  Manages a collection of Spot objects and draws them as a background.
    """

    def __init__(self, w: int, h: int, count: int = 8) -> None:
        """
        @brief  Initialize layer with a given number of spots.
        @param  w      Canvas width.
        @param  h      Canvas height.
        @param  count  Spot count (8–12 is reasonable).
        """
        self._count = max(0, count)
        self.spots: List[Spot] = [Spot(w, h) for _ in range(self._count)]

    def resize(self, w: int, h: int) -> None:
        """
        @brief  Re-seed spots on window resize to fit new bounds.
        """
        self.spots = [Spot(w, h) for _ in range(self._count)]

    def update(self, dt: float, w: int, h: int) -> None:
        """
        @brief  Advance all spots.
        """
        for s in self.spots:
            s.update(dt, w, h)

    def draw(self, dest: pygame.Surface) -> None:
        """
        @brief  Draw all spots (under foreground content).
        """
        for s in self.spots:
            s.draw(dest)