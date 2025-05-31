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
