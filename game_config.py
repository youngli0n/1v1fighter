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
    'text': (0, 0, 0)               # Black
} 