import random

import pytest

from astar import astar_search, astar_to_nearest_pellet
from bfs import bfs_search, bfs_next_step, distance_map, nearest_reachable
from dfs import dfs_search


def assert_valid_path(maze, path, start, goal):
    assert path[0] == start and path[-1] == goal
    for a, b in zip(path, path[1:], strict=False):
        assert b in maze.get_neighbors(*a)


@pytest.fixture
def pairs(reachable):
    rng = random.Random(0)
    return [(rng.choice(reachable), rng.choice(reachable)) for _ in range(300)]


def test_astar_matches_bfs_length_and_never_expands_more(maze, pairs):
    for start, goal in pairs:
        a_path, _, a_m = astar_search(maze, start, goal)
        b_path, _, b_m = bfs_search(maze, start, goal)
        assert_valid_path(maze, a_path, start, goal)
        assert len(a_path) == len(b_path)          # both optimal
        assert a_m.path_cost == len(a_path) - 1
        assert a_m.nodes_explored <= b_m.nodes_explored


def test_dfs_finds_a_valid_but_not_shorter_path(maze, pairs):
    for start, goal in pairs:
        d_path, _, _ = dfs_search(maze, start, goal)
        b_path, _, _ = bfs_search(maze, start, goal)
        assert_valid_path(maze, d_path, start, goal)
        assert len(d_path) >= len(b_path)


def test_start_equals_goal(maze):
    s = maze.pacman_start
    for search in (astar_search, bfs_search, dfs_search):
        path, _, metrics = search(maze, s, s)
        assert path == [s]
        assert metrics.path_found


def test_unreachable_goal_returns_empty_path(maze):
    wall = next(iter(maze.walls))
    for search in (astar_search, bfs_search, dfs_search):
        path, _, metrics = search(maze, maze.pacman_start, wall)
        assert path == []
        assert not metrics.path_found


def test_astar_avoids_blocked_cells(maze):
    start, goal = maze.pacman_start, (16, 14)
    direct, _, _ = astar_search(maze, start, goal)
    blocked = frozenset({direct[2]})
    detour, _, _ = astar_search(maze, start, goal, blocked)
    assert detour and not blocked & set(detour)
    assert len(detour) > len(direct)


def test_bfs_next_step_is_first_step_of_shortest_path(maze, pairs):
    for start, goal in pairs:
        step = bfs_next_step(maze, start, goal)
        if start == goal:
            assert step is None
            continue
        dist = distance_map(maze, [goal])
        assert step in maze.get_neighbors(*start)
        assert dist[step] == dist[start] - 1


def test_distance_map_matches_bfs(maze, pairs):
    for start, goal in pairs[:50]:
        path, _, _ = bfs_search(maze, start, goal)
        assert distance_map(maze, [start])[goal] == len(path) - 1


def test_nearest_reachable_is_truly_nearest(maze, reachable):
    rng = random.Random(1)
    for _ in range(100):
        start = rng.choice(reachable)
        targets = set(rng.sample(reachable, 10))
        found = nearest_reachable(maze, start, targets)
        dist = distance_map(maze, [start])
        assert dist[found] == min(dist[t] for t in targets)


def test_nearest_reachable_respects_blocked_cells(maze):
    start = maze.pacman_start
    near = nearest_reachable(maze, start, maze.pellets)
    assert nearest_reachable(maze, start, {near}, frozenset({near})) is None


def test_astar_to_nearest_pellet_beats_manhattan_choice(maze):
    # From (10, 9) the Manhattan-nearest pellet (14, 9) is 9 steps further
    # by path than the truly nearest one
    start = (10, 9)
    pellets = maze.pellets | maze.power_pellets
    path, _, _, target = astar_to_nearest_pellet(maze, start, pellets)
    dist = distance_map(maze, [start])
    assert target != (14, 9)
    assert len(path) - 1 == min(dist[p] for p in pellets)
    assert dist[(14, 9)] - (len(path) - 1) == 9


def test_astar_to_nearest_pellet_with_no_pellets(maze):
    path, explored, _, target = astar_to_nearest_pellet(maze, maze.pacman_start, set())
    assert (path, explored, target) == ([], set(), None)
