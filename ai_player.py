import math
from game_config import GAME_CONFIG

class AIPlayer:
    """AI-controlled player that uses simple heuristics to challenge Player 1"""
    
    def __init__(self, player2, player1):
        self.player2 = player2
        self.player1 = player1
        self.last_shot_time = 0
        self.shot_cooldown = 1.0 / GAME_CONFIG['fire_rate']  # Minimum time between shots
        
    def update(self, dt, current_time):
        """Update AI behavior based on game state"""
        # Calculate distances and directions
        dx = self.player1.x - self.player2.x
        dy = self.player1.y - self.player2.y
        distance = math.sqrt(dx*dx + dy*dy)
        
        # Movement logic
        if not self.player2.shield_active:
            # Move towards center line while maintaining distance from player1
            target_x = GAME_CONFIG['tiles_width'] / 2
            target_y = self.player1.y  # Mirror player1's vertical position
            
            # Calculate movement direction
            move_x = 0
            move_y = 0
            
            # Horizontal movement (towards center)
            if self.player2.x > target_x:
                move_x = -1
            elif self.player2.x < target_x:
                move_x = 1
                
            # Vertical movement (mirror player1)
            if self.player2.y > target_y:
                move_y = -1
            elif self.player2.y < target_y:
                move_y = 1
                
            # Apply movement
            self.player2.move(move_x * GAME_CONFIG['player_speed'], 
                            move_y * GAME_CONFIG['player_speed'], 
                            dt, current_time, self.player1)
        
        # Shooting logic
        if (not self.player2.shield_active and 
            distance < GAME_CONFIG['tiles_width'] / 2 and 
            current_time - self.last_shot_time > self.shot_cooldown):
            self.player2.shoot(current_time)
            self.last_shot_time = current_time
            
        # Shield logic
        # Activate shield if player1 is shooting and we're close
        if (len(self.player1.projectiles) > 0 and 
            distance < GAME_CONFIG['tiles_width'] / 3):
            self.player2.shield_active = True
        else:
            self.player2.shield_active = False 