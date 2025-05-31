import heapq
import time
from collections import deque
from constants import DIRECTIONS

# Giving details explanation of the code:
"""
======================= PathfindingManager Class =======================
This class is responsible for managing pathfinding algorithms for AI players in a maze game.
"""


class PathfindingManager:
    def __init__(self, ai_player):
        self.ai_player = ai_player

    def find_path(self, maze, start, goal, algorithm="astar", ghost_distances=None):
        algorithms = {
            "bfs": self._breadth_first_search,
            "dfs": self._depth_first_search,
            "astar": self._a_star_search,
            "ucs": self._uniform_cost_search,
        }

        if algorithm in algorithms:
            return algorithms[algorithm](maze, start, goal, ghost_distances)
        return []

    def _manhattan_distance(self, a, b):
        return abs(a[0] - b[0]) + abs(a[1] - b[1])

    def _breadth_first_search(self, maze, start, goal, ghost_distances=None):
        queue = deque([(start, [start])])
        visited = {start}

        while queue:
            current, path = queue.popleft()
            if current == goal:
                self.ai_player.ai_state.path = path
                return path

            for next_x, next_y, _ in maze.get_neighbors(current[0], current[1]):
                next_pos = (next_x, next_y)
                if next_pos not in visited:
                    visited.add(next_pos)
                    queue.append((next_pos, path + [next_pos]))

        self.ai_player.ai_state.path = []
        return []

    def _depth_first_search(self, maze, start, goal, ghost_distances=None):
        stack = [(start, [start])]
        visited = {start}

        while stack:
            current, path = stack.pop()
            if current == goal:
                self.ai_player.ai_state.path = path
                return path

            for next_x, next_y, _ in maze.get_neighbors(current[0], current[1]):
                next_pos = (next_x, next_y)
                if next_pos not in visited:
                    visited.add(next_pos)
                    stack.append((next_pos, path + [next_pos]))
        self.ai_player.ai_state.path = []
        return []

    def _a_star_search(self, maze, start, goal, ghost_distances=None):
        def heuristic(a, b):
            return self._manhattan_distance(a, b)

        def ghost_penalty(pos, detect_distance=3):
            if not ghost_distances:
                return 0
            penalty = 0
            for ghost_pos, _ in ghost_distances:
                dist = self._manhattan_distance(pos, ghost_pos)
                if dist <= detect_distance:
                    penalty += (4 - dist) * 5
            return penalty

        open_set = [(0, start, [start])]
        closed_set = set()

        while open_set:
            f_score, current, path = heapq.heappop(open_set)
            if current == goal:
                self.ai_player.ai_state.path = path
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

        self.ai_player.ai_state.path = []
        return []

    def _uniform_cost_search(self, maze, start, goal, ghost_distances=None):
        def get_cost(pos, detect_distance=3):
            base_cost = 1
            if ghost_distances:
                for ghost_pos, _ in ghost_distances:
                    dist = self._manhattan_distance(pos, ghost_pos)
                    if dist <= detect_distance:
                        base_cost += (4 - dist) * 5
            return base_cost

        priority_queue = [(0, start, [start])]
        visited = {}

        while priority_queue:
            cost, current, path = heapq.heappop(priority_queue)

            if current in visited and visited[current] <= cost:
                continue

            visited[current] = cost

            if current == goal:
                self.ai_player.ai_state.path = path
                return path

            for next_x, next_y, _ in maze.get_neighbors(current[0], current[1]):
                next_pos = (next_x, next_y)
                new_cost = cost + get_cost(next_pos)

                if next_pos not in visited or visited[next_pos] > new_cost:
                    heapq.heappush(priority_queue, (new_cost, next_pos, path + [next_pos]))

        self.ai_player.ai_state.path = []
        return []

    def compare_algorithms(self, maze, start, goal):
        results = {}

        for algorithm in ["bfs", "dfs", "astar", "ucs"]:
            start_time = time.time()
            path = self.find_path(maze, start, goal, algorithm)
            end_time = time.time()

            results[algorithm] = {'path_length': len(path), 'computation_time': end_time - start_time, 'path': path}

        return results
