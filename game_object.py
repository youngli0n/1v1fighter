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


def generate_object(object_type, walls, existing_objects=None, player1_pos=None, player2_pos=None):
    """
    Generate a random object of a specific type with placement guardrails
    
    Args:
        object_type: String indicating type ('speed_boost' or 'speed_debuff')
        walls: List of existing walls to avoid placing objects on
        existing_objects: List of already placed objects to avoid overlapping
        player1_pos: (x, y) tuple of player 1 position
        player2_pos: (x, y) tuple of player 2 position
        
    Returns:
        GameObject instance or None if no valid position found
    """
    if not GAME_CONFIG['objects_enabled']:
        return None
    
    if existing_objects is None:
        existing_objects = []
    
    # Guardrail constants from game_config
    min_distance_from_border = GAME_CONFIG['min_distance_from_border']
    min_distance_from_player = GAME_CONFIG['min_distance_from_player']
    min_distance_between_objects = GAME_CONFIG['min_distance_between_objects']
    min_distance_from_center_line = GAME_CONFIG['min_distance_from_center_line']
    max_attempts = GAME_CONFIG['object_generation_max_attempts']
    
    attempts = 0
    
    while attempts < max_attempts:
        attempts += 1
        
        # Random position within bounds minus border buffer
        x = random.uniform(min_distance_from_border, GAME_CONFIG['tiles_width'] - GAME_CONFIG['object_size'] - min_distance_from_border)
        y = random.uniform(min_distance_from_border, GAME_CONFIG['tiles_height'] - GAME_CONFIG['object_size'] - min_distance_from_border)
        
        # Create temporary object to check collision
        temp_object = GameObject(x, y, (0, 0, 0))
        
        # Guardrail 1: Check distance from borders (redundant but explicit check)
        too_close_to_border = False
        if (x < min_distance_from_border or 
            x > GAME_CONFIG['tiles_width'] - GAME_CONFIG['object_size'] - min_distance_from_border or
            y < min_distance_from_border or 
            y > GAME_CONFIG['tiles_height'] - GAME_CONFIG['object_size'] - min_distance_from_border):
            too_close_to_border = True
        
        if too_close_to_border:
            continue
        
        # Guardrail 2: Check if overlaps with walls
        overlaps_wall = False
        for wall in walls:
            if temp_object.rect.colliderect(wall.rect):
                overlaps_wall = True
                break
        
        if overlaps_wall:
            continue
        
        # Guardrail 2.5: Check distance from center line (player border)
        map_center_x = GAME_CONFIG['tiles_width'] / 2
        too_close_to_center = abs(x - map_center_x) < min_distance_from_center_line
        
        if too_close_to_center:
            continue
        
        # Guardrail 3: Check distance from player starting positions
        too_close_to_player = False
        if player1_pos:
            dx = x - player1_pos[0]
            dy = y - player1_pos[1]
            distance = math.sqrt(dx * dx + dy * dy)
            if distance < min_distance_from_player:
                too_close_to_player = True
        
        if player2_pos and not too_close_to_player:
            dx = x - player2_pos[0]
            dy = y - player2_pos[1]
            distance = math.sqrt(dx * dx + dy * dy)
            if distance < min_distance_from_player:
                too_close_to_player = True
        
        if too_close_to_player:
            continue
        
        # Guardrail 4: Check if overlaps with existing objects
        overlaps_object = False
        for existing_obj in existing_objects:
            dx = x - existing_obj.x
            dy = y - existing_obj.y
            distance = math.sqrt(dx * dx + dy * dy)
            if distance < min_distance_between_objects:
                overlaps_object = True
                break
        
        if overlaps_object:
            continue
        
        # All guardrails passed - create the appropriate object type
        if object_type == 'speed_boost':
            return SpeedBoostObject(x, y)
        elif object_type == 'speed_debuff':
            return SpeedDebuffObject(x, y)
    
    # Couldn't find valid position after many attempts
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
                obj = generate_object('speed_boost', walls, objects, player1_pos, player2_pos)
            else:
                obj = generate_object('speed_debuff', walls, objects, player1_pos, player2_pos)
            
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
                        obj = SpeedDebuffObject(x, y)
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
                obj = generate_object('speed_boost', walls, objects, player1_pos, player2_pos)
            else:
                obj = generate_object('speed_debuff', walls, objects, player1_pos, player2_pos)
            
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
                        obj = SpeedDebuffObject(x, y)
                    objects.append(obj)
    
    return objects
