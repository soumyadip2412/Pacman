import pytest

from game import DEATH_PAUSE_TICKS, FRIGHT_TICKS, Game
from utils import LEFT, RIGHT

# A straight corridor: Pac-Man in the middle, ghost spawns at both ends
CORRIDOR = [
    [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
    [1, 'G', 2, 2, 2, 'P', 2, 2, 3, 'G', 1],
    [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
]


def freeze_ghosts(game):
    """Stop ghosts from moving on their own so a test can place them."""
    for g in game.ghosts:
        g.update = lambda *a, **k: None


def manual_game(**kwargs):
    game = Game("Medium", ai_mode=False, seed=0, layout=CORRIDOR, **kwargs)
    freeze_ghosts(game)
    return game


def step_until_pacman_moves(game):
    start = (game.pacman.row, game.pacman.col)
    for _ in range(10):
        game.step()
        if (game.pacman.row, game.pacman.col) != start or game.pacman.dead:
            return
    raise AssertionError("Pac-Man never moved")


def test_unknown_difficulty_is_rejected():
    with pytest.raises(ValueError, match="difficulty"):
        Game("Impossible")


def test_two_ghosts_on_one_tick_cost_one_life():
    game = manual_game()
    pac = game.pacman
    for g in game.ghosts:
        g.row, g.col = pac.row, pac.col
    game.step()
    assert pac.lives == 2
    assert game.death_pause == DEATH_PAUSE_TICKS


def test_ghost_swapping_cells_with_pacman_is_a_hit():
    game = manual_game()
    pac, ghost = game.pacman, game.ghosts[0]
    ghost.row, ghost.col = pac.row, pac.col + 1
    game.ghosts[1].row, game.ghosts[1].col = 1, 1

    def swap(*_):                       # ghost steps into Pac-Man's old cell
        ghost.row, ghost.col = 1, 5
    ghost.update = swap

    game.steer(RIGHT)
    step_until_pacman_moves(game)
    assert pac.lives == 2


def test_power_pellet_frightens_once_and_eaten_ghost_respawns_normal():
    game = manual_game()
    pac = game.pacman
    right = [g for i, g in enumerate(game.ghosts) if game.ghost_spawn(i) == (1, 9)]
    game.steer(RIGHT)
    while (pac.row, pac.col) != (1, 8):
        game.step()
    assert pac.powered
    assert all(g.frightened for g in game.ghosts)
    assert all(g.fright_timer <= FRIGHT_TICKS for g in game.ghosts)

    # Eat the frightened ghosts waiting in the next cell
    step_until_pacman_moves(game)
    assert pac.total_ghosts_eaten == len(right) == 2
    assert pac.score == 2 * 10 + 50 + 2 * 200   # two pellets, power pellet, two ghosts

    # They respawn and stay normal while Pac-Man is still powered
    for _ in range(20):
        game.step()
    assert pac.powered
    assert not any(g.frightened for g in right)


def test_death_pause_then_respawn():
    game = manual_game()
    pac = game.pacman
    game.steer(LEFT)
    game.ghosts[0].row, game.ghosts[0].col = 1, 4
    step_until_pacman_moves(game)
    assert pac.dead and pac.lives == 2
    for _ in range(DEATH_PAUSE_TICKS):
        game.step()
    assert not pac.dead
    assert (pac.row, pac.col) == game.maze.pacman_start
    assert [(g.row, g.col) for g in game.ghosts] == [game.ghost_spawn(i) for i in range(4)]


def test_game_over_after_last_life():
    game = manual_game()
    game.pacman.lives = 1
    game.ghosts[0].row, game.ghosts[0].col = game.pacman.row, game.pacman.col
    game.step()
    assert game.game_over and not game.won and not game.finished
    for _ in range(DEATH_PAUSE_TICKS):
        game.step()
    assert game.finished


def test_win_when_last_pellet_is_eaten():
    game = Game("Easy", ai_mode=True, seed=0, layout=[
        [1, 1, 1, 1, 1],
        [1, 'P', 2, 'G', 1],
        [1, 1, 1, 1, 1],
    ])
    freeze_ghosts(game)
    game.ghosts = game.ghosts[:0]       # no ghosts at all
    for _ in range(10):
        game.step()
    assert game.won and game.finished and game.pellets_left == 0


def snapshot(game):
    return (game.pacman.row, game.pacman.col, game.pacman.score, game.pacman.lives,
            tuple((g.row, g.col, g.frightened) for g in game.ghosts))


def test_same_seed_replays_the_same_game():
    a, b = Game("Hard", seed=7), Game("Hard", seed=7)
    for _ in range(1500):
        a.step()
        b.step()
        assert snapshot(a) == snapshot(b)


def test_restart_resets_everything():
    game = Game("Medium", seed=3)
    for _ in range(300):
        game.step()
    game.restart()
    fresh = Game("Medium", seed=3)
    assert snapshot(game) == snapshot(fresh)
    assert game.pellets_left == fresh.pellets_left and game.tick == 0


@pytest.mark.parametrize("difficulty", ["Easy", "Medium"])
def test_ai_clears_the_real_maze(difficulty):
    game = Game(difficulty, ai_mode=True, seed=0)
    for _ in range(20000):
        game.step()
        if game.finished:
            break
    assert game.finished and game.won
    assert game.pacman.lives >= 1
