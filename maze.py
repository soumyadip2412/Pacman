"""
maze.py - Maze Environment Module
==================================
Defines the grid-based maze environment for the Pac-Man simulation.

STATE SPACE REPRESENTATION:
- State: (row, col) tuple representing a cell in the 2D grid
- Initial State: Starting position of Pac-Man (defined in maze layout)
- Goal State: All pellets collected (empty pellet set)
- Actions: Move UP, DOWN, LEFT, RIGHT (if not blocked by wall)
- Transition Model: Moving to adjacent non-wall cell

CELL TYPES:
  0 = Empty path (walkable)
  1 = Wall (obstacle)
  2 = Pellet (collectible, score +10)
  3 = Power Pellet (collectible, score +50)
  P = Pac-Man start position
  G = Ghost start position
"""

import pygame

# ── Tile / colour constants ──────────────────────────────────────────────────
CELL_SIZE = 28          # pixels per grid cell

# Colours  (R, G, B)
COLOR_WALL          = (30,  30, 140)    # deep blue  – classic Pac-Man wall
COLOR_WALL_BORDER   = (80,  80, 220)    # lighter highlight on top/left edges
COLOR_PATH          = (10,  10,  20)    # near-black background
COLOR_PELLET        = (255, 220, 180)   # warm cream dot
COLOR_POWER_PELLET  = (255, 180,  40)   # amber power pellet
COLOR_EXPLORED      = (40,  60,  80)    # subtle teal – explored nodes overlay
COLOR_PATH_LINE     = (80, 220, 120)    # bright green – A* solution path

# ── Maze Layout ──────────────────────────────────────────────────────────────
# Legend:
#   1  = Wall
#   0  = Empty walkable cell (no pellet)
#   2  = Pellet cell
#   3  = Power Pellet cell
#   'P'= Pac-Man spawn  (treated as walkable, pellet NOT placed)
#   'G'= Ghost spawn    (treated as walkable, no pellet)

MAZE_LAYOUT = [
    [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
    [1,2,2,2,2,2,2,2,2,2,1,2,2,2,2,2,2,2,2,2,1],
    [1,3,1,1,2,1,1,1,2,1,1,1,2,1,1,1,2,1,1,3,1],
    [1,2,1,1,2,1,1,1,2,1,1,1,2,1,1,1,2,1,1,2,1],
    [1,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,1],
    [1,2,1,1,2,1,2,1,1,1,1,1,1,1,2,1,2,1,1,2,1],
    [1,2,2,2,2,1,2,2,2,2,1,2,2,2,2,1,2,2,2,2,1],
    [1,1,1,1,2,1,1,1,0,1,1,1,0,1,1,1,2,1,1,1,1],
    [0,0,0,1,2,1,0,0,0,0,0,0,0,0,0,1,2,1,0,0,0],
    [1,1,1,1,2,1,0,1,1,0,0,0,1,1,0,1,2,1,1,1,1],
    [1,1,1,1,2,0,0,1,'G',0,0,0,'G',1,0,0,2,1,1,1,1],
    [1,1,1,1,2,1,0,1,1,1,1,1,1,1,0,1,2,1,1,1,1],
    [0,0,0,1,2,1,0,0,0,0,0,0,0,0,0,1,2,1,0,0,0],
    [1,1,1,1,2,1,0,1,1,1,1,1,1,1,0,1,2,1,1,1,1],
    [1,2,2,2,2,2,2,2,2,2,1,2,2,2,2,2,2,2,2,2,1],
    [1,2,1,1,2,1,1,1,2,1,1,1,2,1,1,1,2,1,1,2,1],
    [1,3,2,1,2,2,2,2,2,2,'P',2,2,2,2,2,2,1,2,3,1],
    [1,1,2,1,2,1,2,1,1,1,1,1,1,1,2,1,2,1,2,1,1],
    [1,2,2,2,2,1,2,2,2,2,1,2,2,2,2,1,2,2,2,2,1],
    [1,2,1,1,1,1,1,1,2,1,1,1,2,1,1,1,1,1,1,2,1],
    [1,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,1],
    [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
]

ROWS = len(MAZE_LAYOUT)
COLS = len(MAZE_LAYOUT[0])


class Maze:
    """
    Represents the game maze as a 2-D grid.

    Responsibilities
    ----------------
    * Parse the layout to extract wall map, pellet positions, spawn points.
    * Provide neighbour queries used by search algorithms.
    * Render walls, pellets and visualisation overlays.
    """

    def __init__(self):
        self.rows = ROWS
        self.cols = COLS
        self.cell_size = CELL_SIZE

        # -- parse layout ------------------------------------------------
        self.walls   = set()   # (row, col) cells that are walls
        self.pellets = set()   # (row, col) cells with normal pellets
        self.power_pellets = set()  # (row, col) cells with power pellets
        self.pacman_start = None
        self.ghost_starts = []

        self.grid = []         # 2D list: 0=path, 1=wall (after parsing)

        for r, row in enumerate(MAZE_LAYOUT):
            grid_row = []
            for c, cell in enumerate(row):
                if cell == 1:
                    self.walls.add((r, c))
                    grid_row.append(1)
                elif cell == 2:
                    self.pellets.add((r, c))
                    grid_row.append(0)
                elif cell == 3:
                    self.power_pellets.add((r, c))
                    grid_row.append(0)
                elif cell == 'P':
                    self.pacman_start = (r, c)
                    grid_row.append(0)
                elif cell == 'G':
                    self.ghost_starts.append((r, c))
                    grid_row.append(0)
                else:            # 0 – empty walkable cell
                    grid_row.append(0)
            self.grid.append(grid_row)

        self.total_pellets = len(self.pellets) + len(self.power_pellets)

        # Pixel dimensions of the full maze surface
        self.pixel_width  = self.cols * CELL_SIZE
        self.pixel_height = self.rows * CELL_SIZE

    # ── Navigation helpers ────────────────────────────────────────────────
    def is_wall(self, row: int, col: int) -> bool:
        """Return True if (row, col) is a wall or out-of-bounds."""
        if row < 0 or row >= self.rows or col < 0 or col >= self.cols:
            return True
        return (row, col) in self.walls

    def get_neighbors(self, row: int, col: int):
        """
        Return walkable neighbours of (row, col).
        Used by all search algorithms as the successor function.

        Movement directions: UP, DOWN, LEFT, RIGHT (cardinal only).
        Cost per step = 1 (uniform-cost edges).
        """
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
        neighbours = []
        for dr, dc in directions:
            nr, nc = row + dr, col + dc
            if not self.is_wall(nr, nc):
                neighbours.append((nr, nc))
        return neighbours

    def cell_center(self, row: int, col: int):
        """Return pixel (x, y) of the centre of a grid cell."""
        x = col * CELL_SIZE + CELL_SIZE // 2
        y = row * CELL_SIZE + CELL_SIZE // 2
        return (x, y)

    def pixel_to_cell(self, px: int, py: int):
        """Convert pixel coordinates to (row, col)."""
        return (py // CELL_SIZE, px // CELL_SIZE)

    # ── Rendering ────────────────────────────────────────────────────────
    def draw(self, surface, explored_nodes=None, solution_path=None,
             show_overlay=True):
        """
        Draw the complete maze onto *surface*.

        Parameters
        ----------
        explored_nodes : set | None
            Cells visited by the search algorithm – rendered with overlay colour.
        solution_path  : list | None
            Ordered list of (row, col) cells forming the computed path.
        show_overlay   : bool
            Toggle for the visualisation overlay (explored / path).
        """
        # Background
        surface.fill(COLOR_PATH)

        # Explored-nodes overlay (drawn before walls so walls paint on top)
        if show_overlay and explored_nodes:
            for (r, c) in explored_nodes:
                if (r, c) not in self.walls:
                    rect = pygame.Rect(c * CELL_SIZE + 1,
                                       r * CELL_SIZE + 1,
                                       CELL_SIZE - 2, CELL_SIZE - 2)
                    pygame.draw.rect(surface, COLOR_EXPLORED, rect)

        # Solution path overlay
        if show_overlay and solution_path:
            for (r, c) in solution_path:
                if (r, c) not in self.walls:
                    rect = pygame.Rect(c * CELL_SIZE + 4,
                                       r * CELL_SIZE + 4,
                                       CELL_SIZE - 8, CELL_SIZE - 8)
                    pygame.draw.rect(surface, COLOR_PATH_LINE, rect, border_radius=4)

        # Walls
        for (r, c) in self.walls:
            rect = pygame.Rect(c * CELL_SIZE, r * CELL_SIZE,
                               CELL_SIZE, CELL_SIZE)
            pygame.draw.rect(surface, COLOR_WALL, rect)
            # Highlight top & left edges for 3-D effect
            pygame.draw.line(surface, COLOR_WALL_BORDER,
                             (rect.left, rect.top), (rect.right, rect.top), 2)
            pygame.draw.line(surface, COLOR_WALL_BORDER,
                             (rect.left, rect.top), (rect.left, rect.bottom), 2)

        # Pellets
        for (r, c) in self.pellets:
            cx, cy = self.cell_center(r, c)
            pygame.draw.circle(surface, COLOR_PELLET, (cx, cy), 4)

        # Power pellets (larger, pulsing is handled externally)
        for (r, c) in self.power_pellets:
            cx, cy = self.cell_center(r, c)
            pygame.draw.circle(surface, COLOR_POWER_PELLET, (cx, cy), 8)
            # Glow ring
            pygame.draw.circle(surface, (255, 230, 120), (cx, cy), 10, 2)
