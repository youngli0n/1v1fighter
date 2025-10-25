"""Speed Boost Collectible - Increases player speed"""
from game_collectible import GameCollectible, register_collectible_type
from game_config import GAME_CONFIG, COLORS


class SpeedBoostCollectible(GameCollectible):
    """A collectible that increases the player's speed"""
    
    def __init__(self, x, y):
        """
        Initialize a speed boost collectible
        
        Args:
            x: X position in tiles
            y: Y position in tiles
        """
        super().__init__(x, y, COLORS['speed_boost_object'])
    
    def apply_effect(self, player, current_time):
        """
        Increase the player's speed with compounding effect
        
        Args:
            player: The Player that collected this
            current_time: Current game time
        """
        # Calculate time to add (compound if already has speedup effect)
        if current_time < player.speedup_end_time:
            # Already has speedup - extend the duration
            remaining_time = player.speedup_end_time - current_time
            new_total_duration = remaining_time + GAME_CONFIG['speed_boost_duration']
        else:
            # No existing speedup - start fresh
            new_total_duration = GAME_CONFIG['speed_boost_duration']
        
        # Apply the compounded speedup effect
        player.speedup_end_time = current_time + new_total_duration


# Register this collectible type
register_collectible_type('speed_boost', SpeedBoostCollectible)
