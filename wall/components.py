# ============================
# wall/components.py
# Rendering helpers: gradient, word-wrap, idea card, glow
# ============================

# ----------------------------
# Imports
# ----------------------------
# Import typing for hints
from typing import List, Tuple, Dict
# Import pygame for surfaces and fonts
import pygame

# Import theme colors for rendering
from .theme import BG_TOP, BG_BOTTOM, TEXT_MAIN, TEXT_SUB, MAX_TEXT_WIDTH_RATIO


# ----------------------------
# Background
# ----------------------------
def draw_gradient(surface: pygame.Surface, top: Tuple[int,int,int] = BG_TOP, bottom: Tuple[int,int,int] = BG_BOTTOM) -> None:
    """
    @brief  Draw a vertical gradient background.
    @param  surface  Destination surface.
    @param  top      RGB color at top.
    @param  bottom   RGB color at bottom.
    """
    # Get width/height
    w, h = surface.get_size()
    # Paint each row
    for y in range(h):
        t = y / max(1, h - 1)
        r = int(top[0] + (bottom[0] - top[0]) * t)
        g = int(top[1] + (bottom[1] - top[1]) * t)
        b = int(top[2] + (bottom[2] - top[2]) * t)
        pygame.draw.line(surface, (r, g, b), (0, y), (w, y))


# ----------------------------
# Text Wrapping
# ----------------------------
def wrap_lines(text: str, font: pygame.font.Font, max_width: int) -> List[pygame.Surface]:
    """
    @brief  Soft-wrap a string into surfaces that fit within max_width.
    @param  text       Source string.
    @param  font       Pygame font.
    @param  max_width  Max width for a line in pixels.
    @return List of rendered line surfaces.
    """
    # Split into words
    words = text.split()
    # Assemble soft-wrapped lines
    lines: List[str] = []
    cur: List[str] = []
    for w in words:
        cand = (" ".join(cur + [w])).strip()
        width, _ = font.size(cand)
        if width > max_width and cur:
            lines.append(" ".join(cur))
            cur = [w]
        else:
            cur.append(w)
    if cur:
        lines.append(" ".join(cur))
    # Render each line
    return [font.render(line, True, TEXT_MAIN) for line in lines]


# ----------------------------
# Text-only block (no card, no glow)
# ----------------------------
def render_text_block(text: str,
                      author: str,
                      scale: float,
                      fonts: Dict[str, pygame.font.Font],
                      win_w: int) -> pygame.Surface:
    """
    @brief  Render wrapped 'text' plus an author line without any box or glow.
    @param  text     Idea content string.
    @param  author   Author name string.
    @param  scale    Spotlight scale factor (1.0 normal).
    @param  fonts    Dict with 'idea' and 'author' fonts.
    @param  win_w    Current window width, used to compute wrap width.
    @return RGBA surface containing only the text.
    """
    # Compute wrapping width as a ratio of window width
    max_w = int(win_w * MAX_TEXT_WIDTH_RATIO)

    # Render wrapped lines + author line
    lines = wrap_lines(text, fonts["idea"], max_w)
    author_surf = fonts["author"].render(f"— {author}", True, TEXT_SUB)

    # Measure natural size
    gap = 8  # vertical gap between body and author line
    y = 0
    total_w = max([author_surf.get_width()] + [ls.get_width() for ls in lines]) if lines else author_surf.get_width()
    total_h = sum(ls.get_height() for ls in lines) + (max(0, len(lines) - 1) * 4) + gap + author_surf.get_height()

    # Compose an alpha-only surface (no background box)
    content = pygame.Surface((total_w, total_h), pygame.SRCALPHA)
    for ls in lines:
        content.blit(ls, (0, y))
        y += ls.get_height() + 4
    y += max(0, gap - 4)
    content.blit(author_surf, (0, y))

    # Apply spotlight scale (smoothscale keeps it crisp enough at this size)
    sw = max(1, int(total_w * scale))
    sh = max(1, int(total_h * scale))
    scaled = pygame.transform.smoothscale(content, (sw, sh))
    return scaled


# ----------------------------
# Spotlight Glow
# ----------------------------
# def blit_glow(dest: pygame.Surface, surf: pygame.Surface, xy: Tuple[int,int]) -> None:
#     """
#     @brief  Paint a subtle glow under a surface to emphasize spotlight.
#     @param  dest  Destination surface.
#     @param  surf  Foreground surface (for size).
#     @param  xy    Top-left position for the foreground.
#     """
#     # Prepare alpha surface slightly larger than content
#     gw = surf.get_width() + SPOT_GLOW_PAD * 2
#     gh = surf.get_height() + SPOT_GLOW_PAD * 2
#     glow = pygame.Surface((gw, gh), pygame.SRCALPHA)
#     # Tint to accent with desired alpha
#     tint = pygame.Surface((gw, gh), pygame.SRCALPHA)
#     tint.fill((ACCENT[0], ACCENT[1], ACCENT[2], SPOT_GLOW_ALPHA))
#     # Cheap “blur” by layering offsets
#     for off in range(1, 5):
#         glow.blit(surf, (SPOT_GLOW_PAD + off, SPOT_GLOW_PAD + off))
#     glow.blit(tint, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
#     # Draw under the card
#     dest.blit(glow, (xy[0] - SPOT_GLOW_PAD, xy[1] - SPOT_GLOW_PAD))