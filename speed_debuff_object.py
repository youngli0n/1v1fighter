"""Speed Debuff Object - Slows down the opponent"""
from game_object import GameObject, register_object_type
from game_config import COLORS, GAME_CONFIG


class SpeedDebuffObject(GameObject):
    """
    A collectible object that slows down the opponent player
    
    Unlike other objects, this one affects the OTHER player (your opponent),
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


# Register this object type
register_object_type('speed_debuff', SpeedDebuffObject)
