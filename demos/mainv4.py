import pygame
import random
import math
import time
import json
import os
from typing import List, Tuple, Dict, Any
from dataclasses import dataclass, asdict
from enum import Enum

# Initialize Pygame
pygame.init()

# Constants
FPS = 60
MAX_IDEAS = 50
CONFIG_FILE = "ideas_config.json"
PRESETS_FILE = "ideas_presets.json"

# Enhanced color schemes
COLOR_SCHEMES = {
    "midnight": {
        'background': (15, 23, 42),
        'accent': (59, 130, 246),
        'text': (248, 250, 252),
        'secondary': (148, 163, 184)
    },
    "ocean": {
        'background': (12, 74, 110),
        'accent': (34, 197, 94),
        'text': (255, 255, 255),
        'secondary': (156, 163, 175)
    },
    "sunset": {
        'background': (120, 53, 15),
        'accent': (251, 191, 36),
        'text': (255, 255, 255),
        'secondary': (254, 202, 202)
    },
    "forest": {
        'background': (20, 83, 45),
        'accent': (134, 239, 172),
        'text': (255, 255, 255),
        'secondary': (187, 247, 208)
    },
    "neon": {
        'background': (0, 0, 0),
        'accent': (255, 0, 255),
        'text': (0, 255, 255),
        'secondary': (255, 255, 0)
    },
    "monochrome": {
        'background': (30, 30, 30),
        'accent': (200, 200, 200),
        'text': (255, 255, 255),
        'secondary': (150, 150, 150)
    }
}

# Enhanced idea colors with more sophisticated gradients
IDEA_COLOR_PALETTES = {
    "vibrant": [
        [(255, 179, 186), (255, 99, 132)],  # Pink
        [(162, 255, 178), (34, 197, 94)],   # Green
        [(147, 197, 253), (59, 130, 246)],  # Blue
        [(253, 224, 71), (245, 158, 11)],   # Yellow
        [(196, 181, 253), (147, 51, 234)],  # Purple
        [(134, 239, 172), (5, 150, 105)],   # Emerald
        [(251, 191, 36), (245, 101, 101)],  # Orange
        [(165, 180, 252), (99, 102, 241)]   # Indigo
    ],
    "pastel": [
        [(255, 218, 185), (255, 154, 162)],
        [(185, 251, 192), (129, 230, 217)],
        [(162, 210, 255), (138, 176, 255)],
        [(255, 241, 165), (255, 207, 102)],
        [(221, 214, 254), (196, 181, 253)],
        [(187, 247, 208), (134, 239, 172)],
        [(254, 215, 170), (251, 191, 36)],
        [(199, 210, 254), (165, 180, 252)]
    ],
    "dark": [
        [(139, 69, 19), (101, 67, 33)],
        [(25, 135, 84), (32, 201, 151)],
        [(31, 81, 255), (15, 23, 42)],
        [(218, 165, 32), (255, 215, 0)],
        [(75, 0, 130), (138, 43, 226)],
        [(0, 100, 0), (50, 205, 50)],
        [(255, 140, 0), (255, 69, 0)],
        [(72, 61, 139), (106, 90, 205)]
    ]
}

@dataclass
class VisualSettings:
    """Comprehensive visual settings for the application"""
    # Movement
    speed_multiplier: float = 1.0
    float_amplitude: float = 0.5
    bounce_randomness: float = 1.0
    gravity_strength: float = 0.0
    wind_strength: float = 0.0
    
    # Visual
    idea_font_size: int = 50
    entrance_duration: float = 1.0
    particle_count: int = 10
    glow_intensity: float = 0.0
    trail_length: int = 0
    
    # Background
    bg_particle_count: int = 50
    bg_particle_speed: float = 0.5
    background_color: Tuple[int, int, int] = (15, 23, 42)
    
    # Advanced
    color_scheme: str = "midnight"
    idea_palette: str = "vibrant"
    auto_cleanup: bool = True
    collision_detection: bool = False
    physics_enabled: bool = False
    
    # Performance
    vsync_enabled: bool = True
    show_fps: bool = False
    particle_optimization: bool = True
    target_fps: int = 60
    
    # New color controls
    primary_color: Tuple[int, int, int] = (59, 130, 246)
    secondary_color: Tuple[int, int, int] = (34, 197, 94)
    accent_color: Tuple[int, int, int] = (245, 158, 11)

class AdvancedSlider:
    """Enhanced slider with better UX and features"""
    def __init__(self, x, y, width, height, min_val, max_val, initial_val, label, 
                 decimal_places=2, step=None):
        self.rect = pygame.Rect(x, y, width, height)
        self.min_val = min_val
        self.max_val = max_val
        self.val = initial_val
        self.label = label
        self.decimal_places = decimal_places
        self.step = step
        self.dragging = False
        self.hovered = False
        self.handle_rect = pygame.Rect(0, 0, 16, height + 6)
        self.track_rect = pygame.Rect(x, y + height//2 - 2, width, 4)
        self.update_handle_pos()
        
        # Animation
        self.hover_scale = 1.0
        self.target_hover_scale = 1.0
    
    def update_handle_pos(self):
        progress = (self.val - self.min_val) / (self.max_val - self.min_val)
        handle_x = self.rect.x + progress * (self.rect.width - self.handle_rect.width)
        self.handle_rect.x = handle_x
        self.handle_rect.y = self.rect.y - 3
    
    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.hovered = self.handle_rect.collidepoint(event.pos)
            self.target_hover_scale = 1.2 if self.hovered else 1.0
            
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.handle_rect.collidepoint(event.pos):
                self.dragging = True
            elif self.track_rect.collidepoint(event.pos):
                # Click on track to jump to position
                rel_x = event.pos[0] - self.rect.x - self.handle_rect.width // 2
                progress = max(0, min(1, rel_x / (self.rect.width - self.handle_rect.width)))
                self.val = self.min_val + progress * (self.max_val - self.min_val)
                if self.step:
                    self.val = round(self.val / self.step) * self.step
                self.update_handle_pos()
                
        elif event.type == pygame.MOUSEBUTTONUP:
            self.dragging = False
        elif event.type == pygame.MOUSEMOTION and self.dragging:
            rel_x = event.pos[0] - self.rect.x - self.handle_rect.width // 2
            progress = max(0, min(1, rel_x / (self.rect.width - self.handle_rect.width)))
            self.val = self.min_val + progress * (self.max_val - self.min_val)
            if self.step:
                self.val = round(self.val / self.step) * self.step
            self.update_handle_pos()
    
    def update(self):
        # Smooth hover animation
        self.hover_scale += (self.target_hover_scale - self.hover_scale) * 0.2
    
    def render(self, screen, font):
        # Draw track
        track_color = (80, 80, 100) if not self.hovered else (100, 100, 120)
        pygame.draw.rect(screen, track_color, self.track_rect, border_radius=2)
        
        # Draw progress
        progress_width = (self.val - self.min_val) / (self.max_val - self.min_val) * self.track_rect.width
        progress_rect = pygame.Rect(self.track_rect.x, self.track_rect.y, progress_width, self.track_rect.height)
        pygame.draw.rect(screen, (100, 150, 255), progress_rect, border_radius=2)
        
        # Draw handle with hover effect
        handle_size = int(self.handle_rect.width * self.hover_scale)
        handle_y_offset = int((self.handle_rect.width - handle_size) / 2)
        handle_rect = pygame.Rect(
            self.handle_rect.x + (self.handle_rect.width - handle_size) // 2,
            self.handle_rect.y + handle_y_offset,
            handle_size,
            handle_size
        )
        
        handle_color = (120, 170, 255) if self.hovered or self.dragging else (100, 150, 255)
        pygame.draw.ellipse(screen, handle_color, handle_rect)
        pygame.draw.ellipse(screen, (200, 200, 220), handle_rect, 2)
        
        # Draw label and value
        if self.decimal_places == 0:
            value_str = f"{int(self.val)}"
        else:
            value_str = f"{self.val:.{self.decimal_places}f}"
        
        label_text = f"{self.label}: {value_str}"
        text_surface = font.render(label_text, True, (220, 220, 240))
        screen.blit(text_surface, (self.rect.x, self.rect.y - 25))

class ColorPicker:
    def __init__(self, x, y, width, height, initial_color, label):
        self.rect = pygame.Rect(x, y, width, height)
        self.color = initial_color
        self.label = label
        self.r_slider = AdvancedSlider(x, y + 30, width - 50, 20, 0, 255, initial_color[0], "R", 0)
        self.g_slider = AdvancedSlider(x, y + 60, width - 50, 20, 0, 255, initial_color[1], "G", 0)
        self.b_slider = AdvancedSlider(x, y + 90, width - 50, 20, 0, 255, initial_color[2], "B", 0)
        self.color_preview = pygame.Rect(x + width - 40, y + 30, 30, 60)
    
    def handle_event(self, event):
        self.r_slider.handle_event(event)
        self.g_slider.handle_event(event)
        self.b_slider.handle_event(event)
        self.color = (int(self.r_slider.val), int(self.g_slider.val), int(self.b_slider.val))
    
    def update(self):
        self.r_slider.update()
        self.g_slider.update()
        self.b_slider.update()
    
    def render(self, screen, font):
        # Draw label
        text_surface = font.render(self.label, True, (220, 220, 240))
        screen.blit(text_surface, (self.rect.x, self.rect.y))
        
        # Draw sliders
        self.r_slider.render(screen, font)
        self.g_slider.render(screen, font)
        self.b_slider.render(screen, font)
        
        # Draw color preview
        pygame.draw.rect(screen, self.color, self.color_preview)
        pygame.draw.rect(screen, (100, 100, 120), self.color_preview, 2)

class DropdownMenu:
    def __init__(self, x, y, width, height, options, initial_selection, label):
        self.rect = pygame.Rect(x, y, width, height)
        self.options = options
        self.selected = initial_selection
        self.label = label
        self.expanded = False
        self.option_rects = []
        self.hovered_option = -1
        
        # Create option rectangles
        for i in range(len(options)):
            option_rect = pygame.Rect(x, y + height + i * height, width, height)
            self.option_rects.append(option_rect)
    
    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos):
                self.expanded = not self.expanded
                return None
            elif self.expanded:
                for i, option_rect in enumerate(self.option_rects):
                    if option_rect.collidepoint(event.pos):
                        self.selected = self.options[i]
                        self.expanded = False
                        return self.selected
                # Click outside closes dropdown
                self.expanded = False
        
        elif event.type == pygame.MOUSEMOTION and self.expanded:
            self.hovered_option = -1
            for i, option_rect in enumerate(self.option_rects):
                if option_rect.collidepoint(event.pos):
                    self.hovered_option = i
                    break
        
        return None
    
    def render(self, screen, font):
        # Draw label
        label_surface = font.render(self.label, True, (220, 220, 240))
        screen.blit(label_surface, (self.rect.x, self.rect.y - 25))
        
        # Draw main button
        button_color = (60, 70, 90) if not self.expanded else (80, 90, 110)
        pygame.draw.rect(screen, button_color, self.rect, border_radius=5)
        pygame.draw.rect(screen, (120, 130, 150), self.rect, 2, border_radius=5)
        
        # Draw selected text
        selected_surface = font.render(self.selected, True, (220, 220, 240))
        text_rect = selected_surface.get_rect(center=(self.rect.centerx - 10, self.rect.centery))
        screen.blit(selected_surface, text_rect)
        
        # Draw arrow
        arrow_points = [(self.rect.right - 15, self.rect.centery - 3),
                       (self.rect.right - 10, self.rect.centery + 3),
                       (self.rect.right - 5, self.rect.centery - 3)]
        pygame.draw.polygon(screen, (180, 180, 200), arrow_points)
        
        # Draw dropdown options if expanded
        if self.expanded:
            for i, (option, option_rect) in enumerate(zip(self.options, self.option_rects)):
                if i >= len(self.options):
                    break
                    
                # Option background
                bg_color = (80, 90, 110) if i == self.hovered_option else (50, 60, 80)
                pygame.draw.rect(screen, bg_color, option_rect, border_radius=3)
                pygame.draw.rect(screen, (120, 130, 150), option_rect, 1, border_radius=3)
                
                # Option text
                option_surface = font.render(option, True, (220, 220, 240))
                option_text_rect = option_surface.get_rect(center=option_rect.center)
                screen.blit(option_surface, option_text_rect)

class PresetManager:
    """Manages saving and loading of visual presets"""
    def __init__(self):
        self.presets = self.load_presets()
        self.current_preset = "Custom"
    
    def load_presets(self) -> Dict[str, Dict]:
        """Load presets from file"""
        default_presets = {
            "Default": asdict(VisualSettings()),
            "Energetic": asdict(VisualSettings(
                speed_multiplier=2.0, bounce_randomness=1.5, 
                particle_count=20, float_amplitude=1.2
            )),
            "Calm": asdict(VisualSettings(
                speed_multiplier=0.3, bounce_randomness=0.5,
                particle_count=5, float_amplitude=0.3
            )),
            "Neon Dreams": asdict(VisualSettings(
                color_scheme="neon", idea_palette="dark",
                glow_intensity=0.8, particle_count=30
            )),
            "Professional": asdict(VisualSettings(
                color_scheme="monochrome", idea_palette="dark",
                speed_multiplier=0.8, particle_count=8
            ))
        }
        
        if os.path.exists(PRESETS_FILE):
            try:
                with open(PRESETS_FILE, 'r') as f:
                    loaded = json.load(f)
                    default_presets.update(loaded)
            except:
                pass
        
        return default_presets
    
    def save_presets(self):
        """Save presets to file"""
        try:
            with open(PRESETS_FILE, 'w') as f:
                json.dump(self.presets, f, indent=2)
        except:
            pass
    
    def save_preset(self, name: str, settings: VisualSettings):
        """Save current settings as a preset"""
        self.presets[name] = asdict(settings)
        self.save_presets()
        self.current_preset = name
    
    def load_preset(self, name: str) -> VisualSettings:
        """Load a preset by name"""
        if name in self.presets:
            self.current_preset = name
            return VisualSettings(**self.presets[name])
        return VisualSettings()

class EnhancedParticle:
    """More sophisticated particle system"""
    def __init__(self, x, y, color, particle_type="default"):
        self.x = x
        self.y = y
        self.start_x = x
        self.start_y = y
        self.color = color
        self.particle_type = particle_type
        
        if particle_type == "spark":
            self.vx = random.uniform(-4, 4)
            self.vy = random.uniform(-4, 4)
            self.size = random.uniform(1, 3)
            self.life = 1.0
            self.decay = random.uniform(0.02, 0.05)
        elif particle_type == "float":
            self.vx = random.uniform(-1, 1)
            self.vy = random.uniform(-2, -0.5)
            self.size = random.uniform(2, 6)
            self.life = 1.0
            self.decay = random.uniform(0.005, 0.02)
        else:  # default
            self.vx = random.uniform(-2, 2)
            self.vy = random.uniform(-2, 2)
            self.size = random.uniform(2, 5)
            self.life = 1.0
            self.decay = random.uniform(0.005, 0.02)
        
        self.gravity = 0.1 if particle_type == "float" else 0
    
    def update(self, wind_strength=0):
        self.x += self.vx + wind_strength
        self.y += self.vy
        self.vy += self.gravity
        self.life -= self.decay
        
        # Add some physics
        if self.particle_type == "spark":
            self.vx *= 0.98  # Air resistance
            self.vy *= 0.98
    
    def render(self, screen):
        if self.life > 0:
            alpha = max(0, min(255, int(255 * self.life)))
            size = max(1, int(self.size * self.life))
            
            # Add glow effect for certain types
            if self.particle_type == "spark" and size > 2:
                pygame.draw.circle(screen, self.color[:3], (int(self.x), int(self.y)), size + 2)
            
            pygame.draw.circle(screen, self.color[:3], (int(self.x), int(self.y)), size)



class AdvancedFloatingIdea:
    """Enhanced floating idea with more features"""
    def __init__(self, text: str, x: float, y: float, font, settings: VisualSettings):
        self.text = text
        self.original_text = text
        self.x = x
        self.y = y
        self.start_x = x
        self.start_y = y
        
        # Enhanced movement
        base_speed = 0.8
        self.speed_x = random.uniform(-base_speed, base_speed) * settings.speed_multiplier
        self.speed_y = random.uniform(-base_speed, base_speed) * settings.speed_multiplier
        self.original_speed_x = self.speed_x
        self.original_speed_y = self.speed_y
        
        # Physics
        self.velocity_x = 0
        self.velocity_y = 0
        self.mass = len(text) * 0.1 + 1  # Mass based on text length
        
        # Visual properties
        palette = IDEA_COLOR_PALETTES.get(settings.idea_palette, IDEA_COLOR_PALETTES["vibrant"])
        self.colors = random.choice(palette)
        self.font = font
        self.alpha = 0
        self.scale = 0.1
        self.rotation = 0
        
        # Enhanced animation
        self.birth_time = time.time()
        self.phase_offset = random.uniform(0, math.pi * 2)
        self.float_amplitude = random.uniform(0.3, 0.8) * settings.float_amplitude
        
        # Trail effect
        self.trail_points = []
        self.max_trail_length = settings.trail_length
        
        # Enhanced particles
        self.particles = []
        particle_types = ["default", "spark", "float"]
        for _ in range(settings.particle_count):
            p_type = random.choice(particle_types) if settings.particle_count > 15 else "default"
            self.particles.append(EnhancedParticle(x, y, self.colors[0], p_type))
        
        # Store settings
        self.settings = settings
        
        # Advanced properties
        self.health = 100.0
        self.age = 0
        self.highlight = False
        self.selected = False
        
       # Likes: keep count & click area; no size/glow/heart state
        self.likes = 0
        self.click_rect = None  # Will be set during render
        self.like_particles = []  # optional small spark burst on like
    
    def add_like(self):
        """Add a like (no size change)."""
        self.likes += 1

        # Safe spawn position even if update() hasn't run yet
        px = getattr(self, "final_x", self.x)
        py = getattr(self, "final_y", self.y)

        for _ in range(6):
            p = EnhancedParticle(px, py, (255, 100, 150), "spark")
            p.vx = random.uniform(-3, 3)
            p.vy = random.uniform(-4, -1)
            p.life = 1.2
            p.decay = 0.03
            self.like_particles.append(p)

        print(f"Idea '{self.text[:20]}...' now has {self.likes} likes!")
    
    def is_clicked(self, pos):
        """Check if this idea was clicked"""
        if self.click_rect and self.click_rect.collidepoint(pos):
            return True
        return False
    
    def update_font(self, new_font):
        """Update the font for dynamic font size changes"""
        self.font = new_font
    
    def add_to_trail(self):
        if self.max_trail_length > 0:
            self.trail_points.append((self.final_x, self.final_y, time.time()))
            if len(self.trail_points) > self.max_trail_length:
                self.trail_points.pop(0)
    
    def update(self, settings: VisualSettings, wind_strength=0, gravity_strength=0):
        current_time = time.time()
        self.age = current_time - self.birth_time
        
        # Update like particles
        self.like_particles = [p for p in self.like_particles if p.life > 0]
        for particle in self.like_particles:
            particle.update(wind_strength * 0.1)
        
        # Entrance animation: fade/scale in, then lock at 1.0
        if self.age < settings.entrance_duration:
            progress = self.age / settings.entrance_duration
            self.alpha = int(255 * min(1.0, progress))
            # Entrance animation only (no like-based scaling)
            self.scale = 0.3 + 0.7 * min(1.0, progress * 2)
        else:
            self.alpha = 255
            # Keep constant size after entrance
            self.scale = 1.0
        
        # Physics-based movement if enabled
        if settings.physics_enabled:
            # Apply forces
            self.velocity_x += wind_strength / self.mass
            self.velocity_y += gravity_strength / self.mass
            
            # Apply velocity
            self.x += self.velocity_x * settings.speed_multiplier
            self.y += self.velocity_y * settings.speed_multiplier
            
            # Damping
            self.velocity_x *= 0.99
            self.velocity_y *= 0.99
        else:
            # Original movement system
            self.x += self.speed_x * settings.speed_multiplier
            self.y += self.speed_y * settings.speed_multiplier
        
        # Enhanced wave motion
        wave_time = current_time * 0.5
        wave_x = math.sin(wave_time + self.phase_offset) * self.float_amplitude * settings.float_amplitude
        wave_y = math.cos(wave_time * 0.7 + self.phase_offset) * self.float_amplitude * 0.5 * settings.float_amplitude
        
        # Collision detection and bouncing
        margin = 50
        screen_width = pygame.display.get_surface().get_width()
        screen_height = pygame.display.get_surface().get_height()
        
        if self.x <= margin or self.x >= screen_width - margin:
            if settings.physics_enabled:
                self.velocity_x *= -0.8
            else:
                random_factor = random.uniform(0.8, 1.2) * settings.bounce_randomness
                self.speed_x *= -random_factor
                self.speed_x = max(-1.2 * settings.speed_multiplier, 
                                 min(1.2 * settings.speed_multiplier, self.speed_x))
            self.x = max(margin, min(screen_width - margin, self.x))
            
        if self.y <= margin or self.y >= screen_height - 150:
            if settings.physics_enabled:
                self.velocity_y *= -0.8
            else:
                random_factor = random.uniform(0.8, 1.2) * settings.bounce_randomness
                self.speed_y *= -random_factor
                self.speed_y = max(-1.2 * settings.speed_multiplier, 
                                 min(1.2 * settings.speed_multiplier, self.speed_y))
            self.y = max(margin, min(screen_height - 150, self.y))
        
        # Final position with wave
        self.final_x = self.x + wave_x
        self.final_y = self.y + wave_y
        
        # Update trail
        self.add_to_trail()
        
        # Rotation based on movement
        if settings.physics_enabled:
            self.rotation = math.atan2(self.velocity_y, self.velocity_x) * 0.1
        else:
            self.rotation = math.atan2(self.speed_y, self.speed_x) * 0.1
        
        # Update particles
        if not settings.particle_optimization or len(self.particles) < 100:
            self.particles = [p for p in self.particles if p.life > 0]
            for particle in self.particles:
                particle.update(wind_strength * 0.1)
    
    def is_expired(self):
        return False  # Ideas are permanent unless manually removed
    
    def render(self, screen, settings: VisualSettings):
        if self.alpha > 10:
            # Render like particles first (behind text)
            for particle in self.like_particles:
                particle.render(screen)
            
            # Render trail
            if self.trail_points:
                current_time = time.time()
                for i, (x, y, timestamp) in enumerate(self.trail_points):
                    age = current_time - timestamp
                    trail_alpha = max(0, int(100 * (1 - age)))
                    if trail_alpha > 0:
                        trail_color = (*self.colors[0][:3], trail_alpha)
                        size = max(1, int((i + 1) * 2))
                        pygame.draw.circle(screen, trail_color[:3], (int(x), int(y)), size)
            
            # Render particles
            for particle in self.particles:
                particle.render(screen)
            
            # Create text surface
            text_surface = self.font.render(self.text, True, self.colors[0])
            
            # Apply transformations
            text_rect = text_surface.get_rect()
            if self.scale != 1.0 or self.rotation != 0:
                scaled_size = (int(text_rect.width * self.scale), int(text_rect.height * self.scale))
                if scaled_size[0] > 0 and scaled_size[1] > 0:
                    text_surface = pygame.transform.scale(text_surface, scaled_size)
                if self.rotation != 0:
                    text_surface = pygame.transform.rotate(text_surface, math.degrees(self.rotation))
            
            text_surface.set_alpha(self.alpha)
            text_rect = text_surface.get_rect(center=(self.final_x, self.final_y))
            
            # Store click area
            self.click_rect = text_rect.inflate(20, 20)
            
            # --- Subtle glow (small, capped) ---
            total_glow = min(0.35, float(getattr(settings, "glow_intensity", 0.3)))  # cap
            if total_glow > 0:
                glow_surface = text_surface.copy()
                glow_alpha = int(self.alpha * total_glow * 0.6)  # softer
                glow_surface.set_alpha(glow_alpha)

                # small ring of offsets instead of a big square
                glow_radius = 2 if self.likes == 0 else 3
                offsets = []
                for r in range(1, glow_radius + 1):
                    offsets += [(-r, 0), (r, 0), (0, -r), (0, r), (-r, -r), (r, -r), (-r, r), (r, r)]

                for dx, dy in offsets:
                    glow_rect = text_rect.copy()
                    glow_rect.x += dx
                    glow_rect.y += dy
                    screen.blit(glow_surface, glow_rect)
            
            # Selection highlight
            if self.selected:
                highlight_rect = text_rect.inflate(20, 20)
                pygame.draw.rect(screen, (255, 255, 0), highlight_rect, 3)
            
            # Render main text
            screen.blit(text_surface, text_rect)

            # Always show like count once there is at least one like
            if self.likes > 0:
                # 60% of the idea font height → small badge
                count_font_size = max(12, int(self.font.get_height() * 0.6))
                count_font = pygame.font.Font(None, count_font_size)

                like_text = str(self.likes)  # keep it numeric so no missing-glyph boxes
                count_surface = count_font.render(like_text, True, (255, 255, 255))
                count_rect = count_surface.get_rect(midleft=(text_rect.right + 8, text_rect.centery))
                screen.blit(count_surface, count_rect)

                # expand the clickable area to include the count
                if self.click_rect:
                    self.click_rect = self.click_rect.union(count_rect)
                else:
                    self.click_rect = count_rect.copy()



class EnhancedInputBox:
    """Professional input box with advanced features (cleaned & self-contained)"""
    def __init__(self, x, y, width, height, font):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = ""
        self.font = font
        self.active = False
        self.cursor_pos = 0
        self.cursor_visible = True
        self.cursor_timer = 0
        self.placeholder = "Share your brilliant idea... (Click ideas to like them!)"

        # Enhancements
        self.text_history = []
        self.history_index = -1
        self.auto_complete_suggestions = []
        self.show_suggestions = False

        # Visual
        self.border_glow = 0
        self.target_glow = 0

        # Common suggestions
        self.suggestions = [
            "Innovation", "Creativity", "Problem solving", "Team collaboration",
            "User experience", "Sustainability", "Digital transformation",
            "Artificial intelligence", "Data analytics", "Remote work"
        ]

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            was_active = self.active
            self.active = self.rect.collidepoint(event.pos)
            if self.active and not was_active:
                self.target_glow = 20
            elif not self.active and was_active:
                self.target_glow = 0

        if event.type == pygame.KEYDOWN and self.active:
            # Submit (Enter, but not Ctrl+Enter)
            if event.key == pygame.K_RETURN and not (pygame.key.get_pressed()[pygame.K_LCTRL]):
                result = self.text.strip()
                if result:
                    self.text_history.append(result)
                    if len(self.text_history) > 50:
                        self.text_history.pop(0)
                
                # 🔑 Clear the input box after pressing Enter
                self.text = ""
                self.cursor_pos = 0
                self.history_index = -1
                self.show_suggestions = False

                return result

            elif event.key == pygame.K_BACKSPACE:
                if self.cursor_pos > 0:
                    self.text = self.text[:self.cursor_pos-1] + self.text[self.cursor_pos:]
                    self.cursor_pos -= 1
                    self.update_suggestions()

            elif event.key == pygame.K_DELETE:
                if self.cursor_pos < len(self.text):
                    self.text = self.text[:self.cursor_pos] + self.text[self.cursor_pos+1:]

            elif event.key == pygame.K_LEFT:
                self.cursor_pos = max(0, self.cursor_pos - 1)

            elif event.key == pygame.K_RIGHT:
                self.cursor_pos = min(len(self.text), self.cursor_pos + 1)

            elif event.key == pygame.K_HOME:
                self.cursor_pos = 0

            elif event.key == pygame.K_END:
                self.cursor_pos = len(self.text)

            # History navigation
            elif event.key == pygame.K_UP and self.text_history:
                if self.history_index < len(self.text_history) - 1:
                    self.history_index += 1
                    self.text = self.text_history[-(self.history_index + 1)]
                    self.cursor_pos = len(self.text)

            elif event.key == pygame.K_DOWN and self.history_index >= 0:
                self.history_index -= 1
                if self.history_index >= 0:
                    self.text = self.text_history[-(self.history_index + 1)]
                else:
                    self.text = ""
                self.cursor_pos = len(self.text)

            # Tab completion
            elif event.key == pygame.K_TAB and self.auto_complete_suggestions and self.active:
                self.text = self.auto_complete_suggestions[0]
                self.cursor_pos = len(self.text)
                self.show_suggestions = False
                return None

            else:
                # Normal character input
                if len(self.text) < 200 and event.unicode and event.unicode.isprintable():
                    self.text = self.text[:self.cursor_pos] + event.unicode + self.text[self.cursor_pos:]
                    self.cursor_pos += 1
                    self.update_suggestions()

        return None

    def update_suggestions(self):
        """Update auto-complete suggestions based on current text."""
        if len(self.text) >= 2:
            self.auto_complete_suggestions = [
                s for s in self.suggestions
                if s.lower().startswith(self.text.lower()) and s.lower() != self.text.lower()
            ]
            self.show_suggestions = len(self.auto_complete_suggestions) > 0
        else:
            self.auto_complete_suggestions = []
            self.show_suggestions = False

    def update(self):
        # Cursor blinking
        self.cursor_timer += 1
        if self.cursor_timer >= 30:
            self.cursor_visible = not self.cursor_visible
            self.cursor_timer = 0

        # Smooth glow animation
        self.border_glow += (self.target_glow - self.border_glow) * 0.1

    def render(self, screen):
        # Enhanced border with glow
        border_color = (71 + int(self.border_glow), 85 + int(self.border_glow), 105 + int(self.border_glow))

        # Background
        bg_color = (51, 65, 85) if self.active else (30, 41, 59)
        pygame.draw.rect(screen, bg_color, self.rect, border_radius=10)
        pygame.draw.rect(screen, border_color, self.rect, 2, border_radius=10)

        # Text (or placeholder)
        display_text = self.text if self.text else self.placeholder
        text_color = (248, 250, 252) if self.text else (148, 163, 184)

        text_surface = self.font.render(display_text, True, text_color)
        # Truncate if too wide
        if text_surface.get_width() > self.rect.width - 30:
            visible_text = display_text
            while self.font.size(visible_text)[0] > self.rect.width - 30 and len(visible_text) > 0:
                visible_text = visible_text[1:]
            text_surface = self.font.render(visible_text, True, text_color)

        text_x = self.rect.x + 15
        text_y = self.rect.y + (self.rect.height - text_surface.get_height()) // 2
        screen.blit(text_surface, (text_x, text_y))

        # Cursor
        if self.active and self.cursor_visible:
            cursor_text = self.text[:self.cursor_pos]
            cursor_width = self.font.size(cursor_text)[0] if cursor_text else 0
            cursor_x = self.rect.x + 15 + cursor_width
            cursor_y = self.rect.y + 8
            cursor_alpha = int(128 + 127 * math.sin(time.time() * 5))
            cursor_color = (248, 250, 252, cursor_alpha)
            pygame.draw.line(screen, cursor_color[:3],
                             (cursor_x, cursor_y), (cursor_x, cursor_y + self.rect.height - 16), 3)

        # Suggestions
        if self.show_suggestions and self.auto_complete_suggestions:
            suggestion_y = self.rect.bottom + 5
            for i, suggestion in enumerate(self.auto_complete_suggestions[:5]):
                suggestion_rect = pygame.Rect(self.rect.x, suggestion_y + i * 25,
                                              min(200, self.rect.width), 23)
                pygame.draw.rect(screen, (40, 50, 70), suggestion_rect, border_radius=5)
                pygame.draw.rect(screen, (80, 90, 110), suggestion_rect, 1, border_radius=5)
                suggestion_surface = self.font.render(suggestion, True, (200, 200, 220))
                screen.blit(suggestion_surface, (suggestion_rect.x + 8, suggestion_rect.y + 4))



class ProfessionalIdeasDisplay:
    """Main application class with professional features"""
    def __init__(self):
        pygame.display.init()
        
        # Initialize settings FIRST (before everything else)
        self.settings = VisualSettings()
        self.preset_manager = PresetManager()
        
        # Display setup
        self.setup_display()
        
        # Load saved configuration
        self.load_config()
        
        # Load professional fonts (now that settings exist)
        self.setup_fonts()
        
        # Initialize systems
        self.dev_panel = ProfessionalDeveloperPanel(self.screen_width - 450, 50, 440, 700)
        
        # Initialize UI
        self.setup_ui()
        
        # Application state
        self.ideas: List[AdvancedFloatingIdea] = []
        self.running = True
        self.fullscreen = False
        self.paused = False
        self.show_help = False
        
        # Performance monitoring
        self.fps_counter = 0
        self.fps_timer = time.time()
        self.current_fps = 60
        
        # Background system
        self.bg_particles = []
        self.regenerate_bg_particles()
        
        # Statistics
        self.stats = {
            'total_ideas': 0,
            'session_time': time.time(),
            'ideas_per_minute': 0,
            'total_likes': 0
        }
    
    def update(self):
        # Cursor blinking
        self.cursor_timer += 1
        if self.cursor_timer >= 30:
            self.cursor_visible = not self.cursor_visible
            self.cursor_timer = 0
        
        # Smooth glow animation
        self.border_glow += (self.target_glow - self.border_glow) * 0.1
    
    def render(self, screen):
        # Enhanced border with glow
        border_color = (71 + int(self.border_glow), 85 + int(self.border_glow), 105 + int(self.border_glow))
        
        # Background
        bg_color = (51, 65, 85) if self.active else (30, 41, 59)
        pygame.draw.rect(screen, bg_color, self.rect, border_radius=10)
        pygame.draw.rect(screen, border_color, self.rect, 2, border_radius=10)
        
        # Text rendering with better typography
        display_text = self.text if self.text else self.placeholder
        text_color = (248, 250, 252) if self.text else (148, 163, 184)
        
        if display_text:
            # Handle text overflow
            text_surface = self.font.render(display_text, True, text_color)
            text_width = text_surface.get_width()
            
            if text_width > self.rect.width - 30:
                # Scroll text if too long
                visible_text = display_text
                while self.font.size(visible_text)[0] > self.rect.width - 30 and len(visible_text) > 0:
                    visible_text = visible_text[1:]
                text_surface = self.font.render(visible_text, True, text_color)
            
            text_x = self.rect.x + 15
            text_y = self.rect.y + (self.rect.height - text_surface.get_height()) // 2
            screen.blit(text_surface, (text_x, text_y))
        
        # Enhanced cursor
        if self.active and self.cursor_visible:
            cursor_text = self.text[:self.cursor_pos]
            cursor_width = self.font.size(cursor_text)[0] if cursor_text else 0
            cursor_x = self.rect.x + 15 + cursor_width
            cursor_y = self.rect.y + 8
            
            # Animated cursor
            cursor_alpha = int(128 + 127 * math.sin(time.time() * 5))
            cursor_color = (248, 250, 252, cursor_alpha)
            pygame.draw.line(screen, cursor_color[:3], 
                           (cursor_x, cursor_y), (cursor_x, cursor_y + self.rect.height - 16), 3)
        
        # Auto-complete suggestions
        if self.show_suggestions and self.auto_complete_suggestions:
            suggestion_y = self.rect.bottom + 5
            for i, suggestion in enumerate(self.auto_complete_suggestions):
                suggestion_rect = pygame.Rect(self.rect.x, suggestion_y + i * 25, 
                                            min(200, self.rect.width), 23)
                pygame.draw.rect(screen, (40, 50, 70), suggestion_rect, border_radius=5)
                pygame.draw.rect(screen, (80, 90, 110), suggestion_rect, 1, border_radius=5)
                
                suggestion_surface = self.font.render(suggestion, True, (200, 200, 220))
                screen.blit(suggestion_surface, (suggestion_rect.x + 8, suggestion_rect.y + 4))

    def setup_display(self):
        """Initialize display with optimal settings"""
        self.screen_width = 1600
        self.screen_height = 1000
        
        # Try to get optimal display mode
        info = pygame.display.Info()
        if info.current_w >= 1600 and info.current_h >= 1000:
            self.screen_width = min(1600, info.current_w - 100)
            self.screen_height = min(1000, info.current_h - 100)
        
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))
        pygame.display.set_caption("✨ Professional Floating Ideas Display v2.0 - Click to Like!")
        
        # Set application icon (if available)
        try:
            icon = pygame.Surface((32, 32))
            icon.fill((59, 130, 246))
            pygame.draw.circle(icon, (255, 255, 255), (16, 16), 12)
            pygame.display.set_icon(icon)
        except:
            pass
        
        self.clock = pygame.time.Clock()
    
    def setup_fonts(self):
        """Load and configure professional fonts"""
        self.fonts = {}
        
        # Professional font options
        font_families = [
            'Segoe UI', 'Arial', 'Helvetica Neue', 'San Francisco',
            'Roboto', 'Open Sans', 'Inter', 'Source Sans Pro'
        ]
        
        self.base_font_name = None
        for font_name in font_families:
            try:
                test_font = pygame.font.SysFont(font_name, 24)
                if test_font:
                    self.base_font_name = font_name
                    break
            except:
                continue
        
        # Create font sizes
        font_sizes = {
            'small': 16,
            'normal': 20,
            'medium': 24,
            'large': 32,
            'title': 48,
            'huge': 64
        }
        
        for size_name, size in font_sizes.items():
            try:
                if self.base_font_name:
                    self.fonts[size_name] = pygame.font.SysFont(self.base_font_name, size)
                    self.fonts[f'{size_name}_bold'] = pygame.font.SysFont(self.base_font_name, size, bold=True)
                else:
                    self.fonts[size_name] = pygame.font.Font(None, size)
                    self.fonts[f'{size_name}_bold'] = pygame.font.Font(None, size)
            except:
                self.fonts[size_name] = pygame.font.Font(None, size)
                self.fonts[f'{size_name}_bold'] = pygame.font.Font(None, size)
        
        # Update idea font
        self.update_idea_font(self.settings.idea_font_size)
    
    def setup_ui(self):
        """Initialize UI elements"""
        input_y = self.screen_height - 80
        input_width = min(900, self.screen_width - 550)
        
        self.input_box = EnhancedInputBox(50, input_y, input_width, 50, self.fonts['medium'])
        
        # Enhanced button with better styling
        self.submit_button = self.create_button(
            input_width + 70, input_y, 140, 50, "Add Idea", self.add_current_idea
        )
        
        # Additional UI buttons
        self.clear_button = self.create_button(
            input_width + 220, input_y, 100, 50, "Clear All", self.clear_all_ideas
        )
        
        # Quick preset buttons
        self.preset_buttons = []
        presets = ["Calm", "Energetic", "Professional"]
        for i, preset in enumerate(presets):
            btn = self.create_button(
                50 + i * 120, 20, 110, 30, preset, 
                lambda p=preset: self.apply_quick_preset(p)
            )
            self.preset_buttons.append(btn)
    
    def create_button(self, x, y, width, height, text, callback):
        """Create a styled button"""
        return {
            'rect': pygame.Rect(x, y, width, height),
            'text': text,
            'callback': callback,
            'hovered': False,
            'pressed': False,
            'font': self.fonts['normal_bold']
        }
    
    def update_idea_font(self, size):
        """Update font for ideas"""
        try:
            if self.base_font_name:
                self.idea_font = pygame.font.SysFont(self.base_font_name, int(size))
            else:
                self.idea_font = pygame.font.Font(None, int(size))
            
            # Update existing ideas
            for idea in self.ideas:
                idea.update_font(self.idea_font)
        except:
            self.idea_font = pygame.font.Font(None, int(size))
    
    def load_config(self):
        """Load configuration from file"""
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r') as f:
                    config = json.load(f)
                    self.settings = VisualSettings(**config)
            except:
                pass
    
    def save_config(self):
        """Save current configuration"""
        try:
            with open(CONFIG_FILE, 'w') as f:
                json.dump(asdict(self.settings), f, indent=2)
        except:
            pass
    
    def regenerate_bg_particles(self):
        """Generate background particles"""
        self.bg_particles = []
        for _ in range(int(self.settings.bg_particle_count)):
            self.bg_particles.append({
                'x': random.randint(0, self.screen_width),
                'y': random.randint(0, self.screen_height),
                'vx': random.uniform(-0.5, 0.5) * self.settings.bg_particle_speed,
                'vy': random.uniform(-0.5, 0.5) * self.settings.bg_particle_speed,
                'size': random.uniform(1, 4),
                'alpha': random.randint(30, 80),
                'color': random.choice([(100, 116, 139), (59, 130, 246), (34, 197, 94)])
            })
    
    def add_current_idea(self):
        """Add idea from input box"""
        text = self.input_box.text.strip()
        if text:
            self.add_idea(text)
            self.input_box.text = ""
            self.input_box.cursor_pos = 0
            self.input_box.history_index = -1
    
    def add_idea(self, text: str):
        """Add a new floating idea"""
        # Clean up old ideas if at limit
        while len(self.ideas) >= MAX_IDEAS:
            self.ideas.pop(0)
        
        # Smart positioning to avoid overlaps
        position = self.find_good_position()
        
        # Create enhanced idea
        new_idea = AdvancedFloatingIdea(text, position[0], position[1], self.idea_font, self.settings)
        self.ideas.append(new_idea)
        
        # Update statistics
        self.stats['total_ideas'] += 1
        session_time = (time.time() - self.stats['session_time']) / 60
        self.stats['ideas_per_minute'] = self.stats['total_ideas'] / max(session_time, 1)
        
        print(f"✨ Added idea #{self.stats['total_ideas']}: '{text}'")
    
    def find_good_position(self) -> Tuple[float, float]:
        """Find a good position for new idea that doesn't overlap"""
        attempts = 0
        while attempts < 30:
            x = random.randint(100, self.screen_width - 500)
            y = random.randint(100, self.screen_height - 150)
            
            # Check for overlaps
            overlap = False
            for existing_idea in self.ideas[-10:]:  # Check recent ideas
                dx = x - getattr(existing_idea, 'final_x', existing_idea.x)
                dy = y - getattr(existing_idea, 'final_y', existing_idea.y)
                distance = math.sqrt(dx*dx + dy*dy)
                
                if distance < 180:  # Minimum distance
                    overlap = True
                    break
            
            if not overlap:
                return (x, y)
            attempts += 1
        
        # Fallback position
        return (random.randint(200, self.screen_width - 500), 
                random.randint(200, self.screen_height - 200))
    
    def clear_all_ideas(self):
        """Clear all floating ideas"""
        self.ideas.clear()
        print("🗑️ Cleared all ideas")
    
    def apply_quick_preset(self, preset_name: str):
        """Apply a quick preset"""
        self.settings = self.preset_manager.load_preset(preset_name)
        self.dev_panel.apply_preset(preset_name)
        self.update_idea_font(self.settings.idea_font_size)
        self.regenerate_bg_particles()
        print(f"🎨 Applied preset: {preset_name}")
    
    def update(self):
        """Main update loop"""
        if self.paused:
            return
        
        # Get current settings from dev panel
        if self.dev_panel.visible:
            self.settings = self.dev_panel.get_settings()
        
        # Update font if changed
        current_font_size = int(self.settings.idea_font_size)
        if current_font_size != getattr(self, 'last_font_size', 36):
            self.update_idea_font(current_font_size)
            self.last_font_size = current_font_size
        
        # Update background particles
        if len(self.bg_particles) != int(self.settings.bg_particle_count):
            self.regenerate_bg_particles()
        
        for particle in self.bg_particles:
            particle['x'] += particle['vx'] * self.settings.bg_particle_speed
            particle['y'] += particle['vy'] * self.settings.bg_particle_speed
            
            # Wrap around screen
            if particle['x'] < -10:
                particle['x'] = self.screen_width + 10
            elif particle['x'] > self.screen_width + 10:
                particle['x'] = -10
                
            if particle['y'] < -10:
                particle['y'] = self.screen_height + 10
            elif particle['y'] > self.screen_height + 10:
                particle['y'] = -10
        
        # Update UI components
        self.input_box.update()
        self.dev_panel.update()
        
        # Update ideas with physics
        for idea in self.ideas[:]:
            idea.update(self.settings, self.settings.wind_strength, self.settings.gravity_strength)
        
        # Update statistics
        self.stats['total_likes'] = sum(idea.likes for idea in self.ideas)
        
        # Performance monitoring
        self.fps_counter += 1
        if time.time() - self.fps_timer >= 1.0:
            self.current_fps = self.fps_counter
            self.fps_counter = 0
            self.fps_timer = time.time()
    
    def render(self):
        """Main rendering loop"""
        # Use dynamic background color from settings
        if hasattr(self.settings, 'background_color'):
            self.screen.fill(self.settings.background_color)
        else:
            # Fallback to color scheme
            current_scheme = COLOR_SCHEMES.get(self.settings.color_scheme, COLOR_SCHEMES["midnight"])
            self.screen.fill(current_scheme['background'])
        
        # Enhanced background particles
        for particle in self.bg_particles:
            size = int(particle['size'])
            pygame.draw.circle(self.screen, particle['color'], 
                             (int(particle['x']), int(particle['y'])), size)
        
        # Welcome message for empty state
        if not self.ideas:
            self.render_welcome_screen()
        
        # Render floating ideas
        for idea in self.ideas:
            idea.render(self.screen, self.settings)
        
        # Render UI
        self.render_ui()
        
        # Developer panel
        self.dev_panel.render(self.screen)
        
        # Performance overlay
        if self.settings.show_fps:
            self.render_performance_overlay()
        
        # Help overlay
        if self.show_help:
            self.render_help_overlay()
        
        pygame.display.flip()
    
    def render_welcome_screen(self):
        """Render welcome screen when no ideas are present"""
        center_x = self.screen_width // 2
        center_y = self.screen_height // 2 - 100
        
        # Main title with gradient effect
        title_text = "Professional Ideas Visualizer"
        title_surface = self.fonts['title_bold'].render(title_text, True, (248, 250, 252))
        title_rect = title_surface.get_rect(center=(center_x, center_y))
        self.screen.blit(title_surface, title_rect)
        
        # Subtitle
        subtitle_text = "Transform your thoughts into beautiful floating visualizations"
        subtitle_surface = self.fonts['medium'].render(subtitle_text, True, (148, 163, 184))
        subtitle_rect = subtitle_surface.get_rect(center=(center_x, center_y + 50))
        self.screen.blit(subtitle_surface, subtitle_rect)
        
        # Feature highlights
        features = [
            "💖 Click ideas to like them and watch them grow!",
            "🎨 Professional visual presets and custom colors", 
            "⚡ Real-time parameter adjustment with developer panel",
            "🔧 Advanced physics simulation and particle effects"
        ]
        
        for i, feature in enumerate(features):
            feature_surface = self.fonts['normal'].render(feature, True, (180, 190, 200))
            feature_rect = feature_surface.get_rect(center=(center_x, center_y + 100 + i * 30))
            self.screen.blit(feature_surface, feature_rect)
    
    def render_ui(self):
        """Render user interface elements"""
        # Input area
        self.input_box.render(self.screen)
        
        # Buttons
        self.render_button(self.submit_button)
        self.render_button(self.clear_button)
        
        # Preset buttons
        for button in self.preset_buttons:
            self.render_button(button)
        
        # Status bar
        status_y = self.screen_height - 25
        status_items = [
            f"Ideas: {len(self.ideas)}/{MAX_IDEAS}",
            f"Total: {self.stats['total_ideas']}",
            f"Likes: {self.stats['total_likes']}",
            f"Rate: {self.stats['ideas_per_minute']:.1f}/min",
            f"Preset: {self.preset_manager.current_preset}",
            "TAB: Dev Panel | F1: Help | F11: Fullscreen | Click ideas to like!"
        ]
        
        status_text = " | ".join(status_items)
        status_surface = self.fonts['small'].render(status_text, True, (120, 130, 150))
        self.screen.blit(status_surface, (50, status_y))
    
    def render_button(self, button):
        """Render a styled button"""
        # Button colors based on state
        if button['pressed']:
            bg_color = (37, 99, 235)
        elif button['hovered']:
            bg_color = (59, 130, 246)
        else:
            bg_color = (75, 85, 99)
        
        # Draw button with rounded corners
        pygame.draw.rect(self.screen, bg_color, button['rect'], border_radius=8)
        pygame.draw.rect(self.screen, (156, 163, 175), button['rect'], 2, border_radius=8)
        
        # Button text
        text_surface = button['font'].render(button['text'], True, (255, 255, 255))
        text_rect = text_surface.get_rect(center=button['rect'].center)
        self.screen.blit(text_surface, text_rect)
    
    def render_performance_overlay(self):
        """Render performance monitoring overlay"""
        overlay_rect = pygame.Rect(self.screen_width - 200, 10, 180, 120)
        pygame.draw.rect(self.screen, (0, 0, 0, 128), overlay_rect)
        pygame.draw.rect(self.screen, (100, 100, 120), overlay_rect, 2)
        
        perf_data = [
            f"FPS: {self.current_fps}",
            f"Ideas: {len(self.ideas)}",
            f"Total Likes: {self.stats['total_likes']}",
            f"Particles: {sum(len(idea.particles) for idea in self.ideas)}",
            f"BG Particles: {len(self.bg_particles)}"
        ]
        
        for i, data in enumerate(perf_data):
            text_surface = self.fonts['small'].render(data, True, (220, 220, 240))
            self.screen.blit(text_surface, (overlay_rect.x + 10, overlay_rect.y + 10 + i * 20))
    
    def render_help_overlay(self):
        """Render help overlay"""
        overlay_rect = pygame.Rect(100, 100, self.screen_width - 200, self.screen_height - 200)
        pygame.draw.rect(self.screen, (20, 20, 30, 240), overlay_rect)
        pygame.draw.rect(self.screen, (100, 120, 150), overlay_rect, 3, border_radius=10)
        
        # Title
        title_surface = self.fonts['large_bold'].render("Help & Controls", True, (255, 255, 255))
        title_rect = title_surface.get_rect(center=(overlay_rect.centerx, overlay_rect.y + 40))
        self.screen.blit(title_surface, title_rect)
        
        # Close instruction
        close_text = "Press F1 or ESC to close this help"
        close_surface = self.fonts['medium'].render(close_text, True, (180, 180, 200))
        close_rect = close_surface.get_rect(center=(overlay_rect.centerx, overlay_rect.bottom - 30))
        self.screen.blit(close_surface, close_rect)
    
    def handle_events(self):
        """Handle all input events"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.save_config()
                self.running = False
            
            # Global keyboard shortcuts
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_F11:
                    self.toggle_fullscreen()
                elif event.key == pygame.K_ESCAPE:
                    if self.fullscreen:
                        self.toggle_fullscreen()
                    elif self.show_help:
                        self.show_help = False
                elif event.key == pygame.K_F1:
                    self.show_help = not self.show_help
                elif event.key == pygame.K_TAB and not self.input_box.active:
                    self.dev_panel.toggle_visibility()
                elif event.key == pygame.K_SPACE and not self.input_box.active:
                    self.paused = not self.paused
                    print(f"Animation {'paused' if self.paused else 'resumed'}")
                elif event.key == pygame.K_c and pygame.key.get_pressed()[pygame.K_LCTRL]:
                    self.clear_all_ideas()
                elif event.key == pygame.K_s and pygame.key.get_pressed()[pygame.K_LCTRL]:
                    self.save_current_as_preset()
            
            # Skip other event handling if help is shown
            if self.show_help:
                continue
            
            # Check for idea clicks (like system)
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:  # Left click
                for idea in self.ideas:
                    if idea.is_clicked(event.pos):
                        idea.add_like()
                        break  # Only like one idea per click
            
            # Developer panel events (highest priority when visible)
            if self.dev_panel.visible:
                self.dev_panel.handle_event(event)
                # Don't handle other UI if clicking on dev panel
                if event.type == pygame.MOUSEBUTTONDOWN and self.dev_panel.rect.collidepoint(event.pos):
                    continue
            
            # Button events
            self.handle_button_events(event)
            
            # Input box events
            submitted_text = self.input_box.handle_event(event)
            if submitted_text:
                self.add_idea(submitted_text)
    
    def handle_button_events(self, event):
        """Handle button interactions"""
        all_buttons = [self.submit_button, self.clear_button] + self.preset_buttons
        
        for button in all_buttons:
            if event.type == pygame.MOUSEMOTION:
                button['hovered'] = button['rect'].collidepoint(event.pos)
            
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if button['rect'].collidepoint(event.pos):
                    button['pressed'] = True
            
            elif event.type == pygame.MOUSEBUTTONUP:
                if button['pressed'] and button['rect'].collidepoint(event.pos):
                    button['callback']()
                button['pressed'] = False
    
    def save_current_as_preset(self):
        """Save current settings as a new preset"""
        preset_name = f"Custom_{int(time.time())}"
        self.preset_manager.save_preset(preset_name, self.settings)
        print(f"💾 Saved current settings as '{preset_name}'")
    
    def toggle_fullscreen(self):
        """Toggle between fullscreen and windowed mode"""
        self.fullscreen = not self.fullscreen
        
        if self.fullscreen:
            info = pygame.display.Info()
            self.screen_width = info.current_w
            self.screen_height = info.current_h
            self.screen = pygame.display.set_mode((self.screen_width, self.screen_height), pygame.FULLSCREEN)
            print("🖥️ Switched to fullscreen mode")
        else:
            self.screen_width = 1600
            self.screen_height = 1000
            self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))
            print("🪟 Switched to windowed mode")
        
        # Update UI layout for new screen size
        self.setup_ui()
        self.dev_panel = ProfessionalDeveloperPanel(self.screen_width - 450, 50, 440, 700)
        self.regenerate_bg_particles()
    
    def run(self):
        """Main application loop"""
        print("=" * 60)
        print("✨ PROFESSIONAL FLOATING IDEAS DISPLAY v2.0 ✨")
        print("=" * 60)
        print("🚀 Advanced features loaded:")
        print("   • Click ideas to like them and watch them grow!")
        print("   • Real-time parameter adjustment with dev panel")
        print("   • Professional visual presets and custom colors") 
        print("   • Advanced particle systems and physics simulation")
        print("   • Performance monitoring and auto-save configurations")
        print("   • Smart positioning algorithms and collision detection")
        print()
        print("🎮 Quick Controls:")
        print("   TAB - Developer Panel | F1 - Help | F11 - Fullscreen")
        print("   SPACE - Pause | Ctrl+C - Clear | Ctrl+S - Save Preset")
        print("   CLICK IDEAS - Like them and watch them grow larger!")
        print()
        print("💡 Start typing your ideas below and click to like your favorites!")
        print("=" * 60)
        
        target_fps = 60
        
        while self.running:
            # Dynamic FPS adjustment
            if hasattr(self.settings, 'target_fps'):
                target_fps = getattr(self.settings, 'target_fps', 60)
            
            self.handle_events()
            self.update()
            self.render()
            
            # Adaptive frame rate
            if self.settings.vsync_enabled:
                self.clock.tick(target_fps)
            else:
                self.clock.tick_busy_loop(target_fps)
        
        # Cleanup
        self.save_config()
        pygame.quit()
        print("\n🎉 Thank you for using Professional Floating Ideas Display!")
        print("💾 Your settings have been saved automatically.")
        print(f"📊 Session Stats: {self.stats['total_ideas']} ideas, {self.stats['total_likes']} total likes!")    

class ProfessionalDeveloperPanel:
    """Enhanced developer panel with professional features"""
    def __init__(self, x, y, width, height):
        self.rect = pygame.Rect(x, y, width, height)
        self.visible = False
        self.active_tab = "Movement"
        self.scroll_offset = 0
        
        # Fonts
        self.font = pygame.font.Font(None, 18)
        self.title_font = pygame.font.Font(None, 24)
        self.tab_font = pygame.font.Font(None, 20)
        
        # Tabs
        self.tabs = ["Movement", "Visual", "Effects", "Performance", "Colors", "Presets"]
        self.tab_rects = []
        self.setup_tabs()
        
        # Enhanced controls
        self.setup_controls()
        
        # Preset manager
        self.preset_manager = PresetManager()
        
        # Performance monitoring
        self.fps_history = []
        self.show_performance = False
    
    def setup_tabs(self):
        tab_width = self.rect.width // len(self.tabs)
        for i, tab in enumerate(self.tabs):
            tab_rect = pygame.Rect(self.rect.x + i * tab_width, self.rect.y, tab_width, 30)
            self.tab_rects.append(tab_rect)
    
    def setup_controls(self):
        """Setup all control elements"""
        base_x = self.rect.x + 10
        base_y = self.rect.y + 50
        spacing = 70
        
        self.controls = {
            "Movement": [
                AdvancedSlider(base_x, base_y, 200, 20, 0.1, 3.0, 1.0, "Speed Multiplier"),
                AdvancedSlider(base_x, base_y + spacing, 200, 20, 0.1, 2.0, 0.5, "Float Amplitude"),
                AdvancedSlider(base_x, base_y + spacing*2, 200, 20, 0.1, 2.0, 1.0, "Bounce Randomness"),
                AdvancedSlider(base_x, base_y + spacing*3, 200, 20, -2.0, 2.0, 0.0, "Gravity"),
                AdvancedSlider(base_x, base_y + spacing*4, 200, 20, -2.0, 2.0, 0.0, "Wind"),
            ],
            "Visual": [
                AdvancedSlider(base_x, base_y, 200, 20, 16, 72, 36, "Font Size", 0),
                AdvancedSlider(base_x, base_y + spacing, 200, 20, 0.2, 3.0, 1.0, "Entrance Duration"),
                AdvancedSlider(base_x, base_y + spacing*2, 200, 20, 0.0, 1.0, 0.3, "Glow Intensity"),
                AdvancedSlider(base_x, base_y + spacing*3, 200, 20, 0, 20, 0, "Trail Length", 0),
                DropdownMenu(base_x + 250, base_y, 150, 25, 
                           list(COLOR_SCHEMES.keys()), "midnight", "Color Scheme"),
                DropdownMenu(base_x + 250, base_y + spacing, 150, 25, 
                           list(IDEA_COLOR_PALETTES.keys()), "vibrant", "Idea Palette"),
            ],
            "Effects": [
                AdvancedSlider(base_x, base_y, 200, 20, 0, 50, 10, "Particle Count", 0),
                AdvancedSlider(base_x, base_y + spacing, 200, 20, 0, 100, 50, "BG Particles", 0),
                AdvancedSlider(base_x, base_y + spacing*2, 200, 20, 0.1, 2.0, 0.5, "BG Speed"),
            ],
            "Performance": [
                AdvancedSlider(base_x, base_y, 200, 20, 30, 120, 60, "Target FPS", 0),
            ],
            "Colors": [
                ColorPicker(base_x, base_y, 180, 120, (15, 23, 42), "Background"),
                ColorPicker(base_x + 200, base_y, 180, 120, (59, 130, 246), "Primary"),
                ColorPicker(base_x, base_y + 140, 180, 120, (34, 197, 94), "Secondary"),
                ColorPicker(base_x + 200, base_y + 140, 180, 120, (245, 158, 11), "Accent"),
            ]
        }

    def toggle_visibility(self):
        self.visible = not self.visible

    def handle_event(self, event):
        if not self.visible:
            return
        if event.type == pygame.MOUSEBUTTONDOWN:
            for i, tab_rect in enumerate(self.tab_rects):
                if tab_rect.collidepoint(event.pos):
                    self.active_tab = self.tabs[i]
                    return
        if self.active_tab in self.controls:
            for control in self.controls[self.active_tab]:
                if hasattr(control, "handle_event"):
                    control.handle_event(event)

    def update(self):
        if not self.visible:
            return
        if self.active_tab in self.controls:
            for control in self.controls[self.active_tab]:
                if hasattr(control, "update"):
                    control.update()

    def get_settings(self) -> VisualSettings:
        s = VisualSettings()
        if "Movement" in self.controls:
            c = self.controls["Movement"]
            s.speed_multiplier  = c[0].val
            s.float_amplitude   = c[1].val
            s.bounce_randomness = c[2].val
            s.gravity_strength  = c[3].val
            s.wind_strength     = c[4].val
        if "Visual" in self.controls:
            c = self.controls["Visual"]
            s.idea_font_size    = int(c[0].val)
            s.entrance_duration = c[1].val
            s.glow_intensity    = c[2].val
            s.trail_length      = int(c[3].val)
            s.color_scheme      = c[4].selected
            s.idea_palette      = c[5].selected
        if "Effects" in self.controls:
            c = self.controls["Effects"]
            s.particle_count    = int(c[0].val)
            s.bg_particle_count = int(c[1].val)
            s.bg_particle_speed = c[2].val
        if "Performance" in self.controls:
            c = self.controls["Performance"]
            s.target_fps        = int(c[0].val)
        if "Colors" in self.controls:
            c = self.controls["Colors"]
            s.background_color  = c[0].color
            s.primary_color     = c[1].color
            s.secondary_color   = c[2].color
            s.accent_color      = c[3].color
        return s

    def apply_preset(self, preset_name: str):
        settings = self.preset_manager.load_preset(preset_name)
        if "Movement" in self.controls:
            c = self.controls["Movement"]
            c[0].val, c[1].val, c[2].val, c[3].val, c[4].val = (
                settings.speed_multiplier, settings.float_amplitude,
                settings.bounce_randomness, settings.gravity_strength, settings.wind_strength
            )
            for x in c: x.update_handle_pos()
        if "Visual" in self.controls:
            c = self.controls["Visual"]
            c[0].val, c[1].val, c[2].val, c[3].val = (
                settings.idea_font_size, settings.entrance_duration,
                settings.glow_intensity, settings.trail_length
            )
            for x in c[:4]: x.update_handle_pos()
            c[4].selected = settings.color_scheme
            c[5].selected = settings.idea_palette
        if "Effects" in self.controls:
            c = self.controls["Effects"]
            c[0].val, c[1].val, c[2].val = (
                settings.particle_count, settings.bg_particle_count, settings.bg_particle_speed
            )
            for x in c: x.update_handle_pos()
        if "Colors" in self.controls:
            c = self.controls["Colors"]
            c[0].color, c[1].color, c[2].color, c[3].color = (
                settings.background_color, settings.primary_color,
                settings.secondary_color, settings.accent_color
            )
            for picker in c:
                picker.r_slider.val, picker.g_slider.val, picker.b_slider.val = picker.color
                picker.r_slider.update_handle_pos(); picker.g_slider.update_handle_pos(); picker.b_slider.update_handle_pos()

    def render(self, screen):
        if not self.visible:
            hint = "Press TAB to open Developer Panel | F1 for Help | Click ideas to like them!"
            screen.blit(self.font.render(hint, True, (100, 100, 120)), (10, 10))
            return
        pygame.draw.rect(screen, (25, 25, 35), self.rect, border_radius=10)
        pygame.draw.rect(screen, (60, 60, 80), self.rect, 2, border_radius=10)
        for i, (tab, tab_rect) in enumerate(zip(self.tabs, self.tab_rects)):
            tab_color = (40, 40, 50) if tab == self.active_tab else (30, 30, 40)
            border_color = (80, 120, 200) if tab == self.active_tab else (50, 50, 60)
            pygame.draw.rect(screen, tab_color, tab_rect, border_radius=5)
            pygame.draw.rect(screen, border_color, tab_rect, 2, border_radius=5)
            text_color = (220, 220, 240) if tab == self.active_tab else (180, 180, 200)
            surf = self.tab_font.render(tab, True, text_color)
            screen.blit(surf, surf.get_rect(center=tab_rect.center))
        if self.active_tab in self.controls:
            for control in self.controls[self.active_tab]:
                if hasattr(control, "render"):
                    control.render(screen, self.font)
        elif self.active_tab == "Presets":
            self.render_presets_tab(screen, pygame.Rect(self.rect.x, self.rect.y + 35, self.rect.width, self.rect.height - 35))

    def render_presets_tab(self, screen, content_rect):
        y = content_rect.y + 20
        title = self.title_font.render("Visual Presets", True, (220, 220, 240))
        screen.blit(title, (content_rect.x + 10, y))
        y += 40
        for i, name in enumerate(self.preset_manager.presets.keys()):
            btn = pygame.Rect(content_rect.x + 10, y + i * 35, 200, 30)
            is_current = name == self.preset_manager.current_preset
            btn_color = (60, 120, 200) if is_current else (50, 50, 70)
            txt_color = (255, 255, 255) if is_current else (200, 200, 220)
            pygame.draw.rect(screen, btn_color, btn, border_radius=5)
            pygame.draw.rect(screen, (80, 80, 100), btn, 1, border_radius=5)
            label = self.font.render(name, True, txt_color)
            screen.blit(label, label.get_rect(center=btn.center))


# Entry point
if __name__ == "__main__":
    app = ProfessionalIdeasDisplay()
    try:
        app.run()
    except KeyboardInterrupt:
        print("\n⚠️ Application terminated by user.")
        app.save_config()
        pygame.quit()
    except Exception as e:
        print(f"\n❌ An error occurred: {e}")
        print("📧 Please report this issue for assistance.")
        pygame.quit()
    
        