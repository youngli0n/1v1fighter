import pygame
from game_config import GAME_CONFIG


class Wall:
    """Represents a wall that blocks player and projectile movement"""
    
    def __init__(self, x, y):
        """
        Initialize a wall
        
        Args:
            x: X position in tiles (left edge)
            y: Y position in tiles (bottom edge)
        """
        self.x = float(x)
        self.y = float(y)
        self.width = GAME_CONFIG['wall_width']
        self.height = GAME_CONFIG['wall_height']
        
        # Create rect for drawing and collision detection
        self.rect = pygame.Rect(
            int(self.x * GAME_CONFIG['tile_size_in_pixels']),
            int((self.y - self.height) * GAME_CONFIG['tile_size_in_pixels']),  # Bottom-aligned
            int(self.width * GAME_CONFIG['tile_size_in_pixels']),
            int(self.height * GAME_CONFIG['tile_size_in_pixels'])
        )
    
    def get_tile_bounds(self):
        """
        Get the tile coordinates this wall occupies
        
        Returns:
            tuple: (min_x, min_y, max_x, max_y) in tiles
        """
        return (self.x, self.y - self.height, self.x + self.width, self.y)
    
    def overlaps_with(self, other_wall):
        """
        Check if this wall overlaps with another wall
        
        Args:
            other_wall: Another Wall object to check against
            
        Returns:
            True if walls overlap, False otherwise
        """
        self_min_x, self_min_y, self_max_x, self_max_y = self.get_tile_bounds()
        other_min_x, other_min_y, other_max_x, other_max_y = other_wall.get_tile_bounds()
        
        # Check if rectangles overlap
        return not (self_max_x <= other_min_x or self_min_x >= other_max_x or
                   self_max_y <= other_min_y or self_min_y >= other_max_y)
    
    def draw(self, screen):
        """
        Draw the wall on the screen
        
        Args:
            screen: The pygame surface to draw on
        """
        pygame.draw.rect(screen, GAME_CONFIG['wall_color'], self.rect)
