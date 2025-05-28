MAZE_LAYOUT = [
    # Row 0 - Top border
    [3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3],
    # Row 1
    [3, 2, 1, 1, 1, 3, 1, 1, 3, 1, 3, 1, 1, 3, 1, 1, 2, 3],
    # Row 2
    [3, 1, 3, 3, 1, 3, 1, 1, 3, 1, 3, 1, 1, 3, 1, 3, 1, 3],
    # Row 3
    [3, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 3],
    # Row 4
    [3, 1, 3, 1, 3, 3, 1, 3, 3, 3, 3, 3, 1, 3, 3, 1, 1, 3],
    # Row 5 - Ghost spawn area
    [3, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 1, 1, 1, 1, 1, 1, 3],
    # Row 6 - Center area
    [3, 1, 3, 1, 3, 3, 1, 3, 0, 0, 0, 3, 1, 3, 3, 1, 1, 3],
    # Row 7
    [3, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 3],
    # Row 8
    [3, 1, 3, 3, 1, 3, 1, 1, 3, 1, 3, 1, 1, 3, 1, 3, 1, 3],
    # Row 9
    [3, 2, 1, 1, 1, 3, 1, 1, 3, 1, 3, 1, 1, 3, 1, 1, 2, 3],
    # Row 10 - Bottom border
    [3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3],
]

# Position definitions for entities
POSITIONS = {
    # Player starting positions
    'PLAYER1_START': (1, 1),  # Top-left corner
    'PLAYER2_START': (17, 9),  # Bottom-right corner
    # Ghost starting positions
    'INKY_GHOST_START': (9, 5),  # Center area
    # Inky Ghost scatter positions (corners and strategic points)
    'INKY_SCATTER_POINTS': [(1, 1), (4, 1), (4, 3), (1, 3)],  # Top-left corner  # Top-left corridor  # Top-left corridor  # Top-left corridor
    # Alternative spawn points (for respawning or multiple ghosts)
    'GHOST_SPAWN_AREA': {'center': (9, 5), 'left': (8, 5), 'right': (10, 5), 'top': (9, 4), 'bottom': (9, 6)},
    # Power pellet positions (corners for strategic gameplay)
    'POWER_PELLETS': [(1, 1), (17, 1), (1, 9), (17, 9)],
    # Safe zones (areas near starting positions)
    'SAFE_ZONES': {'player1': [(1, 1), (2, 1), (1, 2), (2, 2)], 'player2': [(17, 9), (16, 9), (17, 8), (16, 8)]},
    # Strategic choke points
    'CHOKE_POINTS': [(9, 3), (9, 7), (5, 5), (13, 5)],  # Top center corridor  # Bottom center corridor  # Left center  # Right center
}

# Maze metadata
MAZE_INFO = {
    'width': 19,
    'height': 11,
    'recommended_cell_size': 40,
    'total_size': (760, 440),  # width * cell_size, height * cell_size
    'description': 'Compact layout for 800x600 screen with 40px cells',
}
