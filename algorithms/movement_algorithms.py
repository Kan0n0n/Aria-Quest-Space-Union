import math
import random
import heapq
from collections import deque
from constants import *


class MovementAlgorithms:
    @staticmethod
    def heuristic(a, b):
        return abs(a[0] - b[0]) + abs(a[1] - b[1])

    @staticmethod
    def get_neighbors(maze, pos):
        neighbors = []
        x, y = pos
        for direction in ["UP", "DOWN", "LEFT", "RIGHT"]:
            dx, dy = DIRECTIONS[direction]
            new_x, new_y = x + dx, y + dy
            if maze.is_valid_position(new_x, new_y):
                neighbors.append((new_x, new_y))
        return neighbors

    @staticmethod
    def a_star_pathfinding(maze, start, goal, avoid_positions=None):
        if not goal or start == goal:
            return []

        avoid_positions = avoid_positions or set()

        # Priority queue: (f_score, g_score, position, path)
        open_set = [(0, 0, start, [])]
        closed_set = set()
        iterations = 0
        max_iterations = 500  # Reduced for performance

        while open_set and iterations < max_iterations:
            iterations += 1
            f_score, g_score, current, path = heapq.heappop(open_set)

            if current in closed_set:
                continue

            closed_set.add(current)
            new_path = path + [current]

            # Found goal
            if current == goal:
                result_path = new_path[1:]  # Exclude starting position
                return result_path

            # Explore neighbors
            neighbors = MovementAlgorithms.get_neighbors(maze, current)
            for neighbor in neighbors:
                if neighbor in closed_set:
                    continue

                # Check if neighbor is in avoid positions
                should_avoid = False
                penalty = 0

                for avoid_pos in avoid_positions:
                    if avoid_pos and neighbor == avoid_pos:
                        should_avoid = True
                        break
                    elif avoid_pos:
                        # Add penalty for being close to avoided positions
                        distance_to_avoid = MovementAlgorithms.heuristic(neighbor, avoid_pos)
                        if distance_to_avoid <= 2:
                            penalty += (3 - distance_to_avoid) * 20

                if should_avoid:
                    continue

                new_g_score = g_score + 1
                h_score = MovementAlgorithms.heuristic(neighbor, goal)
                new_f_score = new_g_score + h_score + penalty

                heapq.heappush(open_set, (new_f_score, new_g_score, neighbor, new_path))

        return []  # No path found

    @staticmethod
    def find_safe_escape_path(maze, current_pos, threat_positions, min_distance=5):
        # First, try to find a safe pellet position
        best_pellet = None
        max_min_distance = 0

        for pellet_pos in list(maze.pellets) + list(maze.power_pellets):
            min_threat_distance = float('inf')
            for threat_pos in threat_positions:
                if threat_pos:
                    distance = MovementAlgorithms.heuristic(pellet_pos, threat_pos)
                    min_threat_distance = min(min_threat_distance, distance)
            if min_threat_distance >= min_distance and min_threat_distance > max_min_distance:
                max_min_distance = min_threat_distance
                best_pellet = pellet_pos

        if best_pellet:
            threat_set = {pos for pos in threat_positions if pos}
            return MovementAlgorithms.a_star_pathfinding(maze, current_pos, best_pellet, threat_set)

        # Fallback: original logic (any safe cell)
        best_escape_pos = None
        max_min_distance = 0
        for x in range(maze.width):
            for y in range(maze.height):
                if not maze.is_valid_position(x, y):
                    continue
                min_threat_distance = float('inf')
                for threat_pos in threat_positions:
                    if threat_pos:
                        distance = MovementAlgorithms.heuristic((x, y), threat_pos)
                        min_threat_distance = min(min_threat_distance, distance)
                if min_threat_distance >= min_distance and min_threat_distance > max_min_distance:
                    max_min_distance = min_threat_distance
                    best_escape_pos = (x, y)
        if best_escape_pos:
            threat_set = {pos for pos in threat_positions if pos}
            return MovementAlgorithms.a_star_pathfinding(maze, current_pos, best_escape_pos, threat_set)

        return []

    @staticmethod
    def get_escape_directions(maze, current_pos, threat_pos):
        current_x, current_y = current_pos
        threat_x, threat_y = threat_pos

        # Calculate vector away from threat
        escape_directions = []

        # Prefer directions that increase distance from threat
        for direction, (dx, dy) in DIRECTIONS.items():
            new_x = current_x + dx
            new_y = current_y + dy

            if maze.is_valid_position(new_x, new_y):
                # Calculate if this direction increases distance from threat
                current_distance = MovementAlgorithms.heuristic(current_pos, threat_pos)
                new_distance = MovementAlgorithms.heuristic((new_x, new_y), threat_pos)

                if new_distance > current_distance:
                    escape_directions.append(direction)

        return escape_directions

    @staticmethod
    def find_nearest_pellet(maze, current_pos, avoid_positions=None, blacklist=None, force_from_blacklist=False, prefer_last_blacklisted=False):
        avoid_positions = avoid_positions or set()
        blacklist = blacklist or set()
        current_x, current_y = current_pos

        # Get all available pellets
        all_pellets = []

        if force_from_blacklist and blacklist:
            # Only consider blacklisted pellets
            if prefer_last_blacklisted:
                # Get the most recently blacklisted pellet that still exists
                for pellet_pos in reversed(list(blacklist)):
                    if pellet_pos in maze.pellets or pellet_pos in maze.power_pellets:
                        if pellet_pos not in avoid_positions:
                            return pellet_pos
            else:
                # Consider all blacklisted pellets
                for pellet_pos in blacklist:
                    if pellet_pos in maze.pellets and pellet_pos not in avoid_positions:
                        all_pellets.append((pellet_pos, 1))
                    elif pellet_pos in maze.power_pellets and pellet_pos not in avoid_positions:
                        all_pellets.append((pellet_pos, 2))
        else:
            # Normal operation - exclude blacklisted pellets
            # Add regular pellets
            for pellet_pos in maze.pellets:
                if pellet_pos not in avoid_positions and pellet_pos not in blacklist:
                    all_pellets.append((pellet_pos, 1))  # (position, priority)

            # Add power pellets with higher priority
            for pellet_pos in maze.power_pellets:
                if pellet_pos not in avoid_positions and pellet_pos not in blacklist:
                    all_pellets.append((pellet_pos, 2))  # Higher priority for power pellets

        if not all_pellets:
            if not force_from_blacklist and blacklist:
                # No non-blacklisted pellets available, try from blacklist
                print("No non-blacklisted pellets available, trying from blacklist")
                return MovementAlgorithms.find_nearest_pellet(
                    maze, current_pos, avoid_positions, blacklist, force_from_blacklist=True, prefer_last_blacklisted=True
                )
            return None

        # Find reachable pellets with valid paths
        reachable_pellets = []

        for pellet_pos, priority in all_pellets:
            # Quick distance check first
            distance = MovementAlgorithms.heuristic(current_pos, pellet_pos)

            # Skip pellets that are very far away to improve performance
            if distance > 20:
                continue

            # Check if we can actually reach this pellet
            test_path = MovementAlgorithms.a_star_pathfinding(maze, current_pos, pellet_pos, avoid_positions)

            if test_path:  # Only consider pellets we can actually reach
                # Calculate actual path cost vs straight-line distance
                path_cost = len(test_path)
                efficiency = distance / path_cost if path_cost > 0 else 0

                # Score based on distance, priority, and path efficiency
                score = (priority * 100) + (50 - distance) + (efficiency * 10)

                reachable_pellets.append((pellet_pos, score, distance, test_path))

        if not reachable_pellets:
            # No reachable pellets found, try to find the closest one without avoid_positions
            print(f"No reachable pellets found with avoidance, trying without restrictions")
            return MovementAlgorithms.find_nearest_pellet_simple(maze, current_pos)

        # Sort by score (highest first), then by distance (lowest first)
        reachable_pellets.sort(key=lambda x: (-x[1], x[2]))

        best_pellet = reachable_pellets[0][0]
        pellet_type = "blacklisted" if force_from_blacklist else "normal"
        print(f"Found best reachable {pellet_type} pellet at {best_pellet} (score: {reachable_pellets[0][1]:.1f})")

        return best_pellet

    @staticmethod
    def find_nearest_pellet_simple(maze, current_pos):
        nearest = None
        min_distance = float("inf")
        current_x, current_y = current_pos

        # Check regular pellets
        for pellet_pos in maze.pellets:
            distance = abs(current_x - pellet_pos[0]) + abs(current_y - pellet_pos[1])
            if distance < min_distance:
                min_distance = distance
                nearest = pellet_pos

        # Check power pellets (higher priority)
        for pellet_pos in maze.power_pellets:
            distance = abs(current_x - pellet_pos[0]) + abs(current_y - pellet_pos[1])
            if distance < min_distance * 1.5:  # Give power pellets priority
                min_distance = distance
                nearest = pellet_pos

        return nearest

    @staticmethod
    def position_to_direction(current_pos, target_pos):
        current_x, current_y = current_pos
        target_x, target_y = target_pos

        dx = target_x - current_x
        dy = target_y - current_y

        if dx > 0:
            return "RIGHT"
        elif dx < 0:
            return "LEFT"
        elif dy > 0:
            return "DOWN"
        elif dy < 0:
            return "UP"

        return None

    @staticmethod
    def get_random_valid_direction(maze, current_pos, current_direction=None):
        current_x, current_y = current_pos
        valid_directions = []

        for direction, (dx, dy) in DIRECTIONS.items():
            new_x = current_x + dx
            new_y = current_y + dy
            if maze.is_valid_position(new_x, new_y):
                valid_directions.append(direction)

        if valid_directions:
            # Prefer continuing in the same direction if possible
            if current_direction and current_direction in valid_directions and random.random() < 0.7:
                return current_direction
            else:
                return random.choice(valid_directions)

        return None

    @staticmethod
    def calculate_threat_level(current_pos, threat_positions, threat_ranges):
        threat_level = 0

        for i, threat_pos in enumerate(threat_positions):
            if threat_pos:
                distance = MovementAlgorithms.heuristic(current_pos, threat_pos)
                threat_range = threat_ranges[i] if i < len(threat_ranges) else 5

                if distance <= threat_range:
                    # Closer threats are more dangerous
                    threat_level += (threat_range - distance + 1) * 10

        return threat_level

    @staticmethod
    def is_dead_end(maze, pos):
        neighbors = 0
        x, y = pos
        for dx, dy in DIRECTIONS.values():
            if maze.is_valid_position(x + dx, y + dy):
                neighbors += 1
        return neighbors == 1

    @staticmethod
    def find_power_pellet(maze, current_pos):
        """Find the nearest power pellet"""
        nearest = None
        min_distance = float("inf")
        current_x, current_y = current_pos

        for pellet_pos in maze.power_pellets:
            distance = MovementAlgorithms.heuristic(current_pos, pellet_pos)
            if distance < min_distance:
                min_distance = distance
                nearest = pellet_pos

        return nearest


class AIPlayerMovementStrategy:
    def __init__(self, ai_instance):
        self.ai = ai_instance
        self.algorithms = MovementAlgorithms()
        self.available_strategies = [
            "simple_random",
            "pellet_hunter_safe",
            "pellet_hunter_aggressive",
            "ghost_avoider",
            "power_pellet_hunter",
            "explorer_cautious",
            "competitive_smart",
        ]
        self.current_strategy = "pellet_hunter_safe"  # Default strategy

        # Threat detection parameters
        self.ghost_detection_range = 8
        self.danger_zone_range = 5
        self.flee_priority_distance = 3

    def execute_strategy(self, maze, player_position=None, ghost_positions=None, is_invincible=False):
        ghost_positions = ghost_positions or []

        # Filter out None positions
        active_ghost_positions = [pos for pos in ghost_positions if pos is not None]

        # Calculate current threat level
        threat_level = self.algorithms.calculate_threat_level(
            (self.ai.grid_x, self.ai.grid_y), active_ghost_positions, [self.ghost_detection_range] * len(active_ghost_positions)
        )

        # Check if all pellets are problematic - if so, be more aggressive even with ghosts
        total_pellets = len(maze.pellets) + len(maze.power_pellets)
        all_pellets_problematic = hasattr(self.ai, 'problematic_pellets') and len(self.ai.problematic_pellets) >= total_pellets

        # Override strategy if in immediate danger and not invincible, BUT only if we have non-problematic options
        if not is_invincible and threat_level > 20 and not all_pellets_problematic:
            print(f"AI {self.ai.player_id}: Emergency escape triggered (threat: {threat_level})")
            return self._emergency_escape_strategy(maze, active_ghost_positions)

        # If all pellets are problematic, force pellet_hunter_safe strategy regardless of danger
        if all_pellets_problematic:
            print(f"AI {self.ai.player_id}: All pellets problematic, forcing pellet hunting despite danger")
            return self._pellet_hunter_safe_strategy(maze, active_ghost_positions, is_invincible)

        # Execute selected strategy
        if self.current_strategy == "simple_random":
            return self._simple_random_strategy(maze)
        elif self.current_strategy == "pellet_hunter_safe":
            return self._pellet_hunter_safe_strategy(maze, active_ghost_positions, is_invincible)
        elif self.current_strategy == "pellet_hunter_aggressive":
            return self._pellet_hunter_aggressive_strategy(maze, active_ghost_positions, is_invincible)
        elif self.current_strategy == "ghost_avoider":
            return self._ghost_avoider_strategy(maze, active_ghost_positions)
        elif self.current_strategy == "power_pellet_hunter":
            return self._power_pellet_hunter_strategy(maze, active_ghost_positions, is_invincible)
        elif self.current_strategy == "explorer_cautious":
            return self._explorer_cautious_strategy(maze, active_ghost_positions, is_invincible)
        elif self.current_strategy == "competitive_smart":
            return self._competitive_smart_strategy(maze, player_position, active_ghost_positions, is_invincible)
        else:
            return self._simple_random_strategy(maze)

    def set_strategy(self, strategy_name):
        if strategy_name in self.available_strategies:
            self.current_strategy = strategy_name
            self.ai.path = []
            print(f"AI Player {self.ai.player_id} switched to strategy: {strategy_name}")
            return True
        return False

    def cycle_strategy(self):
        current_index = self.available_strategies.index(self.current_strategy)
        next_index = (current_index + 1) % len(self.available_strategies)
        self.set_strategy(self.available_strategies[next_index])

    def _emergency_escape_strategy(self, maze, ghost_positions):
        # Check if all pellets are problematic - if so, use the same logic as normal mode
        total_pellets = len(maze.pellets) + len(maze.power_pellets)
        all_pellets_problematic = hasattr(self.ai, 'problematic_pellets') and len(self.ai.problematic_pellets) >= total_pellets

        if all_pellets_problematic:
            print(f"AI {self.ai.player_id}: Emergency escape cancelled - all pellets are problematic, must continue hunting")
            return self._pellet_hunter_safe_strategy(maze, ghost_positions, False)

        print(f"AI {self.ai.player_id}: Executing emergency escape")

        # Try to find safe pellets first (non-problematic ones that are far from ghosts)
        avoid_positions = set(pos for pos in ghost_positions if pos)

        # Add problematic pellets to avoid list during emergency
        if hasattr(self.ai, 'problematic_pellets'):
            for pellet in self.ai.problematic_pellets:
                if pellet in maze.pellets or pellet in maze.power_pellets:
                    avoid_positions.add(pellet)

        # Try to find a safe, non-problematic pellet
        safe_target = self.algorithms.find_nearest_pellet(
            maze, (self.ai.grid_x, self.ai.grid_y), avoid_positions, self.ai.problematic_pellets if hasattr(self.ai, 'problematic_pellets') else set()
        )

        if safe_target:
            path = self.algorithms.a_star_pathfinding(maze, (self.ai.grid_x, self.ai.grid_y), safe_target, avoid_positions)
            if path:
                self.ai.path = path
                self.ai.current_path_index = 0
                print(f"AI {self.ai.player_id}: Emergency escape to safe pellet at {safe_target}")
                return True

        # If no safe pellet target, try general escape path
        escape_path = self.algorithms.find_safe_escape_path(maze, (self.ai.grid_x, self.ai.grid_y), ghost_positions, self.flee_priority_distance)

        if escape_path:
            self.ai.path = escape_path
            self.ai.current_path_index = 0
            return True

        # If no escape path found, try immediate evasion
        for ghost_pos in ghost_positions:
            if ghost_pos:
                distance = self.algorithms.heuristic((self.ai.grid_x, self.ai.grid_y), ghost_pos)
                if distance <= self.danger_zone_range:
                    escape_directions = self.algorithms.get_escape_directions(maze, (self.ai.grid_x, self.ai.grid_y), ghost_pos)
                    if escape_directions:
                        direction = escape_directions[0]
                        if direction:
                            self.ai.next_direction = direction
                            return True

        return self._simple_random_strategy(maze)

    def _simple_random_strategy(self, maze):
        direction = self.algorithms.get_random_valid_direction(maze, (self.ai.grid_x, self.ai.grid_y), self.ai.direction)
        if direction:
            self.ai.next_direction = direction
            return True
        return False

    def _pellet_hunter_safe_strategy(self, maze, ghost_positions, is_invincible):
        # Check if all pellets are problematic
        total_pellets = len(maze.pellets) + len(maze.power_pellets)
        all_pellets_problematic = hasattr(self.ai, 'problematic_pellets') and len(self.ai.problematic_pellets) >= total_pellets

        # Adjust ghost avoidance based on desperation level
        if all_pellets_problematic:
            # Very desperate - only avoid ghosts that are extremely close
            avoid_positions = set()
            if not is_invincible:
                for ghost_pos in ghost_positions:
                    if ghost_pos:
                        distance = self.algorithms.heuristic((self.ai.grid_x, self.ai.grid_y), ghost_pos)
                        if distance <= 1:  # Only avoid if touching
                            avoid_positions.add(ghost_pos)
            print(f"AI {self.ai.player_id}: Desperate mode - only avoiding {len(avoid_positions)} very close ghosts")
        else:
            # Normal ghost avoidance
            avoid_positions = set() if is_invincible else set(pos for pos in ghost_positions if pos)

        # Add blacklist for pellets that caused problems
        if not hasattr(self.ai, 'problematic_pellets'):
            self.ai.problematic_pellets = set()

        # If we have a valid path and the target pellet still exists, keep following it
        if self.ai.path and self.ai.current_path_index < len(self.ai.path):
            current_target = self.ai.path[-1]
            if current_target in maze.pellets or current_target in maze.power_pellets:
                # But check if the target is now problematic and we shouldn't go there (unless desperate)
                if current_target in self.ai.problematic_pellets and self.ai.should_ignore_problematic_pellets(maze):
                    print(f"AI {self.ai.player_id}: Current target {current_target} is now problematic, clearing path")
                    self.ai.path.clear()
                    self.ai.current_path_index = 0
                else:
                    # Continue with current path
                    if all_pellets_problematic:
                        print(f"AI {self.ai.player_id}: Continuing path to problematic pellet {current_target} (desperate)")
                    return True

        # Check if we should ignore problematic pellets
        should_ignore_problematic = self.ai.should_ignore_problematic_pellets(maze)

        target = None

        if should_ignore_problematic:
            # Try to find non-problematic pellets first
            non_problematic_pellets = self.ai.get_non_problematic_pellets(maze)
            if non_problematic_pellets:
                print(
                    f"AI {self.ai.player_id}: Looking for non-problematic pellets. Available: {len(non_problematic_pellets)}, Problematic: {len(self.ai.problematic_pellets)}"
                )
                target = self.algorithms.find_nearest_pellet(
                    maze, (self.ai.grid_x, self.ai.grid_y), avoid_positions, self.ai.problematic_pellets  # Pass problematic pellets as blacklist
                )

        # If no non-problematic pellets available or we should eat problematic ones
        if not target:
            # All pellets are problematic or we need to eat them
            # Get the last problematic pellet to eat (backwards through the list)
            target = self.ai.get_last_problematic_pellet_to_eat()

            if target and (target in maze.pellets or target in maze.power_pellets):
                print(f"AI {self.ai.player_id}: All pellets are problematic, eating backwards: {target}")

                # Use the adjusted avoid_positions (reduced when desperate)
                path = self.algorithms.a_star_pathfinding(maze, (self.ai.grid_x, self.ai.grid_y), target, avoid_positions)

                if path:
                    self.ai.path = path
                    self.ai.current_path_index = 0
                    print(f"AI {self.ai.player_id}: Eating problematic pellet backwards at {target}, length: {len(path)}")
                    return True
                else:
                    print(f"AI {self.ai.player_id}: No path to problematic pellet {target}, even with reduced avoidance")

        # Normal pathfinding for non-problematic pellets
        if target:
            path = self.algorithms.a_star_pathfinding(maze, (self.ai.grid_x, self.ai.grid_y), target, avoid_positions)
            if path:
                self.ai.path = path
                self.ai.current_path_index = 0
                pellet_type = "problematic" if target in self.ai.problematic_pellets else "normal"
                print(f"AI {self.ai.player_id}: New path to {pellet_type} pellet at {target}, length: {len(path)}")
                return True
            else:
                # Couldn't find path, blacklist this pellet if it's not already problematic
                if target not in self.ai.problematic_pellets:
                    self.ai.problematic_pellets.add(target)
                    print(f"AI {self.ai.player_id}: No path found to pellet at {target}, blacklisting")

        # Fallback to random movement
        print(f"AI {self.ai.player_id}: No valid pellet targets found, using random movement")
        return self._simple_random_strategy(maze)

    def _competitive_smart_strategy(self, maze, player_position, ghost_positions, is_invincible):
        current_pos = (self.ai.grid_x, self.ai.grid_y)

        # If player is close, try to compete or avoid based on context
        if player_position:
            distance_to_player = self.algorithms.heuristic(current_pos, player_position)

            if distance_to_player < 4:
                # Check if there are ghosts nearby that make competition dangerous
                ghost_threat = False
                if not is_invincible:
                    for ghost_pos in ghost_positions:
                        if ghost_pos:
                            ghost_distance = self.algorithms.heuristic(current_pos, ghost_pos)
                            if ghost_distance <= self.danger_zone_range:
                                ghost_threat = True
                                break

                if ghost_threat:
                    # Avoid both player and ghosts
                    all_threats = [player_position] + ghost_positions
                    escape_path = self.algorithms.find_safe_escape_path(maze, current_pos, all_threats, 5)
                    if escape_path:
                        self.ai.path = escape_path
                        self.ai.current_path_index = 0
                        return True
                else:
                    # Safe to compete with player
                    avoid_positions = set([player_position]) if not is_invincible else set()
                    target = self.algorithms.find_nearest_pellet(maze, current_pos, avoid_positions)
                    if target:
                        path = self.algorithms.a_star_pathfinding(maze, current_pos, target, avoid_positions)
                        if path:
                            self.ai.path = path
                            self.ai.current_path_index = 0
                            return True

        # Default to safe pellet hunting
        return self._pellet_hunter_safe_strategy(maze, ghost_positions, is_invincible)
