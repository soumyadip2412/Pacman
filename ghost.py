"""
ghost.py - Ghost Agent Module
================================
Implements ghost enemies with multiple AI behaviour modes.

GHOST AGENT TYPE: Goal-Based Agent with a mode state machine
-------------------------------------------------------------
Each ghost picks a target cell from its personality and current mode
(chase / scatter / frightened), then takes the next step of a BFS or A*
path toward it.

GHOST BEHAVIOURS (difficulty-configurable):
    BLINKY (Red)  – Pure BFS chaser: always pursues Pac-Man directly.
    PINKY  (Pink) – A* chaser: targets 4 cells AHEAD of Pac-Man.
    INKY   (Cyan) – A* chaser: targets Pac-Man directly (like Blinky).
    CLYDE  (Orange)– BFS but retreats when within 8 cells.
    All ghosts alternate CHASE_TICKS of chase with SCATTER_TICKS of scatter.

SEARCH ALGORITHM USED:
    BFS (Blinky, Clyde) or A* (Pinky, Inky) to compute next step.
    This is recalculated every MOVE_INTERVAL ticks for performance.
"""

import pygame
import math
import random
from bfs   import bfs_next_step
from astar import astar_search
from utils import manhattan_distance, COLORS

CELL_SIZE     = 28
SCATTER_TICKS = 150     # ticks spent in scatter mode before chasing again
CHASE_TICKS   = 300     # ticks spent chasing before scattering

# Ghost colour palette
GHOST_COLORS = {
    "blinky": (220,  40,  40),  # Red
    "pinky" : (255, 160, 200),  # Pink
    "inky"  : (  0, 220, 220),  # Cyan
    "clyde" : (255, 140,   0),  # Orange
}

# Scatter corner targets (row, col) for each ghost personality
SCATTER_CORNERS = {
    "blinky": (1, 19),
    "pinky" : (1,  1),
    "inky"  : (20, 19),
    "clyde" : (20,  1),
}


class Ghost:
    """
    Autonomous ghost agent that chases Pac-Man using BFS or A*.

    Parameters
    ----------
    maze        : Maze
    personality : str – 'blinky' | 'pinky' | 'inky' | 'clyde'
    spawn       : (row, col) – starting position
    use_astar   : bool – True = A*, False = BFS for movement
    move_delay  : int  – ticks between each move (controls speed)
    rng         : random.Random – source for frightened moves (seed it to
                  make games reproducible)
    """

    def __init__(self, maze, personality: str,
                 spawn: tuple, use_astar: bool = False,
                 move_delay: int = 10, rng: random.Random | None = None):
        self.maze        = maze
        self.rng         = rng or random.Random()   # frightened random walk
        self.name        = personality
        self.color       = GHOST_COLORS.get(personality, (200, 200, 200))
        self.row, self.col = spawn
        self.use_astar   = use_astar
        self.move_delay  = move_delay
        self.tick_count  = 0

        # Behaviour FSM state: 'chase' | 'scatter' | 'frightened'
        self.mode        = 'chase'
        self.mode_timer  = 0
        self.frightened  = False
        self.fright_timer= 0
        self.eaten       = False

        # Cached next step (avoids replanning every tick)
        self._next_step  = None
        self._plan_timer = 0
        self.plan_every  = 8    # replan every N ticks

    # ── Behaviour modes ───────────────────────────────────────────────────────

    def _get_target(self, pacman_row: int, pacman_col: int,
                    pacman_dir: tuple) -> tuple:
        """
        Determine the ghost's TARGET cell based on personality + mode.

        BLINKY : targets Pac-Man's exact position (direct chase)
        PINKY  : targets 4 cells AHEAD of Pac-Man (ambush)
        INKY   : targets Pac-Man's exact position (A* instead of BFS)
        CLYDE  : chases when far (>8), scatters when close
        SCATTER: each ghost retreats to its home corner
        """
        if self.frightened:
            # Random walk when frightened
            neighbours = self.maze.get_neighbors(self.row, self.col)
            return self.rng.choice(neighbours) if neighbours else (self.row, self.col)

        if self.mode == 'scatter':
            return SCATTER_CORNERS.get(self.name, (1, 1))

        # Chase mode
        if self.name == 'blinky':
            return (pacman_row, pacman_col)

        elif self.name == 'pinky':
            dr, dc = pacman_dir
            tr = max(0, min(self.maze.rows - 1, pacman_row + dr * 4))
            tc = max(0, min(self.maze.cols - 1, pacman_col + dc * 4))
            # Avoid landing in a wall
            if self.maze.is_wall(tr, tc):
                return (pacman_row, pacman_col)
            return (tr, tc)

        elif self.name == 'inky':
            return (pacman_row, pacman_col)

        elif self.name == 'clyde':
            dist = manhattan_distance((self.row, self.col),
                                      (pacman_row, pacman_col))
            if dist > 8:
                return (pacman_row, pacman_col)
            else:
                return SCATTER_CORNERS.get('clyde', (20, 1))

        return (pacman_row, pacman_col)

    # ── Movement ──────────────────────────────────────────────────────────────

    def update(self, pacman_row: int, pacman_col: int,
               pacman_dir: tuple = (0, 1)):
        """
        Advance the ghost by one game tick.

        Decision cycle:
        1. Update mode timer (scatter ↔ chase alternation)
        2. Compute target cell based on personality
        3. Use BFS / A* to get next step toward target
        4. Move to that step
        """
        self.tick_count  += 1
        self.mode_timer  += 1
        self._plan_timer += 1

        # Frightened countdown
        if self.frightened:
            self.fright_timer -= 1
            if self.fright_timer <= 0:
                self.frightened = False

        # Scatter / Chase alternation
        if not self.frightened:
            if self.mode == 'chase'   and self.mode_timer >= CHASE_TICKS:
                self.mode = 'scatter'
                self.mode_timer = 0
            elif self.mode == 'scatter' and self.mode_timer >= SCATTER_TICKS:
                self.mode = 'chase'
                self.mode_timer = 0

        # Only move on delay ticks
        if self.tick_count % self.move_delay != 0:
            return

        target = self._get_target(pacman_row, pacman_col, pacman_dir)

        # Replan if needed
        if self._plan_timer >= self.plan_every or self._next_step is None:
            self._plan_timer = 0
            if self.use_astar:
                path, _, _ = astar_search(
                    self.maze, (self.row, self.col), target)
                self._next_step = path[1] if len(path) > 1 else None
            else:
                self._next_step = bfs_next_step(
                    self.maze, (self.row, self.col), target)

        if self._next_step:
            self.row, self.col = self._next_step
            self._next_step = None  # consume step

    def frighten(self, duration: int = 200):
        """Activate frightened mode (Pac-Man ate a power pellet)."""
        self.frightened   = True
        self.fright_timer = duration
        self.mode_timer   = 0

    def reset(self, spawn: tuple):
        """Respawn ghost at its start position."""
        self.row, self.col = spawn
        self.frightened    = False
        self.eaten         = False
        self.mode          = 'chase'
        self.mode_timer    = 0
        self._next_step    = None
        self.tick_count    = 0

    # ── Rendering ─────────────────────────────────────────────────────────────

    def draw(self, surface, tick: int):
        """Render the ghost sprite at its current grid cell."""
        cx, cy = self.maze.cell_center(self.row, self.col)
        r      = CELL_SIZE // 2 - 2

        color = self.color
        if self.frightened:
            # Flashing blue/white when about to recover
            if self.fright_timer < 60 and (tick // 8) % 2 == 0:
                color = COLORS["white"]
            else:
                color = (30, 60, 220)

        # Ghost body (dome + skirt)
        rect = pygame.Rect(cx - r, cy - r, r * 2, r * 2)
        pygame.draw.ellipse(surface, color, rect)  # dome

        # Rectangular body below dome
        body = pygame.Rect(cx - r, cy, r * 2, r)
        pygame.draw.rect(surface, color, body)

        # Wavy skirt (3 bumps)
        skirt_y  = cy + r
        bump_w   = (r * 2) // 3
        for i in range(3):
            bx = cx - r + i * bump_w
            bump = pygame.Rect(bx, skirt_y, bump_w, r // 2)
            pygame.draw.ellipse(surface, (10, 10, 20), bump)

        # Eyes
        if not self.frightened:
            self._draw_eyes(surface, cx, cy, r)
        else:
            # Frightened expression
            pygame.draw.arc(surface, COLORS["white"],
                            (cx - r // 2, cy - 4, r, 10),
                            math.pi, 2 * math.pi, 2)

    def _draw_eyes(self, surface, cx, cy, r):
        """Draw ghost eyes with directional pupils."""
        eye_radius = max(3, r // 4)
        pupil_r    = max(2, r // 6)

        for ex_off in (-r // 3, r // 3):
            ex = cx + ex_off
            ey = cy - r // 4

            # White of eye
            pygame.draw.circle(surface, COLORS["white"], (ex, ey), eye_radius)

            # Pupil (blue)
            px_off = ex_off // 3
            pygame.draw.circle(surface, (30, 60, 200),
                               (ex + px_off, ey), pupil_r)
