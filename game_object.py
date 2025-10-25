import pygame
import random
import math
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


# Object Registry - Maps object type strings to their classes
# To add a new object type, just add an entry here and create the corresponding file!
_OBJECT_REGISTRY = {}

def register_object_type(type_name, object_class):
    """
    Register an object type in the registry
    
    Args:
        type_name: String name of the object type (e.g., 'speed_boost')
        object_class: The class that implements this object type
    """
    _OBJECT_REGISTRY[type_name] = object_class

def get_object_class(type_name):
    """
    Get the class for a registered object type
    
    Args:
        type_name: String name of the object type
        
    Returns:
        The class if found, None otherwise
    """
    return _OBJECT_REGISTRY.get(type_name)


def _find_valid_positions(walls, existing_objects, player1_pos, player2_pos, target_side):
    """
    Generate a list of valid positions for object placement using smart grid-based algorithm
    
    Args:
        walls: List of walls to avoid
        existing_objects: List of already placed objects
        player1_pos: (x, y) tuple of player 1 position
        player2_pos: (x, y) tuple of player 2 position
        target_side: 'left' or 'right' to specify which side of the map
    
    Returns:
        List of (x, y) tuples representing valid positions
    """
    valid_positions = []
    
    # Guardrail constants
    min_distance_from_border = GAME_CONFIG['min_distance_from_border']
    min_distance_from_player = GAME_CONFIG['min_distance_from_player']
    min_distance_between_objects = GAME_CONFIG['min_distance_between_objects']
    min_distance_from_center_line = GAME_CONFIG['min_distance_from_center_line']
    
    # Determine valid X bounds based on target side
    map_center_x = GAME_CONFIG['tiles_width'] / 2
    if target_side == 'left':
        min_x = min_distance_from_border
        max_x = map_center_x - min_distance_from_center_line
    else:  # right side
        min_x = map_center_x + min_distance_from_center_line
        max_x = GAME_CONFIG['tiles_width'] - GAME_CONFIG['object_size'] - min_distance_from_border
    
    # Create a grid of potential positions (grid step = object size for efficiency)
    grid_step = GAME_CONFIG['object_size']
    
    # Generate grid positions
    for x in range(int(min_x * (1 / grid_step)), int(max_x * (1 / grid_step))):
        x_pos = x * grid_step
        for y in range(int(min_distance_from_border * (1 / grid_step)), 
                       int((GAME_CONFIG['tiles_height'] - GAME_CONFIG['object_size'] - min_distance_from_border) * (1 / grid_step))):
            y_pos = y * grid_step
            
            # Check if position is valid (all guardrails)
            is_valid = True
            
            # Create temporary object to check collision
            temp_object = GameObject(x_pos, y_pos, (0, 0, 0))
            
            # Guardrail 1: Check if overlaps with walls
            for wall in walls:
                if temp_object.rect.colliderect(wall.rect):
                    is_valid = False
                    break
            
            if not is_valid:
                continue
            
            # Guardrail 2: Check distance from player starting positions
            if player1_pos:
                dx = x_pos - player1_pos[0]
                dy = y_pos - player1_pos[1]
                if math.sqrt(dx * dx + dy * dy) < min_distance_from_player:
                    is_valid = False
                    continue
            
            if player2_pos:
                dx = x_pos - player2_pos[0]
                dy = y_pos - player2_pos[1]
                if math.sqrt(dx * dx + dy * dy) < min_distance_from_player:
                    is_valid = False
                    continue
            
            # Guardrail 3: Check if overlaps with existing objects
            for existing_obj in existing_objects:
                dx = x_pos - existing_obj.x
                dy = y_pos - existing_obj.y
                if math.sqrt(dx * dx + dy * dy) < min_distance_between_objects:
                    is_valid = False
                    break
            
            if is_valid:
                valid_positions.append((x_pos, y_pos))
    
    return valid_positions


def generate_object(object_type, walls, existing_objects=None, player1_pos=None, player2_pos=None, target_side=None):
    """
    Generate a random object of a specific type with smart grid-based placement
    
    Args:
        object_type: String indicating type ('speed_boost', 'speed_buff', etc.)
        walls: List of existing walls to avoid placing objects on
        existing_objects: List of already placed objects to avoid overlapping
        player1_pos: (x, y) tuple of player 1 position
        player2_pos: (x, y) tuple of player 2 position
        target_side: 'left' or 'right' to specify which side of the map
        
    Returns:
        GameObject instance or None if no valid position found
    """
    if not GAME_CONFIG['objects_enabled']:
        return None
    
    if existing_objects is None:
        existing_objects = []
    
    # Get all valid positions for the target side
    valid_positions = _find_valid_positions(walls, existing_objects, player1_pos, player2_pos, target_side)
    
    if not valid_positions:
        # No valid positions available
        return None
    
    # Pick a random position from valid positions
    x, y = random.choice(valid_positions)
    
    # Get the object class from the registry
    object_class = get_object_class(object_type)
    if object_class:
        # Create an instance of the object at the valid position
        return object_class(x, y)
    
    # Object type not found in registry
    print(f"Warning: Object type '{object_type}' not registered!")
    return None


def generate_objects(walls, num_objects, player1_pos=None, player2_pos=None):
    """
    Generate a list of random objects for the match with guaranteed equal distribution
    
    Args:
        walls: List of existing walls
        num_objects: Number of objects to generate (split equally between sides)
        player1_pos: (x, y) tuple of player 1 position
        player2_pos: (x, y) tuple of player 2 position
        
    Returns:
        List of GameObject instances
    """
    objects = []
    
    if not GAME_CONFIG['objects_enabled']:
        return objects
    
    # Split the map in half horizontally (left side for Player 1, right side for Player 2)
    map_center_x = GAME_CONFIG['tiles_width'] / 2
    
    # Calculate objects per side - ensure exact equality
    objects_per_side = num_objects // 2
    extra_object = num_objects % 2  # If odd number, we'll randomly assign the extra one
    
    # Generate objects for LEFT side (Player 1 area)
    for i in range(objects_per_side + (1 if extra_object == 1 and random.random() < 0.5 else 0)):
        attempts = 0
        max_attempts = 100
        obj = None
        
        while attempts < max_attempts and obj is None:
            attempts += 1
            
            # Generate random object type
            if random.random() < 0.5:
                obj = generate_object('speed_boost', walls, objects, player1_pos, player2_pos, 'left')
            else:
                obj = generate_object('speed_buff', walls, objects, player1_pos, player2_pos, 'left')
            
            # Must be on the LEFT side (x < center)
            if obj and obj.x < map_center_x:
                objects.append(obj)
            else:
                obj = None
        
        # If we failed to place on left side, try one more time with specific constraints
        if obj is None:
            # Try generating with constrained X position for left side
            attempts = 0
            while attempts < 50 and obj is None:
                attempts += 1
                # Force X to be in left half
                x = random.uniform(0.5, map_center_x - 0.5)
                y = random.uniform(0.5, GAME_CONFIG['tiles_height'] - 0.5)
                
                # Create temporary object to check collision
                temp_object = GameObject(x, y, (0, 0, 0))
                
                # Check all guardrails
                overlaps_wall = False
                for wall in walls:
                    if temp_object.rect.colliderect(wall.rect):
                        overlaps_wall = True
                        break
                
                if overlaps_wall:
                    continue
                
                too_close_to_player = False
                if player1_pos:
                    dx = x - player1_pos[0]
                    dy = y - player1_pos[1]
                    if math.sqrt(dx * dx + dy * dy) < 2.0:
                        too_close_to_player = True
                
                if player2_pos and not too_close_to_player:
                    dx = x - player2_pos[0]
                    dy = y - player2_pos[1]
                    if math.sqrt(dx * dx + dy * dy) < 2.0:
                        too_close_to_player = True
                
                if too_close_to_player:
                    continue
                
                overlaps_object = False
                for existing_obj in objects:
                    dx = x - existing_obj.x
                    dy = y - existing_obj.y
                    if math.sqrt(dx * dx + dy * dy) < 1.0:
                        overlaps_object = True
                        break
                
                if not overlaps_object:
                    if random.random() < 0.5:
                        obj = SpeedBoostObject(x, y)
                    else:
                        obj = SpeedBuffObject(x, y)
                    objects.append(obj)
    
    # Generate objects for RIGHT side (Player 2 area)
    # If we had an odd number and didn't assign it to left, assign to right
    left_count = len([o for o in objects if o.x < map_center_x])
    right_count = objects_per_side + (1 if extra_object == 1 and left_count == objects_per_side else 0)
    
    for i in range(right_count):
        attempts = 0
        max_attempts = 100
        obj = None
        
        while attempts < max_attempts and obj is None:
            attempts += 1
            
            # Generate random object type
            if random.random() < 0.5:
                obj = generate_object('speed_boost', walls, objects, player1_pos, player2_pos, 'right')
            else:
                obj = generate_object('speed_buff', walls, objects, player1_pos, player2_pos, 'right')
            
            # Must be on the RIGHT side (x >= center)
            if obj and obj.x >= map_center_x:
                objects.append(obj)
            else:
                obj = None
        
        # If we failed to place on right side, try one more time with specific constraints
        if obj is None:
            attempts = 0
            while attempts < 50 and obj is None:
                attempts += 1
                # Force X to be in right half
                x = random.uniform(map_center_x, GAME_CONFIG['tiles_width'] - 0.5)
                y = random.uniform(0.5, GAME_CONFIG['tiles_height'] - 0.5)
                
                # Create temporary object to check collision
                temp_object = GameObject(x, y, (0, 0, 0))
                
                # Check all guardrails
                overlaps_wall = False
                for wall in walls:
                    if temp_object.rect.colliderect(wall.rect):
                        overlaps_wall = True
                        break
                
                if overlaps_wall:
                    continue
                
                too_close_to_player = False
                if player1_pos:
                    dx = x - player1_pos[0]
                    dy = y - player1_pos[1]
                    if math.sqrt(dx * dx + dy * dy) < 2.0:
                        too_close_to_player = True
                
                if player2_pos and not too_close_to_player:
                    dx = x - player2_pos[0]
                    dy = y - player2_pos[1]
                    if math.sqrt(dx * dx + dy * dy) < 2.0:
                        too_close_to_player = True
                
                if too_close_to_player:
                    continue
                
                overlaps_object = False
                for existing_obj in objects:
                    dx = x - existing_obj.x
                    dy = y - existing_obj.y
                    if math.sqrt(dx * dx + dy * dy) < 1.0:
                        overlaps_object = True
                        break
                
                if not overlaps_object:
                    if random.random() < 0.5:
                        obj = SpeedBoostObject(x, y)
                    else:
                        obj = SpeedBuffObject(x, y)
                    objects.append(obj)
    
    return objects
