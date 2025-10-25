import pygame
import random
from game_config import GAME_CONFIG, COLORS


class GameObject:
    """
    Base class for all collectible game objects
    
    This is like a template that defines what ALL objects must have.
    Think of it like a recipe that says "Every object needs:
    - A position (x, y)
    - A way to be drawn
    - A way to check if a player collected it"
    
    Other specific object types (like SpeedBoost) will inherit from this
    and add their own special abilities.
    """
    
    def __init__(self, x, y, color):
        """
        Initialize a game object
        
        Args:
            x: X position in tiles
            y: Y position in tiles
            color: Color of the object (RGB tuple)
        """
        self.x = float(x)
        self.y = float(y)
        self.color = color
        self.size = GAME_CONFIG['object_size']
        
        # Create rect for drawing and collision detection
        self.rect = pygame.Rect(
            int(self.x * GAME_CONFIG['tile_size_in_pixels']),
            int(self.y * GAME_CONFIG['tile_size_in_pixels']),
            int(self.size * GAME_CONFIG['tile_size_in_pixels']),
            int(self.size * GAME_CONFIG['tile_size_in_pixels'])
        )
    
    def is_collected(self, player_rect):
        """
        Check if this object was collected by a player
        
        Args:
            player_rect: The pygame.Rect of the player
            
        Returns:
            True if collision detected, False otherwise
        """
        return self.rect.colliderect(player_rect)
    
    def draw(self, screen):
        """
        Draw the object on the screen
        
        Args:
            screen: The pygame surface to draw on
        """
        pygame.draw.rect(screen, self.color, self.rect)
    
    def apply_effect(self, player, current_time):
        """
        Apply the object's effect to a player
        
        This method is meant to be overridden by child classes.
        Each type of object will do different things.
        
        Args:
            player: The Player object that collected this
            current_time: Current game time
        """
        # Base class does nothing - child classes will override this
        pass


class SpeedBoostObject(GameObject):
    """
    A collectible object that increases the player's speed
    
    This inherits from GameObject, which means it gets all the basic
    stuff (position, drawing, collision) automatically, and then adds
    its own special ability: speed boost!
    
    Think of GameObject as the parent (has eyes, ears, legs) and
    SpeedBoostObject as the child (inherits eyes, ears, legs, PLUS
    can run super fast).
    """
    
    def __init__(self, x, y):
        """
        Initialize a speed boost object
        
        Args:
            x: X position in tiles
            y: Y position in tiles
        """
        # Call the parent class's __init__ method
        # This sets up position, color, size, etc.
        super().__init__(x, y, COLORS['speed_boost_object'])
    
    def apply_effect(self, player, current_time):
        """
        Give the player a speed boost
        
        Args:
            player: The Player object that collected this
            current_time: Current game time
        """
        # Apply speedup effect to the player who collected it
        player.apply_effect('speedup', GAME_CONFIG['speed_boost_duration'], current_time)


class SpeedDebuffObject(GameObject):
    """
    A collectible object that slows down the opponent
    
    Just like SpeedBoostObject, this inherits from GameObject
    but does the opposite - it slows down the enemy player!
    """
    
    def __init__(self, x, y):
        """
        Initialize a speed debuff object
        
        Args:
            x: X position in tiles
            y: Y position in tiles
        """
        # Call the parent class's __init__ method
        super().__init__(x, y, COLORS['speed_debuff_object'])
    
    def apply_effect(self, player, other_player, current_time):
        """
        Slow down the opponent
        
        Args:
            player: The Player object that collected this (not affected)
            other_player: The opponent to slow down
            current_time: Current game time
        """
        # Apply slow effect to the OTHER player (your opponent)
        other_player.apply_effect('slow', GAME_CONFIG['speed_debuff_duration'], current_time)


def generate_object(object_type, walls):
    """
    Generate a random object of a specific type
    
    Args:
        object_type: String indicating type ('speed_boost' or 'speed_debuff')
        walls: List of existing walls to avoid placing objects on
        
    Returns:
        GameObject instance or None if no valid position found
    """
    if not GAME_CONFIG['objects_enabled']:
        return None
    
    attempts = 0
    max_attempts = 100
    
    while attempts < max_attempts:
        attempts += 1
        
        # Random position anywhere on the map
        x = random.uniform(0, GAME_CONFIG['tiles_width'] - GAME_CONFIG['object_size'])
        y = random.uniform(0, GAME_CONFIG['tiles_height'] - GAME_CONFIG['object_size'])
        
        # Create temporary object to check collision
        temp_object = GameObject(x, y, (0, 0, 0))
        
        # Check if overlaps with walls
        overlaps_wall = False
        for wall in walls:
            if temp_object.rect.colliderect(wall.rect):
                overlaps_wall = True
                break
        
        if not overlaps_wall:
            # Valid position - create the appropriate object type
            if object_type == 'speed_boost':
                return SpeedBoostObject(x, y)
            elif object_type == 'speed_debuff':
                return SpeedDebuffObject(x, y)
    
    # Couldn't find valid position after many attempts
    return None


def generate_objects(walls, num_objects):
    """
    Generate a list of random objects for the match
    
    Args:
        walls: List of existing walls
        num_objects: Number of objects to generate
        
    Returns:
        List of GameObject instances
    """
    objects = []
    
    if not GAME_CONFIG['objects_enabled']:
        return objects
    
    # 50/50 chance for each type
    for _ in range(num_objects):
        if random.random() < 0.5:
            obj = generate_object('speed_boost', walls)
        else:
            obj = generate_object('speed_debuff', walls)
        
        if obj:
            objects.append(obj)
    
    return objects
