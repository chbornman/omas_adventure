import pygame
import sys
import math
import os
import random
import asyncio
import json
from datetime import datetime

pygame.init()

# JavaScript bridge for PostHog analytics
def track_event(event_name, properties=None):
    """Track analytics event via JavaScript PostHog SDK"""
    if hasattr(sys, '_emscripten'):  # Running in browser
        try:
            import platform
            if properties is None:
                properties = {}
            # Convert to JSON string for JavaScript
            props_json = json.dumps(properties)
            # Call JavaScript PostHog function
            platform.window.trackEvent(event_name, props_json)
        except Exception as e:
            print(f"Analytics tracking failed: {e}")
    # For local development, you could log to console or file
    else:
        print(f"Analytics: {event_name} - {properties}")

# Game Constants - All tunable parameters in one place

# Screen settings
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
BLUE = (100, 149, 237)
RED = (255, 0, 0)
YELLOW = (255, 255, 0)
GREEN = (0, 255, 0)
DARK_ORANGE = (255, 140, 0)
LIGHT_ORANGE = (255, 200, 100)
TAN = (210, 180, 140)
BROWN = (139, 69, 19)
GRAY = (128, 128, 128)
SILVER = (192, 192, 192)
DARK_GRAY = (64, 64, 64)
WOOD_FLOOR = (160, 120, 80)
OFF_WHITE = (250, 248, 240)
DARK_WOOD = (101, 67, 33)
PLATFORM_SURFACE = (50, 30, 10)  # Darker brown for landable surfaces

# Physics
GRAVITY = 0.5
JUMP_STRENGTH = -12
PLAYER_SPEED = 5

# Attack speeds
HAIRBALL_SPEED = 12  # Florence's long-range attack
MEOW_SPEED = 6      # Shoogie's shorter-range attack
ENEMY_SPEED = 2

# Character jump multipliers
SHOOGIE_JUMP_MULT = 1.0
FLORENCE_JUMP_MULT = 1.2
SUE_JUMP_MULT = 1.1

# Power-up settings
FLORENCE_SPEED_BOOST_DURATION = 600  # 10 seconds at 60 FPS
FLORENCE_SPEED_MULTIPLIER = 2
FLORENCE_JUMP_BOOST_MULTIPLIER = 1.5
SUE_TREAT_JUMP_BOOST = 0.02  # 2% jump boost per treat
SUE_DOUBLE_JUMP_MULTIPLIER = 0.8  # Second jump is 80% of normal

# Sprite sizes
DEFAULT_SPRITE_SIZE = (64, 64)
SUE_SPRITE_SIZE = (96, 96)
SUE_SPRITE_OFFSET = (-16, -32)  # Offset for drawing Sue's larger sprite

# Level generation (base values)
BASE_LEVEL_LENGTH = 10000
BASE_MIN_PLATFORMS = 25
BASE_MAX_PLATFORMS = 35
BASE_MIN_SHELVES = 8
BASE_MAX_SHELVES = 12
BASE_MIN_WINDOWS = 5
BASE_MAX_WINDOWS = 8
BASE_MIN_TREATS = 40
BASE_MAX_TREATS = 55
BASE_MIN_PLANTS = 8
BASE_MAX_PLANTS = 12
BASE_MIN_ENEMIES = 15
BASE_MAX_ENEMIES = 22

# Round progression
ROUND_COMPLETION_BONUS = 1000
ENEMY_INCREASE_PER_ROUND = 0.2  # 20% more enemies per round
LENGTH_INCREASE_PER_ROUND = 0.05  # 5% longer per round

# Platform generation heights
SINGLE_JUMP_HEIGHT = 120  # Conservative estimate for single jump
DOUBLE_JUMP_HEIGHT = 180  # Approximate with double jump
GROUND_Y = 550

# Character pickup positions
FLORENCE_PICKUP_PERCENT = 0.3  # 30% through level
SUE_PICKUP_PERCENT = 0.6       # 60% through level

# Attack ranges and durations
MEOW_LIFETIME = 25  # Shorter lifetime for half distance
MEOW_OMNI_LIFETIME = 40  # Longer lifetime for omnidirectional
ATTACK_COOLDOWN = 300  # Milliseconds between attacks
ATTACK_ANIMATION_DURATION = 20
SUE_POUND_DURATION = 30

# Sue attack effect
SUE_ATTACK_SIZE = (60, 60)
SUE_ATTACK_VELOCITY = 8
SUE_ATTACK_LIFETIME = 25

# Bed dimensions
BED_WIDTH = 300
BED_HEIGHT = 180

# UI settings
NOTIFICATION_DURATION = 180  # 3 seconds at 60 FPS
BIRD_SPACING = 300  # Pixels between bird pictures

# Score values
ENEMY_KILL_SCORE = 50
TREAT_COLLECT_SCORE = 10
PLANT_COLLECT_SCORE = 20
CHARACTER_PICKUP_SCORE = 100
DEATH_PENALTY = 200

# Enemy patrol bounds
MIN_PATROL_DISTANCE = 50
MAX_PATROL_DISTANCE = 300

# High Score System
HIGH_SCORE_FILE = "data/high_scores.json"
MAX_HIGH_SCORES = 10

# Global high scores storage that works in both desktop and web
_high_scores_cache = None

def load_high_scores():
    """Load high scores from persistent storage"""
    global _high_scores_cache
    
    # If we have cached scores, return them
    if _high_scores_cache is not None:
        return _high_scores_cache.copy()
    
    # Try to load from file
    try:
        os.makedirs(os.path.dirname(HIGH_SCORE_FILE), exist_ok=True)
        
        if os.path.exists(HIGH_SCORE_FILE):
            with open(HIGH_SCORE_FILE, 'r') as f:
                scores = json.load(f)
                _high_scores_cache = scores
                return scores
    except:
        pass
    
    # Return empty list if no scores exist yet
    _high_scores_cache = []
    return []

def save_high_scores(scores):
    """Save high scores to persistent storage"""
    global _high_scores_cache
    
    # Always update the cache
    _high_scores_cache = scores.copy()
    
    # Try to save to file (works in desktop, may fail silently in web)
    try:
        os.makedirs(os.path.dirname(HIGH_SCORE_FILE), exist_ok=True)
        with open(HIGH_SCORE_FILE, 'w') as f:
            json.dump(scores, f, indent=2)
    except:
        pass  # Fail silently - cache will persist for this session

def add_high_score(score, round_num, player_name="Anonymous"):
    """Add a new high score and return if it made the top 10"""
    scores = load_high_scores()
    
    new_entry = {
        "score": score,
        "round": round_num,
        "name": player_name,
        "date": datetime.now().strftime("%Y-%m-%d %H:%M")
    }
    
    scores.append(new_entry)
    scores.sort(key=lambda x: x["score"], reverse=True)
    scores = scores[:MAX_HIGH_SCORES]  # Keep only top 10
    
    save_high_scores(scores)
    
    # Return True if this score made it into the top 10
    return new_entry in scores

def get_high_scores():
    """Get formatted high score list for display"""
    scores = load_high_scores()
    if not scores:
        return ["No high scores yet!"]
    
    formatted = []
    for i, score in enumerate(scores, 1):
        name = score.get('name', 'Anonymous')  # Handle old scores without names
        formatted.append(f"{i:2d}. {score['score']:,} pts  {name}  Round {score['round']}")
    
    return formatted

async def get_player_name(screen, score, round_num):
    """Show name input screen and return the entered name"""
    clock = pygame.time.Clock()
    font = pygame.font.Font(None, 72)
    medium_font = pygame.font.Font(None, 48)
    small_font = pygame.font.Font(None, 36)
    
    player_name = ""
    cursor_visible = True
    cursor_timer = 0
    
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "Anonymous"
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    return player_name if player_name.strip() else "Anonymous"
                elif event.key == pygame.K_ESCAPE:
                    return "Anonymous"
                elif event.key == pygame.K_BACKSPACE:
                    player_name = player_name[:-1]
                else:
                    # Add character to name (limit to 15 characters)
                    if len(player_name) < 15 and event.unicode.isprintable():
                        player_name += event.unicode
        
        # Update cursor blink
        cursor_timer += 1
        if cursor_timer >= 30:  # Blink every half second at 60 FPS
            cursor_visible = not cursor_visible
            cursor_timer = 0
        
        # Clear screen with congratulations background
        screen.fill((25, 25, 112))  # Dark blue
        
        # Congratulations title
        congrats_text = font.render("NEW HIGH SCORE!", True, YELLOW)
        congrats_rect = congrats_text.get_rect(center=(SCREEN_WIDTH // 2, 100))
        screen.blit(congrats_text, congrats_rect)
        
        # Score info
        score_text = medium_font.render(f"Score: {score:,} points (Round {round_num})", True, WHITE)
        score_rect = score_text.get_rect(center=(SCREEN_WIDTH // 2, 160))
        screen.blit(score_text, score_rect)
        
        # Name prompt
        prompt_text = medium_font.render("Enter your name:", True, WHITE)
        prompt_rect = prompt_text.get_rect(center=(SCREEN_WIDTH // 2, 220))
        screen.blit(prompt_text, prompt_rect)
        
        # Name input box
        input_box = pygame.Rect(SCREEN_WIDTH // 2 - 150, 260, 300, 50)
        pygame.draw.rect(screen, WHITE, input_box)
        pygame.draw.rect(screen, BLACK, input_box, 3)
        
        # Display current name with cursor
        display_name = player_name
        if cursor_visible:
            display_name += "|"
        
        name_text = medium_font.render(display_name, True, BLACK)
        name_rect = name_text.get_rect(center=(input_box.centerx, input_box.centery))
        screen.blit(name_text, name_rect)
        
        # Instructions
        inst_text = small_font.render("Press ENTER to save or ESC to skip", True, WHITE)
        inst_rect = inst_text.get_rect(center=(SCREEN_WIDTH // 2, 350))
        screen.blit(inst_text, inst_rect)
        
        # Character limit notice
        limit_text = small_font.render(f"{len(player_name)}/15 characters", True, GRAY)
        limit_rect = limit_text.get_rect(center=(SCREEN_WIDTH // 2, 380))
        screen.blit(limit_text, limit_rect)
        
        pygame.display.flip()
        clock.tick(FPS)
        await asyncio.sleep(0)

class Character:
    def __init__(self, name, color, attack_type, jump_multiplier=1.0):
        self.name = name
        self.color = color
        self.attack_type = attack_type
        self.jump_multiplier = jump_multiplier
        self.lives = 3  # Each character starts with 3 lives/hearts
        self.sprite = self.load_sprite()
        
    def load_sprite(self):
        sprite_path = f"sprites/{self.name.lower()}.png"
        try:
            sprite = pygame.image.load(sprite_path)
            # Scale Sue larger than the others
            if self.name == "Sue":
                return pygame.transform.scale(sprite, (96, 96))
            else:
                return pygame.transform.scale(sprite, (64, 64))
        except pygame.error:
            print(f"Could not load sprite: {sprite_path}")
            # Return a fallback colored rectangle
            size = (80, 80) if self.name == "Sue" else (64, 64)
            fallback = pygame.Surface(size)
            fallback.fill(self.color)
            return fallback
    
    def take_damage(self):
        """Character takes damage, returns True if character dies (lives reach 0)"""
        self.lives -= 1
        return self.lives <= 0

class Player:
    def __init__(self, x, y):
        # All possible characters with different jump heights
        self.all_characters = [
            Character("Shoogie", LIGHT_ORANGE, "meow", 1.0),
            Character("Florence", DARK_ORANGE, "hairball", 1.2),
            Character("Sue", WHITE, "spin", 1.1)
        ]
        # Start with only Shoogie
        self.characters = [self.all_characters[0]]  # Start with Shoogie only
        self.current_char_index = 0
        self.current_char = self.characters[0]
        
        self.rect = pygame.Rect(x, y, 64, 64)
        self.sue_attack_effects = []
        self.vel_y = 0
        self.vel_x = 0
        self.on_ground = False
        self.attacks = []
        self.facing_right = True
        self.spin_timer = 0
        self.last_attack_time = 0
        self.attack_animation_timer = 0
        self.has_double_jumped = False
        self.jump_key_pressed = False
        self.jump_input_buffer = 0  # Buffer for jump input to handle async timing
        self.x_key_pressed = False
        self.x_key_debounce_timer = 0
        
        # Power-up states
        self.florence_speed_boost = 0  # Timer for Florence's speed boost
        self.florence_jump_boost = 0   # Timer for Florence's jump boost
        self.shoogie_omnidirectional_charges = 0  # Charges for Shoogie's omnidirectional meow
        self.sue_treat_count = 0       # Count of treats collected by Sue
        
    def switch_character(self, index):
        if 0 <= index < len(self.characters):
            old_character = self.current_char.name if self.current_char else None
            self.current_char_index = index
            self.current_char = self.characters[index]
            
            # Track character usage
            track_event('character_switched', {
                'from_character': old_character,
                'to_character': self.current_char.name,
                'timestamp': datetime.now().isoformat()
            })
            
    def add_character(self, character_name):
        # Add a character if not already collected
        for char in self.all_characters:
            if char.name == character_name and char not in self.characters:
                char.lives = 3  # Reset lives when character joins
                self.characters.append(char)
                return True
        return False
    
    def remove_dead_character(self):
        """Remove current character from rotation if they have no lives left"""
        if self.current_char.lives <= 0:
            # Remove the current character from rotation
            self.characters.remove(self.current_char)
            
            # If no characters left, return True for game over
            if not self.characters:
                return True
            
            # Switch to next available character
            if self.current_char_index >= len(self.characters):
                self.current_char_index = 0
            self.current_char = self.characters[self.current_char_index]
            
        return False  # Game continues
        
    def collect_treat(self):
        # Increment Sue's treat count if she's the current character
        if self.current_char.name == "Sue":
            self.sue_treat_count += 1
            
    def activate_plant_powerup(self):
        # Florence gets speed and jump boost
        if self.current_char.name == "Florence":
            self.florence_speed_boost = 600  # 10 seconds at 60 FPS
            self.florence_jump_boost = 600
            
    def activate_shoogie_powerup(self):
        # Shoogie gets one omnidirectional meow charge
        if self.current_char.name == "Shoogie":
            self.shoogie_omnidirectional_charges += 1
            
    def update(self, platforms, camera_x):
        keys = pygame.key.get_pressed()
        
        self.vel_x = 0
        speed = PLAYER_SPEED
        # Sue gets slightly faster base speed
        if self.current_char.name == "Sue":
            speed *= 1.3
        # Florence gets speed boost during power-up
        elif self.current_char.name == "Florence" and self.florence_speed_boost > 0:
            speed *= 2
            
        if keys[pygame.K_LEFT]:
            self.vel_x = -speed
            self.facing_right = False
        if keys[pygame.K_RIGHT]:
            self.vel_x = speed
            self.facing_right = True
            
        # Handle jump input with async-aware buffering
        up_key_currently_pressed = keys[pygame.K_UP]
        
        # Buffer jump input to handle async timing issues
        if up_key_currently_pressed and not self.jump_key_pressed:
            self.jump_input_buffer = 5  # 5-frame buffer for async timing
        
        # Decrease buffer timer
        if self.jump_input_buffer > 0:
            self.jump_input_buffer -= 1
            
        # Jump if we have buffered input and are able to jump
        jump_pressed = self.jump_input_buffer > 0
        
        # Update key state
        self.jump_key_pressed = up_key_currently_pressed
        
        if jump_pressed:
            if self.on_ground:
                jump_mult = self.current_char.jump_multiplier
                # Florence gets additional jump boost during power-up
                if self.current_char.name == "Florence" and self.florence_jump_boost > 0:
                    jump_mult *= 1.5
                # Sue gets jump boost based on treats collected
                elif self.current_char.name == "Sue" and self.sue_treat_count > 0:
                    jump_mult *= (1 + self.sue_treat_count * 0.02)  # 2% per treat instead of 10%
                    
                self.vel_y = JUMP_STRENGTH * jump_mult
                self.has_double_jumped = False
                self.jump_input_buffer = 0  # Consume the buffered input
            elif self.current_char.name == "Sue" and not self.has_double_jumped:
                # Sue's double jump with up arrow
                jump_mult = self.current_char.jump_multiplier * 0.8
                if self.sue_treat_count > 0:
                    jump_mult *= (1 + self.sue_treat_count * 0.02)  # 2% per treat instead of 10%
                self.vel_y = JUMP_STRENGTH * jump_mult
                self.has_double_jumped = True
                self.jump_input_buffer = 0  # Consume the buffered input
            
        # Handle character switching with X key (cycles through characters)
        x_key_currently_pressed = keys[pygame.K_x]
        
        # Update debounce timer
        if self.x_key_debounce_timer > 0:
            self.x_key_debounce_timer -= 1
        
        # Check for key press with debouncing
        x_key_just_pressed = (x_key_currently_pressed and 
                             not self.x_key_pressed and 
                             self.x_key_debounce_timer == 0)
        
        # Update key state
        if not x_key_currently_pressed and self.x_key_pressed:
            # Key was released, start debounce timer
            self.x_key_debounce_timer = 10  # 10-frame debounce for easier switching
        self.x_key_pressed = x_key_currently_pressed
        
        # Cycle to next character if X was just pressed
        if x_key_just_pressed and len(self.characters) > 1:
            next_index = (self.current_char_index + 1) % len(self.characters)
            self.switch_character(next_index)
            
        self.rect.x += self.vel_x
        
        for platform in platforms:
            if self.rect.colliderect(platform):
                if self.vel_x > 0:
                    self.rect.right = platform.left
                elif self.vel_x < 0:
                    self.rect.left = platform.right
                    
        self.vel_y += GRAVITY
        self.rect.y += self.vel_y
        
        self.on_ground = False
        for platform in platforms:
            if self.rect.colliderect(platform):
                if self.vel_y > 0:
                    self.rect.bottom = platform.top
                    self.vel_y = 0
                    self.on_ground = True
                elif self.vel_y < 0:
                    self.rect.top = platform.bottom
                    self.vel_y = 0
                    
        if self.rect.left < camera_x:
            self.rect.left = camera_x
            
        if self.spin_timer > 0:
            self.spin_timer -= 1
            
        if self.attack_animation_timer > 0:
            self.attack_animation_timer -= 1
            
        # Update power-up timers
        if self.florence_speed_boost > 0:
            self.florence_speed_boost -= 1
        if self.florence_jump_boost > 0:
            self.florence_jump_boost -= 1
            
        # Update Sue's attack effects
        for effect in self.sue_attack_effects[:]:
            effect.update()
            # Remove if it goes off the bottom of the screen
            if effect.rect.y > SCREEN_HEIGHT:
                self.sue_attack_effects.remove(effect)
            
    def attack(self):
        current_time = pygame.time.get_ticks()
        if current_time - self.last_attack_time < 300:
            return
            
        self.last_attack_time = current_time
        self.attack_animation_timer = 20
        
        if self.current_char.attack_type == "hairball":
            direction = 1 if self.facing_right else -1
            attack = Hairball(self.rect.centerx, self.rect.centery, direction)
            self.attacks.append(attack)
        elif self.current_char.attack_type == "meow":
            if self.shoogie_omnidirectional_charges > 0:
                # Use one omnidirectional charge
                self.shoogie_omnidirectional_charges -= 1
                # Omnidirectional meow attack
                for angle in [0, 45, 90, 135, 180, 225, 270, 315]:
                    direction_x = math.cos(math.radians(angle))
                    direction_y = math.sin(math.radians(angle))
                    attack = MeowWave(self.rect.centerx, self.rect.centery, direction_x, direction_y, omnidirectional=True)
                    self.attacks.append(attack)
            else:
                # Normal directional meow
                direction = 1 if self.facing_right else -1
                attack = MeowWave(self.rect.centerx, self.rect.centery, direction)
                self.attacks.append(attack)
        elif self.current_char.attack_type == "spin":
            # Sue's attack: only ground pound
            self.spin_timer = 30
            sue_effect = SueAttackEffect(self.rect.centerx, self.rect.bottom)
            self.sue_attack_effects.append(sue_effect)
            
    def draw(self, screen, camera_x):
        draw_x = self.rect.x - camera_x
        
        # Use the character sprite (attacks are separate)
        current_sprite = self.current_char.sprite
            
        # Flip sprite horizontally if facing left
        if not self.facing_right:
            current_sprite = pygame.transform.flip(current_sprite, True, False)
            
        # Don't show spinning ears animation anymore - just the pound attack
        
        # Draw Sue's attack effects underneath
        for effect in self.sue_attack_effects:
            effect.draw(screen, camera_x)
            
        # Draw the sprite with offset for Sue
        if self.current_char.name == "Sue":
            # Sue's sprite is 96x96 but rect is 64x64, so offset to align bottom
            screen.blit(current_sprite, (draw_x - 16, self.rect.y - 32))
        else:
            screen.blit(current_sprite, (draw_x, self.rect.y))

class Hairball:
    def __init__(self, x, y, direction):
        self.rect = pygame.Rect(x, y, 24, 24)
        self.vel_x = HAIRBALL_SPEED * direction
        self.vel_y = -4
        self.sprite = self.load_sprite()
        
    def load_sprite(self):
        try:
            if os.path.exists("sprites/florence_attack.png"):
                sprite = pygame.image.load("sprites/florence_attack.png")
                return pygame.transform.scale(sprite, (24, 24))
        except pygame.error:
            pass
        # Fallback to drawn hairball
        return None
        
    def update(self):
        self.rect.x += self.vel_x
        self.vel_y += GRAVITY * 0.3
        self.rect.y += self.vel_y
        
    def draw(self, screen, camera_x):
        draw_x = self.rect.x - camera_x
        
        if self.sprite:
            screen.blit(self.sprite, (draw_x, self.rect.y))
        else:
            # Draw hairball with more detail
            pygame.draw.circle(screen, BROWN, (draw_x + 8, self.rect.y + 8), 8)
            # Add texture with smaller circles
            pygame.draw.circle(screen, (100, 50, 25), (draw_x + 5, self.rect.y + 5), 3)
            pygame.draw.circle(screen, (100, 50, 25), (draw_x + 11, self.rect.y + 6), 2)
            pygame.draw.circle(screen, (100, 50, 25), (draw_x + 6, self.rect.y + 11), 2)
            pygame.draw.circle(screen, (100, 50, 25), (draw_x + 10, self.rect.y + 10), 3)
        
class MeowWave:
    def __init__(self, x, y, direction, direction_y=0, omnidirectional=False):
        self.rect = pygame.Rect(x, y, 40, 30)  # Smaller size for shorter range
        self.omnidirectional = omnidirectional
        if omnidirectional:
            self.vel_x = MEOW_SPEED * direction
            self.vel_y = MEOW_SPEED * direction_y
            self.lifetime = 40  # Longer lifetime for omnidirectional
        else:
            self.vel_x = MEOW_SPEED * direction
            self.vel_y = 0
            self.lifetime = 25  # Shorter lifetime for half distance
        self.direction = direction
        self.sprite = self.load_sprite()
        
    def load_sprite(self):
        try:
            if os.path.exists("sprites/shoogie_attack.png"):
                sprite = pygame.image.load("sprites/shoogie_attack.png")
                return pygame.transform.scale(sprite, (40, 30))
        except pygame.error:
            pass
        # Fallback to drawn meow wave
        return None
        
    def update(self):
        self.rect.x += self.vel_x
        if self.omnidirectional:
            self.rect.y += self.vel_y
        self.lifetime -= 1
        
    def draw(self, screen, camera_x):
        draw_x = self.rect.x - camera_x
        
        if self.sprite:
            # Use sprite and flip if going left
            current_sprite = self.sprite
            if self.direction < 0:
                current_sprite = pygame.transform.flip(current_sprite, True, False)
            screen.blit(current_sprite, (draw_x, self.rect.y))
        else:
            # Fallback to drawn sound ripples
            alpha_factor = self.lifetime / 40
            base_color = LIGHT_ORANGE
            for i in range(5):
                ripple_alpha = int(255 * alpha_factor * (1 - i * 0.15))
                if ripple_alpha > 0:
                    ripple_size = 15 + i * 8
                    ripple_thickness = 3 - i // 2
                    
                    if self.direction > 0:
                        # Facing right
                        start_angle = -math.pi/3
                        end_angle = math.pi/3
                    else:
                        # Facing left  
                        start_angle = 2*math.pi/3
                        end_angle = 4*math.pi/3
                    
                    # Draw multiple ripple lines
                    for j in range(ripple_thickness):
                        pygame.draw.arc(screen, base_color,
                                      (draw_x + i * 5, self.rect.y + 10 - ripple_size//2, 
                                       ripple_size, ripple_size),
                                      start_angle, end_angle, 2)
                        
            # Draw "MEOW" text effect 
            if self.lifetime > 20:
                font = pygame.font.Font(None, 16)
                text = font.render("MEOW!", True, (255, 100, 100))
                screen.blit(text, (draw_x + 5, self.rect.y - 10))

class SueAttackEffect:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x - 30, y, 60, 60)  # Square dimensions
        self.vel_y = 8  # Moves downward
        self.sprite = self.load_sprite()
        
    def load_sprite(self):
        try:
            if os.path.exists("sprites/sue_attack.png"):
                sprite = pygame.image.load("sprites/sue_attack.png")
                return pygame.transform.scale(sprite, (60, 60))  # Square scaling
        except pygame.error:
            pass
        return None
        
    def update(self):
        self.rect.y += self.vel_y  # Move down
        
    def draw(self, screen, camera_x):
        draw_x = self.rect.x - camera_x
        if self.sprite:
            screen.blit(self.sprite, (draw_x, self.rect.y))
        else:
            # Fallback effect
            pygame.draw.ellipse(screen, (100, 100, 100), 
                              (draw_x, self.rect.y, self.rect.width, self.rect.height))

class Plant:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, 48, 50)
        self.collected = False
        
    def draw(self, screen, camera_x):
        if not self.collected:
            draw_x = self.rect.x - camera_x
            # Draw Monstera plant
            # Pot
            pygame.draw.polygon(screen, (139, 69, 19), [
                (draw_x + 14, self.rect.y + 40),
                (draw_x + 34, self.rect.y + 40),
                (draw_x + 30, self.rect.y + 50),
                (draw_x + 18, self.rect.y + 50)
            ])
            pygame.draw.rect(screen, (160, 82, 45), (draw_x + 12, self.rect.y + 38, 24, 4))
            
            # Main stem
            pygame.draw.rect(screen, (34, 139, 34), (draw_x + 22, self.rect.y + 25, 4, 20))
            
            # Draw big Monstera leaves with splits
            leaf_green = (0, 100, 0)
            dark_green = (0, 80, 0)
            
            # Left leaf
            pygame.draw.ellipse(screen, leaf_green, (draw_x, self.rect.y + 5, 25, 30))
            # Splits in left leaf
            pygame.draw.line(screen, screen.get_at((0, 0))[:3], (draw_x + 8, self.rect.y + 12), (draw_x + 5, self.rect.y + 15), 2)
            pygame.draw.line(screen, screen.get_at((0, 0))[:3], (draw_x + 8, self.rect.y + 20), (draw_x + 5, self.rect.y + 23), 2)
            pygame.draw.line(screen, screen.get_at((0, 0))[:3], (draw_x + 12, self.rect.y + 15), (draw_x + 10, self.rect.y + 18), 2)
            # Leaf vein
            pygame.draw.line(screen, dark_green, (draw_x + 12, self.rect.y + 10), (draw_x + 12, self.rect.y + 30), 1)
            
            # Right leaf
            pygame.draw.ellipse(screen, leaf_green, (draw_x + 23, self.rect.y, 25, 32))
            # Splits in right leaf
            pygame.draw.line(screen, screen.get_at((0, 0))[:3], (draw_x + 40, self.rect.y + 8), (draw_x + 43, self.rect.y + 11), 2)
            pygame.draw.line(screen, screen.get_at((0, 0))[:3], (draw_x + 40, self.rect.y + 16), (draw_x + 43, self.rect.y + 19), 2)
            pygame.draw.line(screen, screen.get_at((0, 0))[:3], (draw_x + 36, self.rect.y + 12), (draw_x + 38, self.rect.y + 15), 2)
            # Leaf vein
            pygame.draw.line(screen, dark_green, (draw_x + 36, self.rect.y + 5), (draw_x + 36, self.rect.y + 27), 1)
            
            # Center smaller leaf
            pygame.draw.ellipse(screen, dark_green, (draw_x + 18, self.rect.y + 12, 12, 15))

class DogTreat:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, 48, 32)
        self.collected = False
        self.sprite = self.load_sprite()
        
    def load_sprite(self):
        try:
            if os.path.exists("sprites/dogbone.png"):
                sprite = pygame.image.load("sprites/dogbone.png")
                return pygame.transform.scale(sprite, (48, 32))
        except pygame.error:
            pass
        # Fallback to drawn dog bone
        return None
        
    def draw(self, screen, camera_x):
        if not self.collected:
            draw_x = self.rect.x - camera_x
            
            if self.sprite:
                screen.blit(self.sprite, (draw_x, self.rect.y))
            else:
                # Fallback to drawn dog bone shape (scaled up 2x)
                # Main bar
                pygame.draw.rect(screen, TAN, (draw_x + 12, self.rect.y + 12, 24, 8))
                # Left bone end
                pygame.draw.circle(screen, TAN, (draw_x + 12, self.rect.y + 16), 12)
                # Right bone end  
                pygame.draw.circle(screen, TAN, (draw_x + 36, self.rect.y + 16), 12)
                # Bone details
                pygame.draw.circle(screen, WHITE, (draw_x + 12, self.rect.y + 16), 6)
                pygame.draw.circle(screen, WHITE, (draw_x + 36, self.rect.y + 16), 6)
            
class Enemy:
    def __init__(self, x, y, left_bound, right_bound, top_bound=None, bottom_bound=None, movement_type="horizontal", speed_multiplier=1.0):
        self.rect = pygame.Rect(x, y, 32, 32)
        self.movement_type = movement_type
        self.left_bound = left_bound
        self.right_bound = right_bound
        self.top_bound = top_bound if top_bound is not None else y - 100
        self.bottom_bound = bottom_bound if bottom_bound is not None else y + 100
        
        # Circular movement variables
        self.center_x = x
        self.center_y = y
        self.radius = 120  # Wider circular path
        self.angle = 0
        self.angular_speed = 0.05 * speed_multiplier
        
        # Self-spinning variables
        self.rotation_angle = 0
        self.rotation_speed = 0.1  # Much slower self-spinning
        
        base_speed = ENEMY_SPEED * speed_multiplier
        
        if movement_type == "horizontal":
            self.vel_x = base_speed
            self.vel_y = 0
        elif movement_type == "vertical":
            self.vel_x = 0
            self.vel_y = base_speed
        else:  # circular
            self.vel_x = 0
            self.vel_y = 0
            
        self.sprite = self.load_sprite()
        
    def load_sprite(self):
        try:
            if os.path.exists("sprites/scissors.png"):
                sprite = pygame.image.load("sprites/scissors.png")
                return pygame.transform.scale(sprite, (32, 32))
        except pygame.error:
            pass
        # Fallback to drawn scissors
        return None
        
    def update(self):
        if self.movement_type == "horizontal":
            self.rect.x += self.vel_x
            # Add buffer to prevent rapid flipping at boundaries
            if (self.vel_x < 0 and self.rect.left <= self.left_bound + 5) or \
               (self.vel_x > 0 and self.rect.right >= self.right_bound - 5):
                self.vel_x *= -1
        elif self.movement_type == "vertical":
            self.rect.y += self.vel_y
            # Add buffer to prevent rapid flipping at boundaries
            if (self.vel_y < 0 and self.rect.top <= self.top_bound + 5) or \
               (self.vel_y > 0 and self.rect.bottom >= self.bottom_bound - 5):
                self.vel_y *= -1
        else:  # circular
            self.angle += self.angular_speed
            self.rect.x = int(self.center_x + math.cos(self.angle) * self.radius)
            self.rect.y = int(self.center_y + math.sin(self.angle) * self.radius)
            # Update self-spinning rotation
            self.rotation_angle += self.rotation_speed
            
    def draw(self, screen, camera_x):
        draw_x = self.rect.x - camera_x
        
        if self.sprite:
            # Handle sprite rotation and flipping based on movement type
            current_sprite = self.sprite
            if self.movement_type == "horizontal" and self.vel_x < 0:
                current_sprite = pygame.transform.flip(current_sprite, True, False)
                screen.blit(current_sprite, (draw_x, self.rect.y))
            elif self.movement_type == "vertical" and self.vel_y < 0:
                current_sprite = pygame.transform.flip(current_sprite, False, True)
                screen.blit(current_sprite, (draw_x, self.rect.y))
            elif self.movement_type == "circular":
                # Rotate the sprite for self-spinning effect
                rotation_degrees = math.degrees(self.rotation_angle)
                current_sprite = pygame.transform.rotate(self.sprite, rotation_degrees)
                # Adjust position to account for rotation changing sprite size
                rotated_rect = current_sprite.get_rect(center=(draw_x + 16, self.rect.y + 16))
                screen.blit(current_sprite, rotated_rect.topleft)
            else:
                screen.blit(current_sprite, (draw_x, self.rect.y))
        else:
            # Fallback to drawn scissors
            # Handle
            pygame.draw.rect(screen, SILVER, (draw_x + 5, self.rect.y, 20, 15))
            pygame.draw.rect(screen, GRAY, (draw_x + 5, self.rect.y + 15, 20, 5))
            # Blades
            pygame.draw.polygon(screen, SILVER, [
                (draw_x + 10, self.rect.y + 20),
                (draw_x + 5, self.rect.y + 30),
                (draw_x + 15, self.rect.y + 32),
                (draw_x + 20, self.rect.y + 20)
            ])
            # Center screw
            pygame.draw.circle(screen, DARK_GRAY, (draw_x + 15, self.rect.y + 10), 3)

class CharacterPickup:
    def __init__(self, x, y, character_name):
        self.rect = pygame.Rect(x, y, 64, 64)
        self.character_name = character_name
        self.collected = False
        self.sprite = self.load_sprite()
        self.bob_timer = 0
        
    def load_sprite(self):
        try:
            sprite_path = f"sprites/{self.character_name.lower()}.png"
            if os.path.exists(sprite_path):
                sprite = pygame.image.load(sprite_path)
                if self.character_name == "Sue":
                    return pygame.transform.scale(sprite, (80, 80))
                else:
                    return pygame.transform.scale(sprite, (64, 64))
        except pygame.error:
            pass
        return None
        
    def update(self):
        self.bob_timer += 0.1
        
    def draw(self, screen, camera_x):
        if not self.collected:
            draw_x = self.rect.x - camera_x
            
            # Bobbing animation
            bob_offset = math.sin(self.bob_timer) * 5
            draw_y = self.rect.y + bob_offset
            
            # Draw glowing effect background
            for i in range(3):
                glow_color = (255, 255, 100, 100 - i * 30)
                pygame.draw.circle(screen, YELLOW, (int(draw_x + 32), int(draw_y + 32)), 40 + i * 5, 2)
            
            if self.sprite:
                screen.blit(self.sprite, (draw_x, draw_y))
            else:
                # Fallback - draw colored rectangle with character initial
                color = DARK_ORANGE if self.character_name == "Florence" else LIGHT_ORANGE if self.character_name == "Shoogie" else WHITE
                pygame.draw.rect(screen, color, (draw_x, draw_y, 64, 64))
                
                # Draw character initial
                font = pygame.font.Font(None, 48)
                text = font.render(self.character_name[0], True, BLACK)
                text_rect = text.get_rect(center=(draw_x + 32, draw_y + 32))
                screen.blit(text, text_rect)
        
class Bed:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, 300, 180)
        
    def draw(self, screen, camera_x):
        draw_x = self.rect.x - camera_x
        
        # Window on the right side (above bed level)
        window_x = draw_x + self.rect.width + 20
        window_y = self.rect.y - 80
        # Window frame
        pygame.draw.rect(screen, BROWN, (window_x, window_y, 80, 100))
        # Window glass (light blue)
        pygame.draw.rect(screen, (173, 216, 230), (window_x + 8, window_y + 8, 64, 84))
        # Window cross bars
        pygame.draw.rect(screen, BROWN, (window_x + 36, window_y + 8, 8, 84))
        pygame.draw.rect(screen, BROWN, (window_x + 8, window_y + 46, 64, 8))
        
        # Curtains on both sides
        # Left curtain
        curtain_color = (139, 69, 19)  # Saddle brown
        pygame.draw.polygon(screen, curtain_color, [
            (draw_x - 20, self.rect.y - 50),
            (draw_x + 40, self.rect.y - 30),
            (draw_x + 40, self.rect.y + 150),
            (draw_x - 20, self.rect.y + 130)
        ])
        # Right curtain 
        pygame.draw.polygon(screen, curtain_color, [
            (draw_x + self.rect.width - 40, self.rect.y - 30),
            (draw_x + self.rect.width + 20, self.rect.y - 50),
            (draw_x + self.rect.width + 20, self.rect.y + 130),
            (draw_x + self.rect.width - 40, self.rect.y + 150)
        ])
        
        # Bed frame (scaled 1.5x)
        pygame.draw.rect(screen, BROWN, (draw_x, self.rect.y + 90, self.rect.width, 90))
        # Mattress (scaled 1.5x)
        pygame.draw.rect(screen, WHITE, (draw_x + 15, self.rect.y + 45, self.rect.width - 30, 135))
        # Pillows (scaled 1.5x)
        pygame.draw.ellipse(screen, (240, 240, 240), (draw_x + 30, self.rect.y + 52, 90, 52))
        pygame.draw.ellipse(screen, (240, 240, 240), (draw_x + self.rect.width - 120, self.rect.y + 52, 90, 52))
        # Blanket (scaled 1.5x)
        pygame.draw.rect(screen, (200, 100, 100), (draw_x + 37, self.rect.y + 82, self.rect.width - 75, 97))

class Camera:
    def __init__(self):
        self.x = 0
        
    def update(self, player):
        target_x = player.rect.x - SCREEN_WIDTH // 3
        self.x += (target_x - self.x) * 0.1
        self.x = max(0, self.x)

def create_level(round_num=1):
    platforms = []
    platform_types = []
    treats = []
    plants = []
    enemies = []
    character_pickups = []
    
    # Calculate scaled values based on round number
    level_scaling = 1 + (round_num - 1) * LENGTH_INCREASE_PER_ROUND
    enemy_scaling = 1 + (round_num - 1) * ENEMY_INCREASE_PER_ROUND
    
    # Set level length with scaling
    LEVEL_LENGTH = int(BASE_LEVEL_LENGTH * level_scaling)
    
    # Scale enemy counts
    MIN_ENEMIES = int(BASE_MIN_ENEMIES * enemy_scaling)
    MAX_ENEMIES = int(BASE_MAX_ENEMIES * enemy_scaling)
    
    # Create floor segments
    ground_segments = LEVEL_LENGTH // 400 + 1
    for i in range(ground_segments):
        platforms.append(pygame.Rect(i * 400, 550, 400, 50))
        platform_types.append("floor")
    
    # Generate platforms in sections: first section single-jump only, later sections can require double jump
    furniture_types = ["table", "sofa", "chair", "bookshelf", "leather_couch", "grey_couch"]
    num_platforms = random.randint(BASE_MIN_PLATFORMS, BASE_MAX_PLATFORMS)
    
    # Maximum jump height calculations
    SINGLE_JUMP_HEIGHT = 120  # Conservative estimate for single jump
    DOUBLE_JUMP_HEIGHT = 180  # Approximate with double jump (single + 80% second jump)
    GROUND_Y = 550
    
    # Define level sections
    FLORENCE_PICKUP_SECTION = LEVEL_LENGTH * 0.3   # 30% - Florence pickup
    SUE_PICKUP_SECTION = LEVEL_LENGTH * 0.6         # 60% - Sue pickup
    
    used_positions = set()
    
    for i in range(num_platforms):
        # Try to find a non-overlapping position
        attempts = 0
        while attempts < 50:
            x = random.randint(200, LEVEL_LENGTH - 300)
            
            # Determine if this platform can require double jump (after Sue pickup)
            can_require_double_jump = x > SUE_PICKUP_SECTION
            max_jump_height = DOUBLE_JUMP_HEIGHT if can_require_double_jump else SINGLE_JUMP_HEIGHT
            
            # Ensure platform is reachable
            if len(platforms) <= 1:  # First few platforms must be reachable from ground
                min_platform_y = GROUND_Y - SINGLE_JUMP_HEIGHT + 50
                y = random.randint(min_platform_y, 500)
            else:
                # Find nearest platforms within reasonable horizontal distance
                nearby_platforms = [p for p in platforms if abs(p.x - x) < 300]
                if nearby_platforms:
                    # Platform can be reached from a nearby platform
                    min_y_from_platforms = min(p.y - max_jump_height + 30 for p in nearby_platforms)
                    min_y_from_ground = GROUND_Y - max_jump_height + 50
                    max_reachable_y = max(min_y_from_platforms, min_y_from_ground)
                else:
                    # Must be reachable from ground
                    max_reachable_y = GROUND_Y - max_jump_height + 50
                
                # For later sections, occasionally create challenging jumps
                if can_require_double_jump and random.random() < 0.3:  # 30% chance of difficult jump
                    y = random.randint(max_reachable_y, max_reachable_y + 50)
                else:
                    y = random.randint(max_reachable_y, 500)
            
            width = random.randint(120, 220)
            
            # Check if position overlaps with existing platforms
            new_rect = pygame.Rect(x, y, width, 20)
            overlap = False
            for existing_pos in used_positions:
                if new_rect.colliderect(pygame.Rect(existing_pos[0] - 50, existing_pos[1] - 50, 
                                                  existing_pos[2] + 100, 100)):
                    overlap = True
                    break
            
            if not overlap:
                platforms.append(new_rect)
                platform_types.append(random.choice(furniture_types))
                used_positions.add((x, y, width))
                break
            attempts += 1
    
    # Add wall-mounted shelves as higher platforms
    num_shelves = random.randint(BASE_MIN_SHELVES, BASE_MAX_SHELVES)
    for i in range(num_shelves):
        x = random.randint(300, LEVEL_LENGTH - 300)
        y = random.randint(150, 350)
        width = random.randint(80, 150)
        platforms.append(pygame.Rect(x, y, width, 15))
        platform_types.append("shelf")
        
    # Add windowsills
    num_windows = random.randint(BASE_MIN_WINDOWS, BASE_MAX_WINDOWS)
    for i in range(num_windows):
        x = random.randint(400, LEVEL_LENGTH - 400)
        y = random.randint(250, 400)
        width = random.randint(120, 180)
        platforms.append(pygame.Rect(x, y, width, 20))
        platform_types.append("windowsill")
    
    # Generate dog treats randomly throughout level
    num_treats = random.randint(BASE_MIN_TREATS, BASE_MAX_TREATS)
    
    # Distribute treats more evenly across different platform heights
    platform_groups = {
        'high': [p for p in platforms[1:] if p.y < 300],
        'mid': [p for p in platforms[1:] if 300 <= p.y < 450],
        'low': [p for p in platforms[1:] if p.y >= 450]
    }
    
    treats_per_group = num_treats // 3
    
    for group_name, group_platforms in platform_groups.items():
        for i in range(treats_per_group):
            if group_platforms:
                platform = random.choice(group_platforms)
                # Vary placement on platform
                x = platform.x + random.randint(10, max(10, platform.width - 58))
                y = platform.y - 35
            else:
                # Fallback to random placement
                x = random.randint(100, LEVEL_LENGTH - 100)
                if group_name == 'high':
                    y = random.randint(200, 280)
                elif group_name == 'mid':
                    y = random.randint(350, 430)
                else:
                    y = 500
            treats.append(DogTreat(x, y))
    
    # Add remaining treats randomly
    for _ in range(num_treats - treats_per_group * 3):
        if random.random() < 0.8 and platforms:
            platform = random.choice(platforms[1:])
            x = platform.x + random.randint(10, max(10, platform.width - 58))
            y = platform.y - 35
        else:
            x = random.randint(100, LEVEL_LENGTH - 100)
            y = 500
        treats.append(DogTreat(x, y))
    
    # Generate plants for Florence's power-up
    num_plants = random.randint(BASE_MIN_PLANTS, BASE_MAX_PLANTS)
    
    # Spread plants across different heights
    for i in range(num_plants):
        if i < 2 and platform_groups['high']:  # First 2 on high platforms
            platform = random.choice(platform_groups['high'])
            x = platform.x + random.randint(10, max(10, platform.width - 58))
            y = platform.y - 50
        elif i < 4 and platform_groups['mid']:  # Next 2 on mid platforms
            platform = random.choice(platform_groups['mid'])
            x = platform.x + random.randint(10, max(10, platform.width - 58))
            y = platform.y - 50
        elif i < 6 and platforms:  # Next 2 on any platform
            platform = random.choice(platforms[1:])
            x = platform.x + random.randint(10, max(10, platform.width - 58))
            y = platform.y - 50
        else:  # Rest on ground
            x = random.randint(100, LEVEL_LENGTH - 100)
            y = 500
            
        plants.append(Plant(x, y))
    
    # Place character pickups at strategic locations
    # Florence pickup at 30% through level
    florence_x = FLORENCE_PICKUP_SECTION + random.randint(-100, 100)
    florence_platforms = [p for p in platforms if abs(p.x - florence_x) < 200]
    if florence_platforms:
        platform = random.choice(florence_platforms)
        florence_y = platform.y - 80
    else:
        florence_y = 470
    character_pickups.append(CharacterPickup(florence_x, florence_y, "Florence"))
    
    # Sue pickup at 60% through level
    sue_x = SUE_PICKUP_SECTION + random.randint(-100, 100)
    sue_platforms = [p for p in platforms if abs(p.x - sue_x) < 200]
    if sue_platforms:
        platform = random.choice(sue_platforms)
        sue_y = platform.y - 80
    else:
        sue_y = 470
    character_pickups.append(CharacterPickup(sue_x, sue_y, "Sue"))
    
    # Generate random enemies
    enemies = generate_enemies(LEVEL_LENGTH, MIN_ENEMIES, MAX_ENEMIES, round_num)
    
    # Add bed at the end of the level
    bed = Bed(LEVEL_LENGTH - 350, 370)
    
    return platforms, platform_types, treats, plants, enemies, bed, character_pickups

def generate_enemies(level_length, min_enemies, max_enemies, round_num=1):
    """Generate a fresh set of enemies for the level"""
    enemies = []
    num_enemies = random.randint(min_enemies, max_enemies)
    
    # Speed increases with rounds
    speed_multiplier = 1.0 + (round_num - 1) * 0.3  # 30% faster each round
    
    # Enemy type distribution changes with rounds
    if round_num == 1:
        # Round 1: Only horizontal
        horizontal_count = num_enemies
        vertical_count = 0
        circular_count = 0
    elif round_num <= 3:
        # Rounds 2-3: Add vertical
        horizontal_count = int(num_enemies * 0.7)
        vertical_count = num_enemies - horizontal_count
        circular_count = 0
    else:
        # Round 4+: Add circular
        horizontal_count = int(num_enemies * 0.5)
        vertical_count = int(num_enemies * 0.3)
        circular_count = num_enemies - horizontal_count - vertical_count
    
    # Generate horizontal enemies
    for _ in range(horizontal_count):
        x = random.randint(300, level_length - 300)
        y = random.randint(200, 520)
        left_bound = x - random.randint(MIN_PATROL_DISTANCE, MAX_PATROL_DISTANCE)
        right_bound = x + random.randint(MIN_PATROL_DISTANCE, MAX_PATROL_DISTANCE)
        left_bound = max(0, left_bound)
        right_bound = min(level_length, right_bound)
        
        # Randomize individual speed within a range
        individual_speed = speed_multiplier * random.uniform(0.7, 1.3)
        enemies.append(Enemy(x, y, left_bound, right_bound, movement_type="horizontal", speed_multiplier=individual_speed))
    
    # Generate vertical enemies
    for _ in range(vertical_count):
        x = random.randint(300, level_length - 300)
        y = random.randint(300, 450)
        top_bound = y - random.randint(MIN_PATROL_DISTANCE, MAX_PATROL_DISTANCE)
        bottom_bound = y + random.randint(MIN_PATROL_DISTANCE, MAX_PATROL_DISTANCE)
        top_bound = max(100, top_bound)
        bottom_bound = min(520, bottom_bound)
        
        # Randomize individual speed within a range
        individual_speed = speed_multiplier * random.uniform(0.7, 1.3)
        enemies.append(Enemy(x, y, 0, level_length, top_bound, bottom_bound, movement_type="vertical", speed_multiplier=individual_speed))
    
    # Generate circular enemies
    for _ in range(circular_count):
        x = random.randint(400, level_length - 400)
        y = random.randint(250, 400)
        
        # Randomize individual speed within a range
        individual_speed = speed_multiplier * random.uniform(0.7, 1.3)
        enemies.append(Enemy(x, y, 0, level_length, movement_type="circular", speed_multiplier=individual_speed))
    
    return enemies

async def show_finish_screen(screen, score, round_num):
    font = pygame.font.Font(None, 72)
    medium_font = pygame.font.Font(None, 48)
    small_font = pygame.font.Font(None, 36)
    
    # Load character sprites for celebration animation
    try:
        characters = [
            pygame.image.load("sprites/shoogie.png"),
            pygame.image.load("sprites/florence.png"), 
            pygame.image.load("sprites/sue.png")
        ]
        characters = [pygame.transform.scale(char, (48, 48)) for char in characters]
    except:
        characters = []
    
    animation_time = 0
    running = True
    
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    return True
                elif event.key == pygame.K_ESCAPE:
                    return False
        
        animation_time += 1
        
        # Gradient background (night sky)
        screen.fill((25, 25, 112))  # Midnight blue
        
        # Draw stars
        for i in range(20):
            star_x = (i * 40 + animation_time) % SCREEN_WIDTH
            star_y = 50 + (i * 17) % 100
            pygame.draw.circle(screen, WHITE, (star_x, star_y), 2)
        
        # Title with sleeping animation
        title_color = WHITE if (animation_time // 30) % 2 else YELLOW
        title_text = font.render("Time for Bed!", True, title_color)
        title_rect = title_text.get_rect(center=(SCREEN_WIDTH//2, 80))
        screen.blit(title_text, title_rect)
        
        # Draw bed
        bed_x = SCREEN_WIDTH // 2 - 150
        bed_y = 120
        pygame.draw.rect(screen, BROWN, (bed_x, bed_y + 60, 300, 60))  # Bed frame
        pygame.draw.rect(screen, WHITE, (bed_x + 10, bed_y + 30, 280, 90))  # Mattress
        pygame.draw.rect(screen, (200, 100, 100), (bed_x + 20, bed_y + 50, 260, 70))  # Blanket
        
        # Characters sleeping on bed with gentle animation
        for i, char in enumerate(characters):
            char_x = bed_x + 50 + i * 80
            char_y = bed_y + 40 + math.sin(animation_time * 0.05 + i) * 3
            screen.blit(char, (char_x, char_y))
            
            # Sleeping "Z"s
            z_offset = math.sin(animation_time * 0.1 + i * 2) * 5
            z_text = small_font.render("Z", True, WHITE)
            screen.blit(z_text, (char_x + 50, char_y - 20 + z_offset))
        
        # Round completed
        round_text = medium_font.render(f"Round {round_num} Complete!", True, GREEN)
        round_rect = round_text.get_rect(center=(SCREEN_WIDTH//2, 250))
        screen.blit(round_text, round_rect)
        
        # Round bonus
        bonus_text = small_font.render(f"Round Bonus: +{ROUND_COMPLETION_BONUS:,}", True, GREEN)
        bonus_rect = bonus_text.get_rect(center=(SCREEN_WIDTH//2, 290))
        screen.blit(bonus_text, bonus_rect)
        
        # Score
        score_text = medium_font.render(f"Total Score: {score:,}", True, YELLOW)
        score_rect = score_text.get_rect(center=(SCREEN_WIDTH//2, 340))
        screen.blit(score_text, score_rect)
        
        # Check if this would be a high score
        high_scores = load_high_scores()
        would_be_high_score = (not high_scores or 
                              len(high_scores) < MAX_HIGH_SCORES or 
                              score > high_scores[-1]["score"])
        
        if would_be_high_score:
            high_score_text = medium_font.render("POTENTIAL HIGH SCORE!", True, YELLOW)
            high_rect = high_score_text.get_rect(center=(SCREEN_WIDTH//2, 380))
            screen.blit(high_score_text, high_rect)
        
        # Next round preview
        next_round_text = small_font.render(f"Next: Round {round_num + 1} - Harder challenges await!", True, LIGHT_ORANGE)
        next_round_rect = next_round_text.get_rect(center=(SCREEN_WIDTH//2, 430))
        screen.blit(next_round_text, next_round_rect)
        
        # Instructions
        inst_text = small_font.render("Press ENTER to continue or ESC to quit", True, WHITE)
        inst_rect = inst_text.get_rect(center=(SCREEN_WIDTH//2, 480))
        screen.blit(inst_text, inst_rect)
        
        pygame.display.flip()
        await asyncio.sleep(0)  # Allow other tasks to run
        
    return False

def draw_house_interior(screen, camera_x):
    # Fill background with off-white walls
    screen.fill(OFF_WHITE)
    
    # Draw wood floor
    floor_y = 500
    pygame.draw.rect(screen, WOOD_FLOOR, (0, floor_y, SCREEN_WIDTH, SCREEN_HEIGHT - floor_y))
    
    # Draw wood floor planks
    for i in range(0, SCREEN_WIDTH + 200, 100):
        plank_x = (i - (camera_x % 100))
        pygame.draw.line(screen, DARK_WOOD, (plank_x, floor_y), (plank_x, SCREEN_HEIGHT), 2)
        
    # Draw bird pictures on walls for decoration
    bird_spacing = 300
    bird_types = ['duck', 'cardinal', 'sparrow', 'adult_duck', 'swan', 'robin']
    
    for i in range(0, 12000, bird_spacing):
        picture_x = i - camera_x
        if -100 < picture_x < SCREEN_WIDTH + 100:
            # Frame with more height variation
            # Use multiple factors for more varied placement
            height_variation = (i % 7) * 30 + (i % 3) * 20 + ((i // bird_spacing) % 4) * 15
            frame_y = 120 + height_variation  # Range from 120 to ~320
            pygame.draw.rect(screen, DARK_WOOD, (picture_x, frame_y, 60, 60), 3)
            pygame.draw.rect(screen, (220, 220, 200), (picture_x + 3, frame_y + 3, 54, 54))
            
            # Choose bird type based on position
            bird_type = bird_types[(i // bird_spacing) % len(bird_types)]
            
            if bird_type == 'duck':  # Young duck
                # Duck body
                pygame.draw.ellipse(screen, YELLOW, (picture_x + 15, frame_y + 25, 30, 20))
                # Duck head
                pygame.draw.circle(screen, YELLOW, (picture_x + 38, frame_y + 20), 8)
                # Duck bill
                pygame.draw.polygon(screen, (255, 140, 0), [
                    (picture_x + 43, frame_y + 20),
                    (picture_x + 48, frame_y + 18),
                    (picture_x + 48, frame_y + 22)
                ])
                # Duck eye
                pygame.draw.circle(screen, BLACK, (picture_x + 40, frame_y + 18), 2)
                # Wing detail
                pygame.draw.arc(screen, (200, 200, 0), (picture_x + 20, frame_y + 25, 15, 15), 0, 3.14, 2)
                
            elif bird_type == 'cardinal':
                # Cardinal body
                pygame.draw.ellipse(screen, (220, 20, 60), (picture_x + 18, frame_y + 28, 25, 18))
                # Head with crest
                pygame.draw.circle(screen, (220, 20, 60), (picture_x + 35, frame_y + 25), 7)
                # Crest
                pygame.draw.polygon(screen, (220, 20, 60), [
                    (picture_x + 35, frame_y + 20),
                    (picture_x + 33, frame_y + 15),
                    (picture_x + 37, frame_y + 15)
                ])
                # Black face mask
                pygame.draw.polygon(screen, BLACK, [
                    (picture_x + 35, frame_y + 23),
                    (picture_x + 40, frame_y + 25),
                    (picture_x + 35, frame_y + 27),
                    (picture_x + 32, frame_y + 25)
                ])
                # Beak
                pygame.draw.polygon(screen, (255, 140, 0), [
                    (picture_x + 40, frame_y + 25),
                    (picture_x + 44, frame_y + 25),
                    (picture_x + 42, frame_y + 27)
                ])
                # Eye
                pygame.draw.circle(screen, WHITE, (picture_x + 36, frame_y + 24), 2)
                pygame.draw.circle(screen, BLACK, (picture_x + 36, frame_y + 24), 1)
                
            elif bird_type == 'sparrow':
                # Sparrow body
                pygame.draw.ellipse(screen, (139, 90, 43), (picture_x + 20, frame_y + 30, 20, 15))
                # Head
                pygame.draw.circle(screen, (160, 110, 60), (picture_x + 35, frame_y + 28), 6)
                # Wing detail
                pygame.draw.ellipse(screen, (110, 70, 30), (picture_x + 23, frame_y + 32, 12, 10))
                # Beak
                pygame.draw.polygon(screen, (60, 40, 20), [
                    (picture_x + 39, frame_y + 28),
                    (picture_x + 42, frame_y + 27),
                    (picture_x + 39, frame_y + 29)
                ])
                # Eye
                pygame.draw.circle(screen, BLACK, (picture_x + 36, frame_y + 27), 1)
                # Tail
                pygame.draw.polygon(screen, (110, 70, 30), [
                    (picture_x + 22, frame_y + 35),
                    (picture_x + 15, frame_y + 38),
                    (picture_x + 18, frame_y + 40),
                    (picture_x + 22, frame_y + 38)
                ])
                
            elif bird_type == 'adult_duck':
                # Adult duck body (mallard)
                pygame.draw.ellipse(screen, (160, 160, 160), (picture_x + 12, frame_y + 25, 35, 22))
                # Head (green for male mallard)
                pygame.draw.circle(screen, (0, 128, 0), (picture_x + 40, frame_y + 20), 9)
                # White neck ring
                pygame.draw.arc(screen, WHITE, (picture_x + 32, frame_y + 24, 16, 10), 0, 3.14, 3)
                # Bill
                pygame.draw.ellipse(screen, (255, 165, 0), (picture_x + 46, frame_y + 19, 10, 4))
                # Eye
                pygame.draw.circle(screen, BLACK, (picture_x + 42, frame_y + 18), 2)
                # Wing detail
                pygame.draw.ellipse(screen, (110, 110, 110), (picture_x + 18, frame_y + 28, 20, 12))
                
            elif bird_type == 'swan':
                # Swan body
                pygame.draw.ellipse(screen, WHITE, (picture_x + 15, frame_y + 30, 30, 20))
                # Neck
                pygame.draw.polygon(screen, WHITE, [
                    (picture_x + 35, frame_y + 35),
                    (picture_x + 38, frame_y + 20),
                    (picture_x + 42, frame_y + 18),
                    (picture_x + 43, frame_y + 25),
                    (picture_x + 40, frame_y + 35)
                ])
                # Head
                pygame.draw.ellipse(screen, WHITE, (picture_x + 38, frame_y + 15, 10, 8))
                # Beak
                pygame.draw.polygon(screen, (255, 140, 0), [
                    (picture_x + 46, frame_y + 18),
                    (picture_x + 50, frame_y + 18),
                    (picture_x + 46, frame_y + 20)
                ])
                # Black marking
                pygame.draw.polygon(screen, BLACK, [
                    (picture_x + 42, frame_y + 17),
                    (picture_x + 46, frame_y + 18),
                    (picture_x + 42, frame_y + 19)
                ])
                # Eye
                pygame.draw.circle(screen, BLACK, (picture_x + 42, frame_y + 17), 1)
                
            elif bird_type == 'robin':
                # Robin body
                pygame.draw.ellipse(screen, (110, 70, 30), (picture_x + 20, frame_y + 28, 22, 17))
                # Red breast
                pygame.draw.ellipse(screen, (220, 60, 40), (picture_x + 25, frame_y + 32, 15, 12))
                # Head
                pygame.draw.circle(screen, (110, 70, 30), (picture_x + 36, frame_y + 25), 7)
                # Beak
                pygame.draw.polygon(screen, (255, 165, 0), [
                    (picture_x + 41, frame_y + 25),
                    (picture_x + 45, frame_y + 24),
                    (picture_x + 41, frame_y + 26)
                ])
                # Eye
                pygame.draw.circle(screen, WHITE, (picture_x + 37, frame_y + 24), 2)
                pygame.draw.circle(screen, BLACK, (picture_x + 37, frame_y + 24), 1)
        
    # Furniture is now drawn as platforms instead of background decoration

def draw_furniture_platform(screen, platform, camera_x, furniture_type):
    draw_x = platform.x - camera_x
    
    if furniture_type == "table":
        # Draw table legs first
        leg_height = 40
        pygame.draw.rect(screen, DARK_WOOD, (draw_x + 10, platform.y + platform.height, 8, leg_height))
        pygame.draw.rect(screen, DARK_WOOD, (draw_x + platform.width - 18, platform.y + platform.height, 8, leg_height))
        # Draw table top (landable surface)
        pygame.draw.rect(screen, PLATFORM_SURFACE, (draw_x, platform.y, platform.width, platform.height))
        
    elif furniture_type == "sofa":
        # Draw sofa base
        pygame.draw.rect(screen, (120, 80, 60), (draw_x, platform.y + 10, platform.width, platform.height + 20))
        # Draw back
        pygame.draw.rect(screen, (100, 60, 40), (draw_x, platform.y - 30, platform.width, 40))
        # Draw arms
        pygame.draw.rect(screen, (100, 60, 40), (draw_x - 10, platform.y - 30, 20, platform.height + 50))
        pygame.draw.rect(screen, (100, 60, 40), (draw_x + platform.width - 10, platform.y - 30, 20, platform.height + 50))
        # Draw seat surface (landable)
        pygame.draw.rect(screen, PLATFORM_SURFACE, (draw_x, platform.y, platform.width, platform.height))
        
    elif furniture_type == "leather_couch":
        # Draw leather couch in rich brown
        leather_brown = (101, 67, 33)
        leather_dark = (80, 53, 26)
        # Draw base
        pygame.draw.rect(screen, leather_brown, (draw_x, platform.y + 10, platform.width, platform.height + 20))
        # Draw back with tufted pattern
        pygame.draw.rect(screen, leather_dark, (draw_x, platform.y - 35, platform.width, 45))
        # Tufting details
        for i in range(3):
            tuft_x = draw_x + (platform.width // 4) * (i + 1)
            pygame.draw.circle(screen, leather_brown, (tuft_x, platform.y - 15), 4)
        # Draw arms
        pygame.draw.rect(screen, leather_dark, (draw_x - 12, platform.y - 35, 24, platform.height + 55))
        pygame.draw.rect(screen, leather_dark, (draw_x + platform.width - 12, platform.y - 35, 24, platform.height + 55))
        # Draw seat surface (landable)
        pygame.draw.rect(screen, PLATFORM_SURFACE, (draw_x, platform.y, platform.width, platform.height))
        # Highlight for leather shine
        pygame.draw.line(screen, (120, 80, 40), (draw_x + 10, platform.y + 5), (draw_x + platform.width - 10, platform.y + 5), 2)
        
    elif furniture_type == "grey_couch":
        # Draw modern grey couch
        grey_main = (128, 128, 128)
        grey_dark = (96, 96, 96)
        grey_light = (160, 160, 160)
        # Draw base
        pygame.draw.rect(screen, grey_main, (draw_x, platform.y + 10, platform.width, platform.height + 20))
        # Draw back with modern straight lines
        pygame.draw.rect(screen, grey_dark, (draw_x, platform.y - 40, platform.width, 50))
        # Draw cushion divisions
        cushion_width = platform.width // 3
        for i in range(2):
            cushion_x = draw_x + cushion_width * (i + 1)
            pygame.draw.line(screen, grey_dark, (cushion_x, platform.y - 40), (cushion_x, platform.y + 20), 3)
        # Draw modern slim arms
        pygame.draw.rect(screen, grey_dark, (draw_x - 8, platform.y - 40, 16, platform.height + 60))
        pygame.draw.rect(screen, grey_dark, (draw_x + platform.width - 8, platform.y - 40, 16, platform.height + 60))
        # Draw seat surface (landable)
        pygame.draw.rect(screen, PLATFORM_SURFACE, (draw_x, platform.y, platform.width, platform.height))
        # Add cushion highlights
        for i in range(3):
            cushion_x = draw_x + cushion_width * i + 10
            pygame.draw.rect(screen, grey_light, (cushion_x, platform.y + 2, cushion_width - 20, 4))
        
    elif furniture_type == "chair":
        # Draw chair back
        pygame.draw.rect(screen, DARK_WOOD, (draw_x, platform.y - 40, 8, 50))
        # Draw legs
        pygame.draw.rect(screen, DARK_WOOD, (draw_x + 5, platform.y + platform.height, 8, 30))
        pygame.draw.rect(screen, DARK_WOOD, (draw_x + platform.width - 13, platform.y + platform.height, 8, 30))
        # Draw seat (landable surface)
        pygame.draw.rect(screen, PLATFORM_SURFACE, (draw_x, platform.y, platform.width, platform.height))
        
    elif furniture_type == "bookshelf":
        # Draw bookshelf structure
        pygame.draw.rect(screen, DARK_WOOD, (draw_x, platform.y - 60, platform.width, platform.height + 60))
        # Draw shelves
        for shelf_y in range(platform.y - 60, platform.y + platform.height, 25):
            pygame.draw.line(screen, BLACK, (draw_x, shelf_y), (draw_x + platform.width, shelf_y), 2)
        # Draw top surface (landable)
        pygame.draw.rect(screen, PLATFORM_SURFACE, (draw_x, platform.y, platform.width, platform.height))
        
    else:  # Default platform
        pygame.draw.rect(screen, PLATFORM_SURFACE, (draw_x, platform.y, platform.width, platform.height))

async def show_title_screen(screen):
    """Show title screen with high scores until ENTER is pressed"""
    clock = pygame.time.Clock()
    font = pygame.font.Font(None, 72)
    medium_font = pygame.font.Font(None, 48)
    small_font = pygame.font.Font(None, 36)
    
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    return  # Start the game
        
        # Clear screen with gradient background
        screen.fill(BLUE)
        
        # Game title
        title_text = font.render("Oma's Game", True, WHITE)
        title_rect = title_text.get_rect(center=(SCREEN_WIDTH // 2, 80))
        screen.blit(title_text, title_rect)
        
        # Subtitle
        subtitle_text = medium_font.render("Help the pets reach Oma's bed!", True, WHITE)
        subtitle_rect = subtitle_text.get_rect(center=(SCREEN_WIDTH // 2, 140))
        screen.blit(subtitle_text, subtitle_rect)
        
        # TODO: Re-enable high scores display later
        # High scores
        # high_score_title = medium_font.render("HIGH SCORES", True, YELLOW)
        # score_rect = high_score_title.get_rect(center=(SCREEN_WIDTH // 2, 200))
        # screen.blit(high_score_title, score_rect)
        
        # high_scores = get_high_scores()
        # for i, score_line in enumerate(high_scores[:8]):  # Show top 8
        #     score_text = small_font.render(score_line, True, WHITE)
        #     score_rect = score_text.get_rect(center=(SCREEN_WIDTH // 2, 240 + i * 30))
        #     screen.blit(score_text, score_rect)
        
        # Instructions
        start_text = medium_font.render("Press ENTER to start", True, GREEN)
        start_rect = start_text.get_rect(center=(SCREEN_WIDTH // 2, 520))
        screen.blit(start_text, start_rect)
        
        
        pygame.display.flip()
        clock.tick(FPS)
        await asyncio.sleep(0)

async def show_game_over_screen(screen, final_score, round_reached):
    """Show game over screen with character chase animation"""
    
    # Track game over event
    track_event('game_over', {
        'final_score': final_score,
        'round_reached': round_reached,
        'timestamp': datetime.now().isoformat()
    })
    
    clock = pygame.time.Clock()
    font = pygame.font.Font(None, 72)
    medium_font = pygame.font.Font(None, 48)
    small_font = pygame.font.Font(None, 36)
    
    # Load character sprites and scissors
    characters = [
        pygame.image.load("sprites/shoogie.png"),
        pygame.image.load("sprites/florence.png"), 
        pygame.image.load("sprites/sue.png")
    ]
    characters = [pygame.transform.scale(char, (64, 64)) for char in characters]
    
    try:
        scissors = pygame.image.load("sprites/scissors.png")
        scissors = pygame.transform.scale(scissors, (80, 80))
    except:
        # Create fallback scissors if sprite doesn't exist
        scissors = pygame.Surface((80, 80))
        scissors.fill(RED)
        pygame.draw.polygon(scissors, SILVER, [(10, 20), (70, 20), (40, 60)])
    
    # Animation variables
    animation_time = 0
    chase_speed = 3
    
    # TODO: Re-enable high score functionality later
    # Check if this is a high score and get player name if needed
    # current_scores = load_high_scores()
    # is_high_score = (len(current_scores) < MAX_HIGH_SCORES or 
    #                  final_score > current_scores[-1]["score"] if current_scores else True)
    
    # player_name = "Anonymous"
    # if is_high_score:
    #     player_name = await get_player_name(screen, final_score, round_reached)
    
    # Add to high scores with player name
    # made_high_score = add_high_score(final_score, round_reached, player_name)
    
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    return  # Return to title screen
                elif event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()
        
        # Clear screen
        screen.fill(BLACK)
        
        # Game Over title
        game_over_text = font.render("GAME OVER", True, RED)
        title_rect = game_over_text.get_rect(center=(SCREEN_WIDTH // 2, 50))
        screen.blit(game_over_text, title_rect)
        
        # Final score
        score_text = medium_font.render(f"Final Score: {final_score:,}", True, WHITE)
        score_rect = score_text.get_rect(center=(SCREEN_WIDTH // 2, 100))
        screen.blit(score_text, score_rect)
        
        round_text = medium_font.render(f"Reached Round: {round_reached}", True, WHITE)
        round_rect = round_text.get_rect(center=(SCREEN_WIDTH // 2, 140))
        screen.blit(round_text, round_rect)
        
        
        # Character chase animation
        animation_time += 1
        base_y = 250
        
        for i, char in enumerate(characters):
            char_x = -100 + (animation_time * chase_speed) + (i * 80)
            char_y = base_y + math.sin(animation_time * 0.1 + i) * 20
            
            if char_x < SCREEN_WIDTH + 100:  # Only draw if on screen
                screen.blit(char, (char_x, char_y))
        
        # Scissors chasing
        scissors_x = -180 + (animation_time * chase_speed)
        scissors_y = base_y + 10
        if scissors_x < SCREEN_WIDTH + 100:
            screen.blit(scissors, (scissors_x, scissors_y))
        
        # Reset animation when everything is off screen
        if animation_time * chase_speed > SCREEN_WIDTH + 300:
            animation_time = 0
        
        
        # Instructions
        continue_text = medium_font.render("Press ENTER to continue", True, GREEN)
        continue_rect = continue_text.get_rect(center=(SCREEN_WIDTH // 2, 560))
        screen.blit(continue_text, continue_rect)
        
        pygame.display.flip()
        clock.tick(FPS)
        await asyncio.sleep(0)

async def main():
    print("Starting game...")
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Oma's Adventure")
    clock = pygame.time.Clock()
    print("Display initialized")
    
    
    # Main game loop with screens
    while True:
        # Show title screen
        await show_title_screen(screen)
        
        # Start new game
        current_round = 1
        total_score = 0
        
        # Track game start
        track_event('game_started', {
            'timestamp': datetime.now().isoformat(),
            'starting_round': current_round
        })
        
        game_running = await run_game(screen, current_round, total_score)
        
        if not game_running:
            break
    
    pygame.quit()
    sys.exit()

async def run_game(screen, current_round, total_score):
    """Run the main game loop and return True if should continue, False if quit"""
    clock = pygame.time.Clock()
    
    player = Player(100, 400)
    # Reset all character lives for new game
    for character in player.all_characters:
        character.lives = 3
    
    camera = Camera()
    platforms, platform_types, treats, plants, enemies, bed, character_pickups = create_level(current_round)
    print("Level created")
    
    score = 0  # Start each game with fresh score
    treats_collected = 0
    font = pygame.font.Font(None, 36)
    small_font = pygame.font.Font(None, 24)
    game_finished = False
    
    # Notification system
    notification_text = ""
    notification_timer = 0
    
    running = True
    print("Starting main loop")
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False  # Quit game
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    player.attack()
                    
        # Add right-side wall to prevent passing over the bed (level end)
        bed_right_wall = pygame.Rect(bed.rect.x + bed.rect.width, bed.rect.y - 100, 20, 120)  # Wall on right side to block passage
        all_platforms = platforms + [bed_right_wall]
        
        player.update(all_platforms, camera.x)
        camera.update(player)
        
        # (Removed double jump notification timer)
            
        # Update character pickups
        for pickup in character_pickups:
            pickup.update()
            
        # Update notification timer
        if notification_timer > 0:
            notification_timer -= 1
        
        for attack in player.attacks[:]:
            attack.update()
            if isinstance(attack, (Hairball, MeowWave)):
                if attack.rect.y > SCREEN_HEIGHT or attack.rect.x < camera.x - 100 or attack.rect.x > camera.x + SCREEN_WIDTH + 100:
                    player.attacks.remove(attack)
                elif isinstance(attack, MeowWave) and attack.lifetime <= 0:
                    player.attacks.remove(attack)
                else:
                    for enemy in enemies[:]:
                        if attack.rect.colliderect(enemy.rect):
                            enemies.remove(enemy)
                            if attack in player.attacks:
                                player.attacks.remove(attack)
                            score += 50
                            # Shoogie gets omnidirectional charge when killing with meow
                            if isinstance(attack, MeowWave) and player.current_char.name == "Shoogie":
                                player.activate_shoogie_powerup()
                            
        # Sue's old spin attack code - no longer needed since it's just a ground pound now
                    
        # Check Sue's attack effects against enemies
        for effect in player.sue_attack_effects:
            for enemy in enemies[:]:
                if effect.rect.colliderect(enemy.rect):
                    enemies.remove(enemy)
                    score += 50
                    
        for treat in treats:
            if not treat.collected and player.rect.colliderect(treat.rect):
                treat.collected = True
                treats_collected += 1
                score += 10
                # Sue gets treat count increase
                player.collect_treat()
                
        # Check plant pickups
        for plant in plants:
            if not plant.collected and player.rect.colliderect(plant.rect):
                plant.collected = True
                score += 20
                # Florence gets speed and jump boost
                player.activate_plant_powerup()
                    
        # Check character pickups
        for pickup in character_pickups:
            if not pickup.collected and player.rect.colliderect(pickup.rect):
                pickup.collected = True
                if player.add_character(pickup.character_name):
                    score += 100  # Bonus points for character pickup
                    # Auto-switch to the new character
                    player.switch_character(len(player.characters) - 1)
                    # Show notification
                    notification_text = f"New character: {pickup.character_name}! Press X to switch!"
                    notification_timer = 180  # 3 seconds at 60 FPS
                
        for enemy in enemies:
            enemy.update()
            if player.rect.colliderect(enemy.rect):
                # Character takes damage and loses a life
                character_died = player.current_char.take_damage()
                score = max(0, score - DEATH_PENALTY)
                
                # Reset position and camera
                player.rect.x = 100
                player.rect.y = 400
                camera.x = 0
                
                if character_died:
                    # Remove dead character from rotation
                    all_characters_dead = player.remove_dead_character()
                    if all_characters_dead:
                        # Game over - show game over screen with total + current round score
                        final_score = total_score + score
                        await show_game_over_screen(screen, final_score, current_round)
                        return True  # Return to title screen
                
                # Regenerate all enemies when player takes damage
                level_scaling = 1 + (current_round - 1) * LENGTH_INCREASE_PER_ROUND
                enemy_scaling = 1 + (current_round - 1) * ENEMY_INCREASE_PER_ROUND
                level_length = int(BASE_LEVEL_LENGTH * level_scaling)
                min_enemies = int(BASE_MIN_ENEMIES * enemy_scaling)
                max_enemies = int(BASE_MAX_ENEMIES * enemy_scaling)
                enemies = generate_enemies(level_length, min_enemies, max_enemies, current_round)
                
        # Check if player reached the bed
        if player.rect.colliderect(bed.rect):
            game_finished = True
            # Add round completion bonus
            score += ROUND_COMPLETION_BONUS
            total_score += score
            
            if await show_finish_screen(screen, total_score, current_round):
                # Track level completion
                track_event('level_completed', {
                    'round_completed': current_round,
                    'score_earned': score,
                    'total_score': total_score,
                    'treats_collected': treats_collected,
                    'timestamp': datetime.now().isoformat()
                })
                
                # Advance to next round
                current_round += 1
                player = Player(100, 400)
                camera = Camera()
                platforms, platform_types, treats, plants, enemies, bed, character_pickups = create_level(current_round)
                score = 0  # Reset score for new round
                treats_collected = 0
                game_finished = False
            else:
                return True  # Return to title screen
                
        # Draw house interior background
        draw_house_interior(screen, camera.x)
        
        for i, platform in enumerate(platforms):
            if platform.x - camera.x < SCREEN_WIDTH and platform.x - camera.x + platform.width > 0:
                furniture_type = platform_types[i] if i < len(platform_types) else "default"
                if furniture_type == "floor":
                    # Draw floor platforms normally
                    pygame.draw.rect(screen, DARK_WOOD, 
                                   (platform.x - camera.x, platform.y, platform.width, platform.height))
                else:
                    # Draw furniture platforms
                    draw_furniture_platform(screen, platform, camera.x, furniture_type)
                
        for treat in treats:
            if treat.rect.x - camera.x < SCREEN_WIDTH and treat.rect.x - camera.x > -48:
                treat.draw(screen, camera.x)
                
        for plant in plants:
            if plant.rect.x - camera.x < SCREEN_WIDTH and plant.rect.x - camera.x > -32:
                plant.draw(screen, camera.x)
                
        for pickup in character_pickups:
            if pickup.rect.x - camera.x < SCREEN_WIDTH and pickup.rect.x - camera.x > -64:
                pickup.draw(screen, camera.x)
                
        for enemy in enemies:
            if enemy.rect.x - camera.x < SCREEN_WIDTH and enemy.rect.x - camera.x > -30:
                enemy.draw(screen, camera.x)
                
        for attack in player.attacks:
            attack.draw(screen, camera.x)
            
        player.draw(screen, camera.x)
        
        # Draw bed
        if bed.rect.x - camera.x < SCREEN_WIDTH and bed.rect.x - camera.x > -200:
            bed.draw(screen, camera.x)
        
        score_text = font.render(f"Score: {score}", True, BLACK)
        screen.blit(score_text, (10, 10))
        
        treats_text = font.render(f"Treats: {treats_collected}", True, BLACK)
        screen.blit(treats_text, (10, 45))
        
        round_text = font.render(f"Round: {current_round}", True, BLACK)
        screen.blit(round_text, (10, 80))
        
        # Draw character roster with sprites and hearts
        chars_title = font.render("Characters:", True, BLACK)
        screen.blit(chars_title, (10, 115))
        
        char_y = 145
        for i, character in enumerate(player.characters):
            # Character sprite (mini version)
            mini_sprite = pygame.transform.scale(character.sprite, (32, 32))
            screen.blit(mini_sprite, (15, char_y))
            
            # Character name
            char_name = small_font.render(character.name, True, BLACK)
            screen.blit(char_name, (55, char_y + 5))
            
            # Current character indicator
            if character == player.current_char:
                pygame.draw.rect(screen, YELLOW, (12, char_y - 3, 38, 38), 3)
            
            # Hearts for this character
            for heart_i in range(3):
                heart_x = 140 + heart_i * 18
                heart_y = char_y + 8
                if heart_i < character.lives:
                    # Filled heart (red)
                    pygame.draw.polygon(screen, RED, [
                        (heart_x + 8, heart_y + 3),     # top point
                        (heart_x + 4, heart_y),         # left top curve
                        (heart_x, heart_y + 4),         # left bottom curve
                        (heart_x + 8, heart_y + 12),    # bottom point
                        (heart_x + 16, heart_y + 4),    # right bottom curve
                        (heart_x + 12, heart_y),        # right top curve
                    ])
                else:
                    # Empty heart (gray outline)
                    pygame.draw.polygon(screen, GRAY, [
                        (heart_x + 8, heart_y + 3),     # top point
                        (heart_x + 4, heart_y),         # left top curve
                        (heart_x, heart_y + 4),         # left bottom curve
                        (heart_x + 8, heart_y + 12),    # bottom point
                        (heart_x + 16, heart_y + 4),    # right bottom curve
                        (heart_x + 12, heart_y),        # right top curve
                    ], 2)
            
            char_y += 45  # Space between characters
        
        # Show power-up status (adjust based on number of characters)
        y_offset = 145 + len(player.characters) * 45 + 10
        if player.florence_speed_boost > 0:
            florence_text = small_font.render(f"Florence: Speed Boost ({player.florence_speed_boost//60 + 1}s)", True, GREEN)
            screen.blit(florence_text, (10, y_offset))
            y_offset += 25
            
        if player.shoogie_omnidirectional_charges > 0:
            shoogie_text = small_font.render(f"Shoogie: Omni Attacks x{player.shoogie_omnidirectional_charges}", True, GREEN)
            screen.blit(shoogie_text, (10, y_offset))
            y_offset += 25
            
        if player.sue_treat_count > 0:
            sue_jump_text = small_font.render(f"Sue: Jump Boost +{player.sue_treat_count * 2}%", True, GREEN)
            screen.blit(sue_jump_text, (10, y_offset))
            y_offset += 25
        
        # Modern controls panel with background
        controls_bg = pygame.Surface((240, 120))
        controls_bg.set_alpha(180)
        controls_bg.fill((30, 30, 30))  # Dark semi-transparent background
        screen.blit(controls_bg, (SCREEN_WIDTH - 250, 5))
        
        # Controls title
        controls_title = small_font.render("CONTROLS", True, WHITE)
        screen.blit(controls_title, (SCREEN_WIDTH - 240, 12))
        
        # Modern controls with icons/symbols
        controls = [
            "← →     Movement",
            "↑       Jump (2x for Sue)", 
            "SPACE   Attack",
            "X       Switch Cat"
        ]
        
        # Show notification if active
        if notification_timer > 0:
            notification_surface = font.render(notification_text, True, GREEN)
            notification_bg = pygame.Surface((notification_surface.get_width() + 20, notification_surface.get_height() + 10))
            notification_bg.set_alpha(200)
            notification_bg.fill((0, 0, 0))
            screen.blit(notification_bg, (SCREEN_WIDTH // 2 - notification_surface.get_width() // 2 - 10, 100))
            screen.blit(notification_surface, (SCREEN_WIDTH // 2 - notification_surface.get_width() // 2, 105))
        
        # Draw controls with modern styling
        for i, text in enumerate(controls):
            control_text = small_font.render(text, True, WHITE)
            screen.blit(control_text, (SCREEN_WIDTH - 240, 35 + i * 20))
        
        pygame.display.flip()
        clock.tick(FPS)
        await asyncio.sleep(0)  # Allow other tasks to run
        
    return True  # Should never reach here, but return to title screen if it does

print("Python script loaded")

if __name__ == "__main__":
    print("Running main function")
    asyncio.run(main())
else:
    print(f"Script imported as {__name__}")