MAZE_LAYOUT = [
    # Row 0 - Top border
    [3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3],
    # Row 1 
    [3, 2, 1, 1, 1, 1, 1, 1, 3, 1, 3, 1, 1, 1, 1, 1, 0, 3],
    # Row 2 
    [3, 1, 3, 1, 1, 3, 1, 1, 1, 1, 1, 1, 1, 3, 1, 1, 1, 3],
    # Row 3
    [3, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 3],
    # Row 4
    [3, 1, 1, 1, 3, 1, 1, 3, 3, 3, 3, 3, 1, 1, 3, 1, 1, 3],
    # Row 5
    [3, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 1, 1, 1, 1, 1, 1, 3],
    # Row 6
    [3, 1, 1, 1, 3, 1, 1, 3, 0, 0, 0, 3, 1, 1, 3, 1, 1, 3],
    # Row 7 
    [3, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 3],
    # Row 8 
    [3, 1, 3, 1, 1, 3, 1, 1, 1, 1, 1, 1, 1, 3, 1, 1, 1, 3],
    # Row 9 
    [3, 0, 1, 1, 1, 1, 1, 1, 3, 1, 3, 1, 1, 1, 1, 1, 0, 3],
    # Row 10 
    [3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3],
]

# Position definitions for entities
POSITIONS = {
    # Player starting positions
    'PLAYER1_START': (1, 1),  # Top-left corner
    'PLAYER2_START': (16, 9),  # Bottom-right corner
    # Ghost starting positions
    'INKY_GHOST_START': (9, 5),  # Center area
    # Inky Ghost scatter point (one single point outside the maze on the right)
    'INKY_GHOST_SCATTER_POINT': (18, 5),  # Right side of the maze
    'GHOST_RESPAWN_POINT': {'INKY': (9, 5)},  # Center area for Inky
}

# Maze metadata
MAZE_INFO = {
    'width': 19,
    'height': 11,
    'recommended_cell_size': 40,
    'total_size': (760, 440),  # width * cell_size, height * cell_size
    'description': 'Compact layout for 800x600 screen with 40px cells',
}
