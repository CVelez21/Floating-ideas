# ============================
# wall/theme.py
# Visual theme + layout constants + font builders
# ============================

# ----------------------------
# Imports
# ----------------------------
# Import typing for explicit hints
from typing import Tuple, Dict
# Import pygame to build fonts
import pygame


# ----------------------------
# Colors (calm, professional)
# ----------------------------
# Top/bottom background gradient
BG_TOP: Tuple[int, int, int] = (9, 13, 24)
BG_BOTTOM: Tuple[int, int, int] = (21, 29, 45)
# Accent + text
ACCENT: Tuple[int, int, int] = (93, 196, 255)
TEXT_MAIN: Tuple[int, int, int] = (235, 242, 255)
TEXT_SUB: Tuple[int, int, int] = (168, 179, 196)


# ----------------------------
# Layout constants
# ----------------------------
# Initial window size, margins, header/footer placement
WIN_W_DEFAULT: int = 1920
WIN_H_DEFAULT: int = 1080
MARGIN_X: int = 80
HEADER_Y: int = 90
FOOTER_Y: int = 60

# Card max width as a fraction of window width
MAX_TEXT_WIDTH_RATIO: float = 0.42

# Motion parameters (gentle)
DRIFT_PX_S: float = 12.0
DRIFT_VAR: float = 0.6
BOB_PX: float = 8.0

# Spotlight visuals and timing
SPOTLIGHT_PERIOD: float = 7.0
SPOT_SCALE_MAX: float = 1.28
SPOT_GLOW_ALPHA: int = 70
SPOT_GLOW_PAD: int = 10

# Poll fallback interval (seconds)
POLL_EVERY: float = 15.0

# Default header text
DEFAULT_HEADER: str = "What ways can we use AI?"


# ----------------------------
# Fonts
# ----------------------------
def build_fonts() -> Dict[str, pygame.font.Font]:
    """
    @brief  Create and return the font set used by the wall.
    @return Dict with keys: 'header', 'idea', 'author', 'footer'.
    """
    # Use professional, widely available faces with fallbacks
    header = pygame.font.SysFont("Helvetica Neue, Helvetica, Arial", 64, bold=True)
    idea = pygame.font.SysFont("Helvetica Neue, Helvetica, Arial", 28)
    author = pygame.font.SysFont("Helvetica Neue, Helvetica, Arial", 22)
    footer = pygame.font.SysFont("Helvetica Neue, Helvetica, Arial", 20)
    return {"header": header, "idea": idea, "author": author, "footer": footer}