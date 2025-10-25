import pygame
from game_config import GAME_CONFIG


class Projectile:
    """Represents a bullet shot by a player"""
    
    def __init__(self, x, y, direction, speed_multiplier=1.0):
        """
        Initialize a projectile
        
        Args:
            x: Starting x position (in tiles)
            y: Starting y position (in tiles)
            direction: Direction of travel (1 for P1 going right, -1 for P2 going left)
            speed_multiplier: Speed multiplier for the projectile (default 1.0)
        """
        self.x = float(x)
        self.y = float(y)
        self.direction = direction  # 1 for P1, -1 for P2
        self.speed_multiplier = speed_multiplier  # Speed multiplier (1.0 = normal, 2.0 = double speed)
        
        # Create rect for drawing, converting float positions to integers
        self.rect = pygame.Rect(
            int(self.x * GAME_CONFIG['tile_size_in_pixels']),
            int(self.y * GAME_CONFIG['tile_size_in_pixels']),
            GAME_CONFIG['projectile_size'] * GAME_CONFIG['tile_size_in_pixels'],
            GAME_CONFIG['projectile_size'] * GAME_CONFIG['tile_size_in_pixels']
        )
    
    def update(self, dt):
        """
        Move the projectile based on its speed and direction
        
        Args:
            dt: Time delta (in seconds) since last frame
        """
        self.x += self.direction * GAME_CONFIG['projectile_speed'] * self.speed_multiplier * dt
        self.rect.x = int(self.x * GAME_CONFIG['tile_size_in_pixels'])
    
    def draw(self, screen):
        """
        Draw the projectile on the screen
        
        Args:
            screen: The pygame surface to draw on
        """
        pygame.draw.rect(screen, GAME_CONFIG['projectile_color'], self.rect)
