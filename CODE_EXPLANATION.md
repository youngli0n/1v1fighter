# Code Explanation: 1v1 Fighter Game

## Overview
This is a 2-player racing game where players shoot at each other while racing to the center line. Getting hit slows you down, hitting someone speeds you up.

---

## Project Structure

The code has been refactored into separate files for easier understanding:

- **`projectile.py`** - Contains the Projectile class
- **`player.py`** - Contains the Player class
- **`game_state.py`** - Contains the GameState class
- **`game_config.py`** - Contains all game configuration settings
- **`ai_player.py`** - Contains the AI controller
- **`wall.py`** - Contains the Wall class for obstacles
- **`game_object.py`** - Contains the GameObject system with inheritance
- **`main.py`** - Main game file with game loop and instructions screen
- **`renderer.py`** - Handles all drawing and rendering operations

## Key Classes and What They Do

### 1. **Projectile Class** (projectile.py)
Represents a bullet shot by a player.

**Parameters:**
- `x, y`: Position on the game board (in tiles)
- `direction`: Which way it moves (1 = right, -1 = left)

**Methods:**
- `update(dt)`: Moves the projectile forward each frame
- `draw(screen)`: Draws it on screen

---

### 2. **Player Class** (player.py)
Represents one of the two players in the game.

#### Key Parameters:
- `x, y`: Player position (in tiles, stored as float for smooth movement)
- `color`: Red (Player 1) or Blue (Player 2)
- `slow_end_time`: When the "slow" effect expires
- `speedup_end_time`: When the "speedup" effect expires
- `shield_active`: Whether the shield is currently up
- `shield_boosts`: List of temporary speed boosts from blocking
- `projectiles`: List of bullets currently flying
- `last_shot_time`: When the player last fired

#### Important Methods:

**`move(dx, dy, dt, current_time, other_player)`**
- **Purpose**: Moves the player
- **Parameters**:
  - `dx`: Horizontal movement (-1 = left, 0 = none, 1 = right)
  - `dy`: Vertical movement (-1 = up, 0 = none, 1 = down)
  - `dt`: Time since last frame (in seconds)
  - `current_time`: Current game time
  - `other_player`: The other player (for collision detection)
- **What it does**: 
  1. Checks if shield is up (only vertical movement allowed)
  2. Calculates speed multiplier (affected by slow/speedup effects)
  3. Updates position based on movement and speed
  4. Prevents moving outside boundaries or into the other player

**`shoot(current_time)`**
- **Purpose**: Fires a projectile
- **What it does**: Creates a new projectile and adds it to the list, if allowed by fire rate

**`update_projectiles(dt, other_player, current_time)`**
- **Purpose**: Updates all flying bullets and checks for hits
- **What it does**:
  1. Moves all projectiles
  2. Removes projectiles that go off screen
  3. Checks if any hit the other player
  4. On hit: slows the target, speeds up the shooter (if not shielded)
  5. Removes the projectile after hit

**`get_total_speed_multiplier(current_time)`**
- **Purpose**: Calculates how fast the player should move
- **Returns**: A number (1.0 = normal speed, 0.5 = half speed, 1.5 = 50% faster)
- **What it does**:
  1. Starts with base speed of 100%
  2. Adds shield boosts (from blocking projectiles)
  3. Applies slow effect (if hit) or speedup effect (if hit someone)
  4. Returns the combined speed multiplier

**`apply_effect(effect_type, duration, current_time)`**
- **Purpose**: Applies a status effect to the player
- **Effects**:
  - `'slow'`: Slows the player down
  - `'speedup'`: Speeds the player up
  - `'block'`: Adds a speed boost from successful block

**`get_progress()`**
- **Purpose**: Calculates how close the player is to the center line
- **Returns**: A number from 0 to 100 (percentage)

---

### 3. **GameState Class** (game_state.py)
Tracks game progression (rounds, matches, countdown).

**Key variables:**
- `round_wins`: Score for each player [P1 wins, P2 wins]
- `current_round`: Which round we're on
- `match_over`: Whether someone won the match
- `round_over`: Whether someone won the current round
- `countdown_active`: Whether countdown is showing

---

### 4. **Wall Class** (wall.py)
Represents wall obstacles that block player and projectile movement.

**Parameters:**
- `x, y`: Position (in tiles) - bottom edge of wall
- `width`: Wall width (default 0.5 tiles)
- `height`: Wall height (default 3 tiles)

**Methods:**
- `get_tile_bounds()`: Returns the area the wall occupies
- `overlaps_with(other_wall)`: Checks if this wall overlaps another wall
- `draw(screen)`: Draws the wall on screen

**Features:**
- Walls are randomly placed at match start
- Mirrored on both sides for fair gameplay
- Have minimum distance requirement (5 tiles) to prevent clustering
- Block player movement and projectile shots

---

### 5. **GameObject System** (game_object.py)
Uses Python inheritance to create collectible objects.

**Base Class: `GameObject`**
- Defines common features: position, collision, drawing
- Acts as a template for all collectible objects

**Child Classes:**

**`SpeedBoostObject`** (inherits from GameObject)
- Green object
- Effect: Increases the collecting player's speed for a duration
- Applies speedup effect to the player who collects it

**`SpeedDebuffObject`** (inherits from GameObject)
- Orange object
- Effect: Slows down the opponent
- Applies slow effect to the other player (not the collector)

**Key Concepts:**
- **Inheritance**: `SpeedBoostObject` and `SpeedDebuffObject` inherit all properties and methods from `GameObject`, then add their own special behavior in `apply_effect()`.
- **Polymorphism**: Both object types can be treated as `GameObject` instances (e.g., stored in the same list, drawn the same way), but each behaves differently when `apply_effect()` is called.
- **Component-Based Design**: Each object type is self-contained with its own behavior, making it easy to add new object types without modifying existing code.
- **Position Generation**: Objects are randomly placed on the map, avoiding walls.

### Object Placement Guardrails:
The object generation system includes three important guardrails to ensure fair and balanced gameplay:

1. **No Wall Overlap**: Objects cannot be placed where walls exist, preventing impossible-to-reach objects.
2. **Safe Distance from Players**: Objects must be at least 2 tiles away from player starting positions, preventing unfair advantages at round start.
3. **No Object Overlap**: Objects must be at least 1 tile apart from each other, ensuring each object is clearly distinguishable and collectible.

These guardrails are checked during object generation using distance calculations:
```python
distance = math.sqrt((x1 - x2)**2 + (y1 - y2)**2)
```

---

### 6. **Renderer Class** (renderer.py)
Handles all drawing and rendering operations for the game.

**Key Methods:**

**`draw_instructions_screen()`**
- **Purpose**: Displays the game instructions at startup
- **Features**:
  - Responsive font sizing that adjusts to fit screen size
  - Calculates optimal font size to ensure all content fits
  - Uses binary search algorithm to find best font size
  - Automatically wraps text to fit screen width
  - Shows: objective, walls, controls, hit effects, blocking, match structure
  - Press SPACE to start the game

**`draw_stats_panel(player1, player2)`**
- Draws the stats panel showing player speeds, shields, and progress bars

**`draw_countdown(game_state)`**
- Draws the countdown timer before each round starts

**`draw_round_victory_screen()`** and **`draw_match_victory_screen()`**
- Display victory screens after rounds and matches

---

## Game Flow (Main Loop)

The main game loop in main.py runs every frame:

1. **Calculate time**: `dt = clock.tick(60) / 1000` - time since last frame
2. **Handle input**: Keyboard events (movement, shooting, shields)
3. **Update players**: Move them based on input and speed modifiers (checking wall collisions)
4. **Update bullets**: Move all projectiles and check for hits (with players and walls)
5. **Check object collection**: See if players collected any objects and apply effects
6. **Check win condition**: Has anyone reached 100% progress?
7. **Draw everything**: Walls, objects, players, bullets, stats panel, UI
8. **Repeat**: Go back to step 1

---

## How Speed System Works

### Speed Effects Chain:

1. **You get hit** → `update_projectiles()` detects collision
2. **Effect applied** → `apply_effect('slow', 2.0)` sets `slow_end_time`
3. **Speed calculated** → `move()` calls `get_total_speed_multiplier()`
4. **Movement adjusted** → Position = old_position + movement × speed_multiplier

### Example:
```python
# Player gets hit, slow_end_time is set to current_time + 2.0
# In move(), get_total_speed_multiplier() returns 0.5 (50% speed)
# Position updates: new_x = x + dx * dt * 0.5
# Player moves at half speed for 2 seconds
```

---

## Key Parameters Explained

- **dt** (delta time): How much time passed since last frame (in seconds)
  - Example: At 60 FPS, dt ≈ 0.0167 seconds per frame
  
- **speed_multiplier**: How fast relative to normal
  - 1.0 = 100% speed (normal)
  - 0.5 = 50% speed (slowed)
  - 1.5 = 150% speed (speedup)

- **current_time**: Current game time (seconds since game started)
  - Used to track when effects expire

- **tiles vs pixels**: Game uses "tiles" for logic (1 tile = 20 pixels for display)

---

## Important Config Values (from game_config.py)

- `player_speed`: 5 (tiles per second - base movement speed)
- `fire_rate`: 5 (shots per second)
- `slow_factor`: 0.5 (hit player moves at 50% speed)
- `slow_duration`: 2.0 (slow lasts 2 seconds)
- `speedup_factor`: 1.5 (hitting someone gives 150% speed)
- `speedup_duration`: 1.0 (speedup lasts 1 second)
- `walls_enabled`: True (enable/disable wall obstacles)
- `num_walls_per_side`: 5 (number of walls on each player's side)
- `wall_min_distance`: 5 (minimum distance between walls in tiles)
- `objects_enabled`: True (enable/disable collectible objects)
- `num_objects_per_match`: 10 (total objects per match)
- `speed_boost_duration`: 5.0 (how long speed boost lasts)
- `speed_boost_multiplier`: 1.3 (30% speed increase)

---

## Simple Flow Example: Player Shoots and Hits

```
1. Player presses shoot key
   ↓
2. shoot() creates Projectile, adds to projectiles list
   ↓
3. update_projectiles() runs every frame
   ↓
4. Projectile moves: x += direction * speed * dt
   ↓
5. Collision detected: projectile.rect.colliderect(other_player.rect)
   ↓
6. If no shield:
   - other_player.apply_effect('slow') → slows target
   - self.apply_effect('speedup') → speeds up shooter
   ↓
7. Projectile removed
   ↓
8. Next frame: get_total_speed_multiplier() returns new speeds
   ↓
9. move() uses new speed_multiplier for movement
```

---

## Tips for Understanding

1. **Follow the data flow**: Input → Update → Draw (repeat)
2. **Remember dt**: Movement = distance_per_second × dt
3. **Effects are timed**: They expire based on current_time
4. **Position in tiles**: Logic uses tiles, rendering converts to pixels
5. **Lists are modified while iterating**: Notice `[:]` slicing in update_projectiles
