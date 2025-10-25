# How to Add New Object Types - Tutorial for Liam

Hi Liam! This guide will teach you how to add new collectible object types to the game. We'll walk through the general process and then do a specific example together!

## 📚 Understanding the Basics

### What is Inheritance?
Think of inheritance like a family tree! The parent class (`GameObject`) has all the basic features that every object needs (like where it is, what color it is, etc.). Then, each child class (like `SpeedBoostObject`) gets those features for FREE and adds its own special ability.

It's like how you might have your dad's eyes (inherited feature) but your own special hobby (new feature you added)!

### The Object System Structure

```
GameObject (Parent)
├── SpeedBoostObject (Child) - Makes you faster
├── SpeedDebuffObject (Child) - Slows opponent
└── YOUR_NEW_OBJECT (Child) - Does something cool!
```

---

## 🎯 Step-by-Step Guide to Adding a New Object Type

### Step 1: Add Configuration to `game_config.py`

Open the file `game_config.py` and add your settings:

```python
# In the GAME_CONFIG dictionary, add your new object settings:
'your_object_duration': 5.0,  # How long the effect lasts (seconds)
'your_object_value': 2.0,     # The strength/power of the effect

# In the COLORS dictionary, add a color for your object:
'your_object': (255, 100, 50)  # RGB color (Red, Green, Blue)
```

**Example**: We're making a "Pierce" object, so we'd add:
```python
'pierce_duration': 1.0,  # You can break through walls for 1 second
'pierce_object': (255, 0, 255)  # Purple color
```

### Step 2: Create a New File for Your Object! ✨

**This is the best part** - you only need to edit ONE file to add a new object! Create a new file called `your_object_name.py` (e.g., `pierce_object.py`):

```python
"""Your Object - Description of what it does"""
from game_object import GameObject, register_object_type
from game_config import GAME_CONFIG, COLORS


class YourObject(GameObject):
    """A collectible object that does something special!"""
    
    def __init__(self, x, y):
        """
        Initialize your object
        
        Args:
            x: X position in tiles
            y: Y position in tiles
        """
        # Call the parent class's __init__ method with the color
        super().__init__(x, y, COLORS['your_object'])
    
    def apply_effect(self, player, current_time):
        """
        Apply the special effect to the player
        
        Args:
            player: The Player object that collected this
            current_time: Current game time
        """
        # TODO: Add your effect logic here!
        pass


# Register this object type - THIS IS THE MAGIC LINE! 🪄
register_object_type('your_object', YourObject)
```

### Step 3: Register Your Object in `objects.py`

Open `objects.py` and add one line:

```python
# At the top, add:
import your_object_name  # This will auto-register your object!
```

**That's it!** The registry system handles everything else automatically. No need to modify any other files! 🎉

### Step 4: Update Player Class (if needed)

If your object affects the player, you might need to add a method to `player.py`:

```python
# Add a method to the Player class:
def set_special_ability(self, ability_type, end_time):
    """Set a special ability with an expiration time"""
    self.special_ability = ability_type
    self.special_ability_end_time = end_time
```

### Step 5: Update Collection Logic in `main.py`

In `main.py`, find where objects are collected and add logic for your object:

```python
# Find the object collection code and add your special handling:
if isinstance(obj, YourObject):
    obj.apply_effect(player1, current_time)
    # Add any special visual effects here if you want!
```

### Step 6: Test Your Object!

Run the game and make sure your object:
- ✅ Appears on the map with the right color
- ✅ Can be collected by walking into it
- ✅ Applies the effect you designed
- ✅ Works correctly!

---

## 🎮 Complete Example: Pierce Ability Object

Now let's create the "Pierce" ability together - it lets players break through walls for a short time!

### Step 1: Configuration (`game_config.py`)

Already added! We added:
- `'pierce_duration': 1.0`
- `'pierce_object': (255, 0, 255)`

### Step 2: Create PierceObject Class (`game_object.py`)

Add this class after `SpeedDebuffObject`:

```python
class PierceObject(GameObject):
    """A collectible object that allows walking through walls"""
    
    def __init__(self, x, y):
        """
        Initialize a pierce object
        
        Args:
            x: X position in tiles
            y: Y position in tiles
        """
        super().__init__(x, y, COLORS['pierce_object'])
    
    def apply_effect(self, player, current_time):
        """
        Grant the player wall-piercing ability
        
        Args:
            player: The Player object that collected this
            current_time: Current game time
        """
        # Set the player's pierce ability with expiration time
        player.pierce_ability = True
        player.pierce_ability_end_time = current_time + GAME_CONFIG['pierce_duration']
```

### Step 3: Update Generation (`game_object.py`)

Add to the `generate_object` function:

```python
elif object_type == 'pierce':
    return PierceObject(x, y)
```

Update `generate_objects` to include pierce objects:

```python
# Choose randomly between 3 types (33% each)
rand = random.random()
if rand < 0.33:
    obj = generate_object('speed_boost', walls, objects, player1_pos, player2_pos)
elif rand < 0.66:
    obj = generate_object('speed_debuff', walls, objects, player1_pos, player2_pos)
else:
    obj = generate_object('pierce', walls, objects, player1_pos, player2_pos)
```

### Step 4: Update Player Class (`player.py`)

In the `Player.__init__` method, add:
```python
# Add after line ~40
self.pierce_ability = False
self.pierce_ability_end_time = 0
```

In the `Player.reset` method, add:
```python
# Reset pierce ability
self.pierce_ability = False
self.pierce_ability_end_time = 0
```

In the `Player.move` method, find the wall collision check and modify it:
```python
# Find this code (around line 120):
if walls:
    temp_rect = pygame.Rect(...) # Create temp rect for new position
    for wall in walls:
        if temp_rect.colliderect(wall.rect):
            can_move = False
            break

# Change it to:
if walls and not self.pierce_ability:
    temp_rect = pygame.Rect(...)
    for wall in walls:
        if temp_rect.colliderect(wall.rect):
            can_move = False
            break
```

Also update the `Player.move` method to check for expired pierce:
```python
# At the start of move method, check if pierce expired:
if self.pierce_ability and current_time >= self.pierce_ability_end_time:
    self.pierce_ability = False
```

### Step 5: Update Main Loop (`main.py`)

The collection code should already work! Just verify it handles `PierceObject`:

```python
# This code should already work for any GameObject:
if obj.is_collected(player1.rect):
    if isinstance(obj, SpeedDebuffObject):
        obj.apply_effect(player1, player2, current_time)
    else:
        obj.apply_effect(player1, current_time)
    game_objects.remove(obj)
```

---

## 🎨 Tips for Creating Great Objects

1. **Keep it simple**: Start with one effect, then add more if needed
2. **Test often**: Make sure your object doesn't break the game!
3. **Balance is key**: Make sure your object isn't too powerful or too weak
4. **Have fun**: This is your game - make it awesome!

---

## 🐛 Common Issues and Solutions

**Problem**: My object doesn't appear on the map!
- **Solution**: Check that you added it to `generate_object` and `generate_objects` functions

**Problem**: My object appears but nothing happens when I collect it!
- **Solution**: Make sure `apply_effect` is doing something, and check the collection code in `main.py`

**Problem**: The game crashes when I collect my object!
- **Solution**: Check that all player attributes you're using exist in the Player class

---

## 🚀 What's Next?

Now that you know how to add objects, try creating:
- **Shield Object**: Temporary invincibility
- **Multi-Shot Object**: Fire multiple bullets at once
- **Teleport Object**: Instantly jump forward
- **Freeze Object**: Freeze the opponent in place

The sky's the limit! Have fun coding! 🎮✨
