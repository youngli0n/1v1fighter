# Game configuration - all game settings are stored here for easy modification
GAME_CONFIG = {
    'tile_size_in_pixels': 20,      # Size of one tile in pixels
    'tiles_width': 40,    # Width of the game board in tiles
    'tiles_height': 20,   # Height of the game board in tiles
    'stats_panel_height_in_pixels': 100,  # Height of the stats panel in pixels
    'player_speed': 5,    # Player movement speed in tiles per second
    'fps': 60,           # Frames per second - controls game smoothness
    
    # Shooting configuration
    'fire_rate': 5,              # shots per second
    'projectile_speed': 100,      # tiles per second
    'projectile_size': 1,        # in tiles
    'projectile_color': (0,0,0), # RGB tuple
    'slow_factor': 0.5,          # target speed multiplier
    'slow_duration': 2.0,        # seconds
    'speedup_factor': 1.5,       # shooter speed multiplier
    'speedup_duration': 1.0,     # seconds
    
    # Shield configuration
    'shield_boost_duration': 4.0,  # seconds
    'shield_boost_amount': 0.05,   # 5% speed boost per block
    'shield_boost_max': 0.5,       # maximum 50% total boost
    
    # Wall configuration
    'walls_enabled': True,         # Set to False to disable walls
    'num_walls_per_side': 5,       # Number of walls on each player's side
    'wall_width': 0.5,             # Wall width in tiles (half player size)
    'wall_height': 3,              # Wall height in tiles (3x player size)
    'wall_min_distance': 5,        # Minimum distance between walls in tiles
    'wall_color': (128, 128, 128), # Gray color for walls
    
    # Round configuration
    'rounds_to_win': 3,          # First to X rounds wins the match
    'countdown_ticks': 3,       # Countdown starts from this number
    'countdown_duration': 2,    # Total duration of countdown sequence in seconds
    
    # AI configuration
    'ai_enabled': False,        # Set to True to enable AI control for Player 2
    
    # Object configuration
    'objects_enabled': True,         # Set to False to disable collectible objects
    'num_objects_per_match': 10,    # Total number of objects to spawn per match
    'object_spawn_rate': 1.0,       # How often objects spawn (seconds between spawns)
    'object_size': 0.8,             # Object size in tiles
    'speed_boost_duration': 5.0,    # Duration of speed boost effect (seconds)
    'speed_boost_multiplier': 1.3,  # Speed multiplier (1.3 = 30% faster)
    'speed_debuff_duration': 3.0,   # Duration of speed debuff effect (seconds)
    'speed_debuff_multiplier': 0.7, # Speed multiplier (0.7 = 30% slower)
    'pierce_duration': 1.0,         # Duration of pierce ability (seconds) - ability to break through walls
    
    # Object placement guardrails
    'min_distance_from_border': 0.5,      # Minimum distance from map edges in tiles
    'min_distance_from_player': 2.0,      # Minimum distance from player spawn in tiles
    'min_distance_between_objects': 1.0,  # Minimum distance between objects in tiles
    'min_distance_from_center_line': 1.0, # Minimum distance from center line (player border) in tiles
    'object_generation_max_attempts': 100, # Maximum attempts to place an object
}

# Calculate window dimensions in pixels based on tile counts
GAME_CONFIG['window_width_in_pixels'] = GAME_CONFIG['tiles_width'] * GAME_CONFIG['tile_size_in_pixels']
GAME_CONFIG['window_height_in_pixels'] = (GAME_CONFIG['tiles_height'] * GAME_CONFIG['tile_size_in_pixels'] + 
                                        GAME_CONFIG['stats_panel_height_in_pixels'])

# Colors used in the game - defined as RGB tuples
COLORS = {
    'background': (255, 255, 255),  # White
    'center_line': (0, 0, 0),       # Black
    'player1': (255, 0, 0),         # Red
    'player2': (0, 0, 255),         # Blue
    'stats_panel': (240, 240, 240), # Light gray
    'progress_bar_bg': (200, 200, 200),  # Darker gray
    'progress_bar_fill': (0, 150, 0),    # Green
    'text': (0, 0, 0),              # Black
    'speed_boost_object': (0, 255, 0),   # Green for speed boost
    'speed_debuff_object': (255, 140, 0), # Orange for speed debuff
    'pierce_object': (255, 0, 255)  # Purple for pierce ability
} 