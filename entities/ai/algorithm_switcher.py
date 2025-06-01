import time
import os
from datetime import datetime
from collections import defaultdict
import json


import time
import os
from datetime import datetime
from collections import defaultdict
import json


class AIBenchmark:
    def __init__(self):
        self.results = defaultdict(list)
        self.current_test = None
        self.start_time = None
        self.algorithm_times = {}
        self.algorithm_stats = {}  # Nơi lưu trữ các chỉ số tổng quát cho mỗi lần chạy

    def start_benchmark(self, algorithm_name, maze_name="default_maze"):
        """
        Start benchmarking for a general AI run.
        Args:
            algorithm_name (str): The name of the AI algorithm being tested.
            maze_name (str): The name of the maze layout used for the test.
        """
        self.current_test = {
            'algorithm': algorithm_name,
            'maze': maze_name,
            'start_time': time.time(),
            'initial_pellet_count': 0,  # Sẽ được cập nhật sau
            'initial_power_pellet_count': 0,  # Sẽ được cập nhật sau
            'stats': {
                'duration_seconds': 0,
                'total_moves': 0,
                'pellets_eaten': 0,
                'power_pellets_eaten': 0,
                'ghosts_eaten': 0,
                'deaths': 0,
                'power_pellets_used_effectively': 0,
                'corners_visited_count': 0,  # Mới
                'all_corners_visited': False,  # Mới
                'game_result': 'INCOMPLETE',  # 'WIN', 'LOSS', 'INCOMPLETE'
                'pathfinding_bfs_nodes_expanded': 0,
                'pathfinding_dfs_nodes_expanded': 0,
                'pathfinding_astar_nodes_expanded': 0,
                'pathfinding_ucs_nodes_expanded': 0,
            },
        }

    def update_benchmark_stats(self, ai_player, maze):
        """
        Update the current test's statistics based on the AIPlayer and Maze state.
        Call this periodically during the game loop.
        """
        if not self.current_test:
            return

        stats = self.current_test['stats']

        # Total moves can be tracked by AIPlayer (e.g., in its update method, increment a counter)
        # Or you can increment it here based on actual movement.
        # For simplicity, let's assume ai_player has a `total_moves` counter.
        stats['total_moves'] = ai_player.total_moves_made

        # Pellets and Power Pellets eaten
        initial_pellets = len(maze.initial_pellets_set)  # Cần maze lưu trữ tổng số chấm ban đầu
        current_pellets_left = len(ai_player.ai_state.uncollected_pellets)
        current_power_pellets_left = len(ai_player.ai_state.power_pellets_remaining)

        stats['pellets_eaten'] = initial_pellets - current_pellets_left
        stats['power_pellets_eaten'] = len(maze.initial_power_pellets_set) - current_power_pellets_left  # Cần maze lưu trữ ban đầu

        # Ghost stats from AIState
        stats['ghosts_eaten'] = ai_player.ai_state.algorithm_stats['ghosts_eaten']
        stats['deaths'] = ai_player.ai_state.algorithm_stats['deaths']
        stats['power_pellets_used_effectively'] = ai_player.ai_state.algorithm_stats['power_pellets_used_effectively']

        # Corner Problem stats
        stats['corners_visited_count'] = len(ai_player.ai_state.corner_been_through)
        stats['all_corners_visited'] = ai_player.ai_state.is_through_four_corners

        # Pathfinding stats (nodes expanded)
        # Assuming PathfindingManager accumulates these and AIState has access
        stats['pathfinding_bfs_nodes_expanded'] = ai_player.pathfinding.total_nodes_expanded.get("bfs", 0)
        stats['pathfinding_dfs_nodes_expanded'] = ai_player.pathfinding.total_nodes_expanded.get("dfs", 0)
        stats['pathfinding_astar_nodes_expanded'] = ai_player.pathfinding.total_nodes_expanded.get("astar", 0)
        stats['pathfinding_ucs_nodes_expanded'] = ai_player.pathfinding.total_nodes_expanded.get("ucs", 0)

    def end_benchmark(self, game_result, final_duration):
        """
        End benchmarking and record results.
        Args:
            game_result (str): 'WIN', 'LOSS'
            final_duration (float): The total duration of the game in seconds.
        """
        if not self.current_test:
            return

        self.current_test['stats']['duration_seconds'] = final_duration
        self.current_test['stats']['game_result'] = game_result

        # Record this run's results
        self.results[self.current_test['algorithm']].append(self.current_test)

        # Clear current test
        self.current_test = None

    def save_results(self, filename="benchmark_results.json"):
        """Save all collected benchmark results to a JSON file."""
        output_dir = "benchmark_results"
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        full_path = os.path.join(output_dir, filename)

        # Convert defaultdict to dict for JSON serialization
        results_to_save = dict(self.results)

        # Make sets JSON serializable by converting them to lists or tuples
        for algo_results in results_to_save.values():
            for test_run in algo_results:
                if 'stats' in test_run and 'all_corners_visited' in test_run['stats']:
                    # Remove the specific stats that might cause issues if not needed in saved data
                    # Or convert them to a serializable format if needed
                    pass
                # Ensure tuples/sets are converted to lists
                if 'corner_been_through' in test_run['ai_state']:  # Assuming ai_state is directly in test_run
                    test_run['ai_state']['corner_been_through'] = list(test_run['ai_state']['corner_been_through'])

        with open(full_path, 'w') as f:
            json.dump(results_to_save, f, indent=4)
        print(f"Benchmark results saved to {full_path}")

    def load_results(self, filename="benchmark_results.json"):
        """Load benchmark results from a JSON file."""
        full_path = os.path.join("benchmark_results", filename)
        if os.path.exists(full_path):
            with open(full_path, 'r') as f:
                loaded_results = json.load(f)
                self.results = defaultdict(list, loaded_results)
            print(f"Benchmark results loaded from {full_path}")
        else:
            print(f"No benchmark results file found at {full_path}")

    def summarize_results(self):
        """Prints a summary of the collected benchmark results."""
        print("\n--- AI Benchmark Summary ---")
        for algo, runs in self.results.items():
            print(f"\nAlgorithm: {algo}")
            total_duration = sum(r['stats']['duration_seconds'] for r in runs if r['stats']['game_result'] == 'WIN')
            total_moves = sum(r['stats']['total_moves'] for r in runs)
            total_pellets = sum(r['stats']['pellets_eaten'] for r in runs)
            total_ghosts_eaten = sum(r['stats']['ghosts_eaten'] for r in runs)
            total_deaths = sum(r['stats']['deaths'] for r in runs)
            wins = sum(1 for r in runs if r['stats']['game_result'] == 'WIN')
            losses = sum(1 for r in runs if r['stats']['game_result'] == 'LOSS')
            total_runs = len(runs)

            avg_duration = total_duration / wins if wins > 0 else 0
            avg_moves = total_moves / total_runs if total_runs > 0 else 0

            print(f"  Total Runs: {total_runs}")
            print(f"  Wins: {wins} ({wins/total_runs*100:.2f}%)")
            print(f"  Losses: {losses} ({losses/total_runs*100:.2f}%)")
            print(f"  Avg. Duration (Wins): {avg_duration:.2f} s")
            print(f"  Avg. Total Moves: {avg_moves:.0f}")
            print(f"  Total Pellets Eaten: {total_pellets}")
            print(f"  Total Ghosts Eaten: {total_ghosts_eaten}")
            print(f"  Total Deaths: {total_deaths}")


class AlgorithmSwitcher:
    def __init__(self):
        self.available_algorithms = [
            "reflex_agent",
            "smart_hunter",
            "simple_bfs",
            "simple_dfs",
            "simple_ucs",
            "simple_astar",
            "competitive",
            "all_food_collector",
            "four_corner_problem",
        ]
        self.current_algorithm_index = 0
        self.current_algorithm = self.available_algorithms[0]

    def next_algorithm(self):
        """Switch to next algorithm"""
        self.current_algorithm_index = (self.current_algorithm_index + 1) % len(self.available_algorithms)
        self.current_algorithm = self.available_algorithms[self.current_algorithm_index]
        return self.current_algorithm

    def previous_algorithm(self):
        """Switch to previous algorithm"""
        self.current_algorithm_index = (self.current_algorithm_index - 1) % len(self.available_algorithms)
        self.current_algorithm = self.available_algorithms[self.current_algorithm_index]
        return self.current_algorithm

    def set_algorithm(self, algorithm_name):
        """Set specific algorithm"""
        if algorithm_name in self.available_algorithms:
            self.current_algorithm = algorithm_name
            self.current_algorithm_index = self.available_algorithms.index(algorithm_name)
            return True
        return False

    def get_algorithm_info(self):
        """Get current algorithm info"""
        return {
            'current': self.current_algorithm,
            'index': self.current_algorithm_index,
            'total': len(self.available_algorithms),
            'all': self.available_algorithms,
        }
