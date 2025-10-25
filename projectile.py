import pygame
import math
from game_config import GAME_CONFIG


class Projectile:
    """Represents a bullet shot by a player"""
    
    def __init__(self, x, y, direction, is_deflected=False):
        """
        Initialize a projectile
        
        Args:
            x: Starting x position (in tiles)
            y: Starting y position (in tiles)
            direction: Direction of travel (1 for P1 going right, -1 for P2 going left)
            is_deflected: Whether this is a deflected shot (travels 2x speed)
        """
        self.x = float(x)
        self.y = float(y)
        self.direction = direction  # 1 for P1, -1 for P2
        self.is_deflected = is_deflected
        
        # Create rect for drawing, converting float positions to integers
        self.rect = pygame.Rect(
            int(self.x * GAME_CONFIG['tile_size_in_pixels']),
            int(self.y * GAME_CONFIG['tile_size_in_pixels']),
            GAME_CONFIG['projectile_size'] * GAME_CONFIG['tile_size_in_pixels'],
            GAME_CONFIG['projectile_size'] * GAME_CONFIG['tile_size_in_pixels']
        )
    
    def get_speed_multiplier(self):
        """Get the speed multiplier for this projectile"""
        return 2.0 if self.is_deflected else 1.0
    
    def update(self, dt):
        """
        Move the projectile based on its speed and direction
        
        Args:
            dt: Time delta (in seconds) since last frame
        """
        speed_multiplier = self.get_speed_multiplier()
        self.x += self.direction * GAME_CONFIG['projectile_speed'] * speed_multiplier * dt
        self.rect.x = int(self.x * GAME_CONFIG['tile_size_in_pixels'])
    
    def get_movement_with_substeps(self, dt, max_step_size=0.5):
        """
        Calculate the movement path with sub-steps for collision detection
        
        Args:
            dt: Time delta (in seconds) since last frame
            max_step_size: Maximum distance to move per sub-step (in tiles)
            
        Returns:
            list: List of intermediate positions (x, y) including start and end
        """
        speed_multiplier = self.get_speed_multiplier()
        distance = abs(self.direction * GAME_CONFIG['projectile_speed'] * speed_multiplier * dt)
        
        # If moving slow enough, no sub-stepping needed
        if distance <= max_step_size:
            return [(self.x, self.y), (self.x + self.direction * distance, self.y)]
        
        # Calculate number of sub-steps needed
        num_steps = math.ceil(distance / max_step_size)
        step_size = distance / num_steps
        
        positions = []
        for i in range(num_steps + 1):
            step_distance = step_size * i
            x_pos = self.x + self.direction * step_distance
            positions.append((x_pos, self.y))
        
        return positions
    
    def draw(self, screen):
        """
        Draw the projectile on the screen
        
        Args:
            screen: The pygame surface to draw on
        """
        pygame.draw.rect(screen, GAME_CONFIG['projectile_color'], self.rect)
