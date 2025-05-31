from .base_behavior import BaseBehavior
import random
from constants import DIRECTIONS


class SimpleBFSBehavior(BaseBehavior):
    def execute(self, maze, situation):
        """Simple BFS-based behavior"""
        # Add ghost escape check
        if not situation.get('has_power') and situation.get('ghost_distances'):
            min_ghost_distance = min(dist for _, dist in situation['ghost_distances'])
            if min_ghost_distance <= 4 and not self.ai_player.is_invincible:
                self._escape_from_ghosts(maze, situation['ghost_distances'])
                return

        target = situation.get('nearest_pellet')
        if target:
            path = self.ai_player.pathfinding.find_path(maze, (self.ai_player.grid_x, self.ai_player.grid_y), target, "bfs")
            if path and len(path) > 1:
                next_pos = path[1]
                self._set_direction_to_position(next_pos)
            else:
                self._random_movement(maze)
        else:
            self._random_movement(maze)

    def _random_movement(self, maze):
        """Fallback random movement"""
        valid_directions = []
        for direction, (dx, dy) in DIRECTIONS.items():
            new_x = self.ai_player.grid_x + dx
            new_y = self.ai_player.grid_y + dy
            if maze.is_valid_position(new_x, new_y):
                valid_directions.append(direction)

        if valid_directions:
            self.ai_player.next_direction = random.choice(valid_directions)


class SimpleDFSBehavior(BaseBehavior):
    def execute(self, maze, situation):
        """Simple DFS-based behavior"""
        # Add ghost escape check
        if not situation.get('has_power') and situation.get('ghost_distances'):
            min_ghost_distance = min(dist for _, dist in situation['ghost_distances'])
            if min_ghost_distance <= 4 and not self.ai_player.is_invincible:
                self._escape_from_ghosts(maze, situation['ghost_distances'])
                return

        target = situation.get('nearest_pellet')
        if target:
            path = self.ai_player.pathfinding.find_path(maze, (self.ai_player.grid_x, self.ai_player.grid_y), target, "dfs")
            if path and len(path) > 1:
                next_pos = path[1]
                self._set_direction_to_position(next_pos)
            else:
                self._random_movement(maze)
        else:
            self._random_movement(maze)

    def _random_movement(self, maze):
        """Fallback random movement"""
        valid_directions = []
        for direction, (dx, dy) in DIRECTIONS.items():
            new_x = self.ai_player.grid_x + dx
            new_y = self.ai_player.grid_y + dy
            if maze.is_valid_position(new_x, new_y):
                valid_directions.append(direction)

        if valid_directions:
            self.ai_player.next_direction = random.choice(valid_directions)


class SimpleAStarBehavior(BaseBehavior):
    def execute(self, maze, situation):
        """Simple A*-based behavior"""
        # Add ghost escape check
        if not situation.get('has_power') and situation.get('ghost_distances'):
            min_ghost_distance = min(dist for _, dist in situation['ghost_distances'])
            if min_ghost_distance <= 4 and not self.ai_player.is_invincible:
                self._escape_from_ghosts(maze, situation['ghost_distances'])
                return

        target = situation.get('nearest_pellet')
        if target:
            path = self.ai_player.pathfinding.find_path(maze, (self.ai_player.grid_x, self.ai_player.grid_y), target, "astar")
            if path and len(path) > 1:
                next_pos = path[1]
                self._set_direction_to_position(next_pos)
            else:
                self._random_movement(maze)
        else:
            self._random_movement(maze)

    def _random_movement(self, maze):
        """Fallback random movement"""
        valid_directions = []
        for direction, (dx, dy) in DIRECTIONS.items():
            new_x = self.ai_player.grid_x + dx
            new_y = self.ai_player.grid_y + dy
            if maze.is_valid_position(new_x, new_y):
                valid_directions.append(direction)

        if valid_directions:
            self.ai_player.next_direction = random.choice(valid_directions)


class SimpleUCSBehavior(BaseBehavior):
    def execute(self, maze, situation):
        """Simple UCS-based behavior"""
        # Add ghost escape check
        if not situation.get('has_power') and situation.get('ghost_distances'):
            min_ghost_distance = min(dist for _, dist in situation['ghost_distances'])
            if min_ghost_distance <= 4 and not self.ai_player.is_invincible:
                self._escape_from_ghosts(maze, situation['ghost_distances'])
                return

        target = situation.get('nearest_pellet')
        if target:
            path = self.ai_player.pathfinding.find_path(maze, (self.ai_player.grid_x, self.ai_player.grid_y), target, "ucs")
            if path and len(path) > 1:
                next_pos = path[1]
                self._set_direction_to_position(next_pos)
            else:
                self._random_movement(maze)
        else:
            self._random_movement(maze)

    def _random_movement(self, maze):
        """Fallback random movement"""
        valid_directions = []
        for direction, (dx, dy) in DIRECTIONS.items():
            new_x = self.ai_player.grid_x + dx
            new_y = self.ai_player.grid_y + dy
            if maze.is_valid_position(new_x, new_y):
                valid_directions.append(direction)

        if valid_directions:
            self.ai_player.next_direction = random.choice(valid_directions)
