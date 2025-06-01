from collections import deque
from constants import *


class AIState:
    def __init__(self, ai_type, start_x, start_y):
        self.ai_type = ai_type

        # Movement and pathfinding
        self.path = []
        self.current_target = None
        self.direction = "LEFT"
        self.next_direction = "LEFT"

        # Anti-stuck mechanism
        self.recent_positions = deque(maxlen=10)
        self.stuck_counter = 0
        self.last_position = (start_x, start_y)

        # Decision making
        self.decision_timer = 0
        self.last_known_player_pos = None
        self.exploration_bonus = {}
        self.danger_zones = set()

        self.uncollected_pellets = set()
        self.power_pellets_remaining = set()
        self.visited_cells_count = {}

        self.is_through_four_corners = False
        self.corner_been_through = set()
        self.four_corners_start_time = None
        self.four_corners_completion_time = None
        self.four_corners_duration = 0

        # Statistics
        self.algorithm_stats = {
            'bfs_steps': 0,
            'dfs_steps': 0,
            'astar_steps': 0,
            'ucs_steps': 0,
            'ghosts_eaten': 0,
            'deaths': 0,
            'power_pellets_used_effectively': 0,
        }

    def update(self):
        self.decision_timer += 1

    def add_recent_position(self, position):
        self.recent_positions.append(position)

    def is_position_recent(self, position):
        return position in self.recent_positions

    def initialize_pellets(self, maze):
        """Initializes the set of uncollected pellets and power pellets from the maze."""
        self.uncollected_pellets = set(maze.pellets)
        self.power_pellets_remaining = set(maze.power_pellets)
        # Khởi tạo visited_cells_count
        for y in range(maze.height):
            for x in range(maze.width):
                self.visited_cells_count[(x, y)] = 0

    def pellet_eaten(self, position):
        """Removes a pellet from the uncollected_pellets set."""
        if position in self.uncollected_pellets:
            self.uncollected_pellets.remove(position)
        if position in self.power_pellets_remaining:
            self.power_pellets_remaining.remove(position)

    def increment_visited_count(self, position):
        """Increments the visit count for a given cell."""
        self.visited_cells_count[position] = self.visited_cells_count.get(position, 0) + 1

    def add_corner_been_through(self, corner):
        """Adds a corner to the set of corners that have been traversed."""
        self.corner_been_through.add(corner)
        if len(self.corner_been_through) == 4:
            self.is_through_four_corners = True
            print("AI has been through all four corners of the maze.")