from .base_behavior import BaseBehavior
import random
from constants import DIRECTIONS


class AllFoodCollectionBehavior(BaseBehavior):
    def __init__(self, ai_player):
        super().__init__(ai_player)
        self.initial_pellets_set = False  # Dùng để khởi tạo lần đầu

    def execute(self, maze, situation):
        # Khởi tạo tập hợp các chấm ban đầu chỉ một lần
        if not self.initial_pellets_set:
            self.ai_player.ai_state.initialize_pellets(maze)
            self.initial_pellets_set = True
            # Cập nhật trạng thái pellets đã ăn trong AIState khi Pac-Man di chuyển
            # Điều này có thể được xử lý trong AIPlayer.update hoặc trong Maze class
            # Ví dụ: ai_player.py update_position() khi ăn chấm

        current_pos = (self.ai_player.grid_x, self.ai_player.grid_y)

        # Cập nhật số lần thăm ô hiện tại
        self.ai_player.ai_state.increment_visited_count(current_pos)

        # Logic thoát ma (Priority 1)
        if not situation.get('has_power') and situation.get('immediate_danger'):
            self._escape_from_ghosts(maze, situation['ghost_distances'])
            return

        # Logic ăn Power Pellet (Priority 2)
        if situation.get('nearest_power_pellet') and self._should_get_power_pellet_smart(situation):
            self._hunt_target(maze, situation['nearest_power_pellet'], situation)
            return

        # Logic săn ma khi có Power Pellet (Priority 3)
        if situation.get('has_power') and self._should_hunt_ghosts_smart(situation):
            self._hunt_ghosts(maze, situation)
            return

        # Logic thu thập tất cả thức ăn (Priority 4)
        if situation.get('pellets_left_count') > 0:
            # Tìm chấm chưa ăn gần nhất, ưu tiên các chấm chưa được thăm nhiều
            target_pellet = self._find_best_uncollected_pellet(maze)

            if target_pellet:
                # Sử dụng A* hoặc UCS với cost function được điều chỉnh để ưu tiên exploration
                path = self.ai_player.pathfinding.find_path(maze, current_pos, target_pellet, "astar", situation['ghost_distances'])
                if path and len(path) > 1:
                    next_pos = path[1]
                    self._set_direction_to_position(next_pos)
                else:
                    # Nếu không tìm thấy đường đến mục tiêu, thử di chuyển ngẫu nhiên hoặc tìm mục tiêu khác
                    self._random_movement(maze)
            else:
                # Không còn chấm nào để ăn (có thể đã ăn hết hoặc lỗi)
                self._random_movement(maze)
        else:
            # Đã ăn hết chấm, có thể chuyển sang trạng thái "tìm kiếm ma" hoặc "kết thúc màn"
            self._random_movement(maze)  # Hoặc bất kỳ hành vi cuối game nào

    def _find_best_uncollected_pellet(self, maze):
        """
        Finds the best uncollected pellet to target, prioritizing less visited paths.
        This is a heuristic, can be improved with more complex calculations.
        """
        uncollected = list(self.ai_player.ai_state.uncollected_pellets)
        if not uncollected:
            return None

        current_pos = (self.ai_player.grid_x, self.ai_player.grid_y)

        # Sort pellets by a weighted cost (distance + visited penalty)
        # This is a simplified heuristic. A full "all food" might need TSP or a more advanced exploration strategy.

        best_target = None
        min_weighted_cost = float('inf')

        for pellet_pos in uncollected:
            # Approximate cost (Manhattan distance)
            distance = self._manhattan_distance(current_pos, pellet_pos)

            # Add penalty for paths through highly visited areas
            # A better approach would be to simulate path and check visited cells along the path

            # For simplicity, let's just use Manhattan and prioritize power pellets.

            # If this is a power pellet, give it a high priority
            if pellet_pos in self.ai_player.ai_state.power_pellets_remaining:
                # Give a strong bonus for power pellets, making them "cheaper"
                current_weighted_cost = distance - 1000
            else:
                # For regular pellets, penalize based on how much the destination area has been visited
                # This encourages going to unexplored areas
                visited_count_at_target = self.ai_player.ai_state.visited_cells_count.get(pellet_pos, 0)
                current_weighted_cost = distance + (visited_count_at_target * 5)  # Scale penalty

            if current_weighted_cost < min_weighted_cost:
                min_weighted_cost = current_weighted_cost
                best_target = pellet_pos

        return best_target

    # Kế thừa các hàm như _escape_from_ghosts, _should_get_power_pellet_smart,
    # _hunt_target, _should_hunt_ghosts_smart, _hunt_ghosts, _set_direction_to_position,
    # _random_movement từ BaseBehavior.
    # Đảm bảo BaseBehavior có các hàm này. Nếu không, copy từ ReflexAgentBehavior.

    # Cần sao chép các hàm từ ReflexAgentBehavior nếu AllFoodCollectionBehavior không kế thừa từ nó
    # Hoặc đảm bảo BaseBehavior chứa các hàm chung này.

    def _manhattan_distance(self, pos1, pos2):
        return abs(pos1[0] - pos2[0]) + abs(pos1[1] - pos2[1])

    def _should_get_power_pellet_smart(self, situation):
        # Logic từ ReflexAgentBehavior
        # prioritize getting power pellets unless in immediate danger and no power
        if situation.get('nearest_power_pellet'):
            if not situation.get('has_power'):
                # Go for power pellet if not currently powered up
                return True
            elif situation.get('has_power') and situation.get('power_time_left') < 50:  # Arbitrary threshold
                # Go for power pellet if current power is running low and there are ghosts nearby
                if any(dist <= 10 for _, dist in situation['ghost_distances']):
                    return True
        return False

    def _hunt_target(self, maze, target_pos, situation):
        # Logic từ ReflexAgentBehavior
        current_pos = (self.ai_player.grid_x, self.ai_player.grid_y)
        path = self.ai_player.pathfinding.find_path(maze, current_pos, target_pos, "astar", situation['ghost_distances'])
        if path and len(path) > 1:
            next_pos = path[1]
            self._set_direction_to_position(next_pos)
        else:
            self._random_movement(maze)

    def _should_hunt_ghosts_smart(self, situation):
        # Logic từ ReflexAgentBehavior
        if situation.get('has_power') and situation.get('power_time_left') > 30:  # Only hunt if enough time
            # Check if there are ghosts within a reasonable distance to hunt
            for ghost_pos, dist in situation['ghost_distances']:
                if dist < 8:  # If ghost is relatively close
                    return True
        return False

    def _hunt_ghosts(self, maze, situation):
        # Logic từ ReflexAgentBehavior
        current_pos = (self.ai_player.grid_x, self.ai_player.grid_y)
        target_ghost = None
        min_dist_to_ghost = float('inf')

        # Find the closest ghost that is not too far away
        for ghost_pos, dist in situation['ghost_distances']:
            if dist < min_dist_to_ghost and dist < 10:  # Only consider relatively close ghosts
                min_dist_to_ghost = dist
                target_ghost = ghost_pos

        if target_ghost:
            # Hunt the closest ghost
            path = self.ai_player.pathfinding.find_path(maze, current_pos, target_ghost, "astar", situation['ghost_distances'])
            if path and len(path) > 1:
                next_pos = path[1]
                self._set_direction_to_position(next_pos)
            else:
                self._random_movement(maze)
        else:
            self._random_movement(maze)  # No ghosts to hunt, fallback

    def _escape_from_ghosts(self, maze, ghost_distances):
        # Logic từ ReflexAgentBehavior
        current_pos = (self.ai_player.grid_x, self.ai_player.grid_y)
        best_dir = None
        max_safety_score = -float('inf')

        for direction, (dx, dy) in DIRECTIONS.items():
            next_x, next_y = current_pos[0] + dx, current_pos[1] + dy
            next_pos = (next_x, next_y)

            if maze.is_valid_position(next_x, next_y):
                safety_score = 0
                # Calculate safety score based on distance to ghosts from next_pos
                for ghost_pos, _ in ghost_distances:
                    dist_from_ghost = self._manhattan_distance(next_pos, ghost_pos)
                    safety_score += dist_from_ghost  # Maximize distance from ghosts

                if safety_score > max_safety_score:
                    max_safety_score = safety_score
                    best_dir = direction

        if best_dir:
            self.ai_player.next_direction = best_dir
        else:
            self._random_movement(maze)  # Fallback if stuck

    def _random_movement(self, maze):
        # Logic từ BaseBehavior / SimpleBehavior
        valid_directions = []
        current_pos = (self.ai_player.grid_x, self.ai_player.grid_y)
        for direction, (dx, dy) in DIRECTIONS.items():
            new_x = current_pos[0] + dx
            new_y = current_pos[1] + dy
            if maze.is_valid_position(new_x, new_y):
                valid_directions.append(direction)

        if valid_directions:
            self.ai_player.next_direction = random.choice(valid_directions)
        else:
            self.ai_player.next_direction = self.ai_player.direction  # Stay put if no valid moves
