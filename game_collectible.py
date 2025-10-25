import pygame
import random
import math
from game_config import GAME_CONFIG, COLORS


class GameCollectible:
    """
    Base class for all collectible game items
    
    This is like a template that defines what ALL collectibles must have.
    Think of it like a recipe that says "Every collectible needs:
    - A position (x, y)
    - A way to be drawn
    - A way to check if a player collected it"
    
    Other specific collectible types (like SpeedBoost) will inherit from this
    and add their own special abilities.
    """
    
    def __init__(self, x, y, color):
        """
        Initialize a game collectible
        
        Args:
            x: X position in tiles
            y: Y position in tiles
            color: Color of the collectible (RGB tuple)
        """
        self.x = float(x)
        self.y = float(y)
        self.color = color
        self.size = GAME_CONFIG['collectible_size']
        
        # Create rect for drawing and collision detection
        self.rect = pygame.Rect(
            int(self.x * GAME_CONFIG['tile_size_in_pixels']),
            int(self.y * GAME_CONFIG['tile_size_in_pixels']),
            int(self.size * GAME_CONFIG['tile_size_in_pixels']),
            int(self.size * GAME_CONFIG['tile_size_in_pixels'])
        )
    
    def is_collected(self, player_rect):
        """
        Check if this collectible was collected by a player
        
        Args:
            player_rect: The pygame.Rect of the player
            
        Returns:
            True if collision detected, False otherwise
        """
        return self.rect.colliderect(player_rect)
    
    def draw(self, screen):
        """
        Draw the collectible on the screen
        
        Args:
            screen: The pygame surface to draw on
        """
        pygame.draw.rect(screen, self.color, self.rect)
    
    def apply_effect(self, player, current_time):
        """
        Apply the collectible's effect to a player
        
        This method is meant to be overridden by child classes.
        Each type of collectible will do different things.
        
        Args:
            player: The Player that collected this
            current_time: Current game time
        """
        # Base class does nothing - child classes will override this
        pass


# Collectible Registry - Maps collectible type strings to their classes
# To add a new collectible type, just add an entry here and create the corresponding file!
_COLLECTIBLE_REGISTRY = {}

def register_collectible_type(type_name, collectible_class):
    """
    Register a collectible type in the registry
    
    Args:
        type_name: String name of the collectible type (e.g., 'speed_boost')
        collectible_class: The class that implements this collectible type
    """
    _COLLECTIBLE_REGISTRY[type_name] = collectible_class

def get_collectible_class(type_name):
    """
    Get the class for a registered collectible type
    
    Args:
        type_name: String name of the collectible type
        
    Returns:
        The class if found, None otherwise
    """
    return _COLLECTIBLE_REGISTRY.get(type_name)


def _find_valid_positions(walls, existing_collectibles, player1_pos, player2_pos, target_side):
    """
    Generate a list of valid positions for collectible placement using smart grid-based algorithm
    
    Args:
        walls: List of walls to avoid
        existing_collectibles: List of already placed collectibles
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
    min_distance_between_collectibles = GAME_CONFIG['min_distance_between_collectibles']
    min_distance_from_center_line = GAME_CONFIG['min_distance_from_center_line']
    
    # Determine valid X bounds based on target side
    map_center_x = GAME_CONFIG['tiles_width'] / 2
    if target_side == 'left':
        min_x = min_distance_from_border
        max_x = map_center_x - min_distance_from_center_line
    else:  # right side
        min_x = map_center_x + min_distance_from_center_line
        max_x = GAME_CONFIG['tiles_width'] - GAME_CONFIG['collectible_size'] - min_distance_from_border
    
    # Create a grid of potential positions (grid step = collectible size for efficiency)
    grid_step = GAME_CONFIG['collectible_size']
    
    # Generate grid positions
    for x in range(int(min_x * (1 / grid_step)), int(max_x * (1 / grid_step))):
        x_pos = x * grid_step
        for y in range(int(min_distance_from_border * (1 / grid_step)), 
                       int((GAME_CONFIG['tiles_height'] - GAME_CONFIG['collectible_size'] - min_distance_from_border) * (1 / grid_step))):
            y_pos = y * grid_step
            
            # Check if position is valid (all guardrails)
            is_valid = True
            
            # Create temporary collectible to check collision
            temp_object = GameCollectible(x_pos, y_pos, (0, 0, 0))
            
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
            
            # Guardrail 3: Check if overlaps with existing collectibles
            for existing_obj in existing_collectibles:
                dx = x_pos - existing_obj.x
                dy = y_pos - existing_obj.y
                if math.sqrt(dx * dx + dy * dy) < min_distance_between_collectibles:
                    is_valid = False
                    break
            
            if is_valid:
                valid_positions.append((x_pos, y_pos))
    
    return valid_positions


def generate_collectible(collectible_type, walls, existing_collectibles=None, player1_pos=None, player2_pos=None, target_side=None):
    """
    Generate a random collectible of a specific type with smart grid-based placement
    
    Args:
        collectible_type: String indicating type ('speed_boost', 'speed_buff', etc.)
        walls: List of existing walls to avoid placing collectibles on
        existing_collectibles: List of already placed collectibles to avoid overlapping
        player1_pos: (x, y) tuple of player 1 position
        player2_pos: (x, y) tuple of player 2 position
        target_side: 'left' or 'right' to specify which side of the map
        
    Returns:
        GameCollectible instance or None if no valid position found
    """
    if not GAME_CONFIG['collectibles_enabled']:
        return None
    
    if existing_collectibles is None:
        existing_collectibles = []
    
    # Get all valid positions for the target side
    valid_positions = _find_valid_positions(walls, existing_collectibles, player1_pos, player2_pos, target_side)
    
    if not valid_positions:
        # No valid positions available
        return None
    
    # Pick a random position from valid positions
    x, y = random.choice(valid_positions)
    
    # Get the collectible class from the registry
    collectible_class = get_collectible_class(collectible_type)
    if collectible_class:
        # Create an instance of the collectible at the valid position
        return collectible_class(x, y)
    
    # Collectible type not found in registry
    print(f"Warning: Collectible type '{collectible_type}' not registered!")
    return None


def generate_collectibles(walls, num_collectibles, player1_pos=None, player2_pos=None):
    """
    Generate a list of random collectibles for the match with guaranteed equal distribution
    
    Args:
        walls: List of existing walls
        num_collectibles: Number of collectibles to generate (split equally between sides)
        player1_pos: (x, y) tuple of player 1 position
        player2_pos: (x, y) tuple of player 2 position
        
    Returns:
        List of GameCollectible instances
    """
    collectibles = []
    
    if not GAME_CONFIG['objects_enabled']:
        return collectibles
    
    # Split the map in half horizontally (left side for Player 1, right side for Player 2)
    map_center_x = GAME_CONFIG['tiles_width'] / 2
    
    # Calculate collectibles per side - ensure exact equality
    collectibles_per_side = num_collectibles // 2
    extra_collectible = num_collectibles % 2  # If odd number, we'll randomly assign the extra one
    
    # Generate collectibles for LEFT side (Player 1 area)
    for i in range(collectibles_per_side + (1 if extra_collectible == 1 and random.random() < 0.5 else 0)):
        attempts = 0
        max_attempts = 100
        collectible = None
        
        while attempts < max_attempts and collectible is None:
            attempts += 1
            
            # Generate random collectible type
            if random.random() < 0.5:
                collectible = generate_collectible('speed_boost', walls, collectibles, player1_pos, player2_pos, 'left')
            else:
                collectible = generate_collectible('speed_buff', walls, collectibles, player1_pos, player2_pos, 'left')
            
            # Must be on the LEFT side (x < center)
            if collectible and collectible.x < map_center_x:
                collectibles.append(collectible)
            else:
                collectible = None
        
        # If we failed to place on left side, try one more time with specific constraints
        if collectible is None:
            # Try generating with constrained X position for left side
            attempts = 0
            while attempts < 50 and collectible is None:
                attempts += 1
                # Force X to be in left half
                x = random.uniform(0.5, map_center_x - 0.5)
                y = random.uniform(0.5, GAME_CONFIG['tiles_height'] - 0.5)
                
                # Create temporary collectible to check collision
                temp_object = GameCollectible(x, y, (0, 0, 0))
                
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
                
                overlaps_collectible = False
                for existing_collectible in collectibles:
                    dx = x - existing_collectible.x
                    dy = y - existing_collectible.y
                    if math.sqrt(dx * dx + dy * dy) < 1.0:
                        overlaps_collectible = True
                        break
                
                if not overlaps_collectible:
                    from speed_boost_collectible import SpeedBoostCollectible
                    from speed_buff_collectible import SpeedBuffCollectible
                    if random.random() < 0.5:
                        collectible = SpeedBoostCollectible(x, y)
                    else:
                        collectible = SpeedBuffCollectible(x, y)
                    collectibles.append(collectible)
    
    # Generate collectibles for RIGHT side (Player 2 area)
    # If we had an odd number and didn't assign it to left, assign to right
    left_count = len([c for c in collectibles if c.x < map_center_x])
    right_count = collectibles_per_side + (1 if extra_collectible == 1 and left_count == collectibles_per_side else 0)
    
    for i in range(right_count):
        attempts = 0
        max_attempts = 100
        collectible = None
        
        while attempts < max_attempts and collectible is None:
            attempts += 1
            
            # Generate random collectible type
            if random.random() < 0.5:
                collectible = generate_collectible('speed_boost', walls, collectibles, player1_pos, player2_pos, 'right')
            else:
                collectible = generate_collectible('speed_buff', walls, collectibles, player1_pos, player2_pos, 'right')
            
            # Must be on the RIGHT side (x >= center)
            if collectible and collectible.x >= map_center_x:
                collectibles.append(collectible)
            else:
                collectible = None
        
        # If we failed to place on right side, try one more time with specific constraints
        if collectible is None:
            attempts = 0
            while attempts < 50 and collectible is None:
                attempts += 1
                # Force X to be in right half
                x = random.uniform(map_center_x, GAME_CONFIG['tiles_width'] - 0.5)
                y = random.uniform(0.5, GAME_CONFIG['tiles_height'] - 0.5)
                
                # Create temporary collectible to check collision
                temp_object = GameCollectible(x, y, (0, 0, 0))
                
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
                
                overlaps_collectible = False
                for existing_collectible in collectibles:
                    dx = x - existing_collectible.x
                    dy = y - existing_collectible.y
                    if math.sqrt(dx * dx + dy * dy) < 1.0:
                        overlaps_collectible = True
                        break
                
                if not overlaps_collectible:
                    from speed_boost_collectible import SpeedBoostCollectible
                    from speed_buff_collectible import SpeedBuffCollectible
                    if random.random() < 0.5:
                        collectible = SpeedBoostCollectible(x, y)
                    else:
                        collectible = SpeedBuffCollectible(x, y)
                    collectibles.append(collectible)
    
    return collectibles
