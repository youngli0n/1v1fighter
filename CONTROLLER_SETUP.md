# Xbox Controller Setup Guide

## Quick Start

1. **Connect Controllers**: Plug in both Xbox controllers via USB or pair via Bluetooth
2. **Enable in Config**: Open `game_config.py` and change `'use_controllers': False` to `'use_controllers': True`
3. **Run Game**: Start the game with `python main.py`

## Button Mapping

### Controller 1 (Player 1 - Red)
- **Left Stick**: Move in all directions
- **A Button**: Shoot
- **B Button**: Shield (hold to activate)

### Controller 2 (Player 2 - Blue)
- **Left Stick**: Move in all directions
- **A Button**: Shoot
- **B Button**: Shield (hold to activate)

## How It Works

When controllers are enabled:
- The game automatically detects connected controllers
- Controller 1 controls Player 1
- Controller 2 controls Player 2
- Keyboard controls are disabled for the respective players

When controllers are disabled:
- Player 1 uses keyboard (WASD, V, B)
- Player 2 uses keyboard (Arrows, ,, .)
- Or Player 2 can be AI-controlled

## Troubleshooting

**Controllers not working?**
- Check that `'use_controllers': True` in `game_config.py`
- Verify controllers are connected (check terminal output on startup)
- Make sure you have at least 2 controllers connected for 2-player mode

**Mixed input mode?**
- When controllers are enabled, keyboard input is ignored for movement/actions
- Only menu controls (SPACE, R) work from keyboard

