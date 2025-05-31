from abc import ABC, abstractmethod
from constants import DIRECTIONS
from collections import deque
import random


class BaseBehavior(ABC):

    def __init__(self, ai_player):
        self.ai_player = ai_player

    @abstractmethod
    def execute(self, maze, situation):
        """
        Execute the behavior logic based on the current maze and situation.
        This method should be implemented by subclasses to define specific behaviors.
        """
        pass

    def _manhattan_distance(self, a, b):
        """
        Calculate the Manhattan distance between two points.
        :param a: First point (x1, y1)
        :param b: Second point (x2, y2)
        :return: Manhattan distance
        """
        return abs(a[0] - b[0]) + abs(a[1] - b[1])

    def _set_direction_to_position(self, target_pos):
        """
        Set the entity's direction towards a target position.
        :param target_position: Target position (x, y)
        """
        current_pos = (self.ai_player.grid_x, self.ai_player.grid_y)
        dx = target_pos[0] - current_pos[0]
        dy = target_pos[1] - current_pos[1]

        if abs(dx) >= abs(dy):
            direction = "RIGHT" if dx > 0 else "LEFT"
        else:
            direction = "DOWN" if dy > 0 else "UP"

        self.ai_player.next_direction = direction

    def _find_nearest_pellet(self, maze):
        """Find the nearest pellet"""
        if not maze.pellets:
            return None

        current_pos = (self.ai_player.grid_x, self.ai_player.grid_y)
        return min(maze.pellets, key=lambda p: self._manhattan_distance(current_pos, p))

    def _enhanced_simple_ai(self, maze, situation):
        """Fallback behavior"""
        import random

        valid_directions = []
        for direction, (dx, dy) in DIRECTIONS.items():
            new_x = self.ai_player.grid_x + dx
            new_y = self.ai_player.grid_y + dy
            if maze.is_valid_position(new_x, new_y):
                valid_directions.append(direction)

        if valid_directions:
            self.ai_player.next_direction = random.choice(valid_directions)

    def _escape_from_ghosts(self, maze, ghost_distances):
        """Lựa chọn hướng di chuyển để tránh ma, đồng thời ưu tiên đi về phía pellet nếu không quá nguy hiểm."""

        LOOKAHEAD = 8  # Increased for better prediction

        def simulate_ghost_astar(maze, ghost_pos, target_pos):
            import heapq

            def heuristic(a, b):
                return abs(a[0] - b[0]) + abs(a[1] - b[1])

            open_set = [(0, ghost_pos, [ghost_pos], None)]  # (f_score, position, path, previous_direction)
            visited = {ghost_pos}

            while open_set and len(open_set) < 50:  # Limit computation
                f_score, current, path, prev_direction = heapq.heappop(open_set)

                if len(path) >= LOOKAHEAD:
                    return path[1:]  # Return path without start position

                for direction, (dx, dy) in DIRECTIONS.items():
                    neighbor = (current[0] + dx, current[1] + dy)

                    if not maze.is_valid_position(neighbor[0], neighbor[1]):
                        continue

                    if neighbor in visited:
                        continue

                    if prev_direction is not None:
                        # Apply no-reverse rule for ghosts
                        reverse_dirs = {"UP": "DOWN", "DOWN": "UP", "LEFT": "RIGHT", "RIGHT": "LEFT"}
                        if direction == reverse_dirs[prev_direction]:
                            continue

                    visited.add(neighbor)
                    new_path = path + [neighbor]
                    g_score = len(new_path) - 1
                    h_score = heuristic(neighbor, target_pos)
                    f_score = g_score + h_score

                    heapq.heappush(open_set, (f_score, neighbor, new_path, direction))

            return []

        def predict_ghost_positions_smart():
            future_positions = set()

            for (gx, gy), _ in ghost_distances:
                # Simulate ghost A* pathfinding behavior
                current_pos = (gx, gy)
                ai_pos = (self.ai_player.grid_x, self.ai_player.grid_y)

                # Ghosts use A* to chase, so predict their optimal path
                ghost_path = simulate_ghost_astar(maze, current_pos, ai_pos)

                # Add predicted positions along their path
                for i, pos in enumerate(ghost_path[:LOOKAHEAD]):
                    future_positions.add(pos)

                # Also add positions from greedy movement (fallback behavior)
                for direction, (dx, dy) in DIRECTIONS.items():
                    for step in range(1, LOOKAHEAD + 1):
                        nx, ny = gx + dx * step, gy + dy * step
                        if not maze.is_valid_position(nx, ny):
                            break
                        future_positions.add((nx, ny))

            return future_positions

        def get_escape_score(pos, depth):
            min_ghost_dist = min(self._manhattan_distance(pos, (gx, gy)) for (gx, gy), _ in ghost_distances)

            # Base safety score
            score = min_ghost_dist * 4

            # Heavy penalty for predicted ghost positions
            if pos in ghost_future_positions:
                score -= 150

            # Intersection penalty (ghosts can change direction here)
            neighbors = [(nx, ny) for nx, ny, _ in maze.get_neighbors(pos[0], pos[1]) if maze.is_valid_position(nx, ny)]
            if len(neighbors) >= 3:  # Intersection
                score -= 20

            # Tunnel bonus (ghosts can't easily change direction)
            elif len(neighbors) <= 1 and depth > 0:
                score += 10  # Actually beneficial in some cases

            # Corner bonus (forces ghost to make decision)
            elif len(neighbors) == 2:
                score += 5

            # Power pellet escape route
            power_pellets = maze.power_pellets
            if power_pellets and min_ghost_dist <= 4:
                nearest_power = min(power_pellets, key=lambda p: self._manhattan_distance(pos, p))
                power_dist = self._manhattan_distance(pos, nearest_power)
                score += max(0, 20 - power_dist * 2)

            # Endgame strategy - be more aggressive about collecting remaining pellets
            if min_ghost_dist > 3:
                remaining_pellets = maze.pellets
                if remaining_pellets:
                    nearest_pellet = min(remaining_pellets, key=lambda p: self._manhattan_distance(pos, p))
                    pellet_dist = self._manhattan_distance(pos, nearest_pellet)
                    score += max(0, 15 - pellet_dist)

            # Depth penalty
            score -= depth * 3

            return score

        # Predict ghost movements using their actual algorithm constraints
        ghost_future_positions = predict_ghost_positions_smart()

        # BFS with enhanced scoring
        start = (self.ai_player.grid_x, self.ai_player.grid_y)
        queue = deque([(start, [], 0)])
        visited = set([start])
        best_path, best_score = None, -float('inf')

        while queue:
            pos, path, depth = queue.popleft()

            if depth > LOOKAHEAD:
                continue

            score = get_escape_score(pos, depth)

            if score > best_score:
                best_score, best_path = score, path

            # Expand neighbors
            for nx, ny, _ in maze.get_neighbors(pos[0], pos[1]):
                if maze.is_valid_position(nx, ny) and (nx, ny) not in visited:
                    visited.add((nx, ny))
                    queue.append(((nx, ny), path + [(nx, ny)], depth + 1))

        # Execute best path
        if best_path and len(best_path) > 0:
            next_x, next_y = best_path[0]
            self._set_direction_to_position((next_x, next_y))
            return

        # Enhanced fallback with ghost constraint awareness
        best_dir, best_dir_score = None, -float('inf')
        for direction, (dx, dy) in DIRECTIONS.items():
            nx, ny = self.ai_player.grid_x + dx, self.ai_player.grid_y + dy
            if not maze.is_valid_position(nx, ny):
                continue

            score = get_escape_score((nx, ny), 1)

            # Bonus for moving to positions that force ghost direction changes
            neighbors = [(nnx, nny) for nnx, nny, _ in maze.get_neighbors(nx, ny) if maze.is_valid_position(nnx, nny)]
            if len(neighbors) >= 3:  # Intersection - ghost must choose
                score += 10

            if score > best_dir_score:
                best_dir_score, best_dir = score, direction

        if best_dir:
            self.next_direction = best_dir
        else:
            self._enhanced_simple_ai(maze, {})
