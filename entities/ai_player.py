import pygame
import random
from collections import deque
from constants import *
from benchmark_stuff import AIBenchmark
from entities.player_base import PlayerBase
import math
import heapq


class AIPlayer(PlayerBase):
    def __init__(self, player_id, start_x, start_y, sprite_manager, ai_type="simple"):
        super().__init__(player_id, start_x, start_y, sprite_manager)
        self.direction = "LEFT"
        self.next_direction = "LEFT"
        self.speed = AI_SPEED
        self.ai_type = ai_type
        self.path = []
        self.target = None
        self.decision_timer = 0
        self.current_target = None  # Current target position for hunting

        # Enhanced AI state tracking
        self.power_timer = 0  # Time remaining with power pellet effect
        self.last_known_player_pos = None
        self.danger_zones = set()  # Positions to avoid
        self.exploration_bonus = {}  # Bonus for exploring new areas

        # NEW: Anti-stuck mechanism
        self.recent_positions = deque(maxlen=10)  # Track last 10 positions
        self.stuck_counter = 0
        self.last_position = (start_x, start_y)

        # Enhanced power pellet management
        self.power_mode_active = False
        self.power_pellet_eaten_time = 0
        self.ghost_hunt_targets = []
        self.power_mode_strategy = "aggressive"  # aggressive, cautious, balanced

        self.benchmark = None
        self.benchmark_enabled = False  # Enable benchmarking if needed

        # Algorithm comparison data
        self.algorithm_stats = {
            'bfs_steps': 0,
            'dfs_steps': 0,
            'astar_steps': 0,
            'ucs_steps': 0,
            'ghosts_eaten': 0,
            'deaths': 0,
            'power_pellets_used_effectively': 0,
        }

    def set_benchmark(self, benchmark):
        """Set benchmark instance"""
        self.benchmark = benchmark
        self.benchmark_enabled = True

    def change_algorithm(self, new_ai_type):
        """Change AI algorithm type"""
        old_type = self.ai_type
        self.ai_type = new_ai_type

        # Reset some state when changing algorithms
        self.path = []
        self.current_target = None
        self.decision_timer = 0

        print(f"AI algorithm changed from {old_type} to {new_ai_type}")
        return old_type

    def _benchmark_algorithm(self, algorithm_name, maze, start, target):
        """Benchmark a specific algorithm"""
        if not self.benchmark_enabled or not self.benchmark:
            return []

        self.benchmark.start_benchmark(algorithm_name, target, start)

        # Run the algorithm
        if algorithm_name == "bfs":
            path = self._breadth_first_search(maze, start, target)
        elif algorithm_name == "dfs":
            path = self._depth_first_search(maze, start, target)
        elif algorithm_name == "astar":
            path = self._a_star_search(maze, start, target)
        elif algorithm_name == "ucs":
            path = self._uniform_cost_search(maze, start, target)
        else:
            path = []

        # Record results
        self.benchmark.end_benchmark(path_found=len(path) > 0, path_length=len(path) if path else 0)

        return path

    def run_comprehensive_benchmark(self, maze, num_tests=10):
        """Run comprehensive benchmark on all algorithms"""
        if not self.benchmark_enabled:
            return

        algorithms = ["bfs", "dfs", "astar", "ucs"]

        # Get random targets for testing
        all_pellets = list(maze.pellets) + list(maze.power_pellets)
        if len(all_pellets) < num_tests:
            targets = all_pellets * (num_tests // len(all_pellets) + 1)
        else:
            targets = all_pellets[:num_tests]

        start_pos = (self.grid_x, self.grid_y)

        print(f"Running comprehensive benchmark with {num_tests} tests per algorithm...")

        for algorithm in algorithms:
            print(f"Testing {algorithm.upper()}...")
            for i, target in enumerate(targets[:num_tests]):
                self._benchmark_algorithm(algorithm, maze, start_pos, target)

        print("Benchmark completed!")

    def manage_power_pellet_state(self, maze, ghosts_positions):
        """Enhanced power pellet state management"""
        if self.power_timer > 0:
            self.power_mode_active = True
            time_remaining = self.power_timer

            # Strategy based on remaining time
            if time_remaining > 180:  # More than 3 seconds
                self.power_mode_strategy = "aggressive"
            elif time_remaining > 60:  # 1-3 seconds
                self.power_mode_strategy = "balanced"
            else:  # Less than 1 second
                self.power_mode_strategy = "cautious"

            # Hunt ghosts if strategy allows
            if self.power_mode_strategy in ["aggressive", "balanced"]:
                self._hunt_ghosts_intelligently(maze, ghosts_positions)
            else:
                # Retreat when time is almost up
                self._retreat_from_ghosts(maze, ghosts_positions)
        else:
            if self.power_mode_active:
                # Just exited power mode
                self.power_mode_active = False
                self._evaluate_power_pellet_effectiveness()

    def _hunt_ghosts_intelligently(self, maze, ghosts_positions):
        """Hunt ghosts with intelligent strategy during power mode"""
        if not ghosts_positions:
            return

        # Find the best ghost to hunt
        best_ghost = None
        best_score = -1

        for ghost_pos in ghosts_positions:
            distance = self._manhattan_distance((self.grid_x, self.grid_y), ghost_pos)
            time_to_reach = distance  # Simplified estimation

            # Score based on distance and time remaining
            if time_to_reach < self.power_timer // 20:  # Can reach in time
                score = 100 - distance  # Prefer closer ghosts
                if score > best_score:
                    best_score = score
                    best_ghost = ghost_pos

        if best_ghost:
            self.current_target = best_ghost
            path = self._a_star_search(maze, (self.grid_x, self.grid_y), best_ghost)
            if path and len(path) > 1:
                self.path = path
                next_pos = path[1]
                self._set_direction_to_position(next_pos)

    def _retreat_from_ghosts(self, maze, ghosts_positions):
        """Retreat strategy when power time is running out"""
        if not ghosts_positions:
            return

        # Find safest direction - away from all ghosts
        best_direction = None
        best_distance = -1

        for direction, (dx, dy) in DIRECTIONS.items():
            new_x = self.grid_x + dx
            new_y = self.grid_y + dy

            if maze.is_valid_position(new_x, new_y):
                min_ghost_distance = min(self._manhattan_distance((new_x, new_y), ghost_pos) for ghost_pos in ghosts_positions)

                if min_ghost_distance > best_distance:
                    best_distance = min_ghost_distance
                    best_direction = direction

        if best_direction:
            self.next_direction = best_direction

    def _evaluate_power_pellet_effectiveness(self):
        """Evaluate how effectively the power pellet was used"""
        # This would track if ghosts were eaten during power mode
        # For now, just increment the counter
        self.algorithm_stats['power_pellets_used_effectively'] += 1

    def update(self, maze, player_position=None, ghosts_positions=None):
        # Use base class methods
        self.update_invincibility()
        self.update_animation()

        # Update power timer
        if self.power_timer > 0:
            self.power_timer -= 1

        current_pos = (self.grid_x, self.grid_y)
        if current_pos != self.last_position:
            self.recent_positions.append(self.last_position)
            self.last_position = current_pos
            self.stuck_counter = 0
        else:
            self.stuck_counter += 1

        if self.stuck_counter > 30:  # If stuck for too long
            valid_directions = []
            for direction, (dx, dy) in DIRECTIONS.items():
                new_x = self.grid_x + dx
                new_y = self.grid_y + dy
                if maze.is_valid_position(new_x, new_y):
                    valid_directions.append(direction)

            if valid_directions:
                self.next_direction = random.choice(valid_directions)
                self.stuck_counter = 0

        self.decision_timer += 1

        # Update last known player position
        if player_position:
            self.last_known_player_pos = player_position

        # Make decisions every few frames to avoid too frequent changes
        if self.decision_timer >= 8:  # Slightly more responsive
            self._make_intelligent_decision(maze, player_position, ghosts_positions)
            self.decision_timer = 0

        # Check if AI is stuck and needs immediate help
        if self._is_stuck(maze):
            self._find_alternative_direction(maze)
            # Force immediate direction change if stuck
            if self.next_direction != self.direction:
                dx, dy = DIRECTIONS[self.next_direction]
                new_x = self.grid_x + dx
                new_y = self.grid_y + dy
                if maze.is_valid_position(new_x, new_y):
                    self.direction = self.next_direction
                    self.movement_progress = 0.0

        # FIXED: Allow direction changes at any point during movement, not just at 0.1
        if self.movement_progress <= 0.3:
            dx, dy = DIRECTIONS[self.next_direction]
            new_x = self.grid_x + dx
            new_y = self.grid_y + dy

            if maze.is_valid_position(new_x, new_y):
                self.direction = self.next_direction

        # Move in current direction
        dx, dy = DIRECTIONS[self.direction]
        target_x = self.grid_x + dx
        target_y = self.grid_y + dy

        if maze.is_valid_position(target_x, target_y):
            self.moving = True
            self.movement_progress += self.speed / CELL_SIZE

            if self.movement_progress >= 1.0:
                # Reached next cell
                self.grid_x = target_x
                self.grid_y = target_y
                self.movement_progress = 0.0

                # Collect pellets and handle power pellets
                points = maze.collect_pellet(self.grid_x, self.grid_y)
                self.score += points

                # If we collected a power pellet, activate power mode
                if points >= 50:
                    self.power_timer = 300
        else:
            self.moving = False
            self.movement_progress = 0.0
            self._find_alternative_direction(maze)
            self.movement_progress = 0.0

        # Update pixel position for smooth movement
        self._update_pixel_position()

    def _make_intelligent_decision(self, maze, player_position=None, ghosts_positions=None):
        """Enhanced decision making based on the ReflexAgent concept"""
        if self.is_dead():
            return

        # Analyze current situation
        situation = self._analyze_situation(maze, player_position, ghosts_positions)

        if self.ai_type == "reflex_agent":
            self._reflex_agent_behavior(maze, situation)
        elif self.ai_type == "smart_hunter":
            self._smart_hunter_ai(maze, situation)
        elif self.ai_type == "competitive":
            self._competitive_ai(maze, player_position)
        else:
            self._enhanced_simple_ai(maze, situation)

    def _analyze_situation(self, maze, player_position, ghosts_positions):
        """Analyze the current game situation for intelligent decision making"""
        situation = {
            'has_power': self.power_timer > 0,
            'power_time_left': self.power_timer,
            'nearest_pellet': self._find_nearest_pellet(maze),
            'nearest_power_pellet': self._find_nearest_power_pellet(maze),
            'player_distance': float('inf'),
            'ghost_distances': [],
            'safe_directions': self._get_safe_directions(maze, ghosts_positions),
            'exploration_opportunities': self._find_unexplored_areas(maze),
        }

        if player_position:
            situation['player_distance'] = self._manhattan_distance((self.grid_x, self.grid_y), player_position)

        if ghosts_positions:
            for ghost_pos in ghosts_positions:
                distance = self._manhattan_distance((self.grid_x, self.grid_y), ghost_pos)
                situation['ghost_distances'].append((ghost_pos, distance))

        return situation

    def _reflex_agent_behavior(self, maze, situation):
        # Get current state evaluation
        state_evaluation = self._evaluate_game_state(maze, situation)

        # Priority 1: Immediate danger avoidance
        if state_evaluation['immediate_danger'] and not situation['has_power']:
            self.current_target = None
            self._escape_from_ghosts(maze, situation['ghost_distances'])
            return

        # Priority 2: Power pellet strategy
        if self._should_get_power_pellet(situation, state_evaluation):
            self.current_target = situation['nearest_power_pellet']
            self._hunt_target(maze, situation['nearest_power_pellet'])
            return

        # Priority 3: Ghost hunting during power mode
        if situation['has_power'] and self._should_hunt_ghosts(situation, state_evaluation):
            self.manage_power_pellet_state(maze, [pos for pos, _ in situation['ghost_distances']])
            return

        # Priority 4: Competitive behavior
        if self._should_compete_with_player(situation, state_evaluation):
            self._competitive_behavior(maze, situation)
            return

        # Priority 5: Food collection strategy
        if situation['nearest_pellet']:
            self.current_target = situation['nearest_pellet']
            self._hunt_target(maze, situation['nearest_pellet'])
        else:
            # Exploration or special problems
            self._handle_special_objectives(maze)

    def _evaluate_game_state(self, maze, situation):
        """Comprehensive game state evaluation"""
        evaluation = {
            'immediate_danger': False,
            'ghost_threat_level': 0,
            'food_scarcity': len(maze.pellets) / max(1, maze.initial_pellet_count) if hasattr(maze, 'initial_pellet_count') else 1,
            'power_opportunity': False,
            'competition_pressure': False,
        }

        # Evaluate ghost threat
        if situation['ghost_distances']:
            min_ghost_dist = min(dist for _, dist in situation['ghost_distances'])
            evaluation['immediate_danger'] = min_ghost_dist <= 2
            evaluation['ghost_threat_level'] = max(0, 5 - min_ghost_dist) / 5

        # Evaluate power pellet opportunity
        if situation['nearest_power_pellet'] and situation['ghost_distances']:
            power_dist = self._manhattan_distance((self.grid_x, self.grid_y), situation['nearest_power_pellet'])
            min_ghost_dist = min(dist for _, dist in situation['ghost_distances'])
            evaluation['power_opportunity'] = power_dist < min_ghost_dist

        return evaluation

    def _should_get_power_pellet(self, situation, evaluation):
        """Decide whether to prioritize getting a power pellet"""
        if not situation['nearest_power_pellet']:
            return False

        # Get power pellet if ghosts are nearby and we can reach it safely
        return evaluation['ghost_threat_level'] > 0.3 and evaluation['power_opportunity']

    def _should_hunt_ghosts(self, situation, evaluation):
        """Decide whether to hunt ghosts during power mode"""
        if not situation['has_power']:
            return False

        # Hunt if we have enough time and ghosts are reachable
        return situation['power_time_left'] > 60 and situation['ghost_distances'] and min(dist for _, dist in situation['ghost_distances']) <= 8

    def _should_compete_with_player(self, situation, evaluation):
        """Decide whether to compete directly with player"""
        return situation['player_distance'] <= 5 and situation['player_distance'] != float('inf') and not evaluation['immediate_danger']

    def _handle_special_objectives(self, maze):
        """Handle special objectives when no regular food is available"""
        # Try corners problem
        corners_path = self.solve_corners_problem(maze)
        if corners_path:
            self.path = corners_path
            if len(corners_path) > 1:
                next_pos = corners_path[1]
                self._set_direction_to_position(next_pos)
            return

        # Default exploration
        self._enhanced_simple_ai(maze, {})

    def _smart_hunter_ai(self, maze, situation):
        """Advanced hunting AI using A* pathfinding"""

        if not situation['has_power'] and situation['ghost_distances']:
            min_ghost_distance = min(dist for _, dist in situation['ghost_distances'])
            if min_ghost_distance <= 3:  # Avoid ghosts when close
                self.path = []
                self._escape_from_ghosts(maze, situation['ghost_distances'])
                return

        # Use A* to find optimal path to nearest valuable target
        target = self._select_optimal_target(maze, situation)
        if target:
            path = self._a_star_search(maze, (self.grid_x, self.grid_y), target, situation.get('ghost_distances', []))
            if path and len(path) > 1:
                self.path = path
                next_pos = path[1]
                self._set_direction_to_position(next_pos)
            else:
                self.path = []
                self._enhanced_simple_ai(maze, situation)
        else:
            self.path = []
            self._enhanced_simple_ai(maze, situation)

    def _select_optimal_target(self, maze, situation):
        """Select the most valuable target using heuristic evaluation"""
        targets = []

        # Add regular pellets
        for pellet_pos in maze.pellets:
            distance = self._manhattan_distance((self.grid_x, self.grid_y), pellet_pos)
            value = 10 / (distance + 1)  # Closer = higher value
            targets.append((pellet_pos, value, 'pellet'))

        # Add power pellets with higher priority
        for pellet_pos in maze.power_pellets:
            distance = self._manhattan_distance((self.grid_x, self.grid_y), pellet_pos)
            value = 50 / (distance + 1)  # Much higher value
            targets.append((pellet_pos, value, 'power'))

        # Add exploration bonuses
        for pos, bonus in self.exploration_bonus.items():
            if maze.is_valid_position(pos[0], pos[1]):
                distance = self._manhattan_distance((self.grid_x, self.grid_y), pos)
                value = bonus / (distance + 1)
                targets.append((pos, value, 'explore'))

        if targets:
            # Return the highest value target
            best_target = max(targets, key=lambda x: x[1])
            return best_target[0]
        return None

    def _a_star_search(self, maze, start, goal, ghost_distances=None):
        """A* pathfinding algorithm"""

        def heuristic(pos1, pos2):
            return abs(pos1[0] - pos2[0]) + abs(pos1[1] - pos2[1])

        def ghost_penalty(pos):
            """Add penalty for positions near ghosts"""
            if not ghost_distances:
                return 0

            penalty = 0
            for ghost_pos, _ in ghost_distances:
                dist = abs(pos[0] - ghost_pos[0]) + abs(pos[1] - ghost_pos[1])
                if dist <= 1:  # Within 3 tiles of ghost
                    penalty += (4 - dist) * 5  # Higher penalty for closer positions
            return penalty

        open_set = [(0, start, [start])]
        closed_set = set()

        while open_set:
            f_score, current, path = heapq.heappop(open_set)

            if current == goal:
                return path

            if current in closed_set:
                continue

            closed_set.add(current)

            for next_x, next_y, _ in maze.get_neighbors(current[0], current[1]):
                next_pos = (next_x, next_y)

                if next_pos in closed_set:
                    continue

                new_path = path + [next_pos]
                g_score = len(new_path) - 1
                h_score = heuristic(next_pos, goal)
                ghost_cost = ghost_penalty(next_pos)
                f_score = g_score + h_score + ghost_cost

                heapq.heappush(open_set, (f_score, next_pos, new_path))

        return []  # No path found

    def _escape_from_ghosts(self, maze, ghost_distances):
        """Escape ghosts, but bias toward progress if not in immediate danger."""
        from collections import deque

        LOOKAHEAD = 6
        ghost_future_positions = set()

        # Predict ghost positions for the next few steps
        for ghost_pos, _ in ghost_distances:
            for direction, (dx, dy) in DIRECTIONS.items():
                gx, gy = ghost_pos
                for step in range(1, LOOKAHEAD + 1):
                    nx, ny = gx + dx * step, gy + dy * step
                    if maze.is_valid_position(nx, ny):
                        ghost_future_positions.add((nx, ny))
                    else:
                        break

        start = (self.grid_x, self.grid_y)
        queue = deque()
        queue.append((start, [], 0))
        visited = set()
        best_path = None
        best_score = -float('inf')

        # Find nearest pellet for progress bonus
        nearest_pellet = self._find_nearest_pellet(maze)

        def pellet_distance(pos):
            if nearest_pellet:
                return self._manhattan_distance(pos, nearest_pellet)
            return 0

        while queue:
            (x, y), path, depth = queue.popleft()
            if (x, y) in visited or depth > LOOKAHEAD:
                continue
            visited.add((x, y))

            min_ghost_dist = min(self._manhattan_distance((x, y), ghost_pos) for ghost_pos, _ in ghost_distances)
            future_penalty = -100 if (x, y) in ghost_future_positions else 0
            neighbors = [(nx, ny) for nx, ny, _ in maze.get_neighbors(x, y) if maze.is_valid_position(nx, ny)]
            tunnel_penalty = -30 if len(neighbors) <= 1 and depth > 0 else 0

            # Progress bonus: encourage moving toward pellets if not in immediate danger
            progress_bonus = 0
            if min_ghost_dist > 2:  # Only if not in immediate danger
                progress_bonus = max(0, 10 - pellet_distance((x, y)))  # More bonus the closer to pellet

            score = min_ghost_dist * 3 + future_penalty + tunnel_penalty - depth * 2 + progress_bonus

            if score > best_score:
                best_score = score
                best_path = path

            for nx, ny, _ in maze.get_neighbors(x, y):
                if (nx, ny) not in visited and maze.is_valid_position(nx, ny):
                    queue.append(((nx, ny), path + [(nx, ny)], depth + 1))

        if best_path and len(best_path) > 0:
            next_pos = best_path[0]
            self._set_direction_to_position(next_pos)
        else:
            # Fallback: pick the direction that maximizes immediate distance from ghosts and progress
            best_direction = None
            best_score = -float('inf')
            for direction, (dx, dy) in DIRECTIONS.items():
                nx, ny = self.grid_x + dx, self.grid_y + dy
                if not maze.is_valid_position(nx, ny):
                    continue
                min_ghost_dist = min(self._manhattan_distance((nx, ny), ghost_pos) for ghost_pos, _ in ghost_distances)
                progress_bonus = 0
                if min_ghost_dist > 2 and nearest_pellet:
                    progress_bonus = max(0, 10 - self._manhattan_distance((nx, ny), nearest_pellet))
                score = min_ghost_dist + progress_bonus
                if score > best_score:
                    best_score = score
                    best_direction = direction
            if best_direction:
                self.next_direction = best_direction
            else:
                self._enhanced_simple_ai(maze, {})

    def _hunt_target(self, maze, target):
        """Hunt a specific target using BFS pathfinding with fallback"""
        self.current_target = target

        # First try pathfinding
        path = self._find_path_to_target(maze, target)
        if path and len(path) > 1:
            self.path = path
            next_pos = path[1]
            self._set_direction_to_position(next_pos)
        else:
            # Fallback: use direct direction calculation
            self.path = []
            best_direction = self._get_best_direction_for_target(maze, target)
            if best_direction:
                self.next_direction = best_direction
            else:
                self._enhanced_simple_ai(maze, {})

    def _competitive_behavior(self, maze, situation):
        """Competitive behavior when near player"""
        if situation['nearest_pellet']:
            # Try to reach the nearest pellet before the player
            player_to_pellet = self._manhattan_distance(self.last_known_player_pos or (0, 0), situation['nearest_pellet'])
            ai_to_pellet = self._manhattan_distance((self.grid_x, self.grid_y), situation['nearest_pellet'])

            if ai_to_pellet <= player_to_pellet:
                # We can reach it faster, go for it
                self._hunt_target(maze, situation['nearest_pellet'])
            else:
                # Look for alternative targets
                self._find_alternative_pellet(maze)
        else:
            self._enhanced_simple_ai(maze, situation)

    def _enhanced_simple_ai(self, maze, situation):
        """Enhanced simple AI with better decision making"""
        valid_directions = []
        direction_scores = {}

        for direction, (dx, dy) in DIRECTIONS.items():
            new_x = self.grid_x + dx
            new_y = self.grid_y + dy
            if maze.is_valid_position(new_x, new_y):
                valid_directions.append(direction)

                # Score this direction
                score = 0

                # Prefer continuing in same direction
                if direction == self.direction:
                    score += 1

                # Avoid dead ends
                neighbors = len([n for n in maze.get_neighbors(new_x, new_y)])
                score += neighbors * 2

                # NEW: Penalize directions that lead toward ghosts
                if hasattr(situation, 'ghost_distances') and situation.get('ghost_distances'):
                    for ghost_pos, _ in situation['ghost_distances']:
                        ghost_distance = self._manhattan_distance((new_x, new_y), ghost_pos)
                        if ghost_distance <= 4 and not situation.get('has_power', False):
                            score -= 10  # Heavy penalty for moving toward ghosts

                # Bonus for unexplored areas
                if (new_x, new_y) in self.exploration_bonus:
                    score += self.exploration_bonus.get((new_x, new_y), 0)

                # NEW: Anti-stuck mechanism - penalize going back to recent positions
                if hasattr(self, 'recent_positions'):
                    if (new_x, new_y) in self.recent_positions:
                        score -= 5  # Penalty for revisiting recent positions

                # NEW: Bonus for directions leading toward pellets
                if situation.get('nearest_pellet'):
                    pellet_pos = situation['nearest_pellet']
                    current_dist = self._manhattan_distance((self.grid_x, self.grid_y), pellet_pos)
                    new_dist = self._manhattan_distance((new_x, new_y), pellet_pos)
                    if new_dist < current_dist:
                        score += 3  # Bonus for getting closer to pellets

                direction_scores[direction] = score

        if valid_directions:
            # Choose direction with highest score, with some randomness
            if random.random() < 0.85:  # 80% optimal, 20% random
                best_direction = max(valid_directions, key=lambda d: direction_scores.get(d, 0))
                self.next_direction = best_direction
            else:
                self.next_direction = random.choice(valid_directions)
        else:
            # Emergency fallback - try any direction
            for direction, (dx, dy) in DIRECTIONS.items():
                new_x = self.grid_x + dx
                new_y = self.grid_y + dy
                if maze.is_valid_position(new_x, new_y):
                    self.next_direction = direction
                    break

    # Helper methods
    def _manhattan_distance(self, pos1, pos2):
        return abs(pos1[0] - pos2[0]) + abs(pos1[1] - pos2[1])

    def _find_nearest_power_pellet(self, maze):
        if not maze.power_pellets:
            return None

        nearest = min(maze.power_pellets, key=lambda p: self._manhattan_distance((self.grid_x, self.grid_y), p))
        return nearest

    def _find_nearest_ghost(self, ghost_distances):
        if not ghost_distances:
            return None
        return min(ghost_distances, key=lambda x: x[1])

    def _get_safe_directions(self, maze, ghosts_positions):
        if not ghosts_positions:
            return list(DIRECTIONS.keys())

        safe_directions = []
        for direction, (dx, dy) in DIRECTIONS.items():
            new_x = self.grid_x + dx
            new_y = self.grid_y + dy

            if not maze.is_valid_position(new_x, new_y):
                continue

            # Check if this position is safe from ghosts
            safe = True
            for ghost_pos in ghosts_positions:
                if self._manhattan_distance((new_x, new_y), ghost_pos) <= 2:
                    safe = False
                    break

            if safe:
                safe_directions.append(direction)

        return safe_directions or list(DIRECTIONS.keys())  # Fallback to all directions

    def _find_unexplored_areas(self, maze):
        # This would require tracking visited positions
        # For now, return empty dict
        return {}

    def _find_alternative_pellet(self, maze):
        # Find second nearest pellet
        pellets = list(maze.pellets)
        if len(pellets) >= 2:
            distances = [(p, self._manhattan_distance((self.grid_x, self.grid_y), p)) for p in pellets]
            distances.sort(key=lambda x: x[1])
            if len(distances) > 1:
                self._hunt_target(maze, distances[1][0])
            else:
                self._hunt_target(maze, distances[0][0])

    # Keep existing methods that are still useful
    def _find_nearest_pellet(self, maze):
        nearest = None
        min_distance = float("inf")

        # Check regular pellets
        for pellet_pos in maze.pellets:
            distance = self._manhattan_distance((self.grid_x, self.grid_y), pellet_pos)
            if distance < min_distance:
                min_distance = distance
                nearest = pellet_pos

        # Check power pellets (higher priority)
        for pellet_pos in maze.power_pellets:
            distance = self._manhattan_distance((self.grid_x, self.grid_y), pellet_pos)
            if distance < min_distance * 1.5:  # Give power pellets priority
                min_distance = distance
                nearest = pellet_pos

        return nearest

    def _find_path_to_target(self, maze, target):
        """BFS pathfinding - keeping original for compatibility"""
        start = (self.grid_x, self.grid_y)
        if start == target:
            return [start]

        queue = deque([(start, [start])])
        visited = {start}

        while queue:
            (x, y), path = queue.popleft()

            for new_x, new_y, direction in maze.get_neighbors(x, y):
                if (new_x, new_y) == target:
                    return path + [(new_x, new_y)]

                if (new_x, new_y) not in visited:
                    visited.add((new_x, new_y))
                    queue.append(((new_x, new_y), path + [(new_x, new_y)]))

        return []  # No path found

    def _set_direction_to_position(self, target_pos):
        dx = target_pos[0] - self.grid_x
        dy = target_pos[1] - self.grid_y

        if dx > 0:
            self.next_direction = "RIGHT"
        elif dx < 0:
            self.next_direction = "LEFT"
        elif dy > 0:
            self.next_direction = "DOWN"
        elif dy < 0:
            self.next_direction = "UP"

    def _find_alternative_direction(self, maze):
        """Find alternative direction when blocked, prioritizing the intended path"""
        # If we have a target from our current AI behavior, try to move towards it
        if hasattr(self, 'current_target') and self.current_target:
            best_direction = self._get_best_direction_for_target(maze, self.current_target)
            if best_direction:
                self.next_direction = best_direction
                return

        valid_directions = []
        direction_priorities = {}

        for direction, (dx, dy) in DIRECTIONS.items():
            new_x = self.grid_x + dx
            new_y = self.grid_y + dy
            if maze.is_valid_position(new_x, new_y):
                valid_directions.append(direction)

                # Priority scoring
                priority = 0

                # Prefer the next_direction if it's valid
                if direction == self.next_direction:
                    priority += 100

                # Avoid going backwards unless necessary
                opposite = {"UP": "DOWN", "DOWN": "UP", "LEFT": "RIGHT", "RIGHT": "LEFT"}
                if direction == opposite.get(self.direction):
                    priority -= 50

                # Prefer continuing in same direction
                if direction == self.direction:
                    priority += 20

                direction_priorities[direction] = priority

        if valid_directions:
            # Sort by priority and choose the best option
            best_direction = max(valid_directions, key=lambda d: direction_priorities.get(d, 0))
            self.next_direction = best_direction

            # If we're stuck and need to go backwards, allow it
            if not maze.is_valid_position(self.grid_x + DIRECTIONS[self.direction][0], self.grid_y + DIRECTIONS[self.direction][1]):
                self.direction = best_direction

    def _is_stuck(self, maze):
        """Check if the AI player is stuck and needs immediate direction change"""
        current_dx, current_dy = DIRECTIONS[self.direction]
        target_x = self.grid_x + current_dx
        target_y = self.grid_y + current_dy

        # Check if current direction is blocked
        if not maze.is_valid_position(target_x, target_y):
            return True

        # Check if we haven't moved for a while (movement_progress stuck)
        if not self.moving and self.movement_progress <= 0.1:
            return True

        return False

    def _get_best_direction_for_target(self, maze, target_pos):
        """Get the best direction to move towards a target position"""
        if not target_pos:
            return None

        target_x, target_y = target_pos
        current_x, current_y = self.grid_x, self.grid_y

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

    def render(self, screen, debug_mode=False):
        if self.is_dead():
            return

        # Draw pathfinding debug lines if debug mode is enabled
        if debug_mode and self.path and len(self.path) > 1:
            # Build path points: start at current position, then follow self.path
            path_points = []
            # Current position (with movement progress for smoothness)
            px = self.pixel_x + CELL_SIZE // 2
            py = self.pixel_y + CELL_SIZE // 2
            path_points.append((int(px), int(py)))
            for x, y in self.path:
                path_points.append((x * CELL_SIZE + CELL_SIZE // 2, y * CELL_SIZE + CELL_SIZE // 2))

            # Choose color based on AI type or state
            if self.power_timer > 0:
                line_color = (255, 255, 0)  # Yellow when powered
            elif self.ai_type == "reflex_agent":
                line_color = (0, 255, 0)  # Green for reflex agent
            elif self.ai_type == "smart_hunter":
                line_color = (0, 150, 255)  # Blue for smart hunter
            elif self.ai_type == "competitive":
                line_color = (255, 0, 255)  # Magenta for competitive
            else:
                line_color = (255, 165, 0)  # Orange for other types

            line_width = 4 if self.power_timer > 0 else 3
            pygame.draw.lines(screen, line_color, False, path_points, line_width)

            # Draw circles at each node for clarity
            for i, (x, y) in enumerate(self.path):
                node_pos = (x * CELL_SIZE + CELL_SIZE // 2, y * CELL_SIZE + CELL_SIZE // 2)
                pygame.draw.circle(screen, line_color, node_pos, 6 if i == len(self.path) - 1 else 4, 0)

        # Draw current target if debug mode is enabled
        if debug_mode and hasattr(self, 'current_target') and self.current_target:
            target_x, target_y = self.current_target
            target_pixel = (target_x * CELL_SIZE + CELL_SIZE // 2, target_y * CELL_SIZE + CELL_SIZE // 2)

            # Draw target indicator
            pygame.draw.circle(screen, (255, 255, 255), target_pixel, 8)
            pygame.draw.circle(screen, (255, 0, 0), target_pixel, 6)

        sprite = self.sprite_manager.get_sprite(self.player_id, self.direction.lower())

        # Handle blinking effect during invincibility
        should_render = True
        if self.is_invincible:
            # Blink every 10 frames (6 times per second at 60 FPS)
            should_render = (self.invincibility_blink_timer // 10) % 2 == 0

        if should_render:
            if sprite:
                render_y = self.pixel_y + self.bob_offset

                # Add power mode visual effect
                if self.power_timer > 0:
                    # Create a glowing effect during power mode
                    glow_surface = pygame.Surface((CELL_SIZE + 4, CELL_SIZE + 4))
                    glow_surface.set_alpha(100)
                    glow_color = YELLOW if self.power_timer > 60 else RED
                    pygame.draw.circle(glow_surface, glow_color, (CELL_SIZE // 2 + 2, CELL_SIZE // 2 + 2), CELL_SIZE // 2 + 2)
                    screen.blit(glow_surface, (self.pixel_x - 2, render_y - 2))

                screen.blit(sprite, (self.pixel_x, render_y))
            else:
                # Fallback rendering with enhanced effects
                color = GREEN if self.player_id == "ai1" else ORANGE
                if self.is_invincible:
                    # Make color lighter during invincibility
                    color = tuple(min(255, c + 100) for c in color)
                elif self.power_timer > 0:
                    # Power mode coloring
                    color = YELLOW if self.power_timer > 60 else RED

                pygame.draw.circle(screen, color, (int(self.pixel_x + CELL_SIZE // 2), int(self.pixel_y + CELL_SIZE // 2)), CELL_SIZE // 2 - 2)

        # Debug info text
        if debug_mode:
            font = pygame.font.Font(None, 24)
            debug_info = []

            # AI type and state
            debug_info.append(f"AI: {self.ai_type}")

            # Current target type
            if hasattr(self, 'current_target') and self.current_target:
                debug_info.append(f"Target: {self.current_target}")

            # Power state
            if self.power_timer > 0:
                debug_info.append(f"Power: {self.power_timer // 60 + 1}s")

            # Render debug text
            for i, text in enumerate(debug_info):
                text_surface = font.render(text, True, (255, 255, 255))
                screen.blit(text_surface, (self.pixel_x, self.pixel_y - 30 - (i * 20)))

    def _depth_first_search(self, maze, start, goal):
        """DFS pathfinding algorithm for comparison"""
        stack = [(start, [start])]
        visited = set()

        while stack:
            current, path = stack.pop()

            if current == goal:
                return path

            if current in visited:
                continue

            visited.add(current)

            for next_x, next_y, _ in maze.get_neighbors(current[0], current[1]):
                next_pos = (next_x, next_y)
                if next_pos not in visited:
                    stack.append((next_pos, path + [next_pos]))

        return []

    def _breadth_first_search(self, maze, start, goal):
        """BFS pathfinding algorithm - enhanced version of existing method"""
        from collections import deque

        queue = deque([(start, [start])])
        visited = {start}

        while queue:
            current, path = queue.popleft()

            if current == goal:
                return path

            for next_x, next_y, _ in maze.get_neighbors(current[0], current[1]):
                next_pos = (next_x, next_y)
                if next_pos not in visited:
                    visited.add(next_pos)
                    queue.append((next_pos, path + [next_pos]))

        return []

    def _uniform_cost_search(self, maze, start, goal, ghost_distances=None):
        """UCS pathfinding with ghost avoidance costs"""
        import heapq

        def get_cost(pos):
            base_cost = 1
            if ghost_distances:
                for ghost_pos, _ in ghost_distances:
                    dist = self._manhattan_distance(pos, ghost_pos)
                    if dist <= 2:
                        base_cost += (3 - dist) * 10  # High cost near ghosts
            return base_cost

        priority_queue = [(0, start, [start])]
        visited = {}

        while priority_queue:
            cost, current, path = heapq.heappop(priority_queue)

            if current in visited and visited[current] <= cost:
                continue

            visited[current] = cost

            if current == goal:
                return path

            for next_x, next_y, _ in maze.get_neighbors(current[0], current[1]):
                next_pos = (next_x, next_y)
                new_cost = cost + get_cost(next_pos)

                if next_pos not in visited or visited[next_pos] > new_cost:
                    heapq.heappush(priority_queue, (new_cost, next_pos, path + [next_pos]))

        return []

    def solve_corners_problem(self, maze):
        """Solve corners problem - visit all 4 corners of the maze"""
        corners = [
            (1, 1),  # Top-left
            (maze.width - 2, 1),  # Top-right
            (1, maze.height - 2),  # Bottom-left
            (maze.width - 2, maze.height - 2),  # Bottom-right
        ]

        # Find actual valid corners
        valid_corners = []
        for corner in corners:
            if maze.is_valid_position(corner[0], corner[1]):
                valid_corners.append(corner)

        if not valid_corners:
            return []

        # Use nearest neighbor approach to visit all corners
        current_pos = (self.grid_x, self.grid_y)
        full_path = []
        remaining_corners = valid_corners.copy()

        while remaining_corners:
            # Find nearest corner
            nearest_corner = min(remaining_corners, key=lambda c: self._manhattan_distance(current_pos, c))

            # Find path to nearest corner
            path = self._a_star_search(maze, current_pos, nearest_corner)
            if path:
                full_path.extend(path[1:] if full_path else path)
                current_pos = nearest_corner
                remaining_corners.remove(nearest_corner)
            else:
                break

        return full_path

    def solve_food_search_problem(self, maze):
        """Find optimal path to collect all food"""
        all_food = list(maze.pellets) + list(maze.power_pellets)
        if not all_food:
            return []

        # Use a simplified TSP approach with nearest neighbor
        current_pos = (self.grid_x, self.grid_y)
        full_path = []
        remaining_food = all_food.copy()

        while remaining_food:
            # Find nearest food
            nearest_food = min(remaining_food, key=lambda f: self._manhattan_distance(current_pos, f))

            # Find path to nearest food
            path = self._a_star_search(maze, current_pos, nearest_food)
            if path:
                full_path.extend(path[1:] if full_path else path)
                current_pos = nearest_food
                remaining_food.remove(nearest_food)
            else:
                # Remove unreachable food
                remaining_food.remove(nearest_food)

        return full_path

    def find_path_to_closest_dot(self, maze):
        """Find path to the closest dot using different algorithms"""
        closest_dot = self._find_nearest_pellet(maze)
        if not closest_dot:
            return []

        # Try different algorithms based on AI type
        if self.ai_type == "smart_hunter":
            return self._a_star_search(maze, (self.grid_x, self.grid_y), closest_dot)
        elif self.ai_type == "simple_bfs":
            return self._breadth_first_search(maze, (self.grid_x, self.grid_y), closest_dot)
        elif self.ai_type == "simple_dfs":
            return self._depth_first_search(maze, (self.grid_x, self.grid_y), closest_dot)
        else:
            return self._find_path_to_target(maze, closest_dot)

    def compare_algorithms(self, maze, target):
        """Compare different pathfinding algorithms"""
        start_pos = (self.grid_x, self.grid_y)
        results = {}

        # Test BFS
        import time

        start_time = time.time()
        bfs_path = self._breadth_first_search(maze, start_pos, target)
        bfs_time = time.time() - start_time
        results['bfs'] = {'path_length': len(bfs_path), 'computation_time': bfs_time, 'path': bfs_path}

        # Test DFS
        start_time = time.time()
        dfs_path = self._depth_first_search(maze, start_pos, target)
        dfs_time = time.time() - start_time
        results['dfs'] = {'path_length': len(dfs_path), 'computation_time': dfs_time, 'path': dfs_path}

        # Test A*
        start_time = time.time()
        astar_path = self._a_star_search(maze, start_pos, target)
        astar_time = time.time() - start_time
        results['astar'] = {'path_length': len(astar_path), 'computation_time': astar_time, 'path': astar_path}

        # Test UCS
        start_time = time.time()
        ucs_path = self._uniform_cost_search(maze, start_pos, target)
        ucs_time = time.time() - start_time
        results['ucs'] = {'path_length': len(ucs_path), 'computation_time': ucs_time, 'path': ucs_path}

        return results

    def get_algorithm_performance_stats(self):
        """Get performance statistics for algorithm comparison"""
        return self.algorithm_stats.copy()

    def reset_position(self, x, y):
        """Reset AI player position"""
        self.grid_x = x
        self.grid_y = y
        self.pixel_x = x * CELL_SIZE
        self.pixel_y = y * CELL_SIZE
        self.movement_progress = 0.0
        self.direction = "UP"
