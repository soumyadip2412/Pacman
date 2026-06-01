"""
bfs.py - Breadth-First Search Module
======================================
Implements BFS for pathfinding and ghost chasing behaviour.

ALGORITHM OVERVIEW:
    BFS explores nodes in FIFO (queue) order – level by level.
    It is COMPLETE and OPTIMAL for uniform-cost (unweighted) graphs.

    FIFO Frontier: every node at depth d is explored before depth d+1.

TIME COMPLEXITY  : O(b^d)  – b = branching factor, d = solution depth
SPACE COMPLEXITY : O(b^d)  – stores entire frontier

COMPARISON WITH A*:
    - BFS explores MANY more nodes because it has no heuristic guidance.
    - BFS guarantees the SHORTEST PATH in terms of number of steps.
    - A* achieves the same optimality while expanding far fewer nodes.

DFS COMPARISON:
    - DFS uses a LIFO (stack) frontier – goes deep before broad.
    - DFS is NOT optimal; may find very long paths.
    - DFS uses less memory than BFS (O(bm) vs O(b^d)).
"""

from collections import deque
import time
from utils import reconstruct_path, AlgorithmMetrics


def bfs_search(maze, start: tuple, goal: tuple) -> tuple:
    """
    Breadth-First Search from *start* to *goal*.

    Parameters
    ----------
    maze  : Maze
    start : (row, col) – initial state
    goal  : (row, col) – goal state

    Returns
    -------
    path           : list[(row, col)] – shortest path (fewest hops)
    explored_nodes : set[(row, col)]  – all expanded nodes
    metrics        : AlgorithmMetrics
    """
    t_start = time.perf_counter()

    # FIFO queue – each entry is the current node only
    frontier = deque([start])
    came_from = {start: None}   # tracks parent; also serves as 'visited' set
    explored  = set()

    nodes_explored = 0

    while frontier:
        current = frontier.popleft()

        if current in explored:
            continue

        explored.add(current)
        nodes_explored += 1

        # ── GOAL TEST ────────────────────────────────────────────────────
        if current == goal:
            path = reconstruct_path(came_from, start, goal)
            elapsed = time.perf_counter() - t_start
            metrics = AlgorithmMetrics(
                algorithm      = "BFS",
                nodes_explored = nodes_explored,
                path_length    = len(path),
                execution_time = elapsed,
                path_found     = True,
                path_cost      = len(path) - 1 if path else 0,
            )
            return path, explored, metrics

        # ── EXPAND ───────────────────────────────────────────────────────
        for neighbour in maze.get_neighbors(*current):
            if neighbour not in came_from:
                came_from[neighbour] = current
                frontier.append(neighbour)

    # No path found
    elapsed = time.perf_counter() - t_start
    metrics = AlgorithmMetrics(
        algorithm      = "BFS",
        nodes_explored = nodes_explored,
        path_length    = 0,
        execution_time = elapsed,
        path_found     = False,
        path_cost      = 0,
    )
    return [], explored, metrics


def bfs_next_step(maze, start: tuple, goal: tuple) -> tuple | None:
    """
    Return only the FIRST step of the BFS path from *start* to *goal*.

    Used by the Ghost to compute its next move efficiently without
    storing the entire path.

    Returns
    -------
    (row, col) | None
    """
    if start == goal:
        return None

    frontier = deque([start])
    came_from = {start: None}

    while frontier:
        current = frontier.popleft()

        if current == goal:
            # Reconstruct just the first step
            node = goal
            while came_from[node] != start:
                node = came_from[node]
                if node is None:
                    return None
            return node

        for neighbour in maze.get_neighbors(*current):
            if neighbour not in came_from:
                came_from[neighbour] = current
                frontier.append(neighbour)

    return None     # unreachable
