"""
pacman.py - Pac-Man Agent Module
===================================
Implements Pac-Man as a GOAL-BASED INTELLIGENT AGENT.

AGENT TYPE: Goal-Based Intelligent Agent
-----------------------------------------
A goal-based agent decides its actions based on:
  1. PERCEPT     : Current position, positions of pellets and ghosts
  2. KNOWLEDGE   : Internal maze model (walls, walkable cells)
  3. GOAL        : Collect all pellets without being caught by a ghost
  4. ACTIONS     : Move UP / DOWN / LEFT / RIGHT
  5. REASONING   : A* Search to compute optimal path toward the nearest pellet

AGENT ARCHITECTURE:
    ┌─────────────────────────────────────────────────────┐
    │  ENVIRONMENT (Maze + Ghost positions)               │
    │   → Percept: (position, pellets, ghost_positions)   │
    │                                                     │
    │  AGENT FUNCTION: f(percept) → action               │
    │   1. Plan path to nearest pellet via A*             │
    │   2. Plan around cells near ghosts (danger zone)    │
    │   3. Ghost nearby → replan; trapped → flee          │
    │   4. Follow path step-by-step                       │
    └─────────────────────────────────────────────────────┘

DECISION CYCLE (per game tick):
    perceive() → plan() → act()
"""

import pygame
import math
from astar import astar_to_nearest_pellet
from bfs   import distance_map
from utils  import manhattan_distance, AlgorithmMetrics

CELL_SIZE          = 28
MOVE_SPEED         = 6          # pixels per frame (animation interpolation)
REPLAN_TICKS       = 15         # re-run A* every N game ticks (performance)
PACMAN_MOVE_DELAY  = 4          # ticks between each Pac-Man move (higher = slower)
DANGER_DIST  = 4          # cells – ghost closer than this triggers replanning
DANGER_RADIUS = 2         # steps – cells this close to a ghost are avoided


class PacMan:
    """
    GOAL-BASED INTELLIGENT AGENT: Pac-Man

    The agent continuously re-plans its route using A* Search to collect
    all pellets while avoiding ghosts. It functions autonomously – no
    human input is required, though manual override is supported.

    Attributes
    ----------
    row, col       : current grid cell
    path           : list[(row,col)] – planned A* path to current target
    target         : (row,col) | None – current pellet target
    explored_nodes : set – last A* explored set (for visualisation)
    metrics        : AlgorithmMetrics – last search run stats
    score          : int – pellets collected × value
    lives          : int – lives remaining
    """

    # Animation frame counts for mouth open/close cycle
    _MOUTH_FRAMES = 8

    def __init__(self, maze):
        self.maze = maze

        # Position (grid)
        self.row, self.col = maze.pacman_start

        # Sub-pixel animation position (pixels)
        cx, cy = maze.cell_center(self.row, self.col)
        self.px, self.py = float(cx), float(cy)
        self.target_px, self.target_py = float(cx), float(cy)

        # Movement
        self.direction   = (0, 1)   # facing right initially
        self.moving      = False
        self.move_queue  = []       # planned path in grid steps

        # AI planning
        self.path           = []
        self.target_pellet  = None
        self.explored_nodes = set()
        self.metrics        = AlgorithmMetrics(algorithm="A*")
        self.ticks_since_replan = REPLAN_TICKS  # force plan on first tick
        self.move_tick = 0          # counter for movement delay

        # Cumulative stats (tracked across the entire game)
        self.total_searches       = 0
        self.total_nodes_explored = 0
        self.total_search_time    = 0.0
        self.total_steps_moved    = 0
        self.total_pellets_collected      = 0
        self.total_power_pellets_collected = 0
        self.total_ghosts_eaten           = 0
        self.total_lives_lost             = 0

        # Game state
        self.score    = 0
        self.lives    = 3
        self.powered  = False   # power-pellet mode
        self.power_timer = 0
        self.power_just_activated = False  # set on the tick a power pellet is eaten

        # Animation
        self.mouth_angle = 45
        self.mouth_dir   = -1   # opening / closing
        self.frame       = 0

        # Manual control flag (set True when player presses arrow key)
        self.manual_mode = False
        self.manual_dir  = (0, 1)

        # Previous position (for direction tracking)
        self._prev = (self.row, self.col)

        # Death animation
        self.dead        = False
        self.death_frame = 0

    # ── Perception ────────────────────────────────────────────────────────────

    def perceive(self, ghost_positions: list) -> dict:
        """
        Gather percepts from the environment.
        Returns a percept dict used by the plan() method.
        """
        all_pellets = self.maze.pellets | self.maze.power_pellets
        return {
            "position"       : (self.row, self.col),
            "pellets"        : all_pellets,
            "ghost_positions": ghost_positions,
            "powered"        : self.powered,
        }

    # ── Planning (A* Search) ──────────────────────────────────────────────────

    def plan(self, percept: dict):
        """
        Re-run A* to find a safe path to the nearest pellet.

        The agent replans when:
        - The current path is exhausted
        - A ghost is within DANGER_DIST cells (Manhattan)
        - A fixed number of ticks have elapsed (periodic replanning)

        GHOST AVOIDANCE:
        Every cell within DANGER_RADIUS steps of a non-frightened ghost is
        treated as a wall for this plan, so both the target choice and the
        A* path route around ghosts. If no pellet can be reached safely,
        the agent flees: it steps to the neighbouring cell that is furthest
        (by maze distance) from the nearest ghost.
        """
        pellets = percept["pellets"]
        if not pellets:
            return   # nothing to plan for

        pos    = percept["position"]
        ghosts = percept["ghost_positions"]

        # Danger check – is any ghost within DANGER_DIST of current position?
        danger = any(
            manhattan_distance(pos, gpos) <= DANGER_DIST for gpos in ghosts
        )

        should_replan = (
            not self.path or
            self.ticks_since_replan >= REPLAN_TICKS or
            danger
        )

        if not should_replan:
            return

        self.ticks_since_replan = 0

        # Danger zone: cells close to a ghost by maze distance (never our own
        # cell, so the search can always start)
        ghost_dist = distance_map(self.maze, ghosts) if ghosts else {}
        blocked = frozenset(
            cell for cell, d in ghost_dist.items()
            if d <= DANGER_RADIUS and cell != pos
        )

        # Run A* to the nearest pellet that can be reached safely
        path, explored, metrics, target = astar_to_nearest_pellet(
            self.maze, pos, pellets, blocked
        )

        if path:
            self.path = path[1:]            # strip start node
        elif ghost_dist:
            self.path = self._flee_step(pos, ghost_dist)
        else:
            self.path = []

        self.target_pellet  = target
        self.explored_nodes = explored
        self.metrics        = metrics

        # Accumulate cumulative stats
        self.total_searches       += 1
        self.total_nodes_explored += metrics.nodes_explored
        self.total_search_time    += metrics.execution_time

    def _flee_step(self, pos: tuple, ghost_dist: dict) -> list:
        """Return a one-step path to the neighbour furthest from any ghost."""
        options = self.maze.get_neighbors(*pos) + [pos]
        best = max(options, key=lambda c: ghost_dist.get(c, float('inf')))
        return [] if best == pos else [best]

    # ── Action ────────────────────────────────────────────────────────────────

    def act(self, ghost_positions: list):
        """
        Decide and take the next step along the planned path.

        *ghost_positions* should hold only ghosts that can catch Pac-Man
        (frightened ghosts are not a threat and are left out by the caller).

        In autonomous (AI) mode: follow A* path.
        In manual mode: follow player input direction if walkable.
        """
        self.ticks_since_replan += 1
        self.move_tick += 1

        if self.dead:
            return

        # Only move every PACMAN_MOVE_DELAY ticks
        if self.move_tick % PACMAN_MOVE_DELAY != 0:
            return

        if not self.manual_mode:
            self.plan(self.perceive(ghost_positions))
            self._follow_path()
        else:
            self._follow_manual()

    def _follow_path(self):
        """Move one step along the A* planned path."""
        if self.path:
            next_cell = self.path[0]
            if not self.maze.is_wall(*next_cell):
                self._prev = (self.row, self.col)
                dr = next_cell[0] - self.row
                dc = next_cell[1] - self.col
                if dr != 0 or dc != 0:
                    self.direction = (dr, dc)
                self.row, self.col = next_cell
                self.path.pop(0)
                self.total_steps_moved += 1
        self._collect_pellet()

    def _follow_manual(self):
        """Move in the manually-chosen direction if not blocked."""
        nr = self.row + self.manual_dir[0]
        nc = self.col + self.manual_dir[1]
        if not self.maze.is_wall(nr, nc):
            self._prev = (self.row, self.col)
            self.direction = self.manual_dir
            self.row, self.col = nr, nc
            self.total_steps_moved += 1
        self._collect_pellet()

    def _collect_pellet(self):
        """Check current cell for pellets; update score."""
        pos = (self.row, self.col)
        if pos in self.maze.pellets:
            self.maze.pellets.discard(pos)
            self.score += 10
            self.total_pellets_collected += 1
        elif pos in self.maze.power_pellets:
            self.maze.power_pellets.discard(pos)
            self.score += 50
            self.powered     = True
            self.power_timer = 200   # ticks of power mode
            self.power_just_activated = True
            self.total_power_pellets_collected += 1

    def update_power(self):
        """Tick down power-pellet timer."""
        if self.powered:
            self.power_timer -= 1
            if self.power_timer <= 0:
                self.powered = False

    # ── Rendering ─────────────────────────────────────────────────────────────

    def draw(self, surface, tick: int):
        """Draw Pac-Man at its current grid cell with mouth animation."""
        cx, cy = self.maze.cell_center(self.row, self.col)
        radius  = CELL_SIZE // 2 - 2

        if self.dead:
            self._draw_death(surface, cx, cy, radius)
            return

        # Mouth animation
        self.mouth_angle += self.mouth_dir * 5
        if self.mouth_angle <= 5:
            self.mouth_dir = 1
        elif self.mouth_angle >= 50:
            self.mouth_dir = -1

        # Determine facing angle based on path direction
        angle = self._facing_angle()

        body_color = (255, 220, 0) if not self.powered else (0, 220, 255)

        # Draw filled body circle
        pygame.draw.circle(surface, body_color, (cx, cy), radius)
        # Draw black "mouth" triangle
        mouth_rad = math.radians(self.mouth_angle)
        facing    = math.radians(angle)
        p1 = (cx, cy)
        p2 = (
            int(cx + radius * 1.1 * math.cos(facing + mouth_rad)),
            int(cy - radius * 1.1 * math.sin(facing + mouth_rad)),
        )
        p3 = (
            int(cx + radius * 1.1 * math.cos(facing - mouth_rad)),
            int(cy - radius * 1.1 * math.sin(facing - mouth_rad)),
        )
        pygame.draw.polygon(surface, (10, 10, 20), [p1, p2, p3])

        # Eye
        eye_x = int(cx + radius * 0.35 * math.cos(facing + math.radians(70)))
        eye_y = int(cy - radius * 0.35 * math.sin(facing + math.radians(70)))
        pygame.draw.circle(surface, (10, 10, 20), (eye_x, eye_y), 3)

        # Power glow ring
        if self.powered:
            pygame.draw.circle(surface, (0, 180, 255),
                               (cx, cy), radius + 5, 2)

    def _facing_angle(self) -> float:
        """Return facing direction in degrees (Pygame coordinate system)."""
        dr, dc = self.direction
        if dc > 0:
            return 0.0      # right
        if dc < 0:
            return 180.0    # left
        if dr < 0:
            return 90.0     # up   (screen y inverted)
        if dr > 0:
            return 270.0    # down
        return 0.0

    def _draw_death(self, surface, cx, cy, radius):
        """Death animation: Pac-Man 'closes' into a line."""
        self.death_frame = min(self.death_frame + 1, 18)
        angle = self.death_frame * 5
        pygame.draw.circle(surface, (255, 200, 0), (cx, cy), radius)
        if angle < 90:
            # Draw shrinking mouth gap
            mouth_rad = math.radians(90 - angle)
            p1 = (cx, cy)
            p2 = (int(cx + radius * 1.1 * math.cos(mouth_rad)),
                  int(cy - radius * 1.1 * math.sin(mouth_rad)))
            p3 = (int(cx + radius * 1.1 * math.cos(-mouth_rad)),
                  int(cy - radius * 1.1 * math.sin(-mouth_rad)))
            pygame.draw.polygon(surface, (10, 10, 20), [p1, p2, p3])

    # ── Input handling ────────────────────────────────────────────────────────

    def record_ghost_eaten(self):
        """Record a ghost being eaten during the current game run."""
        self.total_ghosts_eaten += 1

    def record_life_lost(self):
        """Record Pac-Man losing a life during the current game run."""
        self.total_lives_lost += 1

    def reset(self):
        """Reset Pac-Man to starting position after losing a life."""
        self.row, self.col  = self.maze.pacman_start
        self._prev          = (self.row, self.col)
        self.direction      = (0, 1)
        self.path           = []
        self.explored_nodes = set()
        self.dead           = False
        self.death_frame    = 0
        self.powered        = False
        self.power_timer    = 0
        self.power_just_activated = False
        self.manual_mode    = False
        self.ticks_since_replan = REPLAN_TICKS
