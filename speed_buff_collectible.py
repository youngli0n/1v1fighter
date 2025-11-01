"""Speed Buff Collectible - Speeds up the player who collects it"""
from game_collectible import GameCollectible, register_collectible_type
from game_config import COLORS, GAME_CONFIG


class SpeedBuffCollectible(GameCollectible):
    """
    A collectible that increases the player's speed
    
    This collectible speeds up the player who collects it.
    Multiple collections compound the effect (add more time to the buff).
    """
    
    def __init__(self, x, y):
        """
        Initialize a speed buff collectible
        
        Args:
            x: X position in tiles
            y: Y position in tiles
        """
        # Call the parent class's __init__ method
        super().__init__(x, y, COLORS['speed_debuff_object'])  # Using existing color
    
    def apply_effect(self, player, current_time, other_player=None):
        """
        Decrease the other player's speed with compounding effect
        
        Args:
            player: The Player that collected this
            current_time: Current game time
            other_player: The other Player that is being slowed down
        """
        if other_player is not None:
            # Calculate time to add (compound if already has slow effect)
            if current_time < other_player.slow_end_time:
                # Already slowed - extend the duration
                remaining_time = other_player.slow_end_time - current_time
                new_total_duration = remaining_time + GAME_CONFIG['speed_debuff_duration']
            else:
                # No existing slow - start fresh
                new_total_duration = GAME_CONFIG['speed_debuff_duration']

            # Apply the compounded slow effect (NOT speedup!)
            other_player.slow_end_time = current_time + new_total_duration


# Register this collectible type
register_collectible_type('speed_buff', SpeedBuffCollectible)
