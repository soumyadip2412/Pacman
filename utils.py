"""
utils.py - Utility Functions Module
=====================================
Shared helpers: heuristics, direction constants, pixel helpers, and
the AlgorithmMetrics dataclass used for performance comparison.

HEURISTIC FUNCTION (for A*):
    h(n) = Manhattan Distance from node n to goal g
    h(n) = |n.row - g.row| + |n.col - g.col|

    Properties:
    - Admissible  : Never overestimates (diagonal shortcuts are not allowed)
    - Consistent  : h(n) ≤ cost(n→n') + h(n')  ← satisfies triangle inequality
    - Guarantees  : A* with this heuristic finds the OPTIMAL path.
"""

import time
from dataclasses import dataclass

# ── Direction vectors ─────────────────────────────────────────────────────────
UP    = (-1,  0)
DOWN  = ( 1,  0)
LEFT  = ( 0, -1)
RIGHT = ( 0,  1)
DIRECTIONS = [UP, DOWN, LEFT, RIGHT]

# ── Colour palette (shared across modules) ────────────────────────────────────
COLORS = {
    "white"        : (255, 255, 255),
    "black"        : (  0,   0,   0),
    "yellow"       : (255, 220,   0),
    "red"          : (220,  40,  40),
    "cyan"         : (  0, 220, 220),
    "pink"         : (255, 160, 200),
    "orange"       : (255, 140,   0),
    "blue"         : ( 50,  80, 200),
    "green"        : ( 40, 220,  80),
    "dark_blue"    : ( 10,  10,  60),
    "ui_bg"        : ( 15,  15,  35),
    "ui_panel"     : ( 25,  25,  55),
    "ui_highlight" : ( 80, 120, 220),
    "ui_text"      : (200, 210, 240),
    "ui_accent"    : (255, 200,  60),
}

# ── Heuristic functions ───────────────────────────────────────────────────────

def manhattan_distance(pos1: tuple, pos2: tuple) -> int:
    """
    Manhattan Distance heuristic h(n).

    Formula: |r1 - r2| + |c1 - c2|

    Used by A* to estimate the cost from the current node to the goal.
    Since we only allow 4-directional movement with uniform step cost = 1,
    this heuristic is both ADMISSIBLE and CONSISTENT (monotone).

    Parameters
    ----------
    pos1, pos2 : (row, col) tuples

    Returns
    -------
    int  – estimated cost (≥ 0)
    """
    return abs(pos1[0] - pos2[0]) + abs(pos1[1] - pos2[1])


def euclidean_distance(pos1: tuple, pos2: tuple) -> float:
    """
    Euclidean Distance – provided for comparison purposes.
    Also admissible on a 4-directional grid (it is never larger than the
    Manhattan distance), but less informed, so A* would expand more nodes.
    """
    return ((pos1[0] - pos2[0])**2 + (pos1[1] - pos2[1])**2) ** 0.5


# ── Path reconstruction helper ─────────────────────────────────────────────────

def reconstruct_path(came_from: dict, start: tuple, goal: tuple) -> list:
    """
    Trace back through the *came_from* parent dictionary to build the path.

    Parameters
    ----------
    came_from : dict  {node: parent_node}
    start, goal : (row, col)

    Returns
    -------
    list of (row, col) from start → goal (inclusive)
    """
    path = []
    current = goal
    while current != start:
        path.append(current)
        current = came_from.get(current)
        if current is None:
            return []          # no path found
    path.append(start)
    path.reverse()
    return path


# ── Performance metrics dataclass ─────────────────────────────────────────────

@dataclass
class AlgorithmMetrics:
    """
    Captures performance statistics for a single search run.

    Attributes
    ----------
    algorithm     : name of the algorithm ('A*', 'BFS', 'DFS')
    nodes_explored: number of nodes popped from the frontier
    path_length   : number of cells in the solution path, start and goal included
                    (0 if no path); the number of moves is path_cost
    execution_time: wall-clock time in seconds
    path_found    : whether a solution was found
    path_cost     : sum of edge costs along the path (= path_length - 1 for unit cost)
    """
    algorithm      : str   = "Unknown"
    nodes_explored : int   = 0
    path_length    : int   = 0
    execution_time : float = 0.0
    path_found     : bool  = False
    path_cost      : int   = 0

    def summary(self) -> str:
        status = "[Found]" if self.path_found else "[Not Found]"
        return (
            f"[{self.algorithm}] {status} | "
            f"Nodes: {self.nodes_explored} | "
            f"Path: {self.path_length} cells | "
            f"Cost: {self.path_cost} | "
            f"Time: {self.execution_time*1000:.2f} ms"
        )


# ── Timing context manager ────────────────────────────────────────────────────

class Timer:
    """Simple context-manager timer. Usage:  with Timer() as t: ...  t.elapsed"""
    def __enter__(self):
        self._start = time.perf_counter()
        return self
    def __exit__(self, *_):
        self.elapsed = time.perf_counter() - self._start


# ── Pixel / grid helpers ──────────────────────────────────────────────────────

def cell_rect(row: int, col: int, cell_size: int):
    """Return (x, y, w, h) pixel rectangle for a grid cell."""
    return (col * cell_size, row * cell_size, cell_size, cell_size)


def clamp(value, lo, hi):
    """Clamp *value* to the closed interval [lo, hi]."""
    return max(lo, min(hi, value))


def format_time(seconds: float) -> str:
    """Human-readable time string (ms if < 1 s, else seconds)."""
    if seconds < 1.0:
        return f"{seconds * 1000:.1f} ms"
    return f"{seconds:.3f} s"
