"""
main.py - Main Game Entry Point
=================================
Intelligent Pac-Man Agent Using A* Search Algorithm
Academic Assignment - Artificial Intelligence

MODULES OVERVIEW:
    main.py   – Game loop, screens, UI rendering, event handling
    maze.py   – Grid environment: walls, pellets, state space
    pacman.py – Goal-based intelligent agent (A* planner)
    ghost.py  – Ghost agents (BFS / A* chasers, 4 personalities)
    astar.py  – A* search with Manhattan Distance heuristic
    bfs.py    – Breadth-First Search implementation
    dfs.py    – Depth-First Search implementation
    utils.py  – Shared helpers: heuristics, metrics, colours

CONTROLS:
    SPACE        – Toggle AI / Manual mode
    Arrow Keys   – Manual control
    V            – Toggle visualisation overlay (explored nodes + path)
    C            – Show algorithm comparison screen
    R            – Restart game
    ESC          – Quit
"""

import sys
import math
import time
import pygame

from maze   import Maze, CELL_SIZE
from pacman import PacMan
from ghost  import Ghost
from astar  import astar_search
from bfs    import bfs_search
from dfs    import dfs_search
from utils  import COLORS, AlgorithmMetrics, format_time, manhattan_distance

# ── Window / game constants ────────────────────────────────────────────────────
FPS          = 30
PANEL_WIDTH  = 320      # right-side info panel width
TITLE        = "Intelligent Pac-Man  |  A* Search Agent"

# Difficulty presets: (ghost_move_delay, label)
DIFFICULTIES = {
    "Easy"   : 14,
    "Medium" : 10,
    "Hard"   :  6,
}


# ══════════════════════════════════════════════════════════════════════════════
#  FONT CACHE
# ══════════════════════════════════════════════════════════════════════════════
_fonts: dict = {}

def get_font(size: int, bold: bool = False) -> pygame.font.Font:
    key = (size, bold)
    if key not in _fonts:
        try:
            _fonts[key] = pygame.font.SysFont("consolas", size, bold=bold)
        except Exception:
            _fonts[key] = pygame.font.Font(None, size)
    return _fonts[key]


# ══════════════════════════════════════════════════════════════════════════════
#  HELPER – draw text with optional shadow / outline
# ══════════════════════════════════════════════════════════════════════════════
def draw_text(surface, text: str, x: int, y: int,
              size: int = 18, color=None, bold: bool = False,
              shadow: bool = False, center: bool = False):
    color = color or COLORS["ui_text"]
    font  = get_font(size, bold)
    surf  = font.render(text, True, color)
    rect  = surf.get_rect(center=(x, y)) if center else surf.get_rect(topleft=(x, y))
    if shadow:
        sh  = font.render(text, True, (0, 0, 0))
        surface.blit(sh, rect.move(2, 2))
    surface.blit(surf, rect)
    return rect


def build_run_summary_rows(pacman, elapsed_seconds: float):
    """Return compact whole-game statistics for the live panel and end screen."""
    searches = pacman.total_searches
    avg_nodes = pacman.total_nodes_explored / searches if searches else 0.0
    avg_time_ms = (pacman.total_search_time * 1000.0 / searches) if searches else 0.0
    total_pellets = pacman.total_pellets_collected + pacman.total_power_pellets_collected

    return [
        ("Play Time", format_time(elapsed_seconds), COLORS["ui_accent"]),
        ("Searches", str(searches), COLORS["ui_text"]),
        ("Total Nodes", str(pacman.total_nodes_explored), COLORS["ui_text"]),
        ("Avg Nodes", f"{avg_nodes:.1f} / search", COLORS["ui_text"]),
        ("Search Time", format_time(pacman.total_search_time), COLORS["ui_text"]),
        ("Avg Search", f"{avg_time_ms:.2f} ms", COLORS["ui_text"]),
        ("Steps", str(pacman.total_steps_moved), COLORS["ui_text"]),
        ("Pellets", f"{total_pellets} cleared", COLORS["ui_text"]),
        ("Ghosts Eaten", str(pacman.total_ghosts_eaten), COLORS["ui_text"]),
        ("Lives Lost", str(pacman.total_lives_lost), COLORS["ui_text"]),
    ]


# ══════════════════════════════════════════════════════════════════════════════
#  START SCREEN
# ══════════════════════════════════════════════════════════════════════════════
def start_screen(screen, clock, maze_w: int, maze_h: int) -> tuple[str, bool]:
    """
    Animated start screen.
    Returns (difficulty_label, ai_mode: bool).
    """
    total_w = maze_w + PANEL_WIDTH
    total_h = maze_h

    difficulty_keys = list(DIFFICULTIES.keys())
    diff_idx        = 1          # default Medium
    ai_mode         = True
    tick            = 0

    star_positions = [(
        int((i * 137.5) % total_w),
        int((i * 97.3)  % total_h)
    ) for i in range(80)]

    buttons = {
        "start"  : pygame.Rect(total_w // 2 - 110, total_h // 2 + 100, 220, 48),
        "diff"   : pygame.Rect(total_w // 2 - 110, total_h // 2 + 165, 220, 40),
        "ai_tog" : pygame.Rect(total_w // 2 - 110, total_h // 2 + 220, 220, 40),
    }

    while True:
        clock.tick(FPS)
        tick += 1
        mx, my = pygame.mouse.get_pos()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    return difficulty_keys[diff_idx], ai_mode
                if event.key == pygame.K_ESCAPE:
                    pygame.quit(); sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if buttons["start"].collidepoint(mx, my):
                    return difficulty_keys[diff_idx], ai_mode
                if buttons["diff"].collidepoint(mx, my):
                    diff_idx = (diff_idx + 1) % len(difficulty_keys)
                if buttons["ai_tog"].collidepoint(mx, my):
                    ai_mode = not ai_mode

        # ── Draw ──────────────────────────────────────────────────────────
        screen.fill(COLORS["dark_blue"])

        # Stars
        for i, (sx, sy) in enumerate(star_positions):
            alpha = int(128 + 127 * math.sin(tick * 0.05 + i))
            r     = 1 + (i % 2)
            pygame.draw.circle(screen, (alpha, alpha, alpha), (sx, sy), r)

        # Title
        title_y = total_h // 2 - 170
        draw_text(screen, "INTELLIGENT", total_w // 2, title_y,
                  size=52, color=(255, 220, 0), bold=True, shadow=True, center=True)
        draw_text(screen, "PAC-MAN AGENT", total_w // 2, title_y + 60,
                  size=46, color=(255, 255, 255), bold=True, shadow=True, center=True)

        # Subtitle
        draw_text(screen, "A* Search Algorithm  |  AI Academic Project",
                  total_w // 2, title_y + 115,
                  size=19, color=COLORS["ui_highlight"], center=True)

        # Animated Pac-Man icon
        pax = total_w // 2
        pay = title_y + 165
        pmouth = int(30 + 25 * abs(math.sin(tick * 0.1)))
        pygame.draw.circle(screen, (255, 220, 0), (pax, pay), 28)
        mr = math.radians(pmouth)
        pygame.draw.polygon(screen, COLORS["dark_blue"], [
            (pax, pay),
            (int(pax + 32 * math.cos(mr)),  int(pay - 32 * math.sin(mr))),
            (int(pax + 32 * math.cos(-mr)), int(pay - 32 * math.sin(-mr))),
        ])

        # Buttons
        for bid, brect in buttons.items():
            hovered = brect.collidepoint(mx, my)
            bcol    = COLORS["ui_highlight"] if hovered else COLORS["ui_panel"]
            pygame.draw.rect(screen, bcol, brect, border_radius=10)
            pygame.draw.rect(screen, COLORS["ui_highlight"], brect,
                             2, border_radius=10)

            if bid == "start":
                draw_text(screen, "▶  START GAME", brect.centerx, brect.centery,
                          size=22, color=COLORS["ui_accent"], bold=True, center=True)
            elif bid == "diff":
                draw_text(screen,
                          f"Difficulty: {difficulty_keys[diff_idx]}",
                          brect.centerx, brect.centery,
                          size=18, color=COLORS["ui_text"], center=True)
            elif bid == "ai_tog":
                label = "Mode: AI Agent" if ai_mode else "Mode: Manual"
                draw_text(screen, label, brect.centerx, brect.centery,
                          size=18, color=COLORS["ui_text"], center=True)

        # Controls hint
        draw_text(screen, "SPACE=Toggle AI/Manual  |  V=Overlay  |  C=Compare  |  R=Restart",
                  total_w // 2, total_h - 30,
                  size=14, color=(120, 130, 160), center=True)

        pygame.display.flip()


# ══════════════════════════════════════════════════════════════════════════════
#  GAME-OVER / WIN SCREEN
# ══════════════════════════════════════════════════════════════════════════════
def end_screen(screen, clock, won: bool, pacman, total_w: int, total_h: int,
               elapsed_seconds: float) -> bool:
    """Show game-over or win screen. Returns True to replay, False to quit."""
    tick = 0
    while True:
        clock.tick(FPS)
        tick += 1
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    return True
                if event.key == pygame.K_ESCAPE:
                    return False

        screen.fill((5, 5, 20))

        pulse = int(200 + 55 * math.sin(tick * 0.08))

        if won:
            draw_text(screen, "YOU WIN!", total_w // 2, total_h // 2 - 130,
                      size=56, color=(255, 220, 0), bold=True, shadow=True, center=True)
            draw_text(screen, "All pellets collected!", total_w // 2, total_h // 2 - 70,
                      size=24, color=(200, 255, 180), center=True)
        else:
            draw_text(screen, "GAME OVER", total_w // 2, total_h // 2 - 130,
                      size=56, color=(pulse, 40, 40), bold=True, shadow=True, center=True)
            draw_text(screen, "The ghost caught Pac-Man!", total_w // 2, total_h // 2 - 70,
                      size=24, color=(200, 140, 140), center=True)

        # Stats card
        card_top = total_h // 2 - 18
        card_bottom = total_h - 92
        card_rect = pygame.Rect(70, card_top - 12, total_w - 140, card_bottom - card_top + 24)
        pygame.draw.rect(screen, (18, 18, 36), card_rect, border_radius=14)
        pygame.draw.rect(screen, COLORS["ui_highlight"], card_rect, 2, border_radius=14)

        y = card_top
        summary_rows = build_run_summary_rows(pacman, elapsed_seconds)
        headline_rows = [
            ("Final Score", str(pacman.score), COLORS["ui_accent"]),
            ("Play Time", format_time(elapsed_seconds), COLORS["ui_text"]),
            ("Searches", str(pacman.total_searches), COLORS["ui_text"]),
        ]
        for label, value, col in headline_rows:
            draw_text(screen, f"{label:<12}: {value}", total_w // 2, y, size=18, color=col, center=True)
            y += 28

        y += 4
        left_x  = total_w // 2 - 180
        right_x = total_w // 2 + 20
        left_rows  = summary_rows[:4]
        right_rows = summary_rows[4:8]

        draw_text(screen, "Run Totals", total_w // 2, y, size=17,
                  color=COLORS["ui_highlight"], bold=True, center=True)
        y += 24

        for row_index, (label, value, col) in enumerate(left_rows):
            row_y = y + row_index * 22
            draw_text(screen, f"{label:<11}: {value}", left_x, row_y,
                      size=15, color=col)

        for row_index, (label, value, col) in enumerate(right_rows):
            row_y = y + row_index * 22
            draw_text(screen, f"{label:<11}: {value}", right_x, row_y,
                      size=15, color=col)

        footer_rect = pygame.Rect(70, total_h - 72, total_w - 140, 44)
        pygame.draw.rect(screen, (10, 10, 24), footer_rect, border_radius=12)
        pygame.draw.rect(screen, COLORS["ui_panel"], footer_rect, 1, border_radius=12)
        draw_text(screen, "R = Restart   |   ESC = Quit",
                  total_w // 2, total_h - 50,
                  size=18, color=(210, 220, 255), center=True)

        pygame.display.flip()


# ══════════════════════════════════════════════════════════════════════════════
#  ALGORITHM COMPARISON SCREEN
# ══════════════════════════════════════════════════════════════════════════════
def comparison_screen(screen, clock, maze,
                      start: tuple, goal: tuple,
                      total_w: int, total_h: int):
    """
    Run BFS, DFS, A* on the same start→goal pair and display a
    side-by-side performance comparison table.
    """
    # Run all three algorithms
    results = {}
    for name, fn in [("BFS", bfs_search), ("DFS", dfs_search), ("A*", astar_search)]:
        path, explored, metrics = fn(maze, start, goal)
        results[name] = metrics

    waiting = True
    while waiting:
        clock.tick(FPS)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN:
                waiting = False

        screen.fill(COLORS["dark_blue"])
        draw_text(screen, "ALGORITHM PERFORMANCE COMPARISON",
                  total_w // 2, 40, size=26, color=COLORS["ui_accent"],
                  bold=True, center=True)
        draw_text(screen, f"Route: {start} → {goal}",
                  total_w // 2, 80, size=16, color=COLORS["ui_highlight"], center=True)

        # Table header
        headers = ["Algorithm", "Nodes Explored", "Path Length", "Path Cost", "Time (ms)", "Optimal?"]
        col_xs  = [80, 240, 400, 530, 660, 790]
        y       = 130
        for hdr, cx in zip(headers, col_xs):
            draw_text(screen, hdr, cx, y, size=15, color=COLORS["ui_accent"], bold=True)

        # Divider
        pygame.draw.line(screen, COLORS["ui_highlight"], (60, y + 25), (total_w - 60, y + 25), 1)
        y += 45

        row_colors = {
            "BFS": (100, 180, 255),
            "DFS": (255, 130, 100),
            "A*" : (100, 240, 140),
        }
        optimal_map = {"BFS": "Yes", "DFS": "No", "A*": "Yes (h admissible)"}

        for alg in ["BFS", "DFS", "A*"]:
            m   = results[alg]
            col = row_colors[alg]
            row_data = [
                alg,
                str(m.nodes_explored),
                str(m.path_length),
                str(m.path_cost),
                f"{m.execution_time * 1000:.2f}",
                optimal_map[alg],
            ]
            for val, cx in zip(row_data, col_xs):
                draw_text(screen, val, cx, y, size=17, color=col)
            y += 36

        # Insight notes
        y += 20
        notes = [
            "★  A* expands far fewer nodes than BFS thanks to the Manhattan Distance heuristic.",
            "★  BFS guarantees shortest path but explores entire frontier level-by-level.",
            "★  DFS reaches a path quickly but it is NOT optimal (may be much longer).",
            "★  Time Complexity: BFS = O(b^d)  |  DFS = O(b^m)  |  A* ≈ O(b^d) guided.",
        ]
        for note in notes:
            draw_text(screen, note, 70, y, size=14, color=(170, 190, 220))
            y += 26

        draw_text(screen, "Press any key to return to game",
                  total_w // 2, total_h - 40,
                  size=16, color=(130, 150, 200), center=True)

        pygame.display.flip()


# ══════════════════════════════════════════════════════════════════════════════
#  UI PANEL RENDERER
# ══════════════════════════════════════════════════════════════════════════════
def draw_panel(surface, pacman, ghosts, tick: int, show_overlay: bool,
               panel_x: int, panel_h: int, elapsed_seconds: float):
    """
    Draw the right-side information panel showing:
    - Score, lives, mode
    - AI metrics (nodes explored, path cost, time)
    - Ghost status
    - Controls legend
    """
    # Panel background
    panel_rect = pygame.Rect(panel_x, 0, PANEL_WIDTH, panel_h)
    pygame.draw.rect(surface, COLORS["ui_bg"], panel_rect)
    pygame.draw.line(surface, COLORS["ui_highlight"], (panel_x, 0), (panel_x, panel_h), 2)

    px = panel_x + 16
    y  = 14

    # Title
    draw_text(surface, "AI METRICS", px, y, size=20, color=COLORS["ui_accent"], bold=True)
    y += 34

    pygame.draw.line(surface, COLORS["ui_panel"], (px, y), (panel_x + PANEL_WIDTH - 16, y), 1)
    y += 10

    # ── Score & Lives ──────────────────────────────────────────────────────
    draw_text(surface, f"Score  : {pacman.score}", px, y, size=18, color=COLORS["ui_accent"])
    y += 28
    lives_str = "♥ " * pacman.lives + "♡ " * max(0, 3 - pacman.lives)
    draw_text(surface, f"Lives  : {lives_str}", px, y, size=17, color=(220, 60, 60))
    y += 28
    mode_str = "🤖 A* Agent" if not pacman.manual_mode else "🕹 Manual"
    draw_text(surface, f"Mode   : {mode_str}", px, y, size=16, color=COLORS["ui_text"])
    y += 36

    pygame.draw.line(surface, COLORS["ui_panel"], (px, y), (panel_x + PANEL_WIDTH - 16, y), 1)
    y += 12

    # ── A* Metrics ────────────────────────────────────────────────────────
    m = pacman.metrics
    draw_text(surface, "── A* Search Stats ──", px, y, size=15,
              color=COLORS["ui_highlight"], bold=True)
    y += 26

    metrics_rows = [
        ("Algorithm"   , m.algorithm),
        ("Nodes Expl." , str(m.nodes_explored)),
        ("Path Steps"  , str(m.path_length)),
        ("Path Cost"   , str(m.path_cost)),
        ("Exec. Time"  , format_time(m.execution_time)),
        ("Path Found"  , "Yes ✓" if m.path_found else "No ✗"),
    ]
    for label, val in metrics_rows:
        draw_text(surface, f"{label:<13}: {val}", px, y,
                  size=15, color=COLORS["ui_text"])
        y += 22
    y += 10

    pygame.draw.line(surface, COLORS["ui_panel"], (px, y), (panel_x + PANEL_WIDTH - 16, y), 1)
    y += 12

    # ── Whole-run summary ────────────────────────────────────────────────
    draw_text(surface, "── Game Summary ──", px, y, size=15,
              color=COLORS["ui_highlight"], bold=True)
    y += 24

    for label, value, col in build_run_summary_rows(pacman, elapsed_seconds)[:6]:
        draw_text(surface, f"{label:<13}: {value}", px, y, size=14, color=col)
        y += 20
    y += 8

    pygame.draw.line(surface, COLORS["ui_panel"], (px, y), (panel_x + PANEL_WIDTH - 16, y), 1)
    y += 12

    # ── Ghost status ──────────────────────────────────────────────────────
    draw_text(surface, "── Ghost Status ──", px, y, size=15,
              color=COLORS["ui_highlight"], bold=True)
    y += 24

    ghost_algo_map = {
        "blinky": "BFS",  "pinky": "A*",
        "inky"  : "A*",   "clyde": "BFS",
    }
    for g in ghosts:
        status = "FRIGHTENED" if g.frightened else g.mode.upper()
        algo   = ghost_algo_map.get(g.name, "BFS")
        gtext  = f"{g.name.upper():<7} [{algo}] {status}"
        gcol   = g.color if not g.frightened else (100, 100, 255)
        draw_text(surface, gtext, px, y, size=14, color=gcol)
        y += 20
    y += 8

    pygame.draw.line(surface, COLORS["ui_panel"], (px, y), (panel_x + PANEL_WIDTH - 16, y), 1)
    y += 12

    ovl_state = "ON ✓" if show_overlay else "OFF"
    draw_text(surface, f"Overlay : {ovl_state}", px, y, size=14,
              color=(100, 240, 140) if show_overlay else (180, 80, 80))
    y += 28

    pygame.draw.line(surface, COLORS["ui_panel"], (px, y), (panel_x + PANEL_WIDTH - 16, y), 1)
    y += 12

    # ── Controls ──────────────────────────────────────────────────────────
    draw_text(surface, "── Controls ──", px, y, size=15,
              color=COLORS["ui_highlight"], bold=True)
    y += 22
    controls = [
        "SPACE  – Toggle AI/Manual",
        "Arrows – Manual movement",
        "V      – Toggle overlay",
        "C      – Compare algorithms",
        "R      – Restart",
        "ESC    – Quit",
    ]
    for ctrl in controls:
        draw_text(surface, ctrl, px, y, size=12, color=(140, 155, 190))
        y += 16


# ══════════════════════════════════════════════════════════════════════════════
#  MAIN GAME LOOP
# ══════════════════════════════════════════════════════════════════════════════
def run_game(difficulty: str = "Medium", start_ai: bool = True):
    # ── Initialise Pygame ─────────────────────────────────────────────────
    pygame.init()
    pygame.display.set_caption(TITLE)

    maze = Maze()
    move_delay = DIFFICULTIES.get(difficulty, 10)

    total_w = maze.pixel_width  + PANEL_WIDTH
    total_h = maze.pixel_height
    screen  = pygame.display.set_mode((total_w, total_h))
    clock   = pygame.time.Clock()

    # ── Show start screen ─────────────────────────────────────────────────
    difficulty, ai_mode = start_screen(screen, clock, maze.pixel_width, maze.pixel_height)
    move_delay = DIFFICULTIES.get(difficulty, 10)
    game_started_at = time.perf_counter()

    # ── Create agents ─────────────────────────────────────────────────────
    def make_agents():
        nonlocal maze
        maze = Maze()    # fresh maze each restart

        pm = PacMan(maze)
        pm.manual_mode = not ai_mode

        ghost_defs = [
            ("blinky", False, move_delay - 2),
            ("pinky",  True,  move_delay),
            ("inky",   True,  move_delay + 1),
            ("clyde",  False, move_delay - 1),
        ]
        gs = []
        spawns = maze.ghost_starts
        for i, (name, use_astar, delay) in enumerate(ghost_defs):
            spawn = spawns[i % len(spawns)]
            gs.append(Ghost(maze, name, spawn, use_astar=use_astar,
                            move_delay=delay))
        return pm, gs

    pacman, ghosts = make_agents()

    # ── State ─────────────────────────────────────────────────────────────
    show_overlay  = True
    game_over     = False
    won           = False
    tick          = 0
    death_pause   = 0       # ticks to wait after Pac-Man dies

    # Create maze surface (redrawn each frame)
    maze_surf = pygame.Surface((maze.pixel_width, maze.pixel_height))

    # ── Game loop ─────────────────────────────────────────────────────────
    running = True
    while running:
        clock.tick(FPS)
        tick += 1

        # ── Events ────────────────────────────────────────────────────────
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False

                elif event.key == pygame.K_r:
                    pacman, ghosts = make_agents()
                    game_over = won = False
                    tick = 0; death_pause = 0

                elif event.key == pygame.K_SPACE:
                    pacman.manual_mode = not pacman.manual_mode

                elif event.key == pygame.K_v:
                    show_overlay = not show_overlay

                elif event.key == pygame.K_c:
                    if not game_over:
                        all_pellets = maze.pellets | maze.power_pellets
                        if all_pellets:
                            goal = min(all_pellets,
                                       key=lambda p: manhattan_distance(
                                           (pacman.row, pacman.col), p))
                            comparison_screen(screen, clock, maze,
                                              (pacman.row, pacman.col),
                                              goal, total_w, total_h)

                # Manual movement keys
                elif not game_over:
                    pacman.handle_key(event.key)

        if not running:
            break

        # ── Logic update ──────────────────────────────────────────────────
        if not game_over and death_pause == 0:
            ghost_pos_list = [(g.row, g.col) for g in ghosts]

            # Pac-Man act (only non-frightened ghosts are threats)
            pacman.act([(g.row, g.col) for g in ghosts if not g.frightened])
            pacman.update_power()

            # Ghosts act
            pac_dir = (0, 1)
            if pacman.path:
                nr, nc = pacman.path[0]
                pac_dir = (nr - pacman.row, nc - pacman.col)

            for g in ghosts:
                g.update(pacman.row, pacman.col, pac_dir)

            # Power-pellet activation: frighten ghosts once, on the tick the
            # pellet is eaten (not every powered tick, which would re-frighten
            # ghosts that were just eaten and respawned)
            if pacman.power_just_activated:
                pacman.power_just_activated = False
                for g in ghosts:
                    g.frighten(200)

            # ── Collision detection ───────────────────────────────────────
            # A ghost touches Pac-Man if they share a cell now, or if Pac-Man
            # moved into the cell the ghost occupied before it moved (this
            # also catches the two swapping cells and passing through)
            pac_pos = (pacman.row, pacman.col)
            for g, g_prev in zip(ghosts, ghost_pos_list):
                if (g.row, g.col) == pac_pos or g_prev == pac_pos:
                    if g.frightened:
                        # Pac-Man eats ghost
                        g.reset(maze.ghost_starts[ghosts.index(g)
                                                   % len(maze.ghost_starts)])
                        pacman.score += 200
                        pacman.record_ghost_eaten()
                    else:
                        # Ghost catches Pac-Man
                        pacman.lives -= 1
                        pacman.record_life_lost()
                        pacman.dead  = True
                        death_pause  = FPS * 2    # 2-second pause
                        if pacman.lives <= 0:
                            game_over = True
                        break   # at most one life lost per tick

            # ── Win condition ─────────────────────────────────────────────
            remaining = len(maze.pellets) + len(maze.power_pellets)
            if remaining == 0 and not game_over:
                won = game_over = True

        elif death_pause > 0:
            death_pause -= 1
            if death_pause == 0 and pacman.lives > 0:
                pacman.reset()
                for i, g in enumerate(ghosts):
                    g.reset(maze.ghost_starts[i % len(maze.ghost_starts)])

        # ── Rendering ─────────────────────────────────────────────────────
        screen.fill(COLORS["dark_blue"])
        elapsed_seconds = time.perf_counter() - game_started_at

        # Maze
        maze.draw(
            maze_surf,
            explored_nodes = pacman.explored_nodes if show_overlay else None,
            solution_path  = pacman.path           if show_overlay else None,
            show_overlay   = show_overlay,
        )
        screen.blit(maze_surf, (0, 0))

        # Ghosts
        for g in ghosts:
            g.draw(screen, tick)

        # Pac-Man
        pacman.draw(screen, tick)

        # Remaining pellet count on maze
        remaining_count = len(maze.pellets) + len(maze.power_pellets)
        draw_text(screen, f"Pellets left: {remaining_count}",
                  8, maze.pixel_height - 24,
                  size=15, color=(200, 200, 180))

        # Right panel
        draw_panel(screen, pacman, ghosts, tick, show_overlay,
                   maze.pixel_width, maze.pixel_height, elapsed_seconds)

        pygame.display.flip()

        # ── Game-over screen ──────────────────────────────────────────────
        if game_over and death_pause == 0:
            replay = end_screen(screen, clock, won, pacman, total_w, total_h,
                                elapsed_seconds)
            if replay:
                pacman, ghosts = make_agents()
                game_over = won = False
                tick = 0; death_pause = 0
                game_started_at = time.perf_counter()
            else:
                running = False

    pygame.quit()


# ══════════════════════════════════════════════════════════════════════════════
#  ENTRY POINT
# ══════════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    run_game()
