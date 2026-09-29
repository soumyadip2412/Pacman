"""Shared test setup: run pygame headlessly and import the game modules."""
import os
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest  # noqa: E402

from maze import Maze  # noqa: E402


@pytest.fixture
def maze():
    return Maze()


@pytest.fixture
def reachable(maze):
    """Every cell reachable from Pac-Man's start (the playable graph)."""
    from bfs import distance_map
    return sorted(distance_map(maze, [maze.pacman_start]))
