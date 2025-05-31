from .base_behavior import BaseBehavior
from constants import DIRECTIONS
import random


class CompetitiveBehavior(BaseBehavior):
    def execute(self, maze, situation):
        """Competitive behavior that tries to outperform the human player"""
        # Check if we should compete directly with player
        if not situation.get('has_power'):
            min_ghost_distance = min(dist for _, dist in situation['ghost_distances'])
            if min_ghost_distance <= 4 and not self.ai_player.is_invincible:
                self._escape_from_ghosts(maze, situation['ghost_distances'])  # Now uses base class method
                return

        if self._should_compete_with_player(situation):
            self._competitive_strategy(maze, situation)
        else:
            # Fall back to smart hunting
            self._smart_fallback(maze, situation)

    def _should_compete_with_player(self, situation):
        """Decide whether to compete directly with player"""
        player_distance = situation.get('player_distance', float('inf'))
        return player_distance <= 5 and player_distance != float('inf') and not situation.get('immediate_danger', False)

    def _competitive_strategy(self, maze, situation):
        """Direct competition strategy"""
        if situation.get('nearest_pellet'):
            # Try to reach the nearest pellet before the player
            player_pos = situation.get('player_position', (0, 0))
            player_to_pellet = self._manhattan_distance(player_pos, situation['nearest_pellet'])
            ai_to_pellet = self._manhattan_distance((self.ai_player.grid_x, self.ai_player.grid_y), situation['nearest_pellet'])

            if ai_to_pellet <= player_to_pellet:
                # We can reach it faster, go for it
                self._hunt_target(maze, situation['nearest_pellet'])
            else:
                # Look for alternative targets
                self._find_alternative_target(maze)

    def _smart_fallback(self, maze, situation):
        """Fallback to smart hunting if direct competition is not viable"""
        if situation.get('has_power'):
            # If we have power, hunt ghosts
            self._hunt_ghosts(maze, situation)
        else:
            # Otherwise, find the nearest pellet or power pellet
            target = situation.get('nearest_pellet') or situation.get('nearest_power_pellet')
            if target:
                self._hunt_target(maze, target)
            else:
                # No targets available, fallback to exploration
                self._explore(maze)

    def _hunt_target(self, maze, target):
        """Hunt a specific target using pathfinding"""
        path = self.ai_player.pathfinding.find_path(maze, (self.ai_player.grid_x, self.ai_player.grid_y), target, "bfs")
        if path and len(path) > 1:
            self.ai_player.ai_state.path = path
            next_pos = path[1]
            self._set_direction_to_position(next_pos)
        else:
            # Fallback: use direct direction calculation
            self.ai_player.ai_state.path = []
            best_direction = self._get_best_direction_for_target(maze, target)
            if best_direction:
                self.ai_player.next_direction = best_direction
            else:
                self._enhanced_simple_ai(maze, {})

    def _hunt_ghosts(self, maze, situation):
        """Hunt ghosts when in power mode"""
        ghost_distances = situation.get('ghost_distances', [])
        if not ghost_distances:
            return

        # Find the closest ghost
        closest_ghost = min(ghost_distances, key=lambda x: x[1])[0]
        self._hunt_target(maze, closest_ghost)

    def _find_alternative_target(self, maze):
        """Find an alternative target"""
        # Look for the nearest pellet or power pellet
        nearest_pellet = self._find_nearest_pellet(maze)
        nearest_power_pellet = self._find_nearest_power_pellet(maze)

        if nearest_pellet:
            self._hunt_target(maze, nearest_pellet)
        elif nearest_power_pellet:
            self._hunt_target(maze, nearest_power_pellet)
        else:
            self._explore(maze)

    def _find_nearest_power_pellet(self, maze):
        """Find nearest power pellet"""
        if not maze.power_pellets:
            return None

        current_pos = (self.ai_player.grid_x, self.ai_player.grid_y)
        return min(maze.power_pellets, key=lambda p: self._manhattan_distance(current_pos, p))

    def _explore(self, maze):
        """Explore the maze"""
        self._enhanced_simple_ai(maze, {})

    def _get_best_direction_for_target(self, maze, target_pos):
        """Get the best direction to move towards a target position"""
        if not target_pos:
            return None

        target_x, target_y = target_pos
        current_x, current_y = self.ai_player.grid_x, self.ai_player.grid_y

        # Calculate direction preferences based on target
        dx = target_x - current_x
        dy = target_y - current_y

        preferred_directions = []

        # Prioritize horizontal movement if target is farther horizontally
        if abs(dx) >= abs(dy):
            if dx > 0:
                preferred_directions.append("RIGHT")
            elif dx < 0:
                preferred_directions.append("LEFT")
            if dy > 0:
                preferred_directions.append("DOWN")
            elif dy < 0:
                preferred_directions.append("UP")
        else:
            # Prioritize vertical movement if target is farther vertically
            if dy > 0:
                preferred_directions.append("DOWN")
            elif dy < 0:
                preferred_directions.append("UP")
            if dx > 0:
                preferred_directions.append("RIGHT")
            elif dx < 0:
                preferred_directions.append("LEFT")

        # Find the first valid direction from our preferences
        for direction in preferred_directions:
            test_dx, test_dy = DIRECTIONS[direction]
            new_x = current_x + test_dx
            new_y = current_y + test_dy
            if maze.is_valid_position(new_x, new_y):
                return direction

        return None
