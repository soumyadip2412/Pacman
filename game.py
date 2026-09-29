"""
game.py - Game State and Rules
================================
Holds everything that changes during a game (maze pellets, Pac-Man, ghosts,
lives, win / game-over flags) and advances it one tick at a time.

Nothing here draws to the screen or reads the keyboard, so the rules can be
run headlessly: main.py calls Game.step() once per frame and renders the
result, and the tests call it directly.

TICK ORDER (Game.step):
    1. Pac-Man acts (perceive → plan → move every PACMAN_MOVE_DELAY ticks)
    2. Pac-Man's power timer counts down
    3. Each ghost updates (mode timers, target, move every move_delay ticks)
    4. A power pellet eaten this tick frightens every ghost once
    5. Collisions: eat frightened ghosts, lose at most one life
    6. Win check: no pellets left
"""

import random

from maze   import Maze
from pacman import PacMan
from ghost  import Ghost

FPS = 30                    # ticks per second (the render loop runs one tick per frame)
DEATH_PAUSE_TICKS = FPS * 2 # pause after losing a life
FRIGHT_TICKS = 200          # how long a power pellet frightens ghosts
GHOST_EAT_SCORE = 200

# Difficulty presets: base ghost move delay in ticks (lower = faster ghosts)
DIFFICULTIES = {
    "Easy"   : 14,
    "Medium" : 10,
    "Hard"   :  6,
}

# (personality, uses A*, move-delay offset from the difficulty's base delay)
GHOST_SPECS = [
    ("blinky", False, -2),
    ("pinky",  True,   0),
    ("inky",   True,  +1),
    ("clyde",  False, -1),
]


class Game:
    """
    One game from start to win / game over.

    Parameters
    ----------
    difficulty : key of DIFFICULTIES
    ai_mode    : True = Pac-Man plays itself, False = keyboard control
    seed       : seed for the ghosts' random moves; the same seed and inputs
                 always replay the same game
    layout     : optional maze layout (defaults to maze.MAZE_LAYOUT)
    """

    def __init__(self, difficulty: str = "Medium", ai_mode: bool = True,
                 seed: int | None = None, layout=None):
        if difficulty not in DIFFICULTIES:
            raise ValueError(f"unknown difficulty {difficulty!r}; "
                             f"expected one of {sorted(DIFFICULTIES)}")
        self.difficulty = difficulty
        self.ai_mode    = ai_mode
        self.seed       = seed
        self.layout     = layout
        self.restart()

    # ── Lifecycle ─────────────────────────────────────────────────────────────

    def restart(self):
        """Reset to a fresh maze, full lives and ghosts at their spawns."""
        self.rng    = random.Random(self.seed)
        self.maze   = Maze(self.layout) if self.layout is not None else Maze()
        self.pacman = PacMan(self.maze)
        self.pacman.manual_mode = not self.ai_mode

        base = DIFFICULTIES[self.difficulty]
        spawns = self.maze.ghost_starts
        self.ghosts = [
            Ghost(self.maze, name, spawns[i % len(spawns)],
                  use_astar=use_astar, move_delay=max(1, base + offset),
                  rng=self.rng)
            for i, (name, use_astar, offset) in enumerate(GHOST_SPECS)
        ]

        self.tick        = 0
        self.death_pause = 0
        self.game_over   = False
        self.won         = False

    @property
    def finished(self) -> bool:
        """True once the game is over and the death animation has played."""
        return self.game_over and self.death_pause == 0

    @property
    def pellets_left(self) -> int:
        return len(self.maze.pellets) + len(self.maze.power_pellets)

    def ghost_spawn(self, index: int) -> tuple:
        spawns = self.maze.ghost_starts
        return spawns[index % len(spawns)]

    # ── One tick ──────────────────────────────────────────────────────────────

    def step(self):
        """Advance the game by one tick. Does nothing once the game is over."""
        self.tick += 1

        # After a death the board freezes while the death animation plays
        if self.death_pause > 0:
            self.death_pause -= 1
            if self.death_pause == 0 and not self.game_over:
                self.pacman.reset()
                self.pacman.manual_mode = not self.ai_mode
                for i, g in enumerate(self.ghosts):
                    g.reset(self.ghost_spawn(i))
            return

        if self.game_over:
            return

        pacman, ghosts = self.pacman, self.ghosts
        ghost_prev = [(g.row, g.col) for g in ghosts]

        # 1-2. Pac-Man acts (only non-frightened ghosts are threats)
        pacman.act([(g.row, g.col) for g in ghosts if not g.frightened])
        pacman.update_power()

        # 3. Ghosts act; Pinky aims ahead of the direction Pac-Man last moved
        for g in ghosts:
            g.update(pacman.row, pacman.col, pacman.direction)

        # 4. Power-pellet activation: frighten ghosts once, on the tick the
        # pellet is eaten (not every powered tick, which would re-frighten
        # ghosts that were just eaten and respawned)
        if pacman.power_just_activated:
            pacman.power_just_activated = False
            for g in ghosts:
                g.frighten(FRIGHT_TICKS)

        # 5. Collisions
        self._resolve_collisions(ghost_prev)

        # 6. Win condition
        if self.pellets_left == 0 and not self.game_over:
            self.won = self.game_over = True

    def _resolve_collisions(self, ghost_prev: list):
        """
        A ghost touches Pac-Man if they share a cell now, or if Pac-Man moved
        into the cell the ghost occupied before it moved (this also catches
        the two swapping cells and passing through each other).
        """
        pacman = self.pacman
        pac_pos = (pacman.row, pacman.col)

        for i, (g, g_prev) in enumerate(zip(self.ghosts, ghost_prev, strict=True)):
            if (g.row, g.col) != pac_pos and g_prev != pac_pos:
                continue

            if g.frightened:
                # Pac-Man eats the ghost; it respawns as a normal ghost
                g.reset(self.ghost_spawn(i))
                pacman.score += GHOST_EAT_SCORE
                pacman.record_ghost_eaten()
            else:
                # Ghost catches Pac-Man: at most one life lost per tick
                pacman.lives -= 1
                pacman.record_life_lost()
                pacman.dead = True
                self.death_pause = DEATH_PAUSE_TICKS
                if pacman.lives <= 0:
                    self.game_over = True
                break

    # ── Player input ──────────────────────────────────────────────────────────

    def toggle_ai(self):
        """Switch between AI control and keyboard control."""
        self.ai_mode = not self.ai_mode
        self.pacman.manual_mode = not self.ai_mode

    def steer(self, direction: tuple):
        """Keyboard input: move Pac-Man in *direction* and switch to manual."""
        self.pacman.manual_dir = direction
        self.pacman.manual_mode = True
        self.ai_mode = False
