import pygame
import time
from game_config import GAME_CONFIG, COLORS
from projectile import Projectile


class Player:
    """Represents a player in the game"""
    
    def __init__(self, x, y, color):
        """
        Initialize a player
        
        Args:
            x: Starting x position (in tiles)
            y: Starting y position (in tiles)
            color: Player color (Red for P1, Blue for P2)
        """
        # Store position as float values for smooth movement
        self.x = float(x)
        self.y = float(y)
        self.color = color  # Store player color
        
        # Store initial position for reset
        self.start_x = float(x)
        self.start_y = float(y)
        
        # Effect tracking
        self.slow_end_time = 0  # When current slow effect ends
        self.speedup_end_time = 0  # When current speedup effect ends
        self.block_speedups = 0  # Count of active block speedups (max 10 for 50%)
        
        # Shooting
        self.last_shot_time = 0  # Time of last shot
        self.projectiles = []  # List of active projectiles
        
        # Shield
        self.shield_active = False  # Whether shield is currently active
        self.shield_boosts = []  # List of (end_time, boost_amount) tuples
        
        # Create rect for drawing, converting float positions to integers
        self.rect = pygame.Rect(
            int(self.x * GAME_CONFIG['tile_size_in_pixels']),
            int(self.y * GAME_CONFIG['tile_size_in_pixels']),
            GAME_CONFIG['tile_size_in_pixels'],
            GAME_CONFIG['tile_size_in_pixels']
        )
    
    def reset(self):
        """Reset player to initial state (position and effects)"""
        # Reset position
        self.x = self.start_x
        self.y = self.start_y
        
        # Reset effects
        self.slow_end_time = 0
        self.speedup_end_time = 0
        self.block_speedups = 0
        
        # Reset shooting
        self.last_shot_time = 0
        self.projectiles = []
        
        # Reset shield
        self.shield_active = False
        self.shield_boosts = []
        
        # Update rect for drawing
        self.rect.x = int(self.x * GAME_CONFIG['tile_size_in_pixels'])
        self.rect.y = int(self.y * GAME_CONFIG['tile_size_in_pixels'])
    
    def is_slowed(self, current_time):
        """Check if player is currently slowed"""
        return current_time < self.slow_end_time
    
    def is_speedup(self, current_time):
        """Check if player has active speedup effect"""
        return current_time < self.speedup_end_time
    
    def get_total_speed_multiplier(self, current_time):
        """
        Calculate total speed multiplier including all effects and regeneration
        
        Args:
            current_time: Current game time
            
        Returns:
            Speed multiplier (1.0 = normal, 0.5 = half speed, 1.5 = 50% faster)
        """
        # Base speed is always 100%
        base_speed = 1.0
        
        # Calculate shield boost (temporary, from blocking)
        shield_boost = 0.0
        # Remove expired boosts and sum active ones
        self.shield_boosts = [(end_time, boost) for end_time, boost in self.shield_boosts 
                            if current_time < end_time]
        shield_boost = sum(boost for _, boost in self.shield_boosts)
        shield_boost = min(shield_boost, GAME_CONFIG['shield_boost_max'])
        
        # Calculate temporary effect (slow or speedup)
        temp_effect = 0.0
        if self.is_slowed(current_time):
            # Calculate regeneration from slow
            time_remaining = self.slow_end_time - current_time
            slow_factor = GAME_CONFIG['slow_factor']  # e.g., 0.5
            # Linearly regenerate from slow_factor to 1.0
            temp_effect = slow_factor + (1.0 - slow_factor) * (1.0 - time_remaining / GAME_CONFIG['slow_duration'])
        elif self.is_speedup(current_time):
            # Calculate decay from speedup
            time_remaining = self.speedup_end_time - current_time
            speedup_factor = GAME_CONFIG['speedup_factor']  # e.g., 1.5
            # Linearly decay from speedup_factor to 1.0
            temp_effect = 1.0 + (speedup_factor - 1.0) * (time_remaining / GAME_CONFIG['speedup_duration'])
        else:
            temp_effect = 1.0  # No temporary effect
        
        # Combine effects, ensuring we never exceed 100% from regeneration
        total_speed = base_speed + shield_boost
        if temp_effect < 1.0:  # If we're slowed
            total_speed *= temp_effect  # Apply slow multiplicatively
        else:  # If we're sped up
            total_speed = min(total_speed + (temp_effect - 1.0), 1.5)  # Add speedup, cap at 150%
        
        return total_speed
    
    def get_fire_rate_multiplier(self, current_time):
        """Calculate fire rate multiplier based on current speed effects"""
        return self.get_total_speed_multiplier(current_time)
    
    def can_shoot(self, current_time):
        """
        Check if player can shoot based on fire rate and current speed effects
        
        Args:
            current_time: Current game time
            
        Returns:
            True if player can shoot, False otherwise
        """
        if self.shield_active:
            return False
        fire_rate_multiplier = self.get_fire_rate_multiplier(current_time)
        return current_time - self.last_shot_time >= 1.0 / (GAME_CONFIG['fire_rate'] * fire_rate_multiplier)
    
    def apply_effect(self, effect_type, duration, current_time):
        """
        Apply an effect to the player
        
        Args:
            effect_type: Type of effect ('slow', 'speedup', or 'block')
            duration: How long the effect lasts (in seconds)
            current_time: Current game time
        """
        if effect_type == 'slow':
            if not self.is_slowed(current_time):
                self.slow_end_time = current_time + duration
        elif effect_type == 'speedup':
            # Only apply if not already speedup
            if not self.is_speedup(current_time):
                self.speedup_end_time = current_time + duration
        elif effect_type == 'block':
            # Add a new shield boost
            self.shield_boosts.append((current_time + GAME_CONFIG['shield_boost_duration'], 
                                     GAME_CONFIG['shield_boost_amount']))
    
    def shoot(self, current_time):
        """
        Create a new projectile if allowed by fire rate
        
        Args:
            current_time: Current game time
        """
        if self.can_shoot(current_time):
            # Calculate projectile starting position
            projectile_x = self.x + (1 if self.color == COLORS['player1'] else -1)
            projectile_y = self.y
            
            # Create and add projectile
            direction = 1 if self.color == COLORS['player1'] else -1
            self.projectiles.append(Projectile(projectile_x, projectile_y, direction))
            self.last_shot_time = current_time
    
    def move(self, dx, dy, dt, current_time, other_player, walls=None):
        """
        Move the player based on input and speed modifiers
        
        Args:
            dx: Horizontal movement (positive = right, negative = left)
            dy: Vertical movement (positive = down, negative = up)
            dt: Time delta (in seconds) between frames
            current_time: Current game time
            other_player: The other player (for collision detection)
            walls: List of walls to check collision with (optional)
        """
        # If shield is active, only allow vertical movement
        if self.shield_active:
            dx = 0
        
        # Only update position if there's actual movement
        if dx != 0 or dy != 0:
            # Calculate new position in tiles
            speed_multiplier = self.get_total_speed_multiplier(current_time)
            new_x = self.x + dx * dt * speed_multiplier
            new_y = self.y + dy * dt * speed_multiplier
            
            # Check if new position is within screen bounds (in tiles)
            if (0 <= new_x <= GAME_CONFIG['tiles_width'] - 1 and
                0 <= new_y <= GAME_CONFIG['tiles_height'] - 1):
                
                # Check for collision with other player
                # We use a small buffer (0.1 tiles) to prevent players from getting too close
                if (abs(new_x - other_player.x) >= 1.1 or 
                    abs(new_y - other_player.y) >= 1.1):
                    
                    # Check for collision with walls
                    can_move = True
                    if walls:
                        # Create temporary rect for collision detection
                        temp_rect = pygame.Rect(
                            int(new_x * GAME_CONFIG['tile_size_in_pixels']),
                            int(new_y * GAME_CONFIG['tile_size_in_pixels']),
                            GAME_CONFIG['tile_size_in_pixels'],
                            GAME_CONFIG['tile_size_in_pixels']
                        )
                        
                        for wall in walls:
                            if temp_rect.colliderect(wall.rect):
                                can_move = False
                                break
                    
                    if can_move:
                        self.x = new_x
                        self.y = new_y
                        # Update rect for drawing, converting float positions to integers
                        self.rect.x = int(self.x * GAME_CONFIG['tile_size_in_pixels'])
                        self.rect.y = int(self.y * GAME_CONFIG['tile_size_in_pixels'])
    
    def update_projectiles(self, dt, other_player, current_time, walls=None):
        """
        Update all projectiles and check for collisions
        
        Args:
            dt: Time delta (in seconds) between frames
            other_player: The other player (for collision detection)
            current_time: Current game time
            walls: List of walls to check collision with (optional)
        """
        # Update existing projectiles
        for projectile in self.projectiles[:]:
            projectile.update(dt)
            
            # Check if projectile is out of bounds
            if (projectile.x < 0 or 
                projectile.x > GAME_CONFIG['tiles_width'] or
                projectile.y < 0 or 
                projectile.y > GAME_CONFIG['tiles_height']):
                self.projectiles.remove(projectile)
                continue
            
            # Check for collision with walls
            hit_wall = False
            if walls:
                for wall in walls:
                    if projectile.rect.colliderect(wall.rect):
                        self.projectiles.remove(projectile)
                        hit_wall = True
                        break
                
                if hit_wall:
                    continue
            
            # Check for collision with other player
            if projectile.rect.colliderect(other_player.rect):
                # If other player's shield is active, block the projectile and fire back at 2x speed
                if other_player.shield_active:
                    # Give the blocking player a speed boost
                    other_player.apply_effect('block', GAME_CONFIG['shield_boost_duration'], current_time)
                    
                    # Create a deflected projectile that goes back at the attacker
                    # Direction is reversed (if projectile was going right, deflect left, and vice versa)
                    deflect_direction = -projectile.direction
                    
                    # Spawn deflected projectile at the blocking player's position
                    from projectile import Projectile
                    deflected_shot = Projectile(
                        x=other_player.x + (1 if deflect_direction == 1 else -1),
                        y=other_player.y,
                        direction=deflect_direction,
                        is_deflected=True  # This makes it travel at 2x speed
                    )
                    
                    # Add the deflected shot to the blocking player's projectiles
                    # This ensures it won't be deflected by the original shooter's shield
                    other_player.projectiles.append(deflected_shot)
                else:
                    # Apply effects when hit without shield
                    other_player.apply_effect('slow', GAME_CONFIG['slow_duration'], current_time)
                    self.apply_effect('speedup', GAME_CONFIG['speedup_duration'], current_time)
                
                # Remove the original projectile (whether deflected or not)
                self.projectiles.remove(projectile)
    
    def get_progress(self):
        """
        Calculate progress towards center as a percentage (0-100)
        Progress is based on when the player's first pixel reaches the center line
        
        Returns:
            Progress percentage (0-100)
        """
        center_x = GAME_CONFIG['tiles_width'] / 2
        if self.x < center_x:  # Player 1
            # Calculate distance to center, considering player's size
            distance_to_center = center_x - (self.x + 1)  # +1 because we want first pixel to reach
            total_distance = center_x
            return ((total_distance - distance_to_center) / total_distance) * 100
        else:  # Player 2
            # Calculate distance to center, considering player's size
            distance_to_center = (self.x) - center_x  # No +1 because we want first pixel to reach
            total_distance = center_x
            return ((total_distance - distance_to_center) / total_distance) * 100
