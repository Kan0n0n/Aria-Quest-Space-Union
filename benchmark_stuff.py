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
        self.algorithm_stats = {}

    def start_benchmark(self, algorithm_name, target_pos, start_pos):
        """Start benchmarking an algorithm"""
        self.current_test = {'algorithm': algorithm_name, 'target': target_pos, 'start': start_pos, 'start_time': time.time()}

    def end_benchmark(self, path_found, path_length, nodes_expanded=0):
        """End benchmarking and record results"""
        if not self.current_test:
            return

        end_time = time.time()
        duration = end_time - self.current_test['start_time']

        result = {
            'algorithm': self.current_test['algorithm'],
            'target': self.current_test['target'],
            'start': self.current_test['start'],
            'duration': duration,
            'path_found': path_found,
            'path_length': path_length,
            'nodes_expanded': nodes_expanded,
            'timestamp': datetime.now().isoformat(),
        }

        self.results[self.current_test['algorithm']].append(result)
        self.current_test = None

    def get_summary(self):
        """Get benchmark summary"""
        summary = {}
        for algorithm, results in self.results.items():
            if results:
                avg_time = sum(r['duration'] for r in results) / len(results)
                avg_path_length = sum(r['path_length'] for r in results if r['path_found']) / max(1, len([r for r in results if r['path_found']]))
                success_rate = len([r for r in results if r['path_found']]) / len(results)

                summary[algorithm] = {
                    'tests_run': len(results),
                    'average_time': avg_time,
                    'average_path_length': avg_path_length,
                    'success_rate': success_rate,
                    'total_time': sum(r['duration'] for r in results),
                }
        return summary

    def save_to_file(self, filename=None):
        """Save benchmark results to file"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"benchmark_results_{timestamp}.txt"

        os.makedirs("benchmarks", exist_ok=True)
        filepath = os.path.join("benchmarks", filename)

        with open(filepath, 'w') as f:
            f.write("AI Pathfinding Algorithm Benchmark Results\n")
            f.write("=" * 50 + "\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

            summary = self.get_summary()

            # Summary table
            f.write("SUMMARY\n")
            f.write("-" * 30 + "\n")
            f.write(f"{'Algorithm':<12} {'Tests':<6} {'Avg Time':<10} {'Avg Path':<9} {'Success':<8}\n")
            f.write("-" * 55 + "\n")

            for algorithm, stats in summary.items():
                f.write(
                    f"{algorithm:<12} {stats['tests_run']:<6} "
                    f"{stats['average_time']:.4f}s  {stats['average_path_length']:.1f}     "
                    f"{stats['success_rate']:.1%}\n"
                )

            # Detailed results
            f.write("\n\nDETAILED RESULTS\n")
            f.write("-" * 30 + "\n")

            for algorithm, results in self.results.items():
                f.write(f"\n{algorithm.upper()}\n")
                f.write("." * 20 + "\n")

                for i, result in enumerate(results, 1):
                    f.write(f"Test {i}: ")
                    if result['path_found']:
                        f.write(f"Success - Path: {result['path_length']}, Time: {result['duration']:.4f}s\n")
                    else:
                        f.write(f"Failed - Time: {result['duration']:.4f}s\n")

        print(f"Benchmark results saved to: {filepath}")
        return filepath


class AlgorithmSwitcher:
    def __init__(self):
        self.available_algorithms = ["reflex_agent", "smart_hunter", "simple_bfs", "simple_dfs", "simple_ucs", "simple_astar", "competitive"]
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
