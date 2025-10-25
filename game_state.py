import time
from game_config import GAME_CONFIG


class GameState:
    """Tracks the overall game state including rounds and match status"""
    
    def __init__(self):
        """Initialize the game state"""
        self.reset_match()
    
    def reset_match(self):
        """Reset all match-level state"""
        self.round_wins = [0, 0]  # [p1_wins, p2_wins]
        self.current_round = 1
        self.round_history = []  # List of round winners (1 or 2)
        self.match_over = False
        self.round_over = False
        self.countdown_active = True
        self.countdown_ticks = GAME_CONFIG['countdown_ticks']
        self.last_countdown_update = time.time()
    
    def reset_round(self):
        """Reset for a new round"""
        self.round_over = False
        self.countdown_active = True
        self.countdown_ticks = GAME_CONFIG['countdown_ticks']
        self.last_countdown_update = time.time()
    
    def update_countdown(self, current_time):
        """
        Update countdown timer
        
        Args:
            current_time: Current game time
            
        Returns:
            True if countdown is complete, False otherwise
        """
        if self.countdown_active:
            # 4 steps total (3,2,1,GO), so divide total duration by 4
            if current_time - self.last_countdown_update >= GAME_CONFIG['countdown_duration'] / 4:
                self.countdown_ticks -= 1
                self.last_countdown_update = current_time
                if self.countdown_ticks < 0:
                    self.countdown_active = False
                    return True
        return False
    
    def record_round_win(self, winner_num):
        """
        Record a round win and check for match victory
        
        Args:
            winner_num: Player number who won (1 or 2)
        """
        self.round_wins[winner_num - 1] += 1
        self.round_history.append(winner_num)
        self.round_over = True
        
        # Check for match victory
        if self.round_wins[winner_num - 1] >= GAME_CONFIG['rounds_to_win']:
            self.match_over = True
        
        # Increment round number AFTER displaying the victory screen
        self.current_round += 1
    
    def get_match_score(self):
        """
        Return current match score as string
        
        Returns:
            Match score string (e.g., "P1: 2  P2: 1")
        """
        return f"P1: {self.round_wins[0]}  P2: {self.round_wins[1]}"
