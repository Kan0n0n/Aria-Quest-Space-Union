from .base_behavior import BaseBehavior
import random
from constants import DIRECTIONS


class FourCornerProblemBehavior(BaseBehavior):
    def __init__(self, ai_player):
        super().__init__(ai_player)
        # Initialize missing attributes
        self.four_corners = []
        self.corners_initialized = False

    def execute(self, maze, situation):
        """Four corner problem behavior"""
        if not self.corners_initialized:
            self.four_corners = self._find_corners(maze)
            self.corners_initialized = True

        self.ai_player.is_invincible = True  # Always invincible in this mode

        # If we have all corners, try to navigate to them
        current_pos = (self.ai_player.grid_x, self.ai_player.grid_y)

        if self.four_corners:
            if current_pos in self.four_corners:
                # If already at a corner, choose a new corner to go to
                self.four_corners.remove(current_pos)
                self.ai_player.ai_state.add_corner_been_through(current_pos)

            # Find the nearest corner
            if len(self.four_corners) > 1:
                nearest_corner = min(self.four_corners, key=lambda corner: self._manhattan_distance(current_pos, corner))
            else:
                nearest_corner = self.four_corners[0] if self.four_corners else None
            if nearest_corner:
                # Set direction towards the nearest corner
                path = self.ai_player.pathfinding.find_path(maze, (self.ai_player.grid_x, self.ai_player.grid_y), nearest_corner, "astar")
                if path and len(path) > 1:
                    self.path = path
                    next_pos = path[1]
                    self._set_direction_to_position(next_pos)
                else:
                    # If pathfinding fails, fallback to basic movement
                    print("Pathfinding failed, falling back to basic movement.")
                    self._fallback_behavior(maze, situation)
            else:
                # If no corners are reachable, fallback to basic movement
                print("No reachable corners, falling back to basic movement.")
                self._fallback_behavior(maze, situation)
        else:
            # If no corners left, fallback to basic movement
            print("No corners left, falling back to basic movement.")
            self._fallback_behavior(maze, situation)

    def _find_corners(self, maze):
        corners = []
        width, height = maze.width, maze.height

        # Find first row that contains walkable cells (not walls)
        first_road_row = None
        for y in range(height):
            for x in range(width):
                if maze.is_valid_position(x, y):
                    first_road_row = y
                    break
            if first_road_row is not None:
                break

        # Find last row that contains walkable cells (not walls)
        last_road_row = None
        for y in range(height - 1, -1, -1):
            for x in range(width):
                if maze.is_valid_position(x, y):
                    last_road_row = y
                    break
            if last_road_row is not None:
                break

        # If we found valid rows, find the corners
        if first_road_row is not None and last_road_row is not None:
            # Find leftmost and rightmost valid positions in first row
            for x in range(width):
                if maze.is_valid_position(x, first_road_row):
                    corners.append((x, first_road_row))  # Top-left corner
                    break

            for x in range(width - 1, -1, -1):
                if maze.is_valid_position(x, first_road_row):
                    corners.append((x, first_road_row))  # Top-right corner
                    break

            # Find leftmost and rightmost valid positions in last row
            # Only add if it's different from first row
            if last_road_row != first_road_row:
                for x in range(width):
                    if maze.is_valid_position(x, last_road_row):
                        corners.append((x, last_road_row))  # Bottom-left corner
                        break

                for x in range(width - 1, -1, -1):
                    if maze.is_valid_position(x, last_road_row):
                        corners.append((x, last_road_row))  # Bottom-right corner
                        break

        # Remove duplicates while preserving order
        unique_corners = []
        for corner in corners:
            if corner not in unique_corners:
                unique_corners.append(corner)

        return unique_corners

    def _fallback_behavior(self, maze, situation):
        self._enhanced_simple_ai(maze, situation)

    def _enhanced_simple_ai(self, maze, situation):
        nearest_pellet = self._find_nearest_pellet(maze)

        if nearest_pellet:
            # Try to move towards nearest pellet
            best_direction = self._get_best_direction_for_target(maze, nearest_pellet)
            if best_direction:
                self.ai_player.next_direction = best_direction
                return

        # If no pellet or can't reach it, use basic movement
        valid_directions = []
        for direction, (dx, dy) in DIRECTIONS.items():
            new_x = self.ai_player.grid_x + dx
            new_y = self.ai_player.grid_y + dy
            if maze.is_valid_position(new_x, new_y):
                valid_directions.append(direction)

        if valid_directions:
            # Prefer continuing in current direction if possible
            if self.ai_player.direction in valid_directions:
                self.ai_player.next_direction = self.ai_player.direction
            else:
                import random

                self.ai_player.next_direction = random.choice(valid_directions)

    def _get_best_direction_for_target(self, maze, target):
        current_pos = (self.ai_player.grid_x, self.ai_player.grid_y)
        dx = target[0] - current_pos[0]
        dy = target[1] - current_pos[1]

        # Prioritize directions based on distance to target
        directions_to_try = []

        if abs(dx) >= abs(dy):
            if dx > 0:
                directions_to_try.append("RIGHT")
            elif dx < 0:
                directions_to_try.append("LEFT")
            if dy > 0:
                directions_to_try.append("DOWN")
            elif dy < 0:
                directions_to_try.append("UP")
        else:
            if dy > 0:
                directions_to_try.append("DOWN")
            elif dy < 0:
                directions_to_try.append("UP")
            if dx > 0:
                directions_to_try.append("RIGHT")
            elif dx < 0:
                directions_to_try.append("LEFT")

        # Try each direction in priority order
        for direction in directions_to_try:
            if direction in DIRECTIONS:
                new_dx, new_dy = DIRECTIONS[direction]
                new_x = self.ai_player.grid_x + new_dx
                new_y = self.ai_player.grid_y + new_dy
                if maze.is_valid_position(new_x, new_y):
                    return direction

        return None
