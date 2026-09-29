"""Smoke tests: every screen renders on a headless display without crashing."""
import pygame
import pytest

import main
from game import Game


class FakeClock:
    def tick(self, *_):
        return 0


def key(k):
    return pygame.event.Event(pygame.KEYDOWN, key=k)


@pytest.fixture
def scripted_events(monkeypatch):
    """Feed a scripted list of per-frame events into pygame.event.get()."""
    def install(script, quit_after):
        frame = {"n": 0}

        def get(*_a, **_k):
            frame["n"] += 1
            if frame["n"] > quit_after:
                return [pygame.event.Event(pygame.QUIT)]
            return script.get(frame["n"], [])

        monkeypatch.setattr(pygame.event, "get", get)
        monkeypatch.setattr(pygame.time, "Clock", FakeClock)
        return frame
    return install


@pytest.fixture
def screen():
    pygame.init()
    main._fonts.clear()
    return pygame.display.set_mode((main.COLS * main.CELL_SIZE + main.PANEL_WIDTH,
                                    main.ROWS * main.CELL_SIZE))


def test_full_game_loop_renders(scripted_events, monkeypatch):
    monkeypatch.setattr(main, "start_screen", lambda *a: ("Hard", True))
    ended = {}

    def end_screen(screen, clock, won, pacman, *a):
        ended["won"] = won
        return False
    monkeypatch.setattr(main, "end_screen", end_screen)

    frames = scripted_events({
        20: [key(pygame.K_v)],               # overlay off
        40: [key(pygame.K_v)],               # overlay on
        60: [key(pygame.K_c)],               # open comparison screen
        61: [key(pygame.K_SPACE)],           # any key closes it
        80: [key(pygame.K_LEFT)],            # manual control
        120: [key(pygame.K_SPACE)],          # back to AI
        200: [key(pygame.K_r)],              # restart
    }, quit_after=3000)
    main.run_game(seed=0)
    assert frames["n"] > 200


def test_start_screen_returns_choice(scripted_events, screen):
    scripted_events({3: [key(pygame.K_RETURN)]}, quit_after=100)
    assert main.start_screen(screen, FakeClock(), 588, 616) == ("Medium", True)


@pytest.mark.parametrize("won", [True, False])
def test_end_screen_replays_on_r(scripted_events, screen, won):
    game = Game("Easy", seed=0)
    scripted_events({3: [key(pygame.K_r)]}, quit_after=100)
    assert main.end_screen(screen, FakeClock(), won, game.pacman, 908, 616, 12.5) is True


def test_panel_renders_every_state(screen):
    game = Game("Medium", seed=0)
    for lives in (3, 1, 0):
        game.pacman.lives = lives
        for g in game.ghosts[:2]:
            g.frighten(10)
        game.pacman.manual_mode = lives == 1
        main.draw_panel(screen, game.pacman, game.ghosts, 1, lives != 0,
                        588, 616, 3.0)
