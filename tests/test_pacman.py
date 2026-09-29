from bfs import distance_map
from maze import Maze
from pacman import PacMan, DANGER_RADIUS


def percept(pac, ghosts):
    return pac.perceive(ghosts)


def test_plans_to_nearest_pellet_without_ghosts(maze):
    pac = PacMan(maze)
    pac.plan(percept(pac, []))
    assert pac.path and pac.target_pellet in maze.pellets | maze.power_pellets
    assert pac.path[0] in maze.get_neighbors(pac.row, pac.col)


def test_path_keeps_clear_of_ghosts(maze):
    pac = PacMan(maze)
    ghost = (16, 13)                   # three cells to the right on the same row
    pac.plan(percept(pac, [ghost]))
    dist = distance_map(maze, [ghost])
    assert pac.path
    assert all(dist[cell] > DANGER_RADIUS for cell in pac.path)


def test_stays_put_when_boxed_in_between_ghosts(maze):
    pac = PacMan(maze)
    # Pac-Man's start corridor is sealed by a ghost two cells away on each side
    pac.plan(percept(pac, [(16, 8), (16, 12)]))
    assert pac.path == [] and pac.target_pellet is None


def test_flees_away_from_ghost_guarding_the_last_pellet():
    maze = Maze([[1, 1, 1, 1, 1, 1, 1, 1],
                 [1, 0, 0, 'P', 0, 'G', 2, 1],
                 [1, 1, 1, 1, 1, 1, 1, 1]])
    pac = PacMan(maze)
    pac.plan(percept(pac, [(1, 5)]))
    assert pac.path == [(1, 2)]


def test_act_moves_one_cell_every_fourth_tick(maze):
    pac = PacMan(maze)
    start = (pac.row, pac.col)
    for _ in range(3):
        pac.act([])
    assert (pac.row, pac.col) == start
    pac.act([])
    assert (pac.row, pac.col) in maze.get_neighbors(*start)


def test_collecting_pellets_scores(maze):
    pac = PacMan(maze)
    pac.row, pac.col = next(iter(maze.pellets))
    pac._collect_pellet()
    assert pac.score == 10 and (pac.row, pac.col) not in maze.pellets

    pac.row, pac.col = next(iter(maze.power_pellets))
    pac._collect_pellet()
    assert pac.score == 60 and pac.powered and pac.power_just_activated
