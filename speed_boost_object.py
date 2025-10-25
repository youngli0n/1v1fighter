"""Speed Boost Object - Increases player speed"""
from game_object import GameObject, register_object_type
from game_config import GAME_CONFIG, COLORS


class SpeedBoostObject(GameObject):
    """A collectible object that increases the player's speed"""
    
    def __init__(self, x, y):
        """
        Initialize a speed boost object
        
        Args:
            x: X position in tiles
            y: Y position in tiles
        """
        super().__init__(x, y, COLORS['speed_boost_object'])
    
    def apply_effect(self, player, current_time):
        """
        Increase the player's speed
        
        Args:
            player: The Player object that collected this
            current_time: Current game time
        """
        player.apply_effect('speedup', GAME_CONFIG['speed_boost_duration'], current_time)


# Register this object type
register_object_type('speed_boost', SpeedBoostObject)
