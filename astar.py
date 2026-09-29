"""
astar.py - A* Search Algorithm Module
=======================================
Implements the A* (A-Star) search algorithm for optimal pathfinding.

ALGORITHM OVERVIEW:
    A* is an INFORMED search algorithm that combines:
    - g(n) : cost from start to current node n (actual path cost)
    - h(n) : heuristic estimate from n to goal (Manhattan Distance)
    - f(n) = g(n) + h(n)  ← priority used in the open list

    A* is COMPLETE and OPTIMAL when the heuristic is admissible.

STATE SPACE:
    - State      : (row, col) grid position
    - Actions    : Move in 4 cardinal directions (if not wall)
    - Step Cost  : 1 per move (uniform)
    - Goal Test  : current position == goal position

TIME COMPLEXITY  : O(b^d) worst case, where b = branching factor, d = depth
SPACE COMPLEXITY : O(b^d) – stores frontier and explored sets

COMPARISON WITH OTHER ALGORITHMS:
    BFS  : Optimal for unweighted graphs but explores more nodes than A*
    DFS  : Not optimal, may find very long paths or loop
    A*   : Optimal AND efficient – uses heuristic to guide search
"""

import heapq
import time
from utils import manhattan_distance, reconstruct_path, AlgorithmMetrics
from bfs   import nearest_reachable


def astar_search(maze, start: tuple, goal: tuple,
                 blocked: frozenset = frozenset()) -> tuple:
    """
    Run A* search from *start* to *goal* on the given *maze*.

    Parameters
    ----------
    maze    : Maze object  (provides get_neighbors and is_wall)
    start   : (row, col)   – initial state
    goal    : (row, col)   – goal state
    blocked : set of (row, col) – extra cells treated as walls for this
              search (Pac-Man passes the danger zone around ghosts)

    Returns
    -------
    path           : list of (row, col)  – optimal path (empty if not found)
    explored_nodes : set of (row, col)   – all nodes expanded during search
    metrics        : AlgorithmMetrics    – performance statistics
    """
    t_start = time.perf_counter()

    # ── Data structures ──────────────────────────────────────────────────
    # Open list (min-heap): entries are (f_score, g_score, node)
    # On equal f, heapq compares g next, so the node with the LOWER g is popped first.
    open_heap = []
    heapq.heappush(open_heap, (0 + manhattan_distance(start, goal), 0, start))

    # came_from tracks the parent of each expanded node (for path reconstruction)
    came_from = {}

    # g_score[n] = best known cost from start to n
    g_score = {start: 0}

    # explored / closed set – nodes already expanded
    explored = set()

    nodes_explored = 0

    while open_heap:
        f, g, current = heapq.heappop(open_heap)

        # Skip if already expanded (stale heap entry)
        if current in explored:
            continue

        explored.add(current)
        nodes_explored += 1

        # ── GOAL TEST ────────────────────────────────────────────────────
        if current == goal:
            path = reconstruct_path(came_from, start, goal)
            elapsed = time.perf_counter() - t_start
            metrics = AlgorithmMetrics(
                algorithm      = "A*",
                nodes_explored = nodes_explored,
                path_length    = len(path),
                execution_time = elapsed,
                path_found     = True,
                path_cost      = g,
            )
            return path, explored, metrics

        # ── EXPAND NODE (generate successors) ────────────────────────────
        for neighbour in maze.get_neighbors(*current):
            if neighbour in explored or neighbour in blocked:
                continue

            tentative_g = g + 1     # unit step cost

            if tentative_g < g_score.get(neighbour, float('inf')):
                # Found a better path to neighbour
                came_from[neighbour] = current
                g_score[neighbour]   = tentative_g
                h = manhattan_distance(neighbour, goal)
                f_new = tentative_g + h
                heapq.heappush(open_heap, (f_new, tentative_g, neighbour))

    # ── No path found ─────────────────────────────────────────────────────
    elapsed = time.perf_counter() - t_start
    metrics = AlgorithmMetrics(
        algorithm      = "A*",
        nodes_explored = nodes_explored,
        path_length    = 0,
        execution_time = elapsed,
        path_found     = False,
        path_cost      = 0,
    )
    return [], explored, metrics


def astar_to_nearest_pellet(maze, start: tuple, pellets: set,
                            blocked: frozenset = frozenset()) -> tuple:
    """
    Plan a path from *start* to the pellet that is nearest by maze distance.

    Two stages:
      1. Target selection – one multi-goal BFS from *start* stops at the
         first pellet it reaches, which is the truly nearest one by path
         length (a Manhattan pick can be several steps further away).
      2. Path planning   – A* from *start* to that pellet.
    Both stages treat *blocked* cells (the danger zone around ghosts) as
    walls, so the chosen pellet is the nearest one reachable safely.

    Parameters
    ----------
    maze    : Maze object
    start   : (row, col) – Pac-Man's current position
    pellets : set of (row, col) – remaining pellets (normal + power)
    blocked : set of (row, col) – cells to avoid

    Returns
    -------
    best_path    : list[(row, col)]  (empty if no pellet is reachable)
    explored     : set[(row, col)]
    metrics      : AlgorithmMetrics
    best_goal    : (row, col) | None
    """
    target = nearest_reachable(maze, start, pellets, blocked)
    if target is None:
        return [], set(), AlgorithmMetrics(algorithm="A*"), None

    path, explored, metrics = astar_search(maze, start, target, blocked)
    return path, explored, metrics, target
