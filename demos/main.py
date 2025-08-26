import pygame
import random
import math
import time
import json
import os
from typing import List, Tuple, Dict, Any
from dataclasses import dataclass, asdict
from enum import Enum
import colorsys

# Initialize Pygame
pygame.init()
pygame.freetype.init()

# Constants
FPS = 60
MAX_IDEAS = 50
CONFIG_FILE = "ideas_config.json"
PRESETS_FILE = "ideas_presets.json"

# Enhanced color schemes
class ColorScheme(Enum):
    MIDNIGHT = "midnight"
    OCEAN = "ocean" 
    SUNSET = "sunset"
    FOREST = "forest"
    NEON = "neon"
    MONOCHROME = "monochrome"

COLOR_SCHEMES = {
    ColorScheme.MIDNIGHT: {
        'background': (15, 23, 42),
        'accent': (59, 130, 246),
        'text': (248, 250, 252),
        'secondary': (148, 163, 184)
    },
    ColorScheme.OCEAN: {
        'background': (12, 74, 110),
        'accent': (34, 197, 94),
        'text': (255, 255, 255),
        'secondary': (156, 163, 175)
    },
    ColorScheme.SUNSET: {
        'background': (120, 53, 15),
        'accent': (251, 191, 36),
        'text': (255, 255, 255),
        'secondary': (254, 202, 202)
    },
    ColorScheme.FOREST: {
        'background': (20, 83, 45),
        'accent': (134, 239, 172),
        'text': (255, 255, 255),
        'secondary': (187, 247, 208)
    },
    ColorScheme.NEON: {
        'background': (0, 0, 0),
        'accent': (255, 0, 255),
        'text': (0, 255, 255),
        'secondary': (255, 255, 0)
    },
    ColorScheme.MONOCHROME: {
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
    idea_font_size: int = 36
    entrance_duration: float = 1.0
    particle_count: int = 10
    glow_intensity: float = 0.3
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
                glow_color = (*self.color[:3], alpha // 3)
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
    
    def update_font(self, new_font):
        self.font = new_font
    
    def add_to_trail(self):
        if self.max_trail_length > 0:
            self.trail_points.append((self.final_x, self.final_y, time.time()))
            if len(self.trail_points) > self.max_trail_length:
                self.trail_points.pop(0)
    
    def update(self, settings: VisualSettings, wind_strength=0, gravity_strength=0):
        current_time = time.time()
        self.age = current_time - self.birth_time
        
        # Entrance animation
        if self.age < settings.entrance_duration:
            progress = self.age / settings.entrance_duration
            self.alpha = int(255 * min(1.0, progress))
            self.scale = 0.3 + 0.7 * min(1.0, progress * 2)
        else:
            self.alpha = 255
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
            
            # Enhanced glow effect
            if settings.glow_intensity > 0:
                glow_surface = text_surface.copy()
                glow_alpha = int(self.alpha * settings.glow_intensity)
                glow_surface.set_alpha(glow_alpha)
                
                glow_offsets = [(dx, dy) for dx in [-3, -1, 1, 3] for dy in [-3, -1, 1, 3]]
                for dx, dy in glow_offsets:
                    glow_rect = text_rect.copy()
                    glow_rect.x += dx
                    glow_rect.y += dy
                    screen.blit(glow_surface, glow_rect)
            
            # Selection highlight
            if self.selected:
                highlight_rect = text_rect.inflate(20, 20)
                pygame.draw.rect(screen, (255, 255, 0), highlight_rect, 3)
            
            screen.blit(text_surface, text_rect)

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
        self.tabs = ["Movement", "Visual", "Effects", "Performance", "Presets"]
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
            ],
            "Effects": [
                AdvancedSlider(base_x, base_y, 200, 20, 0, 50, 10, "Particle Count", 0),
                AdvancedSlider(base_x, base_y + spacing, 200, 20, 0, 100, 50, "BG Particles", 0),
                AdvancedSlider(base_x, base_y + spacing*2, 200, 20, 0.1, 2.0, 0.5, "BG Speed"),
            ],
            "Performance": [
                AdvancedSlider(base_x, base_y, 200, 20, 30, 120, 60, "Target FPS", 0),
            ]
        }
    
    def handle_event(self, event):
        if not self.visible:
            return
        
        # Tab handling
        if event.type == pygame.MOUSEBUTTONDOWN:
            for i, tab_rect in enumerate(self.tab_rects):
                if tab_rect.collidepoint(event.pos):
                    self.active_tab = self.tabs[i]
                    return
        
        # Control handling
        if self.active_tab in self.controls:
            for control in self.controls[self.active_tab]:
                control.handle_event(event)
    
    def update(self):
        if not self.visible:
            return
        
        # Update controls
        if self.active_tab in self.controls:
            for control in self.controls[self.active_tab]:
                control.update()
    
    def get_settings(self) -> VisualSettings:
        """Extract settings from all controls"""
        settings = VisualSettings()
        
        # Movement tab
        if "Movement" in self.controls:
            controls = self.controls["Movement"]
            settings.speed_multiplier = controls[0].val
            settings.float_amplitude = controls[1].val
            settings.bounce_randomness = controls[2].val
            settings.gravity_strength = controls[3].val
            settings.wind_strength = controls[4].val
        
        # Visual tab
        if "Visual" in self.controls:
            controls = self.controls["Visual"]
            settings.idea_font_size = int(controls[0].val)
            settings.entrance_duration = controls[1].val
            settings.glow_intensity = controls[2].val
            settings.trail_length = int(controls[3].val)
        
        # Effects tab
        if "Effects" in self.controls:
            controls = self.controls["Effects"]
            settings.particle_count = int(controls[0].val)
            settings.bg_particle_count = int(controls[1].val)
            settings.bg_particle_speed = controls[2].val
        
        return settings
    
    def apply_preset(self, preset_name: str):
        """Apply a preset to all controls"""
        settings = self.preset_manager.load_preset(preset_name)
        
        # Update control values
        if "Movement" in self.controls:
            controls = self.controls["Movement"]
            controls[0].val = settings.speed_multiplier
            controls[1].val = settings.float_amplitude
            controls[2].val = settings.bounce_randomness
            controls[3].val = settings.gravity_strength
            controls[4].val = settings.wind_strength
            for control in controls:
                control.update_handle_pos()
        
        if "Visual" in self.controls:
            controls = self.controls["Visual"]
            controls[0].val = settings.idea_font_size
            controls[1].val = settings.entrance_duration
            controls[2].val = settings.glow_intensity
            controls[3].val = settings.trail_length
            for control in controls:
                control.update_handle_pos()
        
        if "Effects" in self.controls:
            controls = self.controls["Effects"]
            controls[0].val = settings.particle_count
            controls[1].val = settings.bg_particle_count
            controls[2].val = settings.bg_particle_speed
            for control in controls:
                control.update_handle_pos()
    
    def render(self, screen):
        if not self.visible:
            hint_text = "Press TAB to open Developer Panel | F1 for Help"
            hint_surface = self.font.render(hint_text, True, (100, 100, 120))
            screen.blit(hint_surface, (10, 10))
            return
        
        # Panel background with rounded corners
        pygame.draw.rect(screen, (25, 25, 35), self.rect, border_radius=10)
        pygame.draw.rect(screen, (60, 60, 80), self.rect, 2, border_radius=10)
        
        # Tabs
        for i, (tab, tab_rect) in enumerate(zip(self.tabs, self.tab_rects)):
            tab_color = (40, 40, 50) if tab == self.active_tab else (30, 30, 40)
            border_color = (80, 120, 200) if tab == self.active_tab else (50, 50, 60)
            
            pygame.draw.rect(screen, tab_color, tab_rect, border_radius=5)
            pygame.draw.rect(screen, border_color, tab_rect, 2, border_radius=5)
            
            text_color = (220, 220, 240) if tab == self.active_tab else (180, 180, 200)
            tab_surface = self.tab_font.render(tab, True, text_color)
            tab_text_rect = tab_surface.get_rect(center=tab_rect.center)
            screen.blit(tab_surface, tab_text_rect)
        
        # Content area
        content_rect = pygame.Rect(self.rect.x, self.rect.y + 35, self.rect.width, self.rect.height - 35)
        
        if self.active_tab in self.controls:
            # Render controls for active tab
            for control in self.controls[self.active_tab]:
                control.render(screen, self.font)
        
        elif self.active_tab == "Presets":
            self.render_presets_tab(screen, content_rect)
        
        # Status bar
        status_y = self.rect.bottom - 25
        status_text = f"Preset: {self.preset_manager.current_preset}"
        status_surface = self.font.render(status_text, True, (180, 180, 200))
        screen.blit(status_surface, (self.rect.x + 10, status_y))
    
    def render_presets_tab(self, screen, content_rect):
        """Render the presets management tab"""
        y_offset = content_rect.y + 20
        
        # Title
        title_surface = self.title_font.render("Visual Presets", True, (220, 220, 240))
        screen.blit(title_surface, (content_rect.x + 10, y_offset))
        y_offset += 40
        
        # Preset buttons
        for i, preset_name in enumerate(self.preset_manager.presets.keys()):
            button_rect = pygame.Rect(content_rect.x + 10, y_offset + i * 35, 200, 30)
            
            # Button appearance
            is_current = preset_name == self.preset_manager.current_preset
            button_color = (60, 120, 200) if is_current else (50, 50, 70)
            text_color = (255, 255, 255) if is_current else (200, 200, 220)
            
            pygame.draw.rect(screen, button_color, button_rect, border_radius=5)
            pygame.draw.rect(screen, (80, 80, 100), button_rect, 1, border_radius=5)
            
            # Button text
            button_surface = self.font.render(preset_name, True, text_color)
            button_text_rect = button_surface.get_rect(center=button_rect.center)
            screen.blit(button_surface, button_text_rect)
        
        # Instructions
        instructions = [
            "Click preset to apply",
            "Ctrl+S to save current as preset",
            "Del to remove selected preset"
        ]
        
        for i, instruction in enumerate(instructions):
            inst_surface = self.font.render(instruction, True, (150, 150, 170))
            screen.blit(inst_surface, (content_rect.x + 250, content_rect.y + 100 + i * 20))
    
    def toggle_visibility(self):
        self.visible = not self.visible

class EnhancedInputBox:
    """Professional input box with advanced features"""
    def __init__(self, x, y, width, height, font):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = ""
        self.font = font
        self.active = False
        self.cursor_pos = 0
        self.cursor_visible = True
        self.cursor_timer = 0
        self.placeholder = "Share your brilliant idea... (Ctrl+Enter for multi-line)"
        
        # Enhancement features
        self.text_history = []
        self.history_index = -1
        self.auto_complete_suggestions = []
        self.show_suggestions = False
        
        # Visual enhancements
        self.border_glow = 0
        self.target_glow = 0
        
        # Common idea suggestions
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
            if event.key == pygame.K_RETURN and not (pygame.key.get_pressed()[pygame.K_LCTRL]):
                result = self.text.strip()
                if result:
                    self.text_history.append(result)
                    if len(self.text_history) > 50:  # Limit history
                        self.text_history.pop(0)
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
            elif event.key == pygame.K_TAB and self.auto_complete_suggestions:
                if self.auto_complete_suggestions:
                    self.text = self.auto_complete_suggestions[0]
                    self.cursor_pos = len(self.text)
                    self.show_suggestions = False
                    
            else:
                if len(self.text) < 200 and event.unicode.isprintable():
                    self.text = self.text[:self.cursor_pos] + event.unicode + self.text[self.cursor_pos:]
                    self.cursor_pos += 1
                    self.update_suggestions()
        
        return None
    
    def update_suggestions(self):
        """Update auto-complete suggestions based on current text"""
        if len(self.text) >= 2:
            self.auto_complete_suggestions = [
                s for s in self.suggestions 
                if s.lower().startswith(self.text.lower()) and s.lower() != self.text.lower()
            ][:5]  # Limit to 5 suggestions
            self.show_suggestions = len(self.auto_complete_suggestions) > 0
        else:
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
        glow_rect = self.rect.inflate(int(self.border_glow/2), int(self.border_glow/2))
        
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

class ProfessionalIdeasDisplay:
    """Main application class with professional features"""
    def __init__(self):
        pygame.display.init()
        
        # Display setup
        self.setup_display()
        
        # Initialize settings first
        self.settings = VisualSettings()
        self.preset_manager = PresetManager()
        
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
            'ideas_per_minute': 0
        }
    
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
        pygame.display.set_caption("✨ Professional Floating Ideas Display v2.0")
        
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
        
        # Performance monitoring
        self.fps_counter += 1
        if time.time() - self.fps_timer >= 1.0:
            self.current_fps = self.fps_counter
            self.fps_counter = 0
            self.fps_timer = time.time()
    
    def render(self):
        """Main rendering loop"""
        # Dynamic background
        current_scheme = COLOR_SCHEMES.get(ColorScheme(self.settings.color_scheme), COLOR_SCHEMES[ColorScheme.MIDNIGHT])
        self.screen.fill(current_scheme['background'])
        
        # Enhanced background particles
        for particle in self.bg_particles:
            size = int(particle['size'])
            alpha_color = (*particle['color'], particle['alpha'])
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
            "🎨 Professional visual presets",
            "⚡ Real-time parameter adjustment", 
            "🔧 Advanced developer tools",
            "💾 Save and load configurations"
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
            f"Rate: {self.stats['ideas_per_minute']:.1f}/min",
            f"Preset: {self.preset_manager.current_preset}",
            "TAB: Dev Panel | F1: Help | F11: Fullscreen"
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
        overlay_rect = pygame.Rect(self.screen_width - 200, 10, 180, 100)
        pygame.draw.rect(self.screen, (0, 0, 0, 128), overlay_rect)
        pygame.draw.rect(self.screen, (100, 100, 120), overlay_rect, 2)
        
        perf_data = [
            f"FPS: {self.current_fps}",
            f"Ideas: {len(self.ideas)}",
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
        
        # Help sections
        help_sections = {
            "Basic Controls": [
                "Enter / Click Add Idea - Submit new idea",
                "Up/Down Arrows - Navigate input history",
                "Tab - Auto-complete suggestions",
                "Ctrl+S - Save current settings as preset"
            ],
            "Developer Panel": [
                "TAB - Toggle developer panel",
                "Movement tab - Speed, bounce, physics",
                "Visual tab - Font, effects, trails",
                "Effects tab - Particles, background",
                "Presets tab - Save/load configurations"
            ],
            "Keyboard Shortcuts": [
                "F1 - Toggle this help",
                "F11 - Toggle fullscreen",
                "ESC - Exit fullscreen",
                "SPACE - Pause/unpause animation",
                "Ctrl+C - Clear all ideas",
                "Ctrl+R - Reset to defaults"
            ],
            "Advanced Features": [
                "Physics simulation with gravity/wind",
                "Particle trail effects",
                "Multiple color schemes",
                "Performance monitoring",
                "Auto-save configurations",
                "Smart positioning system"
            ]
        }
        
        y_offset = overlay_rect.y + 80
        col_width = (overlay_rect.width - 60) // 2
        
        col = 0
        for section, items in help_sections.items():
            x_pos = overlay_rect.x + 30 + col * (col_width + 30)
            
            # Section title
            section_surface = self.fonts['medium_bold'].render(section, True, (100, 150, 255))
            self.screen.blit(section_surface, (x_pos, y_offset))
            
            # Section items
            for i, item in enumerate(items):
                item_surface = self.fonts['normal'].render(item, True, (220, 220, 240))
                self.screen.blit(item_surface, (x_pos + 10, y_offset + 30 + i * 25))
            
            y_offset += 30 + len(items) * 25 + 20
            
            # Switch to second column after first two sections
            if col == 0 and section in ["Developer Panel"]:
                col = 1
                y_offset = overlay_rect.y + 80
        
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
                elif event.key == pygame.K_SPACE:
                    self.paused = not self.paused
                    print(f"Animation {'paused' if self.paused else 'resumed'}")
                elif event.key == pygame.K_c and pygame.key.get_pressed()[pygame.K_LCTRL]:
                    self.clear_all_ideas()
                elif event.key == pygame.K_r and pygame.key.get_pressed()[pygame.K_LCTRL]:
                    self.reset_to_defaults()
                elif event.key == pygame.K_s and pygame.key.get_pressed()[pygame.K_LCTRL]:
                    self.save_current_as_preset()
            
            # Skip other event handling if help is shown
            if self.show_help:
                continue
            
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
    
    def reset_to_defaults(self):
        """Reset all settings to defaults"""
        self.settings = VisualSettings()
        self.dev_panel.apply_preset("Default")
        self.update_idea_font(self.settings.idea_font_size)
        self.regenerate_bg_particles()
        print("🔄 Reset to default settings")
    
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
        print("   • Real-time parameter adjustment")
        print("   • Professional visual presets") 
        print("   • Advanced particle systems")
        print("   • Physics simulation")
        print("   • Performance monitoring")
        print("   • Auto-save configurations")
        print("   • Smart positioning algorithms")
        print()
        print("🎮 Quick Controls:")
        print("   TAB - Developer Panel | F1 - Help | F11 - Fullscreen")
        print("   SPACE - Pause | Ctrl+C - Clear | Ctrl+S - Save Preset")
        print()
        print("💡 Start typing your ideas below and watch them come to life!")
        print("=" * 60)
        
        target_fps = 60
        
        while self.running:
            # Dynamic FPS adjustment
            if hasattr(self.settings, 'target_fps'):
                target_fps = self.settings.target_fps
            
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