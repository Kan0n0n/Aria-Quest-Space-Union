from .base_behavior import BaseBehavior
from constants import *
import math


class ReflexAgentBehavior(BaseBehavior):
    def __init__(self, ai_player):
        super().__init__(ai_player)
        self.optimal_path = None
        self.path_index = 0
        self.power_pellet_areas = set()
        self.game_phase = "initial"  # "initial", "clearing", "endgame"

    def execute(self, maze, situation):
        # Initialize game analtsysis on first call
        if not self.optimal_path:
            self._analyze_game_start(maze)

        self._update_game_phase(maze, situation)

        # Priority 1: Immediate danger avoidance
        if situation.get('immediate_danger') and not situation.get('has_power'):
            self._escape_from_ghosts(maze, situation['ghost_distances'])
            return

        # Priority 2: Power pellet strategy
        if self._should_get_power_pellet_smart(situation):
            self._hunt_target(maze, situation['nearest_power_pellet'])
            return

        # Priority 3: Ghost hunting during power mode
        if situation.get('has_power') and self._should_hunt_ghosts_smart(situation):
            self._hunt_ghosts(maze, situation)
            return

        # Priority 4: Food collection
        self._strategic_food_collection(maze, situation)

    def _analyze_game_start(self, maze):
        for power_pellet in maze.power_pellets:
            for dx in range(-1, 2):
                for dy in range(-1, 2):
                    area_pos = (power_pellet[0] + dx, power_pellet[1] + dy)
                    if maze.is_valid_position(area_pos[0], area_pos[1]):
                        self.power_pellet_areas.add(area_pos)

        # Create optimal path that covers all pellets efficiently
        self.optimal_path = self._create_optimal_pellet_path(maze)
        self.path_index = 0

    def _create_optimal_pellet_path(self, maze):
        if not maze.pellets:
            return []

        # Separate pellets by areas
        safe_pellets = []
        power_area_pellets = []

        for pellet in maze.pellets:
            if pellet in self.power_pellet_areas:
                power_area_pellets.append(pellet)
            else:
                safe_pellets.append(pellet)

        # Create path: safe pellets first, then power area pellets
        path = []
        current_pos = (self.ai_player.grid_x, self.ai_player.grid_y)

        # Phase 1: Collect safe pellets using nearest neighbor heuristic
        remaining_safe = safe_pellets.copy()
        while remaining_safe:
            nearest = min(remaining_safe, key=lambda p: self._manhattan_distance(current_pos, p))
            path.append(nearest)
            current_pos = nearest
            remaining_safe.remove(nearest)

        # Phase 2: Add power area pellets for later
        path.extend(power_area_pellets)

        return path

    def _update_game_phase(self, maze, situation):
        total_pellets = len(maze.pellets)
        maze_total_pellet = maze.total_pellets  # Ensure pellets are counted correctly
        if total_pellets > len(maze.power_pellets) * 10:
            self.game_phase = "initial"
        elif total_pellets > maze_total_pellet * 0.8:
            self.game_phase = "clearing"
        else:
            self.game_phase = "endgame"

    def _should_get_power_pellet_smart(self, situation):
        if not situation.get('nearest_power_pellet'):
            return False

        ghost_distances = situation.get('ghost_distances', [])
        if not ghost_distances:
            return False

        power_pellet_dist = self._manhattan_distance((self.ai_player.grid_x, self.ai_player.grid_y), situation['nearest_power_pellet'])

        ghost_speed = GHOST_SPEED
        ai_speed = AI_SPEED

        min_ghost_distance = min(dist for _, dist in ghost_distances) if ghost_distances else float('inf')

        time_to_power = power_pellet_dist / ai_speed

        ghost_dist_when_power = max(0, min_ghost_distance - time_to_power * ghost_speed)

        # Chỉ lấy power pellet nếu:
        # 1. Ma không thể đến kịp trước khi ăn power pellet
        # 2. AI đang gặp nguy hiểm (ma <= 4 ô) hoặc endgame phase
        should_get = ghost_dist_when_power <= 8 and (min_ghost_distance <= 4 or self.game_phase == "endgame")
        return should_get

    def _should_hunt_ghosts_smart(self, situation):
        ghost_distances = situation.get('ghost_distances', [])
        if not ghost_distances:
            return False

        power_time_left = situation.get('power_time_left', 0)
        min_ghost_dist = min(dist for _, dist in ghost_distances)

        # Assume speeds: AI = 1, Ghost = 1 when fleeing
        ai_speed = AI_SPEED
        ghost_flee_speed = GHOST_SPEED

        # Calculate time needed to catch closest ghost
        # Ghost will flee, so effective chase time is longer
        chase_time_needed = min_ghost_dist / (ai_speed + ghost_flee_speed) * 2

        # Only hunt if we have enough time buffer (at least 30 frames extra)
        return power_time_left > (chase_time_needed + 30)

    def _strategic_food_collection(self, maze, situation):
        # Fallback to nearest pellet strategy
        if situation.get('nearest_pellet'):
            # Avoid power pellet areas if not necessary
            if situation['nearest_pellet'] in self.power_pellet_areas and self._should_avoid_power_area(situation):

                # Find nearest pellet outside power areas
                safe_pellets = [p for p in maze.pellets if p not in self.power_pellet_areas]
                if safe_pellets:
                    current_pos = (self.ai_player.grid_x, self.ai_player.grid_y)
                    target = min(safe_pellets, key=lambda p: self._manhattan_distance(current_pos, p))
                    self._hunt_target(maze, target)
                    return

            self._hunt_target(maze, situation['nearest_pellet'])
        else:
            self._explore(maze)

    def _should_avoid_power_area(self, situation):
        # Avoid if ghosts are far away and we're not in endgame
        ghost_distances = situation.get('ghost_distances', [])
        if not ghost_distances:
            return self.game_phase != "endgame"

        min_ghost_dist = min(dist for _, dist in ghost_distances)

        # Avoid power areas if ghosts are far (>8 tiles) and not in endgame
        return min_ghost_dist > 8 and self.game_phase != "endgame"

    def _hunt_target(self, maze, target):
        """Hunt a specific target using BFS pathfinding with fallback"""
        self.current_target = target

        # First try pathfinding
        path = self.ai_player.pathfinding.find_path(maze, (self.ai_player.grid_x, self.ai_player.grid_y), target, "bfs")
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

    def _hunt_ghosts(self, maze, situation):
        """Hunt ghosts when in power mode"""
        ghost_distances = situation.get('ghost_distances', [])
        if not ghost_distances:
            return

        # Find the closest ghost
        closest_ghost = min(ghost_distances, key=lambda x: x[1])[0]

        # Use pathfinding to get to the ghost
        self._hunt_target(maze, closest_ghost)

    def _explore(self, maze):
        """Explore the maze randomly or towards unexplored areas"""
        unexplored = maze.get_unexplored_positions(self.ai_player.grid_x, self.ai_player.grid_y)
        if unexplored:
            target = min(unexplored, key=lambda pos: self._manhattan_distance((self.ai_player.grid_x, self.ai_player.grid_y), pos))
            self._hunt_target(maze, target)
        else:
            # If everything is explored, fallback to simple AI
            self._enhanced_simple_ai(maze, {})

    def _escape_from_ghosts(self, maze, ghost_distances):
        """Lựa chọn hướng di chuyển để tránh ma, đồng thời ưu tiên đi về phía pellet nếu không quá nguy hiểm."""
        from collections import deque

        # NEW: Don't escape if invincible (just killed by ghost)
        if self.ai_player.is_invincible:
            return

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
            if self.game_phase == "endgame" and min_ghost_dist > 3:
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
