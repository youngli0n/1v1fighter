import pygame
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
    
    def update(self, dt):
        """
        Move the projectile based on its speed and direction
        
        Args:
            dt: Time delta (in seconds) since last frame
        """
        # Deflected shots travel at 2x speed
        speed_multiplier = 2.0 if self.is_deflected else 1.0
        self.x += self.direction * GAME_CONFIG['projectile_speed'] * speed_multiplier * dt
        self.rect.x = int(self.x * GAME_CONFIG['tile_size_in_pixels'])
    
    def draw(self, screen):
        """
        Draw the projectile on the screen
        
        Args:
            screen: The pygame surface to draw on
        """
        pygame.draw.rect(screen, GAME_CONFIG['projectile_color'], self.rect)
