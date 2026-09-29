"""
benchmark.py - Reproducible measurements for the README
=========================================================
Runs headlessly (no window) and prints two tables:

1. Search comparison: A*, BFS and DFS on every ordered pair of reachable
   cells in the maze (or a seeded sample with --pairs N).
2. Agent performance: AI games per difficulty with seeds 0..N-1.

Usage:
    python benchmark.py                 # full run
    python benchmark.py --pairs 2000 --games 10   # quicker sample
"""

import argparse
import os
import random
import statistics
import time

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

from astar import astar_search      # noqa: E402
from bfs   import bfs_search, distance_map  # noqa: E402
from dfs   import dfs_search        # noqa: E402
from game  import DIFFICULTIES, Game  # noqa: E402
from maze  import Maze              # noqa: E402

MAX_TICKS = 18_000   # 10 minutes of game time at 30 FPS


def search_comparison(pairs: int | None):
    maze = Maze()
    cells = sorted(distance_map(maze, [maze.pacman_start]))
    all_pairs = [(a, b) for a in cells for b in cells if a != b]
    if pairs is not None and pairs < len(all_pairs):
        all_pairs = random.Random(0).sample(all_pairs, pairs)

    nodes = {"A*": [], "BFS": [], "DFS": []}
    ratio = []
    for start, goal in all_pairs:
        a_path, _, a = astar_search(maze, start, goal)
        b_path, _, b = bfs_search(maze, start, goal)
        d_path, _, d = dfs_search(maze, start, goal)
        assert len(a_path) == len(b_path), "A* and BFS must both be optimal"
        nodes["A*"].append(a.nodes_explored)
        nodes["BFS"].append(b.nodes_explored)
        nodes["DFS"].append(d.nodes_explored)
        ratio.append((len(d_path) - 1) / (len(b_path) - 1))

    print(f"Search comparison over {len(all_pairs):,} start/goal pairs "
          f"({len(cells)} reachable cells)")
    print(f"{'Algorithm':<10}{'Mean nodes expanded':>22}{'Optimal paths':>16}")
    for name in ("A*", "BFS", "DFS"):
        optimal = "100%" if name != "DFS" else f"{sum(r == 1 for r in ratio) / len(ratio):.0%}"
        print(f"{name:<10}{statistics.mean(nodes[name]):>22.1f}{optimal:>16}")
    print(f"DFS path length vs optimal: mean {statistics.mean(ratio):.2f}x, max {max(ratio):.0f}x\n")


def agent_performance(games: int):
    print(f"AI agent over {games} seeded games per difficulty (limit {MAX_TICKS:,} ticks)")
    print(f"{'Difficulty':<12}{'Wins':>8}{'Lives lost / game':>20}{'Avg A* nodes / plan':>22}")
    for difficulty in DIFFICULTIES:
        wins, lives, searches, total_nodes = 0, 0, 0, 0
        for seed in range(games):
            game = Game(difficulty, ai_mode=True, seed=seed)
            for _ in range(MAX_TICKS):
                game.step()
                if game.finished:
                    break
            wins += game.won
            lives += game.pacman.total_lives_lost
            searches += game.pacman.total_searches
            total_nodes += game.pacman.total_nodes_explored
        print(f"{difficulty:<12}{f'{wins}/{games}':>8}{lives / games:>20.2f}"
              f"{total_nodes / max(searches, 1):>22.1f}")


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    parser.add_argument("--pairs", type=int, default=None,
                        help="sample this many search pairs (default: all)")
    parser.add_argument("--games", type=int, default=40,
                        help="games per difficulty (default: 40)")
    args = parser.parse_args()

    t0 = time.perf_counter()
    search_comparison(args.pairs)
    agent_performance(args.games)
    print(f"\nFinished in {time.perf_counter() - t0:.0f} s")


if __name__ == "__main__":
    main()
