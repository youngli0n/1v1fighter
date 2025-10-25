import pygame
import sys
import time  # For tracking effect durations
import random  # For random wall placement
import math  # For calculating distances
from game_config import GAME_CONFIG, COLORS
from ai_player import AIPlayer
from player import Player
from game_state import GameState
from renderer import Renderer
from wall import Wall
from game_object import generate_objects, SpeedBoostObject, SpeedDebuffObject

# Initialize Pygame - this is required before using any Pygame functions
pygame.init()

# Create the game window
screen = pygame.display.set_mode((GAME_CONFIG['window_width_in_pixels'], GAME_CONFIG['window_height_in_pixels']))
pygame.display.set_caption("Learning Python Game - Sprint 3")

# Create a clock object to control game speed
clock = pygame.time.Clock()

# Initialize font for text rendering
font = pygame.font.Font(None, 32) 

# Create the renderer to handle all drawing operations
renderer = Renderer(screen, font)

# Create game state tracker
game_state = GameState()

def generate_walls():
    """
    Generate walls for a new match with random placement
    
    Returns:
        list: List of Wall objects for both sides
    """
    walls = []
    
    if not GAME_CONFIG['walls_enabled']:
        return walls
    
    player1_start_x = 0
    player1_start_y = GAME_CONFIG['tiles_height'] // 2 - 0.5
    player2_start_x = GAME_CONFIG['tiles_width'] - 1
    player2_start_y = GAME_CONFIG['tiles_height'] // 2 - 0.5
    center_x = GAME_CONFIG['tiles_width'] / 2
    
    # Track positions to avoid overlaps
    placed_positions = []
    
    # Track if at least one wall blocks each player's path
    p1_path_blocked = False
    p2_path_blocked = False
    
    for wall_index in range(GAME_CONFIG['num_walls_per_side']):
        attempts = 0
        max_attempts = 100
        ensure_path_block = (wall_index == 0)  # Force first wall to block a path
        
        while attempts < max_attempts:
            attempts += 1
            
            # Random position on P1's side (left half, not in starting zone)
            x = random.uniform(2, center_x - GAME_CONFIG['wall_width'] - 1)
            y = random.uniform(GAME_CONFIG['wall_height'], GAME_CONFIG['tiles_height'] - 0.5)
            
            # Ensure first wall blocks at least one player's path
            if ensure_path_block and not (p1_path_blocked and p2_path_blocked):
                # Player 1 path is from x=0 to x=center_x (left to center)
                # Player 2 path would be from x=GAME_CONFIG['tiles_width']-1 to x=center_x (right to center, mirrored)
                # Check if this wall would block P1's path
                wall_blocks_p1 = (x < center_x and x + GAME_CONFIG['wall_width'] > 0)
                # For P2 (mirrored), check if mirrored wall would block
                mirrored_x = GAME_CONFIG['tiles_width'] - x - GAME_CONFIG['wall_width']
                wall_blocks_p2 = (mirrored_x > center_x and mirrored_x < GAME_CONFIG['tiles_width'] - 1)
                
                # Skip if we need to block a path but this wall doesn't do it
                if wall_blocks_p1 and p1_path_blocked and not p2_path_blocked and not wall_blocks_p2:
                    continue
                if wall_blocks_p2 and p2_path_blocked and not p1_path_blocked and not wall_blocks_p1:
                    continue
            
            # Create temporary wall to check overlaps
            temp_wall = Wall(x, y)
            
            # Calculate center of the new wall
            new_wall_center_x = x + GAME_CONFIG['wall_width'] / 2
            new_wall_center_y = y - GAME_CONFIG['wall_height'] / 2
            
            # Check if too close to existing walls (minimum distance check)
            too_close = False
            for existing_wall in walls:
                # Calculate center of existing wall
                existing_center_x = existing_wall.x + existing_wall.width / 2
                existing_center_y = existing_wall.y - existing_wall.height / 2
                
                # Calculate distance between centers
                dx = new_wall_center_x - existing_center_x
                dy = new_wall_center_y - existing_center_y
                distance = math.sqrt(dx * dx + dy * dy)
                
                # Check if distance is less than minimum required
                if distance < GAME_CONFIG['wall_min_distance']:
                    too_close = True
                    break
            
            # Check if overlaps with existing walls
            overlaps = False
            for existing_wall in walls:
                if temp_wall.overlaps_with(existing_wall):
                    overlaps = True
                    break
            
            # Check if overlaps with player starting positions
            if not overlaps and not too_close:
                # Check collision with player start zones (1 tile buffer)
                if not (abs(x - player1_start_x) < 1.5 and abs(y - player1_start_y) < 1.5):
                    # Valid position - add wall for P1's side
                    walls.append(Wall(x, y))
                    
                    # Add mirrored wall for P2's side
                    mirrored_x = GAME_CONFIG['tiles_width'] - x - GAME_CONFIG['wall_width']
                    walls.append(Wall(mirrored_x, y))
                    
                    # Track if paths are now blocked
                    if not p1_path_blocked and x < center_x:
                        p1_path_blocked = True
                    if not p2_path_blocked and mirrored_x > center_x:
                        p2_path_blocked = True
                    
                    placed_positions.append((x, y))
                    break
        
        if attempts >= max_attempts:
            # Couldn't find valid position after many attempts
            break
    
    return walls

def reset_players(p1=None, p2=None, walls=None):
    """
    Create or reset players to their starting positions
    
    Args:
        p1: Existing player1 object to reset (None for new player)
        p2: Existing player2 object to reset (None for new player)
        walls: List of walls (for AI controller)
    
    Returns:
        tuple: (player1, player2, ai_controller)
    """
    # If players exist, reset them; otherwise create new ones
    if p1 is not None and p2 is not None:
        # Use the reset method from the Player class
        p1.reset()
        p2.reset()
        player1, player2 = p1, p2
    else:
        # First time - create new players
        # Player 1 starts at left center
        player1 = Player(0, GAME_CONFIG['tiles_height'] // 2 - 0.5, COLORS['player1'])
        # Player 2 starts at right center
        player2 = Player(GAME_CONFIG['tiles_width'] - 1, GAME_CONFIG['tiles_height'] // 2 - 0.5, COLORS['player2'])
    
    # Create AI controller if enabled (pass walls parameter)
    ai_controller = AIPlayer(player2, player1, walls) if GAME_CONFIG['ai_enabled'] else None
    
    return player1, player2, ai_controller

# Main game loop
running = True
game_over = False
winner = None
show_instructions = True  # Show instructions at game start
walls = generate_walls()  # Generate walls at match start
# Generate players first to get their positions for object placement guardrails
player1, player2, ai_controller = reset_players(walls=walls)
# Get player starting positions for object placement
player1_pos = (player1.start_x, player1.start_y)
player2_pos = (player2.start_x, player2.start_y)
game_objects = generate_objects(walls, GAME_CONFIG['num_objects_per_match'], player1_pos, player2_pos)

while running:
    # Calculate delta time in seconds
    dt = clock.tick(GAME_CONFIG['fps']) / 1000.0  # Convert milliseconds to seconds
    current_time = time.time()
    
    # Handle events (keyboard input, window close, etc.)
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            # Handle instructions screen
            if show_instructions:
                if event.key == pygame.K_SPACE:
                    show_instructions = False
                    game_state.reset_round()  # Start the first round
                continue  # Don't process other inputs while instructions are showing
            if game_state.match_over:
                if event.key == pygame.K_r:  # Start new match
                    game_state.reset_match()
                    game_over = False
                    winner = None
                    walls = generate_walls()  # Generate new walls for new match
                    player1, player2, ai_controller = reset_players(player1, player2, walls)
                    # Get player starting positions for object placement
                    player1_pos = (player1.start_x, player1.start_y)
                    player2_pos = (player2.start_x, player2.start_y)
                    game_objects = generate_objects(walls, GAME_CONFIG['num_objects_per_match'], player1_pos, player2_pos)
            elif game_state.round_over:
                if event.key == pygame.K_SPACE:  # Start next round
                    game_state.reset_round()
                    game_over = False
                    winner = None
                    player1, player2, ai_controller = reset_players(player1, player2, walls)
            else:
                # Handle shooting
                if not game_state.countdown_active:
                    if event.key == pygame.K_v:  # Player 1 shoot
                        player1.shoot(current_time)
                    elif event.key == pygame.K_COMMA:  # Player 2 shoot
                        player2.shoot(current_time)
                # Handle shield activation
                if event.key == pygame.K_b:  # Player 1 shield
                    player1.shield_active = True
                elif event.key == pygame.K_PERIOD:  # Player 2 shield
                    player2.shield_active = True
        elif event.type == pygame.KEYUP:
            # Handle shield deactivation
            if event.key == pygame.K_b:  # Player 1 shield
                player1.shield_active = False
            elif event.key == pygame.K_PERIOD:  # Player 2 shield
                player2.shield_active = False
    
    # Update countdown if active
    if game_state.countdown_active:
        if game_state.update_countdown(current_time):
            # Countdown just finished
            pass
    
    if not game_over and not game_state.countdown_active:
        # Get keyboard input for player movement
        keys = pygame.key.get_pressed()
        
        # Calculate movement for Player 1 (WASD)
        dx1 = (keys[pygame.K_d] - keys[pygame.K_a]) * GAME_CONFIG['player_speed']
        dy1 = (keys[pygame.K_s] - keys[pygame.K_w]) * GAME_CONFIG['player_speed']
        
        # Move Player 1
        player1.move(dx1, dy1, dt, current_time, player2, walls)
        
        # Handle Player 2 movement (either AI or keyboard)
        if GAME_CONFIG['ai_enabled'] and ai_controller:
            ai_controller.update(dt, current_time)
        else:
            # Calculate movement for Player 2 (Arrow keys)
            dx2 = (keys[pygame.K_RIGHT] - keys[pygame.K_LEFT]) * GAME_CONFIG['player_speed']
            dy2 = (keys[pygame.K_DOWN] - keys[pygame.K_UP]) * GAME_CONFIG['player_speed']
            player2.move(dx2, dy2, dt, current_time, player1, walls)
        
        # Check win condition
        if player1.get_progress() >= 100:
            game_over = True
            winner = player1
            game_state.record_round_win(1)
        elif player2.get_progress() >= 100:
            game_over = True
            winner = player2
            game_state.record_round_win(2)
        
        # Update and check projectiles
        player1.update_projectiles(dt, player2, current_time, walls)
        player2.update_projectiles(dt, player1, current_time, walls)
        
        # Check for object collection
        for obj in game_objects[:]:  # Use [:] to iterate over a copy
            # Check if player 1 collects the object
            if obj.is_collected(player1.rect):
                if isinstance(obj, SpeedDebuffObject):
                    obj.apply_effect(player1, player2, current_time)
                else:
                    obj.apply_effect(player1, current_time)
                game_objects.remove(obj)
            # Check if player 2 collects the object
            elif obj.is_collected(player2.rect):
                if isinstance(obj, SpeedDebuffObject):
                    obj.apply_effect(player2, player1, current_time)
                else:
                    obj.apply_effect(player2, current_time)
                game_objects.remove(obj)
    
    # Clear the screen with background color
    screen.fill(COLORS['background'])
    
    # Draw instructions screen if showing
    if show_instructions:
        renderer.draw_instructions_screen()
    else:
        # Draw center line
        center_x = GAME_CONFIG['tiles_width'] / 2
        pygame.draw.line(screen, COLORS['center_line'], 
                        (center_x * GAME_CONFIG['tile_size_in_pixels'], 0),
                        (center_x * GAME_CONFIG['tile_size_in_pixels'], 
                         GAME_CONFIG['tiles_height'] * GAME_CONFIG['tile_size_in_pixels']))
        
        # Draw walls
        for wall in walls:
            wall.draw(screen)
        
        # Draw game objects
        for obj in game_objects:
            obj.draw(screen)
        
        # Draw players with shield effect if active
        for player in [player1, player2]:
            if player.shield_active:
                # Draw shield effect (slightly larger rectangle)
                shield_rect = pygame.Rect(
                    player.rect.x - 2,
                    player.rect.y - 2,
                    player.rect.width + 4,
                    player.rect.height + 4
                )
                pygame.draw.rect(screen, player.color, shield_rect, 2)  # 2 is line width
            pygame.draw.rect(screen, player.color, player.rect)
        
        # Draw projectiles
        for projectile in player1.projectiles:
            projectile.draw(screen)
        for projectile in player2.projectiles:
            projectile.draw(screen)
        
        # Draw stats panel
        renderer.draw_stats_panel(player1, player2)
        
        # Draw appropriate victory screen
        if game_over:
            if game_state.match_over:
                renderer.draw_match_victory_screen(winner, player1, player2, game_state)
            else:
                renderer.draw_round_victory_screen(winner, player1, player2, game_state)
        
        # Draw countdown if active
        if game_state.countdown_active:
            renderer.draw_countdown(game_state)
    
    # Update the display
    pygame.display.flip()

# Clean up and exit
pygame.quit()
sys.exit() 