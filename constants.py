# Game Constants
import pygame

# Screen dimensions
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
YELLOW = (255, 255, 0)
BLUE = (0, 0, 255)
RED = (255, 0, 0)
PINK = (255, 184, 255)
CYAN = (0, 255, 255)
ORANGE = (255, 184, 82)
GREEN = (0, 255, 0)

# Updated cell size - increased back to 40 for better visibility
CELL_SIZE = 40

# Player settings
PLAYER_SPEED = 1.5
AI_SPEED = 1.5

# Ghost settings
GHOST_SPEED = 1.0
# Ghost AI state
GHOST_AI_STATES = {"CHASE": "CHASE", "FRIGHTENED": "FRIGHTENED", "EATEN": "EATEN"}

# Game objects
PELLET_SIZE = 8
POWER_PELLET_SIZE = 28  # Adjusted for 40px cells
PELLET_POINTS = 10
POWER_PELLET_POINTS = 32

# Directions
DIRECTIONS = {"UP": (0, -1), "DOWN": (0, 1), "LEFT": (-1, 0), "RIGHT": (1, 0)}

# Key mappings for two players
PLAYER1_KEYS = {pygame.K_w: "UP", pygame.K_s: "DOWN", pygame.K_a: "LEFT", pygame.K_d: "RIGHT"}

PLAYER2_KEYS = {pygame.K_UP: "UP", pygame.K_DOWN: "DOWN", pygame.K_LEFT: "LEFT", pygame.K_RIGHT: "RIGHT"}
