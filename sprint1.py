import pygame
import sys
import time  # For tracking effect durations

# Initialize Pygame - this is required before using any Pygame functions
pygame.init()

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
    'projectile_speed': 50,      # tiles per second
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
    
    # Round configuration
    'rounds_to_win': 3,          # First to X rounds wins the match
    'countdown_seconds': 3,       # Countdown starts from this number
    'countdown_duration': 1.5,    # Total duration of countdown sequence in seconds
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

# Create the game window
screen = pygame.display.set_mode((GAME_CONFIG['window_width_in_pixels'], GAME_CONFIG['window_height_in_pixels']))
pygame.display.set_caption("Learning Python Game - Sprint 3")

# Create a clock object to control game speed
clock = pygame.time.Clock()

# Initialize font for text rendering
font = pygame.font.Font(None, 32)  # Increased font size for better visibility

class Projectile:
    def __init__(self, x, y, direction):
        self.x = float(x)
        self.y = float(y)
        self.direction = direction  # 1 for P1, -1 for P2
        self.rect = pygame.Rect(
            int(self.x * GAME_CONFIG['tile_size_in_pixels']),
            int(self.y * GAME_CONFIG['tile_size_in_pixels']),
            GAME_CONFIG['projectile_size'] * GAME_CONFIG['tile_size_in_pixels'],
            GAME_CONFIG['projectile_size'] * GAME_CONFIG['tile_size_in_pixels']
        )
    
    def update(self, dt):
        """Move the projectile based on its speed and direction"""
        self.x += self.direction * GAME_CONFIG['projectile_speed'] * dt
        self.rect.x = int(self.x * GAME_CONFIG['tile_size_in_pixels'])
    
    def draw(self, screen):
        """Draw the projectile on the screen"""
        pygame.draw.rect(screen, GAME_CONFIG['projectile_color'], self.rect)

class Player:
    def __init__(self, x, y, color):
        # Store position as float values for smooth movement
        self.x = float(x)
        self.y = float(y)
        self.color = color  # Store player color
        self.slow_end_time = 0  # When current slow effect ends
        self.speedup_end_time = 0  # When current speedup effect ends
        self.block_speedups = 0  # Count of active block speedups (max 10 for 50%)
        self.last_shot_time = 0  # Time of last shot
        self.projectiles = []  # List of active projectiles
        self.shield_active = False  # Whether shield is currently active
        self.shield_boosts = []  # List of (end_time, boost_amount) tuples
        
        # Create rect for drawing, converting float positions to integers
        self.rect = pygame.Rect(
            int(self.x * GAME_CONFIG['tile_size_in_pixels']),
            int(self.y * GAME_CONFIG['tile_size_in_pixels']),
            GAME_CONFIG['tile_size_in_pixels'],
            GAME_CONFIG['tile_size_in_pixels']
        )
    
    def is_slowed(self, current_time):
        """Check if player is currently slowed"""
        return current_time < self.slow_end_time
    
    def is_speedup(self, current_time):
        """Check if player has active speedup effect"""
        return current_time < self.speedup_end_time
    
    def get_total_speed_multiplier(self, current_time):
        """Calculate total speed multiplier including all effects and regeneration"""
        # Base speed is always 100%
        base_speed = 1.0
        
        # Calculate shield boost (temporary, from blocking)
        shield_boost = 0.0
        # Remove expired boosts and sum active ones
        self.shield_boosts = [(end_time, boost) for end_time, boost in self.shield_boosts 
                            if current_time < end_time]
        shield_boost = sum(boost for _, boost in self.shield_boosts)
        shield_boost = min(shield_boost, GAME_CONFIG['shield_boost_max'])
        
        # Calculate temporary effect (slow or speedup)
        temp_effect = 0.0
        if self.is_slowed(current_time):
            # Calculate regeneration from slow
            time_remaining = self.slow_end_time - current_time
            slow_factor = GAME_CONFIG['slow_factor']  # e.g., 0.5
            # Linearly regenerate from slow_factor to 1.0
            temp_effect = slow_factor + (1.0 - slow_factor) * (1.0 - time_remaining / GAME_CONFIG['slow_duration'])
        elif self.is_speedup(current_time):
            # Calculate decay from speedup
            time_remaining = self.speedup_end_time - current_time
            speedup_factor = GAME_CONFIG['speedup_factor']  # e.g., 1.5
            # Linearly decay from speedup_factor to 1.0
            temp_effect = 1.0 + (speedup_factor - 1.0) * (time_remaining / GAME_CONFIG['speedup_duration'])
        else:
            temp_effect = 1.0  # No temporary effect
        
        # Combine effects, ensuring we never exceed 100% from regeneration
        total_speed = base_speed + shield_boost
        if temp_effect < 1.0:  # If we're slowed
            total_speed *= temp_effect  # Apply slow multiplicatively
        else:  # If we're sped up
            total_speed = min(total_speed + (temp_effect - 1.0), 1.5)  # Add speedup, cap at 150%
        
        return total_speed
    
    def get_fire_rate_multiplier(self, current_time):
        """Calculate fire rate multiplier based on current speed effects"""
        return self.get_total_speed_multiplier(current_time)
    
    def can_shoot(self, current_time):
        """Check if player can shoot based on fire rate and current speed effects"""
        if self.shield_active:
            return False
        fire_rate_multiplier = self.get_fire_rate_multiplier(current_time)
        return current_time - self.last_shot_time >= 1.0 / (GAME_CONFIG['fire_rate'] * fire_rate_multiplier)
    
    def apply_effect(self, effect_type, duration, current_time):
        """Apply an effect to the player"""
        if effect_type == 'slow':
            if not self.is_slowed(current_time):
                self.slow_end_time = current_time + duration
        elif effect_type == 'speedup':
            # Only apply if not already speedup
            if not self.is_speedup(current_time):
                self.speedup_end_time = current_time + duration
        elif effect_type == 'block':
            # Add a new shield boost
            self.shield_boosts.append((current_time + GAME_CONFIG['shield_boost_duration'], 
                                     GAME_CONFIG['shield_boost_amount']))
    
    def shoot(self, current_time):
        """Create a new projectile if allowed by fire rate"""
        if self.can_shoot(current_time):
            # Calculate projectile starting position
            projectile_x = self.x + (1 if self.color == COLORS['player1'] else -1)
            projectile_y = self.y
            
            # Create and add projectile
            direction = 1 if self.color == COLORS['player1'] else -1
            self.projectiles.append(Projectile(projectile_x, projectile_y, direction))
            self.last_shot_time = current_time
    
    # the parameters mean:
    # dx: horizontal movement (positive = right, negative = left)
    # dy: vertical movement (positive = down, negative = up)
    # dt: time delta (in seconds) between frames, calculated by clock.tick(GAME_CONFIG['fps']) / 1000.0
    def move(self, dx, dy, dt, current_time, other_player):
        # If shield is active, only allow vertical movement
        if self.shield_active:
            dx = 0
        
        # Only update position if there's actual movement
        if dx != 0 or dy != 0:
            # Calculate new position in tiles
            speed_multiplier = self.get_total_speed_multiplier(current_time)
            new_x = self.x + dx * dt * speed_multiplier
            new_y = self.y + dy * dt * speed_multiplier
            
            # Check if new position is within screen bounds (in tiles)
            if (0 <= new_x <= GAME_CONFIG['tiles_width'] - 1 and
                0 <= new_y <= GAME_CONFIG['tiles_height'] - 1):
                
                # Check for collision with other player
                # We use a small buffer (0.1 tiles) to prevent players from getting too close
                if (abs(new_x - other_player.x) >= 1.1 or 
                    abs(new_y - other_player.y) >= 1.1):
                    self.x = new_x
                    self.y = new_y
                    # Update rect for drawing, converting float positions to integers
                    self.rect.x = int(self.x * GAME_CONFIG['tile_size_in_pixels'])
                    self.rect.y = int(self.y * GAME_CONFIG['tile_size_in_pixels'])
    
    def update_projectiles(self, dt, other_player, current_time):
        """Update all projectiles and check for collisions"""
        # Update existing projectiles
        for projectile in self.projectiles[:]:
            projectile.update(dt)
            
            # Check if projectile is out of bounds
            if (projectile.x < 0 or 
                projectile.x > GAME_CONFIG['tiles_width'] or
                projectile.y < 0 or 
                projectile.y > GAME_CONFIG['tiles_height']):
                self.projectiles.remove(projectile)
                continue
            
            # Check for collision with other player
            if projectile.rect.colliderect(other_player.rect):
                # If other player's shield is active, block the projectile
                if other_player.shield_active:
                    other_player.apply_effect('block', GAME_CONFIG['shield_boost_duration'], current_time)
                else:
                    # Apply effects
                    other_player.apply_effect('slow', GAME_CONFIG['slow_duration'], current_time)
                    self.apply_effect('speedup', GAME_CONFIG['speedup_duration'], current_time)
                self.projectiles.remove(projectile)
    
    #this method calculates the progress towards the center of the screen as a percentage (0-100)
    #progress is based on when the player's first pixel reaches the center line
    def get_progress(self):
        """Calculate progress towards center as a percentage (0-100)
        Progress is based on when the player's first pixel reaches the center line"""
        center_x = GAME_CONFIG['tiles_width'] / 2
        if self.x < center_x:  # Player 1
            # Calculate distance to center, considering player's size
            distance_to_center = center_x - (self.x + 1)  # +1 because we want first pixel to reach
            total_distance = center_x
            return ((total_distance - distance_to_center) / total_distance) * 100
        else:  # Player 2
            # Calculate distance to center, considering player's size
            distance_to_center = (self.x) - center_x  # No +1 because we want first pixel to reach
            total_distance = center_x
            return ((total_distance - distance_to_center) / total_distance) * 100

class GameState:
    """Tracks the overall game state including rounds and match status"""
    def __init__(self):
        self.reset_match()
    
    def reset_match(self):
        """Reset all match-level state"""
        self.round_wins = [0, 0]  # [p1_wins, p2_wins]
        self.current_round = 1
        self.round_history = []  # List of round winners (1 or 2)
        self.match_over = False
        self.round_over = False
        self.countdown_active = True
        self.countdown_time = GAME_CONFIG['countdown_seconds']
        self.last_countdown_update = time.time()
    
    def reset_round(self):
        """Reset for a new round"""
        self.round_over = False
        self.countdown_active = True
        self.countdown_time = GAME_CONFIG['countdown_seconds']
        self.last_countdown_update = time.time()
    
    def update_countdown(self, current_time):
        """Update countdown timer, returns True if countdown is complete"""
        if self.countdown_active:
            # 4 steps total (3,2,1,GO), so divide total duration by 4
            if current_time - self.last_countdown_update >= GAME_CONFIG['countdown_duration'] / 4:
                self.countdown_time -= 1
                self.last_countdown_update = current_time
                if self.countdown_time < 0:
                    self.countdown_active = False
                    return True
        return False
    
    def record_round_win(self, winner_num):
        """Record a round win and check for match victory"""
        self.round_wins[winner_num - 1] += 1
        self.round_history.append(winner_num)
        self.round_over = True
        
        # Check for match victory
        if self.round_wins[winner_num - 1] >= GAME_CONFIG['rounds_to_win']:
            self.match_over = True
        
        # Increment round number AFTER displaying the victory screen
        self.current_round += 1
    
    def get_match_score(self):
        """Return current match score as string"""
        return f"P1: {self.round_wins[0]}  P2: {self.round_wins[1]}"

def draw_stats_panel(player1, player2):
    """Draw the stats panel below the game board"""
    # Calculate stats panel position and dimensions
    panel_y = GAME_CONFIG['tiles_height'] * GAME_CONFIG['tile_size_in_pixels']
    panel_height = GAME_CONFIG['stats_panel_height_in_pixels']
    panel_width = GAME_CONFIG['window_width_in_pixels']
    
    # Calculate section dimensions (each player gets half the width)
    section_width = panel_width // 2
    section_padding = max(10, panel_width // 80)  # Responsive padding, minimum 10px
    
    # Calculate element dimensions
    text_height = min(20, panel_height // 5)  # Responsive text height
    bar_height = min(15, panel_height // 6)   # Responsive bar height
    bar_width = min(section_width - 2 * section_padding, 200)  # Cap bar width
    
    # Draw stats panel background
    pygame.draw.rect(screen, COLORS['stats_panel'], 
                    (0, panel_y, panel_width, panel_height))
    
    # Draw vertical separator line
    pygame.draw.line(screen, COLORS['text'],
                    (section_width, panel_y + section_padding),
                    (section_width, panel_y + panel_height - section_padding))
    
    # Helper function to draw player stats
    def draw_player_stats(player, section_x, is_player1):
        # Calculate vertical positions with even spacing
        total_height = 4 * text_height  # Total height needed for all elements
        start_y = panel_y + (panel_height - total_height) // 2  # Center vertically
        
        speed_y = start_y
        shield_y = speed_y + text_height + 5
        boosts_y = shield_y + text_height + 5
        bar_y = boosts_y + text_height + 5
        
        # Get current time for calculations
        current_time = time.time()
        
        # Draw speed text with total speed multiplier
        total_speed = player.get_total_speed_multiplier(current_time)
        speed_text = f"P{1 if is_player1 else 2} Speed: {int(total_speed * 100)}%"
        speed_surface = font.render(speed_text, True, COLORS['text'])
        text_x = section_x + section_padding
        screen.blit(speed_surface, (text_x, speed_y))
        
        # Draw shield status
        shield_text = f"Shield: {'ACTIVE' if player.shield_active else 'inactive'}"
        shield_color = COLORS['player1'] if is_player1 else COLORS['player2']
        shield_surface = font.render(shield_text, True, shield_color if player.shield_active else COLORS['text'])
        screen.blit(shield_surface, (text_x, shield_y))
        
        # Draw active boosts
        active_boosts = len(player.shield_boosts)
        if active_boosts > 0:
            longest_boost = max(end_time for end_time, _ in player.shield_boosts)
            time_remaining = max(0, longest_boost - current_time)
            boosts_text = f"Boosts: {active_boosts} ({time_remaining:.1f}s)"
        else:
            boosts_text = "Boosts: 0"
        boosts_surface = font.render(boosts_text, True, COLORS['text'])
        screen.blit(boosts_surface, (text_x, boosts_y))
        
        # Draw progress bar
        progress = min(100, player.get_progress())  # Cap at 100%
        
        # Draw progress bar background
        bar_x = text_x
        pygame.draw.rect(screen, COLORS['progress_bar_bg'], 
                        (bar_x, bar_y, bar_width, bar_height))
        
        # Draw progress bar fill
        fill_width = int(bar_width * (progress / 100))
        pygame.draw.rect(screen, COLORS['progress_bar_fill'], 
                        (bar_x, bar_y, fill_width, bar_height))
        
        # Draw progress percentage text
        progress_text = f"{int(progress)}%"
        progress_surface = font.render(progress_text, True, COLORS['text'])
        text_width = progress_surface.get_width()
        # Position text to the right of the bar with padding
        progress_x = bar_x + bar_width + section_padding
        progress_y = bar_y + (bar_height - progress_surface.get_height()) // 2  # Center vertically
        screen.blit(progress_surface, (progress_x, progress_y))
    
    # Draw stats for both players
    draw_player_stats(player1, 0, True)  # Player 1 (left section)
    draw_player_stats(player2, section_width, False)  # Player 2 (right section)

def draw_victory_screen(winner, player1, player2):
    """Draw the victory screen showing the winner and final stats"""
    # Create a solid white overlay
    overlay = pygame.Surface((GAME_CONFIG['window_width_in_pixels'], 
                            GAME_CONFIG['window_height_in_pixels']))
    overlay.fill((255, 255, 255))  # White background
    screen.blit(overlay, (0, 0))
    
    # Calculate responsive font sizes
    title_size = min(74, GAME_CONFIG['window_height_in_pixels'] // 10)
    stats_size = min(36, GAME_CONFIG['window_height_in_pixels'] // 20)
    restart_size = min(48, GAME_CONFIG['window_height_in_pixels'] // 15)
    
    # Draw victory message
    victory_font = pygame.font.Font(None, title_size)
    victory_text = f"Player {1 if winner == player1 else 2} Wins!"
    victory_surface = victory_font.render(victory_text, True, winner.color)
    victory_rect = victory_surface.get_rect(center=(GAME_CONFIG['window_width_in_pixels'] // 2, 
                                                  GAME_CONFIG['window_height_in_pixels'] // 4))
    screen.blit(victory_surface, victory_rect)
    
    # Draw final stats
    stats_font = pygame.font.Font(None, stats_size)
    stats_y = victory_rect.bottom + GAME_CONFIG['window_height_in_pixels'] // 10
    
    # Calculate current time once
    current_time = time.time()
    
    # Player stats with capped progress
    def get_player_stats(player, player_num):
        return [
            f"Player {player_num} Final Speed: {int(player.get_total_speed_multiplier(current_time) * 100)}%",
            f"Blocks: {len(player.shield_boosts)}",
            f"Progress: {min(100, int(player.get_progress()))}%"  # Cap at 100%
        ]
    
    # Get stats for both players
    p1_stats = get_player_stats(player1, 1)
    p2_stats = get_player_stats(player2, 2)
    
    # Calculate vertical spacing between stats
    stat_spacing = GAME_CONFIG['window_height_in_pixels'] // 25
    
    # Draw stats with proper spacing
    for i, stat in enumerate(p1_stats + p2_stats):
        stat_surface = stats_font.render(stat, True, COLORS['text'])
        stat_rect = stat_surface.get_rect(center=(GAME_CONFIG['window_width_in_pixels'] // 2, 
                                                stats_y + i * stat_spacing))
        screen.blit(stat_surface, stat_rect)
    
    # Draw restart prompt at the bottom with proper spacing
    restart_font = pygame.font.Font(None, restart_size)
    restart_text = "Press R to Restart"
    restart_surface = restart_font.render(restart_text, True, COLORS['text'])
    restart_rect = restart_surface.get_rect(center=(GAME_CONFIG['window_width_in_pixels'] // 2, 
                                                  GAME_CONFIG['window_height_in_pixels'] * 4 // 5))
    screen.blit(restart_surface, restart_rect)

def draw_round_victory_screen(winner, player1, player2):
    """Draw the round victory screen showing round stats"""
    # Create a solid white overlay
    overlay = pygame.Surface((GAME_CONFIG['window_width_in_pixels'], 
                            GAME_CONFIG['window_height_in_pixels']))
    overlay.fill((255, 255, 255))  # White background
    screen.blit(overlay, (0, 0))
    
    # Calculate responsive font sizes based on window height
    window_height = GAME_CONFIG['window_height_in_pixels']
    title_size = min(64, window_height // 12)  # Reduced from 74
    stats_size = min(32, window_height // 25)  # Reduced from 36
    prompt_size = min(42, window_height // 18)  # Reduced from 48
    
    # Draw round victory message (using current_round - 1 for the round that just finished)
    victory_font = pygame.font.Font(None, title_size)
    victory_text = f"Player {1 if winner == player1 else 2} Wins Round {game_state.current_round - 1}!"
    victory_surface = victory_font.render(victory_text, True, winner.color)
    victory_rect = victory_surface.get_rect(center=(GAME_CONFIG['window_width_in_pixels'] // 2, 
                                                  window_height // 6))  # Moved up from 1/4
    screen.blit(victory_surface, victory_rect)
    
    # Draw round stats with adjusted spacing
    stats_font = pygame.font.Font(None, stats_size)
    stats_y = victory_rect.bottom + window_height // 20  # Reduced spacing
    
    # Draw match score
    score_text = f"Match Score: {game_state.get_match_score()}"
    score_surface = stats_font.render(score_text, True, COLORS['text'])
    score_rect = score_surface.get_rect(center=(GAME_CONFIG['window_width_in_pixels'] // 2, 
                                              stats_y))
    screen.blit(score_surface, score_rect)
    stats_y += window_height // 15  # Adjusted spacing
    
    # Player stats with dynamic spacing
    def draw_player_stats(player, player_num, y_pos):
        stats = [
            f"Player {player_num}:",
            f"Final Speed: {int(player.get_total_speed_multiplier(time.time()) * 100)}%",
            f"Blocks: {len(player.shield_boosts)}",
            f"Progress: {min(100, int(player.get_progress()))}%"
        ]
        
        stat_spacing = window_height // 30  # Dynamic spacing based on window height
        
        for i, stat in enumerate(stats):
            stat_surface = stats_font.render(stat, True, COLORS['text'])
            stat_rect = stat_surface.get_rect(center=(GAME_CONFIG['window_width_in_pixels'] // 2, 
                                                    y_pos + i * stat_spacing))
            screen.blit(stat_surface, stat_rect)
        return y_pos + len(stats) * stat_spacing
    
    # Draw stats for both players with adjusted spacing
    stats_y = draw_player_stats(player1, 1, stats_y)
    stats_y += window_height // 40  # Reduced space between players
    stats_y = draw_player_stats(player2, 2, stats_y)
    
    # Draw continue prompt at the bottom with proper spacing
    prompt_font = pygame.font.Font(None, prompt_size)
    prompt_text = "Press SPACE to start next round"
    prompt_surface = prompt_font.render(prompt_text, True, COLORS['text'])
    prompt_rect = prompt_surface.get_rect(center=(GAME_CONFIG['window_width_in_pixels'] // 2, 
                                                window_height * 9 // 10))  # Moved closer to bottom
    screen.blit(prompt_surface, prompt_rect)

def draw_match_victory_screen(winner, player1, player2):
    """Draw the match victory screen showing match summary"""
    # Create a solid white overlay
    overlay = pygame.Surface((GAME_CONFIG['window_width_in_pixels'], 
                            GAME_CONFIG['window_height_in_pixels']))
    overlay.fill((255, 255, 255))  # White background
    screen.blit(overlay, (0, 0))
    
    # Calculate responsive font sizes
    title_size = min(74, GAME_CONFIG['window_height_in_pixels'] // 10)
    stats_size = min(36, GAME_CONFIG['window_height_in_pixels'] // 20)
    prompt_size = min(48, GAME_CONFIG['window_height_in_pixels'] // 15)
    
    # Draw match victory message
    victory_font = pygame.font.Font(None, title_size)
    victory_text = f"Player {1 if winner == player1 else 2} Wins The Match!"
    victory_surface = victory_font.render(victory_text, True, winner.color)
    victory_rect = victory_surface.get_rect(center=(GAME_CONFIG['window_width_in_pixels'] // 2, 
                                                  GAME_CONFIG['window_height_in_pixels'] // 4))
    screen.blit(victory_surface, victory_rect)
    
    # Draw final score
    score_font = pygame.font.Font(None, stats_size)
    score_text = f"({game_state.round_wins[0]} - {game_state.round_wins[1]})"
    score_surface = score_font.render(score_text, True, COLORS['text'])
    score_rect = score_surface.get_rect(center=(GAME_CONFIG['window_width_in_pixels'] // 2, 
                                              victory_rect.bottom + 40))
    screen.blit(score_surface, score_rect)
    
    # Draw round history
    history_y = score_rect.bottom + 60
    history_font = pygame.font.Font(None, stats_size)
    
    history_title = "Match Summary:"
    title_surface = history_font.render(history_title, True, COLORS['text'])
    title_rect = title_surface.get_rect(center=(GAME_CONFIG['window_width_in_pixels'] // 2, 
                                              history_y))
    screen.blit(title_surface, title_rect)
    
    for i, winner_num in enumerate(game_state.round_history):
        round_text = f"Round {i + 1}: P{winner_num} Win"
        round_surface = history_font.render(round_text, True, COLORS['text'])
        round_rect = round_surface.get_rect(center=(GAME_CONFIG['window_width_in_pixels'] // 2, 
                                                  history_y + 40 + i * 35))
        screen.blit(round_surface, round_rect)
    
    # Draw restart prompt
    prompt_font = pygame.font.Font(None, prompt_size)
    prompt_text = "Press R to start new match"
    prompt_surface = prompt_font.render(prompt_text, True, COLORS['text'])
    prompt_rect = prompt_surface.get_rect(center=(GAME_CONFIG['window_width_in_pixels'] // 2, 
                                                GAME_CONFIG['window_height_in_pixels'] * 4 // 5))
    screen.blit(prompt_surface, prompt_rect)

def draw_countdown():
    """Draw the countdown before round starts"""
    if not game_state.countdown_active:
        return
    
    window_width = GAME_CONFIG['window_width_in_pixels']
    window_height = GAME_CONFIG['window_height_in_pixels']
    
    # Calculate dimensions for the black background rectangle
    rect_width = window_width // 3
    rect_height = window_height // 4
    rect_x = (window_width - rect_width) // 2
    rect_y = (window_height - rect_height) // 2
    
    # Draw round number at the top
    round_font = pygame.font.Font(None, window_height // 8)  # Larger font for round number
    round_text = f"ROUND {game_state.current_round}"
    round_surface = round_font.render(round_text, True, (0, 0, 0))
    round_rect = round_surface.get_rect(center=(window_width // 2, rect_y - round_font.get_height()))
    screen.blit(round_surface, round_rect)
    
    # Check if this is a match point
    is_match_point = False
    if game_state.round_wins[0] == GAME_CONFIG['rounds_to_win'] - 1 or game_state.round_wins[1] == GAME_CONFIG['rounds_to_win'] - 1:
        is_match_point = True
    
    # Draw match point indicator if applicable
    if is_match_point:
        match_point_font = pygame.font.Font(None, window_height // 15)
        match_point_surface = match_point_font.render("MATCH POINT", True, (255, 0, 0))  # Red text
        match_point_rect = match_point_surface.get_rect(center=(window_width // 2, rect_y - round_font.get_height() * 2))
        
        # Draw a red rounded rectangle background
        padding = 20
        bg_rect = pygame.Rect(match_point_rect.left - padding,
                            match_point_rect.top - padding // 2,
                            match_point_rect.width + padding * 2,
                            match_point_rect.height + padding)
        pygame.draw.rect(screen, (255, 0, 0), bg_rect, border_radius=10)
        
        # Draw the text in white
        match_point_surface = match_point_font.render("MATCH POINT", True, (255, 255, 255))
        screen.blit(match_point_surface, match_point_rect)
    
    # Draw black background rectangle for countdown
    countdown_bg = pygame.Rect(rect_x, rect_y, rect_width, rect_height)
    pygame.draw.rect(screen, (0, 0, 0), countdown_bg)
    
    # Draw countdown number or "GO!" in white
    countdown_font = pygame.font.Font(None, window_height // 4)  # Much larger font for countdown
    if game_state.countdown_time > 0:
        text = str(game_state.countdown_time)
    else:
        text = "GO!"
    
    text_surface = countdown_font.render(text, True, (255, 255, 255))  # White text
    text_rect = text_surface.get_rect(center=(window_width // 2, window_height // 2))
    screen.blit(text_surface, text_rect)

# Create game state tracker
game_state = GameState()

def reset_players():
    """Create or reset players to their starting positions"""
    # Player 1 starts at left center
    player1 = Player(0, GAME_CONFIG['tiles_height'] // 2 - 0.5, COLORS['player1'])
    # Player 2 starts at right center
    player2 = Player(GAME_CONFIG['tiles_width'] - 1, GAME_CONFIG['tiles_height'] // 2 - 0.5, COLORS['player2'])
    return player1, player2

# Main game loop
running = True
game_over = False
winner = None
player1, player2 = reset_players()

while running:
    # Calculate delta time in seconds
    dt = clock.tick(GAME_CONFIG['fps']) / 1000.0  # Convert milliseconds to seconds
    current_time = time.time()
    
    # Handle events (keyboard input, window close, etc.)
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if game_state.match_over:
                if event.key == pygame.K_r:  # Start new match
                    game_state.reset_match()
                    game_over = False
                    winner = None
                    player1, player2 = reset_players()
            elif game_state.round_over:
                if event.key == pygame.K_SPACE:  # Start next round
                    game_state.reset_round()
                    game_over = False
                    winner = None
                    player1, player2 = reset_players()
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
        
        # Calculate movement for Player 2 (Arrow keys)
        dx2 = (keys[pygame.K_RIGHT] - keys[pygame.K_LEFT]) * GAME_CONFIG['player_speed']
        dy2 = (keys[pygame.K_DOWN] - keys[pygame.K_UP]) * GAME_CONFIG['player_speed']
        
        # Move players
        player1.move(dx1, dy1, dt, current_time, player2)
        player2.move(dx2, dy2, dt, current_time, player1)
        
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
        player1.update_projectiles(dt, player2, current_time)
        player2.update_projectiles(dt, player1, current_time)
    
    # Clear the screen with background color
    screen.fill(COLORS['background'])
    
    # Draw center line
    center_x = GAME_CONFIG['tiles_width'] / 2
    pygame.draw.line(screen, COLORS['center_line'], 
                    (center_x * GAME_CONFIG['tile_size_in_pixels'], 0),
                    (center_x * GAME_CONFIG['tile_size_in_pixels'], 
                     GAME_CONFIG['tiles_height'] * GAME_CONFIG['tile_size_in_pixels']))
    
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
    draw_stats_panel(player1, player2)
    
    # Draw appropriate victory screen
    if game_over:
        if game_state.match_over:
            draw_match_victory_screen(winner, player1, player2)
        else:
            draw_round_victory_screen(winner, player1, player2)
    
    # Draw countdown if active
    if game_state.countdown_active:
        draw_countdown()
    
    # Update the display
    pygame.display.flip()

# Clean up and exit
pygame.quit()
sys.exit() 