# Two Player Pacman Game

A modular two-player Pacman game built with pygame, featuring human vs AI gameplay with customizable sprites.

## Features

- **Two Player Gameplay**: One human player vs one AI player
- **Modular Design**: Separate components for easy modification and extension
- **Custom Sprite Support**: Easy integration of your own sprite images
- **Multiple AI Types**: Different AI behaviors (simple, pellet hunter, competitive)
- **Smooth Movement**: Pixel-perfect movement between grid cells
- **Score System**: Real-time scoring and winner determination

## File Structure

```
pygame_pacman/
├── main.py              # Main game loop and coordination
├── constants.py         # Game constants and configuration
├── sprite_manager.py    # Sprite loading and management
├── maze.py             # Maze layout and collision detection
├── player.py           # Human player controller
├── ai_player.py        # AI player with different behaviors
├── game_ui.py          # User interface and rendering
├── requirements.txt    # Python dependencies
└── assets/             # Sprite images and game assets
    ├── ena_up.png
    ├── ena_down.png
    ├── ena_left.png
    └── ena_right.png
```

## Installation

1. **Install Python 3.7+** if not already installed
2. **Install pygame**:
   ```bash
   pip install -r requirements.txt
   ```

## How to Run

```bash
python main.py
```

## Controls

- **Player 1 (Human)**: WASD keys

  - W: Up
  - S: Down
  - A: Left
  - D: Right

- **Game Controls**:
  - SPACE: Start game
  - P: Pause/Resume
  - R: Restart game
  - ESC: Quit

## Using Custom Sprites

### Method 1: Automatic Loading

Place your sprite files in the `assets/` folder with these naming conventions:

- Player 1: `ena_up.png`, `ena_down.png`, `ena_left.png`, `ena_right.png`
- AI Player: `ai_up.png`, `ai_down.png`, `ai_left.png`, `ai_right.png`

### Method 2: Manual Loading

Modify the `load_custom_sprites()` function in `main.py`:

```python
def load_custom_sprites(sprite_manager):
    # Custom sprites for player 1
    player1_sprites = {
        'up': 'path/to/your/player1_up.png',
        'down': 'path/to/your/player1_down.png',
        'left': 'path/to/your/player1_left.png',
        'right': 'path/to/your/player1_right.png'
    }
    sprite_manager.load_custom_sprites('player1', player1_sprites)

    # Custom sprites for AI player
    ai_sprites = {
        'up': 'path/to/your/ai_up.png',
        'down': 'path/to/your/ai_down.png',
        'left': 'path/to/your/ai_left.png',
        'right': 'path/to/your/ai_right.png'
    }
    sprite_manager.load_custom_sprites('ai1', ai_sprites)
```

Then uncomment this line in `main.py`:

```python
load_custom_sprites(game.sprite_manager)
```

### Sprite Requirements

- Format: PNG, JPG, JPEG, or GIF
- Size: Any size (will be automatically scaled to fit the game grid)
- Naming: Follow the direction naming convention (up, down, left, right)

## Customization Options

### AI Behavior Types

Change the AI behavior by modifying the `ai_type` parameter in `main.py`:

```python
self.ai_player = AIPlayer(
    player_id="ai1",
    start_x=self.maze.width - 2,
    start_y=self.maze.height - 2,
    sprite_manager=self.sprite_manager,
    ai_type="pellet_hunter"  # Options: "simple", "pellet_hunter", "competitive"
)
```

- **simple**: Random movement, avoids walls
- **pellet_hunter**: Actively seeks nearest pellets
- **competitive**: Competes with human player, moves away when close

### Game Constants

Modify `constants.py` to change game behavior:

- `PLAYER_SPEED`: Human player movement speed
- `AI_SPEED`: AI player movement speed
- `SCREEN_WIDTH/HEIGHT`: Game window size
- `CELL_SIZE`: Size of maze cells
- Color constants for different game elements

### Maze Layout

Modify the `layout` array in `maze.py` to create custom maze designs:

- `1`: Wall
- `0`: Empty space
- `2`: Regular pellet
- `3`: Power pellet

## Component Details

### SpriteManager (`sprite_manager.py`)

- Handles loading and managing custom sprites
- Provides fallback colored circles if sprites are missing
- Supports automatic sprite discovery in assets folder

### Player (`player.py`)

- Human-controlled Pacman character
- Smooth grid-based movement
- Input handling and collision detection
- Score tracking

### AIPlayer (`ai_player.py`)

- AI-controlled Pacman with multiple behavior modes
- Pathfinding algorithms for pellet hunting
- Different personality types for varied gameplay

### Maze (`maze.py`)

- Maze layout and collision detection
- Pellet and power pellet management
- Grid-to-pixel coordinate conversion

### GameUI (`game_ui.py`)

- Score display and game status
- Start screen, pause screen, and game over screen
- Control instructions

## Extending the Game

The modular design makes it easy to extend:

1. **Add More Players**: Create additional Player or AIPlayer instances
2. **New AI Behaviors**: Add new AI types in `ai_player.py`
3. **Power-ups**: Extend the maze system to include special items
4. **Sound Effects**: Add pygame.mixer sounds to various actions
5. **Animations**: Enhance sprite rendering with animation frames

## Troubleshooting

### Common Issues

1. **Sprites not loading**: Check file paths and ensure images exist
2. **Game runs slowly**: Reduce FPS in constants.py or optimize sprite sizes
3. **Import errors**: Ensure pygame is installed: `pip install pygame`

### Performance Tips

- Use smaller sprite images for better performance
- Reduce FPS if experiencing lag
- Optimize maze size for your target performance

## License

This is a template project for educational and personal use. Feel free to modify and extend as needed!
