# ============================
# wall/main.py
# Entrypoint for Floating Ideas showcase wall
# - Initializes Pygame
# - Loads fonts + state
# - Connects to backend via APIClient (REST + WS + poll)
# - Runs frame loop with spotlight + idea bubbles
# - Dev panel (toggle via wrench button) + background spots toggle
# ============================

# ----------------------------
# Imports
# ----------------------------
import math, time
import pygame
from typing import List, Optional  # Optional for wrench hitbox typing

# Background spots layer (ambient blobs)
from .spots import SpotsLayer

# Import theme (visual constants + font builder)
from .theme import (
    WIN_W_DEFAULT, WIN_H_DEFAULT, HEADER_Y, FOOTER_Y,
    SPOTLIGHT_PERIOD, SPOT_SCALE_MAX, DEFAULT_HEADER
)
from .theme import build_fonts

# Import rendering helpers (no glow)
from .components import draw_gradient

# Import sprite class
from .bubbles import IdeaBubble

# Import backend client
from .api_client import APIClient, WallState


def rebuild_bubbles(state: WallState, fonts, win_w: int, win_h: int) -> List[IdeaBubble]:
    """
    @brief  Map current state.ideas into IdeaBubble instances.
    @param  state  Shared wall state (header + ideas).
    @param  fonts  Font dict from theme.build_fonts().
    @param  win_w  Current window width.
    @param  win_h  Current window height.
    @return List of IdeaBubble sprites.
    """
    # Build a new list of IdeaBubble objects from state.ideas
    bubbles: List[IdeaBubble] = []
    for idea in state.ideas:
        bubbles.append(IdeaBubble(idea, fonts, win_w, win_h))
    return bubbles


def draw_dev_panel(screen: pygame.Surface,
                   fonts,
                   clock: pygame.time.Clock,
                   idea_count: int,
                   show_spots: bool) -> dict:
    """
    @brief  Draw a small diagnostics panel and return interactive hitboxes.
    @param  screen       Destination surface.
    @param  fonts        Font dict from theme.build_fonts().
    @param  clock        Pygame clock (for FPS).
    @param  idea_count   Number of bubbles currently on screen.
    @param  show_spots   Whether background spots are currently enabled.
    @return Dict of named pygame.Rect hitboxes for mouse interaction.
    """
    # Panel surface (semi-transparent)
    panel_w, panel_h = 420, 140
    panel = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
    panel.fill((0, 0, 0, 120))

    # Text lines
    small = fonts["footer"]
    lines = [
        f"FPS: {int(clock.get_fps())}",
        f"Ideas: {idea_count}",
        "Toggles:",
    ]

    # Layout text
    y = 10
    for txt in lines:
        panel.blit(small.render(txt, True, (220, 230, 245)), (12, y))
        y += 22

    # Checkbox for Spots
    # - Hitbox rect will be returned so we can toggle with the mouse
    box_x, box_y = 16, y + 6
    box_rect = pygame.Rect(box_x, box_y, 18, 18)
    pygame.draw.rect(panel, (230, 240, 255), box_rect, width=2)
    if show_spots:
        # Filled check mark (simple cross)
        pygame.draw.line(panel, (230, 240, 255), (box_x + 3, box_y + 9), (box_x + 8, box_y + 14), 2)
        pygame.draw.line(panel, (230, 240, 255), (box_x + 8, box_y + 14), (box_x + 15, box_y + 4), 2)

    # Label next to the checkbox
    panel.blit(small.render("Background Spots", True, (220, 230, 245)), (box_x + 28, box_y - 2))

    # Blit panel at top-left
    screen.blit(panel, (12, 12))

    # Return absolute-screen hitboxes for interaction
    hits = {
        "spots_checkbox": pygame.Rect(12 + box_rect.x, 12 + box_rect.y, box_rect.w, box_rect.h),
        "panel_bounds": pygame.Rect(12, 12, panel_w, panel_h),
    }
    return hits


def draw_wrench_button(screen: pygame.Surface) -> pygame.Rect:
    """
    @brief  Draw a small 'wrench' circle button in the top-right.
    @return pygame.Rect for click hit-testing (screen coords).
    """
    PAD = 12
    R   = 16  # radius of button
    w, h = screen.get_size()
    cx, cy = w - (R + PAD), (R + PAD)

    # Button circle (semi-transparent)
    pygame.draw.circle(screen, (0, 0, 0, 120), (cx, cy), R)
    pygame.draw.circle(screen, (220, 230, 245), (cx, cy), R, width=2)

    # Simple 'wrench' glyph (two lines)
    pygame.draw.line(screen, (220, 230, 245), (cx - 6, cy + 5), (cx + 6, cy - 5), 2)
    pygame.draw.line(screen, (220, 230, 245), (cx - 3, cy + 6), (cx + 3, cy), 2)

    # Click rect
    return pygame.Rect(cx - R, cy - R, R * 2, R * 2)


def main() -> None:
    """
    @brief  Initialize and run the Pygame wall loop.
    @detail Handles Pygame setup, backend connection, spotlight cycling,
            bubble updates, and rendering.
    """
    # ----------------------------
    # Initialize pygame
    # ----------------------------
    pygame.init()

    # ----------------------------
    # Window + clock setup
    # ----------------------------
    win_w, win_h = WIN_W_DEFAULT, WIN_H_DEFAULT
    screen = pygame.display.set_mode((win_w, win_h), pygame.RESIZABLE)
    clock = pygame.time.Clock()

    # ----------------------------
    # Load fonts
    # ----------------------------
    fonts = build_fonts()
    header_font = fonts["header"]
    footer_font = fonts["footer"]

    # ----------------------------
    # Background spots layer (+ toggle state)
    # ----------------------------
    spots = SpotsLayer(win_w, win_h, count=8)  # adjust count to taste
    show_spots = True  # controlled via dev panel checkbox

    # ----------------------------
    # Dev panel state + last-frame hitboxes (for clicks)
    # ----------------------------
    show_dev = True                 # dev panel starts visible; click wrench to toggle
    dev_hits: dict = {}             # updated each frame by draw_dev_panel()
    wrench_hit: Optional[pygame.Rect] = None  # wrench button hitbox (top-right)

    # ----------------------------
    # Shared sprite list
    # ----------------------------
    BUBBLES: List[IdeaBubble] = []

    # ----------------------------
    # Refresh callback (rebuilds bubbles when state updates)
    # ----------------------------
    def on_refresh():
        """
        @brief  Callback invoked when header/ideas change.
        """
        nonlocal BUBBLES
        BUBBLES = rebuild_bubbles(state, fonts, win_w, win_h)

    # ----------------------------
    # State + API client
    # ----------------------------
    state = WallState(on_refresh=on_refresh)
    api = APIClient(state=state)

    # Fetch initial header + ideas
    api.fetch_initial()
    # Start websocket thread (live updates)
    api.start_websocket()
    # Start poll fallback thread
    api.start_poll_fallback(interval_sec=15.0)

    # Build initial bubbles
    BUBBLES = rebuild_bubbles(state, fonts, win_w, win_h)

    # ----------------------------
    # Spotlight state
    # ----------------------------
    spot_index = 0
    spot_t = 0.0

    # ----------------------------
    # Timing setup
    # ----------------------------
    last = time.time()
    running = True

    # ----------------------------
    # Main loop
    # ----------------------------
    while running:
        # Handle events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if event.type == pygame.VIDEORESIZE:
                # Update window size
                win_w, win_h = event.w, event.h
                screen = pygame.display.set_mode((win_w, win_h), pygame.RESIZABLE)
                # Rebuild bubbles for new wrap width
                BUBBLES = rebuild_bubbles(state, fonts, win_w, win_h)
                # Resize spots layer to new window
                spots.resize(win_w, win_h)

            # Mouse interaction: dev panel checkbox + wrench toggle
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mx, my = event.pos

                # Toggle Background Spots via checkbox in panel
                if show_dev and dev_hits and dev_hits.get("spots_checkbox") and dev_hits["spots_checkbox"].collidepoint(mx, my):
                    show_spots = not show_spots

                # Toggle dev panel via wrench button (top-right)
                if wrench_hit and wrench_hit.collidepoint(mx, my):
                    show_dev = not show_dev

        # Compute delta time
        now = time.time()
        dt = now - last
        last = now

        # Draw background gradient
        draw_gradient(screen)

        # Background spots (under all text)
        if show_spots:
            spots.update(dt, win_w, win_h)
            spots.draw(screen)

        # Draw header
        header_str = state.header or DEFAULT_HEADER
        header_surf = header_font.render(header_str, True, (93, 196, 255))
        header_rect = header_surf.get_rect(center=(win_w // 2, HEADER_Y))
        screen.blit(header_surf, header_rect)

        # Update spotlight scaling (sine ease in/out over SPOTLIGHT_PERIOD)
        if BUBBLES:
            spot_t += dt
            if spot_t >= SPOTLIGHT_PERIOD:
                spot_t = 0.0
                spot_index = (spot_index + 1) % len(BUBBLES)
            phase = spot_t / SPOTLIGHT_PERIOD
            scale_now = 1.0 + (SPOT_SCALE_MAX - 1.0) * math.sin(math.pi * phase)
        else:
            scale_now = 1.0

        # Update and render each bubble
        for i, b in enumerate(BUBBLES):
            b.update(dt, win_w, win_h)           # physics / drift
            b.scale = scale_now if i == spot_index else 1.0  # spotlight emphasis
            surf = b.surface()                   # render text-only block
            x, y = int(b.x), int(b.y)
            screen.blit(surf, (x, y))

        # Draw footer (idea count)
        footer = footer_font.render(f"Ideas submitted: {len(BUBBLES)}", True, (168, 179, 196))
        foot_rect = footer.get_rect(center=(win_w // 2, win_h - FOOTER_Y))
        screen.blit(footer, foot_rect)

        # Dev panel overlay (draw last so it sits above everything)
        if show_dev:
            dev_hits = draw_dev_panel(screen, fonts, clock, len(BUBBLES), show_spots)
        else:
            dev_hits = {}

        # Draw the wrench button (top-right) and keep its hitbox for clicks
        wrench_hit = draw_wrench_button(screen)

        # Flip buffer and cap FPS
        pygame.display.flip()
        clock.tick(60)

    # ----------------------------
    # Shutdown
    # ----------------------------
    pygame.quit()


if __name__ == "__main__":
    main()