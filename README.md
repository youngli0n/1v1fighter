# 1v1 Fighter

A fast-paced, competitive two-player racing game where players battle to reach the finish line while using strategic abilities to gain advantages. Built with Python and Pygame, this game combines racing mechanics with tactical combat elements.

## Features

- Two-player competitive gameplay
- Unique movement and shooting mechanics
- Shield blocking system with speed boosts
- Dynamic speed effects and regeneration
- Real-time stats tracking
- Dynamic wall obstacles with collision detection
- Collectible objects with positive and negative effects (inheritance-based system)
- AI opponent support (optional)
- Interactive instructions screen at startup with responsive design

## Controls

### Player 1 (Red)
- Movement: WASD
- Shoot: V
- Shield: B

### Player 2 (Blue)
- Movement: Arrow Keys
- Shoot: ,
- Shield: .

## Game Mechanics

- Players race to reach 100% progress
- Shooting slows opponents and speeds up the shooter
- Shield blocks projectiles and grants temporary speed boosts
- Speed effects regenerate over time
- Multiple speed boosts can stack

## Requirements

- Python 3.x
- Pygame

## Installation

1. Clone the repository:
```bash
git clone https://github.com/youngli0n/1v1fighter.git
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the game:
```bash
python main.py
```

## Development

This project was developed in sprints, with each sprint adding new features:
- Sprint 1: Basic movement and game board
- Sprint 2: Stats panel and player information
- Sprint 3: Shooting mechanics and effects
- Sprint 4: Shield system and win conditions
- Sprint 5: Wall obstacles and code refactoring

## License

This project is open source and available under the MIT License. 