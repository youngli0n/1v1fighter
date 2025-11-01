# How to Add New Collectible Types - Tutorial for Liam

Hi Liam! This guide will teach you how to add new collectible types to the game. We'll walk through the general process and then do a specific example together!

## 📚 Understanding the Basics

### What is Inheritance?
Think of inheritance like a family tree! The parent class (`GameCollectible`) has all the basic features that every collectible needs (like where it is, what color it is, etc.). Then, each child class (like `SpeedBoostCollectible`) gets those features for FREE and adds its own special ability.

It's like how you might have your dad's eyes (inherited feature) but your own special hobby (new feature you added)!

### The Collectible System Structure

```
GameCollectible (Parent)
├── SpeedBoostCollectible (Child) - Makes you faster
├── SpeedBuffCollectible (Child) - Slows down opponent
└── YOUR_NEW_COLLECTIBLE (Child) - Does something cool!
```

---

## 🎯 Step-by-Step Guide to Adding a New Collectible Type

### Step 1: Add Configuration to `game_config.py`

Open the file `game_config.py` and add your settings:

```python
# In the GAME_CONFIG dictionary, add your new collectible settings:
'your_collectible_duration': 5.0,  # How long the effect lasts (seconds)
'your_collectible_value': 2.0,     # The strength/power of the effect

# In the COLORS dictionary, add a color for your collectible:
'your_collectible': (255, 100, 50)  # RGB color (Red, Green, Blue)
```

### Step 2: Create a New File for Your Collectible! ✨

**This is the best part** - you only need to edit ONE file to add a new collectible! Create a new file called `your_collectible_name_collectible.py` (e.g., `bullet_pierce_collectible.py`):

```python
"""Your Collectible - Description of what it does"""
from game_collectible import GameCollectible, register_collectible_type
from game_config import GAME_CONFIG, COLORS


class YourCollectible(GameCollectible):
    """A collectible that does something special!"""
    
    def __init__(self, x, y):
        """
        Initialize your collectible
        
        Args:
            x: X position in tiles
            y: Y position in tiles
        """
        # Call the parent class's __init__ method with the color
        super().__init__(x, y, COLORS['your_collectible'])
    
    def apply_effect(self, player, current_time, other_player=None):
        """
        Apply the special effect to the player
        
        Args:
            player: The Player that collected this
            current_time: Current game time
            other_player: The other player (optional, for opponent-targeting effects)
        """
        # TODO: Add your effect logic here!
        pass


# Register this collectible type - THIS IS THE MAGIC LINE! 🪄
register_collectible_type('your_collectible', YourCollectible)
```

### Step 3: Register Your Collectible in `collectibles.py`

Open `collectibles.py` and add one line:

```python
# Add this import at the top:
import your_collectible_name_collectible  # This will auto-register your collectible!
```

**That's it!** The registry system handles everything else automatically. No need to modify any other files! 🎉

### Step 4: Update Player Class (if needed)

If your collectible affects the player, you might need to add attributes to `player.py`:

In the `Player.__init__` method, add:
```python
# Add new attributes for your collectible's effect
self.your_ability = False
self.your_ability_end_time = 0
```

In the `Player.reset` method, add:
```python
# Reset your ability
self.your_ability = False
self.your_ability_end_time = 0
```

### Step 5: Update Game Logic (if needed)

If your collectible needs special logic (like checking if bullets can pierce), update the relevant functions in the appropriate files.

### Step 6: Test Your Collectible!

Run the game and make sure your collectible:
- ✅ Appears on the map with the right color
- ✅ Can be collected by walking into it
- ✅ Applies the effect you designed
- ✅ Works correctly!

---

## 🎮 Complete Example: Bullet Pierce Collectible

Now let's create a "Bullet Pierce" collectible together! This ability makes your bullets destroy walls - when a bullet hits a wall, the wall turns red briefly and then disappears!

### Step 1: Configuration (`game_config.py`)

Add these settings to the `GAME_CONFIG` dictionary:

```python
'bullet_pierce_duration': 10.0,  # Bullets can break walls for 10 seconds
```

Add a color to the `COLORS` dictionary:

```python
'bullet_pierce_collectible': (100, 200, 255)  # Light blue color
```

### Step 2: Create BulletPierceCollectible Class

Create a new file called `bullet_pierce_collectible.py`:

```python
"""Bullet Pierce Collectible - Makes bullets destroy walls"""
from game_collectible import GameCollectible, register_collectible_type
from game_config import GAME_CONFIG, COLORS


class BulletPierceCollectible(GameCollectible):
    """A collectible that makes bullets destroy walls"""
    
    def __init__(self, x, y):
        """
        Initialize a bullet pierce collectible
        
        Args:
            x: X position in tiles
            y: Y position in tiles
        """
        super().__init__(x, y, COLORS['bullet_pierce_collectible'])
    
    def apply_effect(self, player, current_time, other_player=None):
        """
        Grant the player wall-destroying bullets
        
        Args:
            player: The Player that collected this
            current_time: Current game time
            other_player: Not used for this collectible
        """
        # Set the player's bullet pierce ability with expiration time
        player.bullet_pierce_active = True
        player.bullet_pierce_end_time = current_time + GAME_CONFIG['bullet_pierce_duration']


# Register this collectible type
register_collectible_type('bullet_pierce', BulletPierceCollectible)
```

### Step 3: Register in `collectibles.py`

Add this line to `collectibles.py`:

```python
import bullet_pierce_collectible  # Registers 'bullet_pierce'
```

### Step 4: Update Player Class (`player.py`)

In the `Player.__init__` method (around line 30), add:
```python
# Add after the other ability variables
self.bullet_pierce_active = False
self.bullet_pierce_end_time = 0
```

In the `Player.reset` method (around line 50), add:
```python
# Reset bullet pierce ability
self.bullet_pierce_active = False
self.bullet_pierce_end_time = 0
```

### Step 5: Update Wall Class (`wall.py`)

Add methods to the `Wall` class to handle being destroyed:

```python
def mark_for_destruction(self):
    """Mark this wall to be destroyed (turns red)"""
    self.being_destroyed = True

def is_being_destroyed(self):
    """Check if this wall is being destroyed"""
    return hasattr(self, 'being_destroyed') and self.being_destroyed
```

Update the `Wall.__init__` method to add:
```python
self.being_destroyed = False
```

Update the `Wall.draw` method to draw red when being destroyed:

```python
def draw(self, screen):
    """
    Draw the wall on the screen
    
    Args:
        screen: The pygame surface to draw on
    """
    # Draw red if being destroyed, otherwise normal color
    color = (255, 0, 0) if self.being_destroyed else GAME_CONFIG['wall_color']
    pygame.draw.rect(screen, color, self.rect)
```

### Step 6: Update Projectile-Wall Collision Logic (`player.py`)

In the `Player.update_projectiles` method, find where wall collisions are checked (around line 277) and modify it:

**Find this code:**
```python
# Check for collision with walls
hit_wall = False
if walls:
    for wall in walls:
        if projectile.rect.colliderect(wall.rect):
            collision_detected = True
            hit_wall = True
            break
```

**Change it to:**
```python
# Check for collision with walls
hit_wall = False
if walls:
    for wall in walls:
        if projectile.rect.colliderect(wall.rect):
            # Check if player has bullet pierce ability
            if self.bullet_pierce_active:
                # Mark wall for destruction and continue through
                wall.mark_for_destruction()
                # Don't stop the bullet, continue its path!
                continue
            else:
                # Normal collision - bullet stops
                collision_detected = True
                hit_wall = True
                break
```

### Step 7: Update Main Loop (`main.py`)

Add logic to remove destroyed walls. In the main game loop, add this after the projectile updates:

```python
# Check for walls marked for destruction and remove them after a brief delay
for wall in walls[:]:  # Use [:] to iterate over a copy
    if wall.is_being_destroyed():
        walls.remove(wall)
```

Also add logic to check if pierce ability expired. Add this to the player update section:

```python
# Check if bullet pierce ability expired
if player1.bullet_pierce_active and current_time >= player1.bullet_pierce_end_time:
    player1.bullet_pierce_active = False
if player2.bullet_pierce_active and current_time >= player2.bullet_pierce_end_time:
    player2.bullet_pierce_active = False
```

### Step 8: Test Your Collectible!

Run the game and test:
1. Collect the bullet pierce collectible
2. Fire bullets at walls
3. Watch them turn red and disappear! 🎉

---

## 🎨 Tips for Creating Great Collectibles

1. **Keep it simple**: Start with one effect, then add more if needed
2. **Test often**: Make sure your collectible doesn't break the game!
3. **Balance is key**: Make sure your collectible isn't too powerful or too weak
4. **Visual feedback**: Let players know when abilities are active (like showing a status icon)
5. **Have fun**: This is your game - make it awesome!

---

## 🐛 Common Issues and Solutions

**Problem**: My collectible doesn't appear on the map!
- **Solution**: Make sure you added the import to `collectibles.py` and cleared Python's cache by deleting `__pycache__` folders

**Problem**: My collectible appears but nothing happens when I collect it!
- **Solution**: Make sure `apply_effect` is doing something, check that you added the effect attributes to the Player class

**Problem**: The game crashes when I collect my collectible!
- **Solution**: Check that all player attributes you're using exist in the Player class (especially in `__init__` and `reset`)

**Problem**: My ability doesn't expire!
- **Solution**: Make sure you added the expiration check in the main game loop

---

## 🚀 What's Next?

Now that you know how to add collectibles, try creating:
- **Multi-Shot Collectible**: Fire multiple bullets at once
- **Teleport Collectible**: Instantly jump forward
- **Freeze Collectible**: Freeze the opponent in place
- **Shield Collectible**: Temporary invincibility
- **Speed Burst Collectible**: Short super-speed boost

The sky's the limit! Have fun coding! 🎮✨
