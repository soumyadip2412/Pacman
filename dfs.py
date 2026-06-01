"""
dfs.py - Depth-First Search Module
=====================================
Implements DFS for academic comparison with BFS and A*.

ALGORITHM OVERVIEW:
    DFS explores as DEEP as possible before backtracking (LIFO stack).

    KEY PROPERTIES:
    - COMPLETE  : Yes (in finite search spaces with cycle detection)
    - OPTIMAL   : NO – does not guarantee shortest path
    - TIME      : O(b^m) where m = maximum depth of the search space
    - SPACE     : O(b*m) – only stores nodes on current path (stack)

WHEN DFS IS USEFUL:
    - Memory-constrained environments (uses less space than BFS/A*)
    - Solving puzzles where ANY solution (not shortest) is acceptable
    - Detecting connectivity / reachability in a graph

LIMITATION FOR PAC-MAN:
    DFS may find a very long, winding path to the goal instead of the
    optimal (shortest) one. This is illustrated in the performance
    comparison screen of this application.
"""

import time
from utils import reconstruct_path, AlgorithmMetrics


def dfs_search(maze, start: tuple, goal: tuple,
               max_depth: int = 500) -> tuple:
    """
    Depth-First Search from *start* to *goal*.

    Uses an explicit stack (iterative DFS) with visited tracking
    to avoid infinite loops in cyclic graphs.

    Parameters
    ----------
    maze      : Maze
    start     : (row, col) – initial state
    goal      : (row, col) – goal state
    max_depth : int – safety limit to prevent excessive exploration

    Returns
    -------
    path           : list[(row, col)]  – a path (NOT necessarily shortest)
    explored_nodes : set[(row, col)]   – all visited nodes
    metrics        : AlgorithmMetrics
    """
    t_start = time.perf_counter()

    # LIFO stack – each entry is (node, depth)
    stack     = [(start, 0)]
    came_from = {start: None}
    explored  = set()

    nodes_explored = 0

    while stack:
        current, depth = stack.pop()

        if current in explored:
            continue

        explored.add(current)
        nodes_explored += 1

        # ── GOAL TEST ────────────────────────────────────────────────────
        if current == goal:
            path = reconstruct_path(came_from, start, goal)
            elapsed = time.perf_counter() - t_start
            metrics = AlgorithmMetrics(
                algorithm      = "DFS",
                nodes_explored = nodes_explored,
                path_length    = len(path),
                execution_time = elapsed,
                path_found     = True,
                path_cost      = len(path) - 1 if path else 0,
            )
            return path, explored, metrics

        # ── DEPTH LIMIT ───────────────────────────────────────────────────
        if depth >= max_depth:
            continue

        # ── EXPAND (push neighbours onto stack in reverse for consistent order)
        for neighbour in reversed(maze.get_neighbors(*current)):
            if neighbour not in explored:
                if neighbour not in came_from:
                    came_from[neighbour] = current
                stack.append((neighbour, depth + 1))

    # No path found (or depth limit reached)
    elapsed = time.perf_counter() - t_start
    metrics = AlgorithmMetrics(
        algorithm      = "DFS",
        nodes_explored = nodes_explored,
        path_length    = 0,
        execution_time = elapsed,
        path_found     = False,
        path_cost      = 0,
    )
    return [], explored, metrics
