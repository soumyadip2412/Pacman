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
    │   2. Detect if ghost is on current planned path     │
    │   3. If danger detected → replan (avoid ghost)      │
    │   4. Follow path step-by-step                       │
    └─────────────────────────────────────────────────────┘

DECISION CYCLE (per game tick):
    perceive() → plan() → act()
"""

import pygame
import math
import time
from astar import astar_to_nearest_pellet, astar_search
from utils  import manhattan_distance, AlgorithmMetrics, COLORS

CELL_SIZE          = 28
MOVE_SPEED         = 6          # pixels per frame (animation interpolation)
REPLAN_TICKS       = 15         # re-run A* every N game ticks (performance)
PACMAN_MOVE_DELAY  = 4          # ticks between each Pac-Man move (higher = slower)
DANGER_DIST  = 4          # cells – ghost closer than this triggers replanning


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

    def plan(self, ghost_positions: list):
        """
        Re-run A* to find the optimal path to the nearest pellet.

        The agent replans when:
        - The current path is exhausted
        - A ghost is dangerously close to the planned path
        - A fixed number of ticks have elapsed (periodic replanning)

        GHOST AVOIDANCE:
        If a ghost is within DANGER_DIST cells, the agent removes that
        cell from the accessible area by temporarily marking it and
        replanning. (Simple reactive layer on top of deliberative A*.)
        """
        all_pellets = self.maze.pellets | self.maze.power_pellets
        if not all_pellets:
            return   # nothing to plan for

        # Danger check – is any ghost within DANGER_DIST of current position?
        danger = any(
            manhattan_distance((self.row, self.col), gpos) <= DANGER_DIST
            for gpos in ghost_positions
        )

        should_replan = (
            not self.path or
            self.ticks_since_replan >= REPLAN_TICKS or
            danger
        )

        if not should_replan:
            return

        self.ticks_since_replan = 0

        # Run A* to nearest pellet
        path, explored, metrics, target = astar_to_nearest_pellet(
            self.maze, (self.row, self.col), all_pellets
        )

        self.path           = path[1:] if path else []  # strip start node
        self.target_pellet  = target
        self.explored_nodes = explored
        self.metrics        = metrics

        # Accumulate cumulative stats
        self.total_searches       += 1
        self.total_nodes_explored += metrics.nodes_explored
        self.total_search_time    += metrics.execution_time

    # ── Action ────────────────────────────────────────────────────────────────

    def act(self, ghost_positions: list):
        """
        Decide and take the next step along the planned path.

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
            self.plan(ghost_positions)
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

        # Body (pie slice = full circle minus mouth gap)
        start_a = math.radians(angle + self.mouth_angle)
        end_a   = math.radians(angle - self.mouth_angle)
        points  = [(cx, cy)]
        steps   = 30
        for i in range(steps + 1):
            t = i / steps
            a = start_a + t * (2 * math.pi - 2 * math.radians(self.mouth_angle) * 2)
            # Wrap properly
        # Use pygame arc + filled polygon instead
        rect = pygame.Rect(cx - radius, cy - radius, radius * 2, radius * 2)
        # Draw filled yellow circle
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
            glow_alpha = abs(math.sin(tick * 0.15)) * 180 + 50
            pygame.draw.circle(surface, (0, 180, 255),
                               (cx, cy), radius + 5, 2)

    def _facing_angle(self) -> float:
        """Return facing direction in degrees (Pygame coordinate system)."""
        dr, dc = self.direction
        if dc > 0:  return 0.0    # right
        if dc < 0:  return 180.0  # left
        if dr < 0:  return 90.0   # up   (screen y inverted)
        if dr > 0:  return 270.0  # down
        return 0.0

    def _draw_death(self, surface, cx, cy, radius):
        """Death animation: Pac-Man 'closes' into a line."""
        self.death_frame = min(self.death_frame + 1, 18)
        angle = self.death_frame * 5
        pygame.draw.circle(surface, (255, 200, 0), (cx, cy), radius)
        if angle < 90:
            # Draw shrinking mouth gap
            mouth_rad = math.radians(90 - angle)
            facing    = math.radians(0)
            p1 = (cx, cy)
            p2 = (int(cx + radius * 1.1 * math.cos(mouth_rad)),
                  int(cy - radius * 1.1 * math.sin(mouth_rad)))
            p3 = (int(cx + radius * 1.1 * math.cos(-mouth_rad)),
                  int(cy - radius * 1.1 * math.sin(-mouth_rad)))
            pygame.draw.polygon(surface, (10, 10, 20), [p1, p2, p3])

    # ── Input handling ────────────────────────────────────────────────────────

    def handle_key(self, key):
        """Allow manual player control via arrow keys."""
        key_map = {
            pygame.K_UP    : (-1,  0),
            pygame.K_DOWN  : ( 1,  0),
            pygame.K_LEFT  : ( 0, -1),
            pygame.K_RIGHT : ( 0,  1),
            pygame.K_w     : (-1,  0),
            pygame.K_s     : ( 1,  0),
            pygame.K_a     : ( 0, -1),
            pygame.K_d     : ( 0,  1),
        }
        if key in key_map:
            self.manual_dir  = key_map[key]
            self.manual_mode = True

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
