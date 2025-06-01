class DecisionMaker:

    def __init__(self, ai_player):
        self.ai_player = ai_player

    def analyze_situation(self, maze, player_position, ghosts_positions):
        """Analyze the current game situation"""
        situation = {
            'has_power': self.ai_player.power_timer > 0,
            'power_time_left': self.ai_player.power_timer,
            'nearest_pellet': self._find_nearest_pellet(maze),
            'nearest_power_pellet': self._find_nearest_power_pellet(maze),
            'player_distance': float('inf'),
            'player_position': player_position,
            'ghost_distances': [],
            'immediate_danger': False,
            'all_pellets_collected': not self.ai_player.ai_state.uncollected_pellets,  # Trạng thái tất cả đã ăn
            'pellets_left_count': len(self.ai_player.ai_state.uncollected_pellets),
            'power_pellets_left_count': len(self.ai_player.ai_state.power_pellets_remaining),
            'uncollected_pellets': self.ai_player.ai_state.uncollected_pellets,  # Đưa vào situation
            'power_pellets_remaining': self.ai_player.ai_state.power_pellets_remaining,  # Đưa vào situation
        }

        if player_position:
            situation['player_distance'] = self._manhattan_distance((self.ai_player.grid_x, self.ai_player.grid_y), player_position)

        if ghosts_positions:
            for ghost_pos in ghosts_positions:
                distance = self._manhattan_distance((self.ai_player.grid_x, self.ai_player.grid_y), ghost_pos)
                situation['ghost_distances'].append((ghost_pos, distance))

            # Check for immediate danger
            min_ghost_dist = min(dist for _, dist in situation['ghost_distances'])
            situation['immediate_danger'] = min_ghost_dist <= 4 and not self.ai_player.is_invincible

        return situation

    def _manhattan_distance(self, pos1, pos2):
        return abs(pos1[0] - pos2[0]) + abs(pos1[1] - pos2[1])

    # Find the nearest pellet using Manhattan distance
    def _find_nearest_pellet(self, maze):
        if not maze.pellets:
            return None

        current_pos = (self.ai_player.grid_x, self.ai_player.grid_y)
        return min(maze.pellets, key=lambda p: self._manhattan_distance(current_pos, p))

    # Find the nearest pellet using pathfinding
    def _find_nearest_pellet_by_path(self, maze):
        if not maze.pellets:
            return None

        current_pos = (self.ai_player.grid_x, self.ai_player.grid_y)

        # Sử dụng BFS để tìm đường đi đến tất cả các viên chấm
        # và chọn viên có đường đi ngắn nhất
        shortest_path_length = float('inf')
        nearest_pellet_pos = None

        for pellet_pos in maze.pellets:
            path = self.ai_player.pathfinding.find_path(maze, current_pos, pellet_pos, algorithm="bfs")  # hoặc "ucs", "astar"
            if path and len(path) - 1 < shortest_path_length:  # len(path)-1 vì path bao gồm cả điểm bắt đầu
                shortest_path_length = len(path) - 1
                nearest_pellet_pos = pellet_pos
        return nearest_pellet_pos

    def _find_nearest_power_pellet(self, maze):
        if not maze.power_pellets:
            return None

        current_pos = (self.ai_player.grid_x, self.ai_player.grid_y)
        return min(maze.power_pellets, key=lambda p: self._manhattan_distance(current_pos, p))

    def _find_nearest_uncollected_pellet(self, maze):
        if not self.ai_player.ai_state.uncollected_pellets:
            return None
        current_pos = (self.ai_player.grid_x, self.ai_player.grid_y)
        return min(self.ai_player.ai_state.uncollected_pellets, key=lambda p: self._manhattan_distance(current_pos, p))
