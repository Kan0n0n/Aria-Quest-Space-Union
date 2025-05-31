from .base_behavior import BaseBehavior
from constants import DIRECTIONS


class SmartHunterBehavior(BaseBehavior):
    def __init__(self, ai_player):
        super().__init__(ai_player)
        # Initialize missing attributes
        self.exploration_bonus = {}  # Track exploration bonuses for positions

    def execute(self, maze, situation):
        # Check for immediate ghost threats
        if not situation.get('has_power') and situation.get('ghost_distances'):
            min_ghost_distance = min(dist for _, dist in situation['ghost_distances'])
            if min_ghost_distance <= 4 and not self.ai_player.is_invincible:
                self._escape_from_ghosts(maze, situation['ghost_distances'])
                return

        # Use A* to find optimal path to nearest valuable target
        target = self._select_optimal_target(maze, situation)
        if target:
            path = self.ai_player.pathfinding.find_path(
                maze, (self.ai_player.grid_x, self.ai_player.grid_y), target, "astar", situation.get('ghost_distances', [])
            )
            if path and len(path) > 1:
                self.ai_player.ai_state.path = path
                next_pos = path[1]
                self._set_direction_to_position(next_pos)
            else:
                self._fallback_behavior(maze, situation)
        else:
            self._fallback_behavior(maze, situation)

    def _select_optimal_target(self, maze, situation):
        targets = []

        # Add ghost targets with priority
        if situation.get('has_power'):
            if situation.get('ghost_distances'):
                # Prioritize ghosts when in power mode
                for ghost_pos, _ in situation['ghost_distances']:
                    distance = self._manhattan_distance((self.ai_player.grid_x, self.ai_player.grid_y), ghost_pos)
                    value = 100 / (distance + 1)
                    targets.append((ghost_pos, value, 'ghost'))

        # Add regular pellets
        for pellet_pos in maze.pellets:
            distance = self._manhattan_distance((self.ai_player.grid_x, self.ai_player.grid_y), pellet_pos)
            value = 10 / (distance + 1)  # Closer = higher value
            targets.append((pellet_pos, value, 'pellet'))

        # Add power pellets with higher priority
        for pellet_pos in maze.power_pellets:
            distance = self._manhattan_distance((self.ai_player.grid_x, self.ai_player.grid_y), pellet_pos)
            value = 50 / (distance + 1)  # Much higher value
            targets.append((pellet_pos, value, 'power'))

        # Add exploration bonuses
        for pos, bonus in self.exploration_bonus.items():
            if maze.is_valid_position(pos[0], pos[1]):
                distance = self._manhattan_distance((self.ai_player.grid_x, self.ai_player.grid_y), pos)
                value = bonus / (distance + 1)
                targets.append((pos, value, 'explore'))

        if targets:
            # Return the highest value target
            best_target = max(targets, key=lambda x: x[1])
            return best_target[0]
        return None

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
