import pytest

from maze import Maze, MAZE_LAYOUT, validate_layout


def test_default_maze_facts(maze, reachable):
    assert (maze.rows, maze.cols) == (22, 21)
    assert len(maze.pellets) == 166
    assert len(maze.power_pellets) == 4
    assert maze.pacman_start == (16, 10)
    assert len(maze.ghost_starts) == 2
    assert len(reachable) == 209


def test_every_pellet_is_reachable(maze, reachable):
    assert (maze.pellets | maze.power_pellets) <= set(reachable)


def test_neighbours_are_adjacent_and_walkable(maze, reachable):
    for cell in reachable:
        for n in maze.get_neighbors(*cell):
            assert abs(n[0] - cell[0]) + abs(n[1] - cell[1]) == 1
            assert not maze.is_wall(*n)


def test_out_of_bounds_counts_as_wall(maze):
    assert maze.is_wall(-1, 0)
    assert maze.is_wall(0, maze.cols)


@pytest.mark.parametrize("layout, message", [
    ([], "empty"),
    ([[1, 1, 1], [1, 'P']], "row 1"),
    ([[1, 'X', 'P', 'G', 2]], "unknown maze cell"),
    ([[1, 2, 'G', 1]], "exactly one 'P'"),
    ([[1, 'P', 'P', 'G', 2]], "exactly one 'P'"),
    ([[1, 'P', 2, 1]], "ghost spawn"),
    ([[1, 'P', 'G', 0]], "no pellets"),
])
def test_invalid_layouts_are_rejected(layout, message):
    with pytest.raises(ValueError, match=message):
        validate_layout(layout)


def test_custom_layout():
    m = Maze([[1, 1, 1, 1, 1],
              [1, 'P', 2, 'G', 1],
              [1, 1, 1, 1, 1]])
    assert (m.rows, m.cols) == (3, 5)
    assert m.pellets == {(1, 2)}


def test_default_layout_is_valid():
    validate_layout(MAZE_LAYOUT)
