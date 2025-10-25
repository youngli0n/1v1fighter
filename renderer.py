import pygame
import time
from game_config import GAME_CONFIG, COLORS

# Helper function to render multi-line text
def render_multiline_text(font, text, color, max_width):
    """
    Render text with automatic line wrapping
    
    Args:
        font: pygame font object
        text: string to render
        color: text color
        max_width: maximum width before wrapping
        
    Returns:
        list of surface objects, one per line
    """
    words = text.split(' ')
    lines = []
    current_line = []
    
    for word in words:
        test_line = ' '.join(current_line + [word])
        test_surface = font.render(test_line, True, color)
        
        if test_surface.get_width() <= max_width:
            current_line.append(word)
        else:
            if current_line:
                lines.append(font.render(' '.join(current_line), True, color))
            current_line = [word]
    
    if current_line:
        lines.append(font.render(' '.join(current_line), True, color))
    
    return lines


class Renderer:
    """Handles all rendering and drawing operations for the game"""
    
    def __init__(self, screen, font):
        """
        Initialize the renderer
        
        Args:
            screen: The pygame surface to draw on
            font: The font to use for text rendering
        """
        self.screen = screen
        self.font = font
    
    def draw_stats_panel(self, player1, player2):
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
        pygame.draw.rect(self.screen, COLORS['stats_panel'], 
                        (0, panel_y, panel_width, panel_height))
        
        # Draw vertical separator line
        pygame.draw.line(self.screen, COLORS['text'],
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
            speed_surface = self.font.render(speed_text, True, COLORS['text'])
            text_x = section_x + section_padding
            self.screen.blit(speed_surface, (text_x, speed_y))
            
            # Draw shield status
            shield_text = f"Shield: {'ACTIVE' if player.shield_active else 'inactive'}"
            shield_color = COLORS['player1'] if is_player1 else COLORS['player2']
            shield_surface = self.font.render(shield_text, True, shield_color if player.shield_active else COLORS['text'])
            self.screen.blit(shield_surface, (text_x, shield_y))
            
            # Draw active boosts
            active_boosts = len(player.shield_boosts)
            if active_boosts > 0:
                longest_boost = max(end_time for end_time, _ in player.shield_boosts)
                time_remaining = max(0, longest_boost - current_time)
                boosts_text = f"Boosts: {active_boosts} ({time_remaining:.1f}s)"
            else:
                boosts_text = "Boosts: 0"
            boosts_surface = self.font.render(boosts_text, True, COLORS['text'])
            self.screen.blit(boosts_surface, (text_x, boosts_y))
            
            # Draw progress bar
            progress = min(100, player.get_progress())  # Cap at 100%
            
            # Draw progress bar background
            bar_x = text_x
            pygame.draw.rect(self.screen, COLORS['progress_bar_bg'], 
                            (bar_x, bar_y, bar_width, bar_height))
            
            # Draw progress bar fill
            fill_width = int(bar_width * (progress / 100))
            pygame.draw.rect(self.screen, COLORS['progress_bar_fill'], 
                            (bar_x, bar_y, fill_width, bar_height))
            
            # Draw progress percentage text
            progress_text = f"{int(progress)}%"
            progress_surface = self.font.render(progress_text, True, COLORS['text'])
            text_width = progress_surface.get_width()
            # Position text to the right of the bar with padding
            progress_x = bar_x + bar_width + section_padding
            progress_y = bar_y + (bar_height - progress_surface.get_height()) // 2  # Center vertically
            self.screen.blit(progress_surface, (progress_x, progress_y))
        
        # Draw stats for both players
        draw_player_stats(player1, 0, True)  # Player 1 (left section)
        draw_player_stats(player2, section_width, False)  # Player 2 (right section)
    
    def draw_victory_screen(self, winner, player1, player2):
        """Draw the victory screen showing the winner and final stats"""
        # Create a solid white overlay
        overlay = pygame.Surface((GAME_CONFIG['window_width_in_pixels'], 
                                GAME_CONFIG['window_height_in_pixels']))
        overlay.fill((255, 255, 255))  # White background
        self.screen.blit(overlay, (0, 0))
        
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
        self.screen.blit(victory_surface, victory_rect)
        
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
            self.screen.blit(stat_surface, stat_rect)
        
        # Draw restart prompt at the bottom with proper spacing
        restart_font = pygame.font.Font(None, restart_size)
        restart_text = "Press R to Restart"
        restart_surface = restart_font.render(restart_text, True, COLORS['text'])
        restart_rect = restart_surface.get_rect(center=(GAME_CONFIG['window_width_in_pixels'] // 2, 
                                                      GAME_CONFIG['window_height_in_pixels'] * 4 // 5))
        self.screen.blit(restart_surface, restart_rect)
    
    def draw_round_victory_screen(self, winner, player1, player2, game_state):
        """Draw the round victory screen showing round stats"""
        # Create a solid white overlay
        overlay = pygame.Surface((GAME_CONFIG['window_width_in_pixels'], 
                                GAME_CONFIG['window_height_in_pixels']))
        overlay.fill((255, 255, 255))  # White background
        self.screen.blit(overlay, (0, 0))
        
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
        self.screen.blit(victory_surface, victory_rect)
        
        # Draw round stats with adjusted spacing
        stats_font = pygame.font.Font(None, stats_size)
        stats_y = victory_rect.bottom + window_height // 20  # Reduced spacing
        
        # Draw match score
        score_text = f"Match Score: {game_state.get_match_score()}"
        score_surface = stats_font.render(score_text, True, COLORS['text'])
        score_rect = score_surface.get_rect(center=(GAME_CONFIG['window_width_in_pixels'] // 2, 
                                                  stats_y))
        self.screen.blit(score_surface, score_rect)
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
                self.screen.blit(stat_surface, stat_rect)
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
        self.screen.blit(prompt_surface, prompt_rect)
    
    def draw_match_victory_screen(self, winner, player1, player2, game_state):
        """Draw the match victory screen showing match summary"""
        # Create a solid white overlay
        overlay = pygame.Surface((GAME_CONFIG['window_width_in_pixels'], 
                                GAME_CONFIG['window_height_in_pixels']))
        overlay.fill((255, 255, 255))  # White background
        self.screen.blit(overlay, (0, 0))
        
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
        self.screen.blit(victory_surface, victory_rect)
        
        # Draw final score
        score_font = pygame.font.Font(None, stats_size)
        score_text = f"({game_state.round_wins[0]} - {game_state.round_wins[1]})"
        score_surface = score_font.render(score_text, True, COLORS['text'])
        score_rect = score_surface.get_rect(center=(GAME_CONFIG['window_width_in_pixels'] // 2, 
                                                  victory_rect.bottom + 40))
        self.screen.blit(score_surface, score_rect)
        
        # Draw round history
        history_y = score_rect.bottom + 60
        history_font = pygame.font.Font(None, stats_size)
        
        history_title = "Match Summary:"
        title_surface = history_font.render(history_title, True, COLORS['text'])
        title_rect = title_surface.get_rect(center=(GAME_CONFIG['window_width_in_pixels'] // 2, 
                                                  history_y))
        self.screen.blit(title_surface, title_rect)
        
        for i, winner_num in enumerate(game_state.round_history):
            round_text = f"Round {i + 1}: P{winner_num} Win"
            round_surface = history_font.render(round_text, True, COLORS['text'])
            round_rect = round_surface.get_rect(center=(GAME_CONFIG['window_width_in_pixels'] // 2, 
                                                      history_y + 40 + i * 35))
            self.screen.blit(round_surface, round_rect)
        
        # Draw restart prompt
        prompt_font = pygame.font.Font(None, prompt_size)
        prompt_text = "Press R to start new match"
        prompt_surface = prompt_font.render(prompt_text, True, COLORS['text'])
        prompt_rect = prompt_surface.get_rect(center=(GAME_CONFIG['window_width_in_pixels'] // 2, 
                                                    GAME_CONFIG['window_height_in_pixels'] * 4 // 5))
        self.screen.blit(prompt_surface, prompt_rect)
    
    def draw_countdown(self, game_state):
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
        self.screen.blit(round_surface, round_rect)
        
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
            pygame.draw.rect(self.screen, (255, 0, 0), bg_rect, border_radius=10)
            
            # Draw the text in white
            match_point_surface = match_point_font.render("MATCH POINT", True, (255, 255, 255))
            self.screen.blit(match_point_surface, match_point_rect)
        
        # Draw black background rectangle for countdown
        countdown_bg = pygame.Rect(rect_x, rect_y, rect_width, rect_height)
        pygame.draw.rect(self.screen, (0, 0, 0), countdown_bg)
        
        # Draw countdown number or "GO!" in white
        countdown_font = pygame.font.Font(None, window_height // 4)  # Much larger font for countdown
        if game_state.countdown_ticks > 0:
            text = str(game_state.countdown_ticks)
        else:
            text = "GO!"
        
        text_surface = countdown_font.render(text, True, (255, 255, 255))  # White text
        text_rect = text_surface.get_rect(center=(window_width // 2, window_height // 2))
        self.screen.blit(text_surface, text_rect)

    def draw_instructions_screen(self):
        """
        Draw the game instructions screen with responsive sizing
        
        This method draws a formatted instructions screen explaining:
        - Game objective
        - How to use walls
        - Shooting mechanics
        - Hit effects and blocking
        - Game structure (rounds, win conditions)
        
        The screen dynamically adjusts font sizes to ensure all content fits on screen.
        """
        screen = self.screen
        window_width = GAME_CONFIG['window_width_in_pixels']
        window_height = GAME_CONFIG['window_height_in_pixels']
        
        # Create semi-transparent overlay
        overlay = pygame.Surface((window_width, window_height))
        overlay.set_alpha(240)
        overlay.fill((255, 255, 255))
        screen.blit(overlay, (0, 0))
        
        # Define all instruction content
        instructions = [
            ("How to Play", "title"),
            ("1. Race to the finish line first!", "heading"),
            "Reach 100% at center to win the round.",
            ("2. Use walls for cover", "heading"),
            "Hide behind gray walls. They block bullets.",
            ("3. Combat controls", "heading"),
            ("Player 1 (Red):", "p1"),
            "WASD = Move, V = Shoot, B = Shield",
            ("Player 2 (Blue):", "p2"),
            "Arrows = Move, , = Shoot, . = Shield",
            ("4. Getting hit slows you", "heading"),
            f"Speed drops to {GAME_CONFIG['slow_factor']}x ({int((1-GAME_CONFIG['slow_factor'])*100)}% slower) for {GAME_CONFIG['slow_duration']:.0f}s. Attacker speeds up!",
            ("5. Blocking gives speed boost", "heading"),
            f"Each block: +{int(GAME_CONFIG['shield_boost_amount']*100)}% for {GAME_CONFIG['shield_boost_duration']:.0f}s (max {int(GAME_CONFIG['shield_boost_max']*100)}%).",
            ("6. Win {0} rounds to win match".format(GAME_CONFIG['rounds_to_win']), "heading"),
            "Best of {0} rounds.".format(GAME_CONFIG['rounds_to_win'] * 2 - 1),
            ("", "spacer"),
            ("Press SPACE to start", "prompt"),
        ]
        
        # Calculate optimal font size that fits all content
        max_font_size = int(window_height / 15)
        min_font_size = int(window_height / 45)
        
        # Function to calculate total height for a given font size
        def calc_height(base_size):
            title_font = pygame.font.Font(None, int(base_size * 1.8))
            heading_font = pygame.font.Font(None, int(base_size * 1.3))
            body_font = pygame.font.Font(None, base_size)
            prompt_font = pygame.font.Font(None, int(base_size * 1.2))
            
            height = base_size // 3  # Top margin
            text_width = window_width - (window_width // 10) * 2
            
            for text, style in instructions:
                if not text:
                    height += base_size // 3
                    continue
                    
                if style == "title":
                    lines = render_multiline_text(title_font, text, COLORS['text'], text_width)
                    height += len(lines) * title_font.get_height() * 1.3
                elif style == "heading":
                    height += heading_font.get_height() * 0.5  # Extra space before heading
                    lines = render_multiline_text(heading_font, text, COLORS['text'], text_width)
                    height += len(lines) * heading_font.get_height() * 1.2
                elif style == "prompt":
                    lines = render_multiline_text(prompt_font, text, COLORS['text'], text_width)
                    height += len(lines) * prompt_font.get_height() * 1.3
                else:
                    lines = render_multiline_text(body_font, text, COLORS['text'], text_width)
                    height += len(lines) * body_font.get_height() * 1.15
            
            height += base_size // 3  # Bottom margin
            return height
        
        # Binary search for optimal font size
        optimal_size = min_font_size
        for size in range(max_font_size, min_font_size - 1, -2):
            if calc_height(size) <= window_height * 0.95:
                optimal_size = size
                break
        
        # Define fonts with optimal size
        title_font = pygame.font.Font(None, int(optimal_size * 1.8))
        heading_font = pygame.font.Font(None, int(optimal_size * 1.3))
        body_font = pygame.font.Font(None, optimal_size)
        prompt_font = pygame.font.Font(None, int(optimal_size * 1.2))
        
        # Calculate starting Y to center content
        total_height = calc_height(optimal_size)
        y_pos = max((window_height - total_height) / 2, optimal_size // 3)
        
        # Render all instructions with optimal font size
        text_width = window_width - (window_width // 10) * 2
        x_pos = window_width // 10
        
        for text, style in instructions:
            # Skip empty spacer elements
            if not text and style == "spacer":
                y_pos += body_font.get_height() // 2
                continue
            
            # Determine font and color based on style
            if style == "title":
                font = title_font
                color = COLORS['text']
                lines = render_multiline_text(font, text, color, text_width)
                for line in lines:
                    line_x = (window_width - line.get_width()) // 2
                    screen.blit(line, (line_x, y_pos))
                    y_pos += int(font.get_height() * 1.3)
                y_pos += font.get_height() // 2
                
            elif style == "heading":
                font = heading_font
                color = COLORS['text']
                y_pos += font.get_height() // 2
                lines = render_multiline_text(font, text, color, text_width)
                for line in lines:
                    screen.blit(line, (x_pos, y_pos))
                    y_pos += int(font.get_height() * 1.2)
                    
            elif style == "p1":
                font = body_font
                color = COLORS['player1']
                surface = font.render(text, True, color)
                screen.blit(surface, (x_pos, y_pos))
                y_pos += int(font.get_height() * 1.15)
                
            elif style == "p2":
                font = body_font
                color = COLORS['player2']
                surface = font.render(text, True, color)
                screen.blit(surface, (x_pos, y_pos))
                y_pos += int(font.get_height() * 1.15)
                
            elif style == "prompt":
                font = prompt_font
                color = COLORS['text']
                lines = render_multiline_text(font, text, color, text_width)
                for line in lines:
                    line_x = (window_width - line.get_width()) // 2
                    screen.blit(line, (line_x, y_pos))
                    y_pos += int(font.get_height() * 1.3)
                    
            else:  # body text
                font = body_font
                color = COLORS['text']
                lines = render_multiline_text(font, text, color, text_width)
                for line in lines:
                    screen.blit(line, (x_pos, y_pos))
                    y_pos += int(font.get_height() * 1.15)
