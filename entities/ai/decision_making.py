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

    def _find_nearest_pellet(self, maze):
        if not maze.pellets:
            return None

        current_pos = (self.ai_player.grid_x, self.ai_player.grid_y)
        return min(maze.pellets, key=lambda p: self._manhattan_distance(current_pos, p))

    def _find_nearest_power_pellet(self, maze):
        if not maze.power_pellets:
            return None

        current_pos = (self.ai_player.grid_x, self.ai_player.grid_y)
        return min(maze.power_pellets, key=lambda p: self._manhattan_distance(current_pos, p))
