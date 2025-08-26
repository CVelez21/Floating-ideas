import pygame
import random
import math
import time
from typing import List, Tuple
import pygame.freetype

# Initialize Pygame
pygame.init()
pygame.freetype.init()

# Constants
FPS = 60
MAX_IDEAS = 30

# Colors
BACKGROUND = (15, 23, 42)  # Dark blue-gray
INPUT_BOX_COLOR = (30, 41, 59)  # Darker blue-gray
INPUT_BOX_ACTIVE = (51, 65, 85)  # Lighter when active
INPUT_TEXT_COLOR = (248, 250, 252)  # Off-white
BUTTON_COLOR = (59, 130, 246)  # Blue
BUTTON_HOVER = (37, 99, 235)  # Darker blue
BUTTON_TEXT = (255, 255, 255)  # White
TITLE_COLOR = (148, 163, 184)  # Light gray

# Dev panel colors
DEV_PANEL_BG = (20, 20, 30)
DEV_PANEL_BORDER = (60, 60, 80)
DEV_TEXT_COLOR = (200, 200, 220)
DEV_SLIDER_BG = (40, 40, 50)
DEV_SLIDER_HANDLE = (100, 150, 255)

# Gradient colors for ideas
IDEA_COLORS = [
    [(255, 179, 186), (255, 99, 132)],  # Pink gradient
    [(162, 255, 178), (34, 197, 94)],   # Green gradient
    [(147, 197, 253), (59, 130, 246)],  # Blue gradient
    [(253, 224, 71), (245, 158, 11)],   # Yellow gradient
    [(196, 181, 253), (147, 51, 234)],  # Purple gradient
    [(134, 239, 172), (5, 150, 105)],   # Emerald gradient
    [(251, 191, 36), (245, 101, 101)],  # Orange-red gradient
    [(165, 180, 252), (99, 102, 241)],  # Indigo gradient
]

class Slider:
    def __init__(self, x, y, width, height, min_val, max_val, initial_val, label):
        self.rect = pygame.Rect(x, y, width, height)
        self.min_val = min_val
        self.max_val = max_val
        self.val = initial_val
        self.label = label
        self.dragging = False
        self.handle_rect = pygame.Rect(0, 0, 20, height)
        self.update_handle_pos()
    
    def update_handle_pos(self):
        progress = (self.val - self.min_val) / (self.max_val - self.min_val)
        handle_x = self.rect.x + progress * (self.rect.width - self.handle_rect.width)
        self.handle_rect.x = handle_x
        self.handle_rect.y = self.rect.y
    
    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.handle_rect.collidepoint(event.pos):
                self.dragging = True
        elif event.type == pygame.MOUSEBUTTONUP:
            self.dragging = False
        elif event.type == pygame.MOUSEMOTION and self.dragging:
            rel_x = event.pos[0] - self.rect.x - self.handle_rect.width // 2
            progress = max(0, min(1, rel_x / (self.rect.width - self.handle_rect.width)))
            self.val = self.min_val + progress * (self.max_val - self.min_val)
            self.update_handle_pos()
    
    def render(self, screen, font):
        # Draw slider background
        pygame.draw.rect(screen, DEV_SLIDER_BG, self.rect)
        pygame.draw.rect(screen, DEV_PANEL_BORDER, self.rect, 1)
        
        # Draw handle
        pygame.draw.rect(screen, DEV_SLIDER_HANDLE, self.handle_rect)
        
        # Draw label and value
        label_text = f"{self.label}: {self.val:.2f}"
        text_surface = font.render(label_text, True, DEV_TEXT_COLOR)
        screen.blit(text_surface, (self.rect.x, self.rect.y - 25))

class ColorPicker:
    def __init__(self, x, y, width, height, initial_color, label):
        self.rect = pygame.Rect(x, y, width, height)
        self.color = initial_color
        self.label = label
        self.r_slider = Slider(x, y + 30, width - 50, 20, 0, 255, initial_color[0], "R")
        self.g_slider = Slider(x, y + 60, width - 50, 20, 0, 255, initial_color[1], "G")
        self.b_slider = Slider(x, y + 90, width - 50, 20, 0, 255, initial_color[2], "B")
        self.color_preview = pygame.Rect(x + width - 40, y + 30, 30, 60)
    
    def handle_event(self, event):
        self.r_slider.handle_event(event)
        self.g_slider.handle_event(event)
        self.b_slider.handle_event(event)
        self.color = (int(self.r_slider.val), int(self.g_slider.val), int(self.b_slider.val))
    
    def render(self, screen, font):
        # Draw label
        text_surface = font.render(self.label, True, DEV_TEXT_COLOR)
        screen.blit(text_surface, (self.rect.x, self.rect.y))
        
        # Draw sliders
        self.r_slider.render(screen, font)
        self.g_slider.render(screen, font)
        self.b_slider.render(screen, font)
        
        # Draw color preview
        pygame.draw.rect(screen, self.color, self.color_preview)
        pygame.draw.rect(screen, DEV_PANEL_BORDER, self.color_preview, 2)

class DevSettings:
    def __init__(self):
        # Movement settings
        self.speed_multiplier = 1.0
        self.float_amplitude = 0.5
        self.bounce_randomness = 1.0
        
        # Visual settings
        self.idea_font_size = 36
        self.entrance_duration = 1.0
        self.particle_count = 10
        self.glow_intensity = 0.3
        
        # Background settings
        self.bg_particle_count = 50
        self.bg_particle_speed = 0.5
        
        # Color settings
        self.background_color = BACKGROUND

class DeveloperPanel:
    def __init__(self, x, y, width, height):
        self.rect = pygame.Rect(x, y, width, height)
        self.visible = False
        self.font = pygame.font.Font(None, 18)
        self.title_font = pygame.font.Font(None, 24)
        
        # Create sliders and controls
        slider_y = y + 50
        slider_spacing = 100
        
        self.speed_slider = Slider(x + 10, slider_y, 200, 20, 0.1, 3.0, 1.0, "Speed Multiplier")
        self.amplitude_slider = Slider(x + 10, slider_y + slider_spacing, 200, 20, 0.1, 2.0, 0.5, "Float Amplitude")
        self.bounce_slider = Slider(x + 10, slider_y + slider_spacing * 2, 200, 20, 0.1, 2.0, 1.0, "Bounce Randomness")
        self.font_size_slider = Slider(x + 10, slider_y + slider_spacing * 3, 200, 20, 16, 72, 36, "Font Size")
        self.entrance_slider = Slider(x + 10, slider_y + slider_spacing * 4, 200, 20, 0.2, 3.0, 1.0, "Entrance Duration")
        self.particle_slider = Slider(x + 10, slider_y + slider_spacing * 5, 200, 20, 0, 50, 10, "Particle Count")
        
        # Color picker for background
        self.bg_color_picker = ColorPicker(x + 250, y + 50, 180, 120, BACKGROUND, "Background Color")
        
        self.sliders = [
            self.speed_slider, self.amplitude_slider, self.bounce_slider,
            self.font_size_slider, self.entrance_slider, self.particle_slider
        ]
    
    def toggle_visibility(self):
        self.visible = not self.visible
    
    def handle_event(self, event):
        if not self.visible:
            return
        
        for slider in self.sliders:
            slider.handle_event(event)
        
        self.bg_color_picker.handle_event(event)
    
    def get_settings(self):
        settings = DevSettings()
        settings.speed_multiplier = self.speed_slider.val
        settings.float_amplitude = self.amplitude_slider.val
        settings.bounce_randomness = self.bounce_slider.val
        settings.idea_font_size = int(self.font_size_slider.val)
        settings.entrance_duration = self.entrance_slider.val
        settings.particle_count = int(self.particle_slider.val)
        settings.background_color = self.bg_color_picker.color
        return settings
    
    def render(self, screen):
        if not self.visible:
            # Just show toggle hint
            hint_text = "Press TAB to open Developer Panel"
            hint_surface = self.font.render(hint_text, True, (100, 100, 120))
            screen.blit(hint_surface, (10, 10))
            return
        
        # Draw panel background
        pygame.draw.rect(screen, DEV_PANEL_BG, self.rect)
        pygame.draw.rect(screen, DEV_PANEL_BORDER, self.rect, 2)
        
        # Draw title
        title_text = "Developer Panel (TAB to close)"
        title_surface = self.title_font.render(title_text, True, DEV_TEXT_COLOR)
        screen.blit(title_surface, (self.rect.x + 10, self.rect.y + 10))
        
        # Draw controls
        for slider in self.sliders:
            slider.render(screen, self.font)
        
        self.bg_color_picker.render(screen, self.font)
        
        # Instructions
        instructions = [
            "Real-time parameter adjustment",
            "Changes apply immediately",
            "Experiment with different values!"
        ]
        
        for i, instruction in enumerate(instructions):
            inst_surface = self.font.render(instruction, True, (150, 150, 170))
            screen.blit(inst_surface, (self.rect.x + 250, self.rect.y + 200 + i * 20))

class Particle:
    def __init__(self, x, y, color):
        self.x = x
        self.y = y
        self.vx = random.uniform(-2, 2)
        self.vy = random.uniform(-2, 2)
        self.color = color
        self.size = random.uniform(2, 5)
        self.life = 1.0
        self.decay = random.uniform(0.005, 0.02)
    
    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.life -= self.decay
        
    def render(self, screen):
        if self.life > 0:
            alpha = int(255 * self.life)
            color = (*self.color, alpha)
            size = int(self.size * self.life)
            if size > 0:
                pygame.draw.circle(screen, self.color[:3], (int(self.x), int(self.y)), size)

class FloatingIdea:
    def __init__(self, text: str, x: float, y: float, font, settings: DevSettings):
        self.text = text
        self.x = x
        self.y = y
        self.original_font = font
        
        # Movement properties (now adjustable)
        base_speed = 0.8
        self.speed_x = random.uniform(-base_speed, base_speed) * settings.speed_multiplier
        self.speed_y = random.uniform(-base_speed, base_speed) * settings.speed_multiplier
        
        # Visual properties
        self.colors = random.choice(IDEA_COLORS)
        self.font = font
        self.alpha = 0
        self.scale = 0.1
        self.rotation = 0
        self.target_alpha = 255
        self.target_scale = 1.0
        
        # Animation properties (now adjustable)
        self.birth_time = time.time()
        self.phase_offset = random.uniform(0, math.pi * 2)
        self.float_amplitude = random.uniform(0.3, 0.8) * settings.float_amplitude
        self.particles = []
        
        # Create entrance particles (count now adjustable)
        for _ in range(settings.particle_count):
            self.particles.append(Particle(x, y, self.colors[0]))
        
        # Store settings reference
        self.entrance_duration = settings.entrance_duration
        self.bounce_randomness = settings.bounce_randomness
    
    def update_font(self, new_font):
        """Update the font for dynamic font size changes"""
        self.font = new_font
    
    def update(self, settings: DevSettings):
        current_time = time.time()
        age = current_time - self.birth_time
        
        # Smooth entrance animation (duration now adjustable)
        if age < self.entrance_duration:
            self.alpha = int(255 * min(1.0, age / self.entrance_duration))
            self.scale = 0.3 + 0.7 * min(1.0, age * 2 / self.entrance_duration)
        else:
            # After entrance, keep at full opacity
            self.alpha = 255
            self.scale = 1.0
        
        # Main floating movement (speed now adjustable)
        self.x += self.speed_x * settings.speed_multiplier
        self.y += self.speed_y * settings.speed_multiplier
        
        # Add gentle wave motion (amplitude now adjustable)
        wave_time = current_time * 0.5
        wave_x = math.sin(wave_time + self.phase_offset) * self.float_amplitude * settings.float_amplitude
        wave_y = math.cos(wave_time * 0.7 + self.phase_offset) * self.float_amplitude * 0.5 * settings.float_amplitude
        
        # Bounce off edges with adjustable randomness
        margin = 50
        if self.x <= margin or self.x >= SCREEN_WIDTH - margin:
            random_factor = random.uniform(0.8, 1.2) * settings.bounce_randomness
            self.speed_x *= -random_factor
            self.speed_x = max(-1.2 * settings.speed_multiplier, min(1.2 * settings.speed_multiplier, self.speed_x))
            self.x = max(margin, min(SCREEN_WIDTH - margin, self.x))
            
        if self.y <= margin or self.y >= SCREEN_HEIGHT - 150:
            random_factor = random.uniform(0.8, 1.2) * settings.bounce_randomness
            self.speed_y *= -random_factor
            self.speed_y = max(-1.2 * settings.speed_multiplier, min(1.2 * settings.speed_multiplier, self.speed_y))
            self.y = max(margin, min(SCREEN_HEIGHT - 150, self.y))
        
        # Apply wave motion to final position
        self.final_x = self.x + wave_x
        self.final_y = self.y + wave_y
        
        # Gentle rotation based on movement
        self.rotation = math.atan2(self.speed_y, self.speed_x) * 0.1
        
        # Update particles
        self.particles = [p for p in self.particles if p.life > 0]
        for particle in self.particles:
            particle.update()
    
    def is_expired(self):
        return False
    
    def render(self, screen):
        if self.alpha > 10:
            # Render particles
            for particle in self.particles:
                particle.render(screen)
            
            # Create gradient text surface
            text_surface = self.font.render(self.text, True, self.colors[0])
            
            # Scale and rotate the text
            text_rect = text_surface.get_rect()
            if self.scale != 1.0 or self.rotation != 0:
                scaled_size = (int(text_rect.width * self.scale), int(text_rect.height * self.scale))
                if scaled_size[0] > 0 and scaled_size[1] > 0:
                    text_surface = pygame.transform.scale(text_surface, scaled_size)
                if self.rotation != 0:
                    text_surface = pygame.transform.rotate(text_surface, math.degrees(self.rotation))
            
            # Apply alpha
            text_surface.set_alpha(self.alpha)
            
            # Position and blit
            text_rect = text_surface.get_rect(center=(self.final_x, self.final_y))
            
            # Add subtle glow effect
            glow_surface = text_surface.copy()
            glow_surface.set_alpha(self.alpha // 3)
            for dx, dy in [(-2, -2), (-2, 2), (2, -2), (2, 2)]:
                glow_rect = text_rect.copy()
                glow_rect.x += dx
                glow_rect.y += dy
                screen.blit(glow_surface, glow_rect)
            
            screen.blit(text_surface, text_rect)

class InputBox:
    def __init__(self, x, y, width, height, font):
        self.rect = pygame.Rect(x, y, width, height)
        self.color = INPUT_BOX_COLOR
        self.text = ""
        self.font = font
        self.active = False
        self.cursor_pos = 0
        self.cursor_visible = True
        self.cursor_timer = 0
        self.placeholder = "Enter your brilliant idea here..."
    
    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            self.active = self.rect.collidepoint(event.pos)
            self.color = INPUT_BOX_ACTIVE if self.active else INPUT_BOX_COLOR
        
        if event.type == pygame.KEYDOWN and self.active:
            if event.key == pygame.K_RETURN:
                return self.text
            elif event.key == pygame.K_BACKSPACE:
                self.text = self.text[:max(0, self.cursor_pos - 1)] + self.text[self.cursor_pos:]
                self.cursor_pos = max(0, self.cursor_pos - 1)
            elif event.key == pygame.K_DELETE:
                self.text = self.text[:self.cursor_pos] + self.text[self.cursor_pos + 1:]
            elif event.key == pygame.K_LEFT:
                self.cursor_pos = max(0, self.cursor_pos - 1)
            elif event.key == pygame.K_RIGHT:
                self.cursor_pos = min(len(self.text), self.cursor_pos + 1)
            elif event.key == pygame.K_HOME:
                self.cursor_pos = 0
            elif event.key == pygame.K_END:
                self.cursor_pos = len(self.text)
            else:
                if len(self.text) < 100:
                    self.text = self.text[:self.cursor_pos] + event.unicode + self.text[self.cursor_pos:]
                    self.cursor_pos += 1
        
        return None
    
    def update(self):
        self.cursor_timer += 1
        if self.cursor_timer >= 30:
            self.cursor_visible = not self.cursor_visible
            self.cursor_timer = 0
    
    def render(self, screen):
        pygame.draw.rect(screen, self.color, self.rect, border_radius=10)
        pygame.draw.rect(screen, (71, 85, 105) if self.active else (51, 65, 85), self.rect, 2, border_radius=10)
        
        display_text = self.text if self.text else self.placeholder
        text_color = INPUT_TEXT_COLOR if self.text else (148, 163, 184)
        
        if display_text:
            text_surface = self.font.render(display_text, True, text_color)
            text_x = self.rect.x + 15
            text_y = self.rect.y + (self.rect.height - text_surface.get_height()) // 2
            screen.blit(text_surface, (text_x, text_y))
        
        if self.active and self.cursor_visible:
            cursor_text = self.text[:self.cursor_pos]
            cursor_width = self.font.size(cursor_text)[0] if cursor_text else 0
            cursor_x = self.rect.x + 15 + cursor_width
            cursor_y = self.rect.y + 10
            pygame.draw.line(screen, INPUT_TEXT_COLOR, (cursor_x, cursor_y), (cursor_x, cursor_y + self.rect.height - 20), 2)

class Button:
    def __init__(self, x, y, width, height, text, font, callback=None):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.font = font
        self.callback = callback
        self.hovered = False
        self.pressed = False
    
    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.hovered = self.rect.collidepoint(event.pos)
        
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos):
                self.pressed = True
        
        if event.type == pygame.MOUSEBUTTONUP:
            if self.pressed and self.rect.collidepoint(event.pos) and self.callback:
                self.callback()
            self.pressed = False
    
    def render(self, screen):
        color = BUTTON_HOVER if self.hovered else BUTTON_COLOR
        pygame.draw.rect(screen, color, self.rect, border_radius=8)
        
        text_surface = self.font.render(self.text, True, BUTTON_TEXT)
        text_rect = text_surface.get_rect()
        text_pos = (
            self.rect.x + (self.rect.width - text_rect.width) // 2,
            self.rect.y + (self.rect.height - text_rect.height) // 2
        )
        screen.blit(text_surface, text_pos)

class PolishedIdeasDisplay:
    def __init__(self):
        pygame.display.init()
        global SCREEN_WIDTH, SCREEN_HEIGHT
        SCREEN_WIDTH = 1400
        SCREEN_HEIGHT = 900
        
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("✨ Floating Ideas Display - Developer Mode")
        self.clock = pygame.time.Clock()
        
        # Load fonts
        self.font_loaded = False
        try:
            font_options = ['Arial', 'Helvetica', 'Segoe UI', 'San Francisco', 'Roboto', 'Open Sans']
            
            for font_name in font_options:
                try:
                    self.title_font = pygame.font.SysFont(font_name, 54, bold=True)
                    self.base_font_name = font_name
                    self.input_font = pygame.font.SysFont(font_name, 24, bold=False)
                    self.button_font = pygame.font.SysFont(font_name, 22, bold=True)
                    self.font_loaded = True
                    print(f"Using font: {font_name}")
                    break
                except:
                    continue
                    
            if not self.font_loaded:
                self.title_font = pygame.font.Font(None, 54)
                self.base_font_name = None
                self.input_font = pygame.font.Font(None, 24)
                self.button_font = pygame.font.Font(None, 22)
                print("Using default fonts")
                
        except Exception as e:
            print(f"Font loading error: {e}")
            self.title_font = pygame.font.Font(None, 54)
            self.base_font_name = None
            self.input_font = pygame.font.Font(None, 24)
            self.button_font = pygame.font.Font(None, 22)
        
        # Initialize developer panel
        self.dev_panel = DeveloperPanel(SCREEN_WIDTH - 450, 50, 440, 700)
        self.dev_settings = DevSettings()
        
        # Create initial idea font
        self.update_idea_font(36)
        
        self.ideas: List[FloatingIdea] = []
        self.running = True
        self.fullscreen = False
        
        # UI Elements
        input_y = SCREEN_HEIGHT - 80
        input_width = min(800, SCREEN_WIDTH - 500)  # Leave more room for dev panel
        self.input_box = InputBox(50, input_y, input_width, 50, self.input_font)
        self.submit_button = Button(input_width + 70, input_y, 120, 50, "Add Idea", self.button_font, self.add_current_idea)
        
        # Background particles
        self.bg_particles = []
        self.regenerate_bg_particles()
    
    def update_idea_font(self, size):
        """Update the font used for ideas"""
        try:
            if self.font_loaded and self.base_font_name:
                self.idea_font = pygame.font.SysFont(self.base_font_name, int(size), bold=False)
            else:
                self.idea_font = pygame.font.Font(None, int(size))
            
            # Update existing ideas with new font
            for idea in self.ideas:
                idea.update_font(self.idea_font)
        except:
            self.idea_font = pygame.font.Font(None, int(size))
    
    def regenerate_bg_particles(self):
        """Regenerate background particles based on current settings"""
        self.bg_particles = []
        for _ in range(int(self.dev_settings.bg_particle_count)):
            self.bg_particles.append({
                'x': random.randint(0, SCREEN_WIDTH),
                'y': random.randint(0, SCREEN_HEIGHT),
                'vx': random.uniform(-0.5, 0.5) * self.dev_settings.bg_particle_speed,
                'vy': random.uniform(-0.5, 0.5) * self.dev_settings.bg_particle_speed,
                'size': random.uniform(1, 3),
                'alpha': random.randint(20, 60)
            })
    
    def add_current_idea(self):
        if self.input_box.text.strip():
            self.add_idea(self.input_box.text.strip())
            self.input_box.text = ""
            self.input_box.cursor_pos = 0
    
    def add_idea(self, text: str):
        while len(self.ideas) >= MAX_IDEAS:
            self.ideas.pop(0)
        
        attempts = 0
        while attempts < 20:
            x = random.randint(100, SCREEN_WIDTH - 500)  # Leave room for dev panel
            y = random.randint(100, SCREEN_HEIGHT - 150)
            
            overlap = False
            for existing_idea in self.ideas[-5:]:
                distance = math.sqrt((x - getattr(existing_idea, 'final_x', existing_idea.x))**2 + 
                                   (y - getattr(existing_idea, 'final_y', existing_idea.y))**2)
                if distance < 150:
                    overlap = True
                    break
            
            if not overlap:
                break
            attempts += 1
        
        new_idea = FloatingIdea(text, x, y, self.idea_font, self.dev_settings)
        self.ideas.append(new_idea)
        print(f"✨ Added idea: '{text}'")
    
    def update(self):
        # Get current settings from dev panel
        self.dev_settings = self.dev_panel.get_settings()
        
        # Update font size if changed
        current_font_size = int(self.dev_settings.idea_font_size)
        if current_font_size != getattr(self, 'last_font_size', 36):
            self.update_idea_font(current_font_size)
            self.last_font_size = current_font_size
        
        # Update background particles if count changed
        if len(self.bg_particles) != int(self.dev_settings.bg_particle_count):
            self.regenerate_bg_particles()
        
        # Update background particles
        for particle in self.bg_particles:
            particle['x'] += particle['vx'] * self.dev_settings.bg_particle_speed
            particle['y'] += particle['vy'] * self.dev_settings.bg_particle_speed
            
            if particle['x'] < 0 or particle['x'] > SCREEN_WIDTH:
                particle['vx'] *= -1
            if particle['y'] < 0 or particle['y'] > SCREEN_HEIGHT:
                particle['vy'] *= -1
        
        # Update UI
        self.input_box.update()
        
        # Update ideas with current settings
        for idea in self.ideas[:]:
            idea.update(self.dev_settings)
        
        self.ideas = [idea for idea in self.ideas if not idea.is_expired()]
    
    def render(self):
        # Use dynamic background color
        self.screen.fill(self.dev_settings.background_color)
        
        # Render background particles
        for particle in self.bg_particles:
            color = (100, 116, 139)  # Keep consistent with original
            pygame.draw.circle(self.screen, color, 
                             (int(particle['x']), int(particle['y'])), 
                             int(particle['size']))
        
        # Render title
        if not self.ideas:
            title_text = "Share Your Ideas - Developer Mode"
            subtitle_text = "Type below and watch your thoughts come to life! Press TAB for dev panel."
            
            title_surface = self.title_font.render(title_text, True, TITLE_COLOR)
            title_rect = title_surface.get_rect()
            title_pos = ((SCREEN_WIDTH - title_rect.width) // 2, SCREEN_HEIGHT // 2 - 100)
            self.screen.blit(title_surface, title_pos)
            
            subtitle_surface = self.input_font.render(subtitle_text, True, (148, 163, 184))
            subtitle_rect = subtitle_surface.get_rect()
            subtitle_pos = ((SCREEN_WIDTH - subtitle_rect.width) // 2, SCREEN_HEIGHT // 2 - 50)
            self.screen.blit(subtitle_surface, subtitle_pos)
        
        # Render floating ideas
        for idea in self.ideas:
            idea.render(self.screen)
        
        # Render UI elements
        self.input_box.render(self.screen)
        self.submit_button.render(self.screen)
        
        # Instructions
        instruction_text = "Press Enter or click 'Add Idea' to submit • TAB for Developer Panel • F11 for fullscreen"
        instruction_font = pygame.font.Font(None, 20)
        instruction_surface = instruction_font.render(instruction_text, True, (148, 163, 184))
        instruction_pos = (50, SCREEN_HEIGHT - 25)
        self.screen.blit(instruction_surface, instruction_pos)
        
        # Render developer panel
        self.dev_panel.render(self.screen)
        
        pygame.display.flip()
    
    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_F11:
                    self.toggle_fullscreen()
                elif event.key == pygame.K_ESCAPE and self.fullscreen:
                    self.toggle_fullscreen()
                elif event.key == pygame.K_TAB:
                    self.dev_panel.toggle_visibility()
            
            # Handle developer panel events first (if visible)
            if self.dev_panel.visible:
                self.dev_panel.handle_event(event)
                # If clicking on dev panel, don't handle other UI events
                if event.type == pygame.MOUSEBUTTONDOWN and self.dev_panel.rect.collidepoint(event.pos):
                    continue
            
            # Handle input box
            submitted_text = self.input_box.handle_event(event)
            if submitted_text:
                self.add_idea(submitted_text)
                self.input_box.text = ""
                self.input_box.cursor_pos = 0
            
            # Handle button
            self.submit_button.handle_event(event)
    
    def toggle_fullscreen(self):
        self.fullscreen = not self.fullscreen
        if self.fullscreen:
            info = pygame.display.Info()
            global SCREEN_WIDTH, SCREEN_HEIGHT
            SCREEN_WIDTH = info.current_w
            SCREEN_HEIGHT = info.current_h
            self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.FULLSCREEN)
            print("Switched to fullscreen mode")
        else:
            SCREEN_WIDTH = 1400
            SCREEN_HEIGHT = 900
            self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
            print("Switched to windowed mode")
        
        # Update UI elements and dev panel for new screen size
        input_y = SCREEN_HEIGHT - 80
        input_width = min(800, SCREEN_WIDTH - 500)
        self.input_box = InputBox(50, input_y, input_width, 50, self.input_font)
        self.submit_button = Button(input_width + 70, input_y, 120, 50, "Add Idea", self.button_font, self.add_current_idea)
        
        # Update developer panel position
        self.dev_panel = DeveloperPanel(SCREEN_WIDTH - 450, 50, 440, 700)
        
        # Regenerate background particles for new screen size
        self.regenerate_bg_particles()
    
    def run(self):
        print("=== ✨ FLOATING IDEAS DISPLAY - DEVELOPER MODE ✨ ===")
        print("Beautiful GUI interface with live parameter adjustment!")
        print("TAB - Toggle Developer Panel")
        print("F11 - Toggle fullscreen | ESC - Exit fullscreen")
        print("Close the window to exit.\n")
        print("Developer Panel Features:")
        print("- Real-time speed, amplitude, and bounce adjustments")
        print("- Dynamic font size changes")
        print("- Entrance animation duration control")
        print("- Particle count adjustment")
        print("- Live background color picker")
        print("- All changes apply immediately!\n")
        
        while self.running:
            self.handle_events()
            self.update()
            self.render()
            self.clock.tick(FPS)
        
        pygame.quit()
        print("Thanks for using Floating Ideas Display! ✨")

if __name__ == "__main__":
    app = PolishedIdeasDisplay()
    try:
        app.run()
    except KeyboardInterrupt:
        print("\nApplication terminated by user.")
        pygame.quit()