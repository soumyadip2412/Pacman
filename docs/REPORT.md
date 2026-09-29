> **Note (updated):** this is the original academic write-up. Numbers and design details below were corrected to match the code; the up-to-date results come from `python benchmark.py` and are listed in the [README](../README.md#results).

# Intelligent Pac-Man Agent Using A* Search Algorithm

College: [Your College Name]

Department: Department of Computer Science & Engineering

Academic Year: 2025–2026

Project Title: Intelligent Pac-Man Agent Using A* Search Algorithm

Student Name: [Student Full Name]

USN: [Your Student Number]

Guide Name: [Supervisor / Guide Name]

---

## ABSTRACT (150–200 words)

This project implements an intelligent Pac-Man agent using the A* search algorithm to perform goal-directed pathfinding in a grid-based maze environment. The core problem is to collect all pellets while avoiding adversarial agents (ghosts) that follow simple pursuit policies. We model Pac-Man as a goal-based intelligent agent that repeatedly plans optimal paths to the nearest pellet using A*, guided by a Manhattan distance heuristic. For comparison and evaluation, we implement BFS and DFS as alternative search methods and measure metrics such as nodes explored, path length, execution time, and search frequency. The system is implemented in Python using Pygame for visualization; algorithm code leverages heap-based open lists and closed sets for efficient A* operations. Experimental results (per-run summaries and aggregated tables) show that A* explores fewer nodes and achieves optimal path lengths compared to BFS and DFS, while maintaining low execution time suitable for real-time gameplay. The project demonstrates practical applications of heuristic search in real-time agent control and provides a reproducible evaluation framework for academic assessment.

---

## 1. INTRODUCTION

1.1 Importance of AI in Gaming

Artificial Intelligence (AI) plays a central role in modern gaming systems — from NPC behaviour and path planning to dynamic difficulty and procedural content generation. In educational settings, games provide an interactive, visual platform for teaching AI concepts such as search algorithms, heuristics, and agent architectures.

1.2 Intelligent Agents

An intelligent agent perceives its environment, reasons about possible actions, and selects actions that achieve goals. In this project, Pac-Man is modelled as a goal-based intelligent agent that repeatedly plans optimal actions to collect pellets while avoiding ghosts.

1.3 Pathfinding Problems

Pathfinding in grid mazes is a canonical AI problem: the state space is discrete, transitions are deterministic, and costs are typically uniform. Selecting an efficient algorithm and heuristic greatly affects performance in time-sensitive applications like games.

1.4 Why Pac-Man

Pac-Man is a pedagogically rich environment: it combines planning, adversarial dynamics (ghosts), limited resources (lives, pellets), and real-time requirements. It is ideal for exploring informed search (A*) vs. uninformed methods (BFS, DFS).

1.5 Objectives

- Implement A*, BFS, and DFS for grid pathfinding in a Pac-Man maze.
- Model Pac-Man as a goal-based agent that replans periodically.
- Compare algorithms with quantitative metrics (nodes explored, time, path length).
- Create a reproducible evaluation and produce an academic report.

---

## 2. PROBLEM DESCRIPTION & REQUIREMENTS

2.1 Problem Statement

Design and implement a goal-based intelligent Pac-Man agent that collects all pellets in a maze while avoiding ghosts. The agent must plan and execute paths in real time, and the system must record search performance metrics for academic evaluation.

2.2 Functional Requirements

- Autonomous agent using A* to plan paths to pellets.
- Alternative algorithms (BFS, DFS) for offline comparison and demonstration.
- Visualization of maze, explored nodes, and solution path.
- Ghost agents with simple chase/ambush behaviours.
- Restart and quit controls; final run summary.

2.3 Non-functional Requirements

- Real-time responsiveness (30 FPS game loop; search latency << frame time).
- Reproducible metrics and logging.
- Cross-platform using Python and Pygame.
- Clear code structure and documentation for assessment.

2.4 Inputs

- Maze topology (grid walls, pellet positions)
- Initial positions for Pac-Man and ghosts
- Difficulty settings to control ghost speed

2.5 Outputs

- Visual display of the game
- Live metrics panel (nodes explored, execution time, path cost)
- End-of-run summary; reproducible measurements with `benchmark.py`

2.6 Constraints

- 4-directional movement only (UP/DOWN/LEFT/RIGHT)
- Unit step costs
- Limited compute per frame (real-time requirement)

---

## 3. AGENT DESIGN

3.1 Goal-Based Agent

The agent is goal-based: its goal is to reduce the remaining pellet set to empty. The agent repeatedly computes a plan (sequence of moves) to reach the currently selected pellet and executes the plan step-by-step, re-planning when necessary (e.g., if ghosts threaten the path).

3.2 Environment Analysis

- Fully observable: the agent has access to the entire maze and ghost positions.
- Deterministic: actions have predictable outcomes.
- Dynamic: ghosts move independently, changing the state between plans.
- Discrete: the maze is a finite grid of discrete cells.

3.3 State Space Representation

State: (row, col) — the grid cell of Pac-Man. The environment state for planning includes a set of remaining pellets and positions of ghosts (for safety checks).

3.4 Initial State

Pac-Man's spawn location, e.g., (r0, c0). Maze pellet set is initialized from the layout.

3.5 Goal State

All pellets collected: pellet set is empty.

3.6 Agent Architecture

Perceive → Plan → Act cycle:

- Perceive: read Pac-Man position, pellet set, and ghost positions.
- Plan: run A* (to nearest pellet) to compute a path.
- Act: move one step along the planned path, update environment.
- Replan: on path exhaustion, danger detection, or periodic timer.

---

## 4. DESIGN OF THE PROJECT

4.1 System Architecture

The system consists of:

- Frontend / Renderer: `main.py` and `pygame` display loop.
- Agent module: `pacman.py` containing the agent's planning and act cycle.
- Search modules: `astar.py`, `bfs.py`, `dfs.py` implementing algorithms.
- Maze model: `maze.py` representing walls, pellets, and conversions between cell coordinates and pixels.
- Utilities: `utils.py` for metric dataclasses, timing, and helpers.

4.2 Module Explanation

- `main.py`: Game loop, UI panels, start and end screens, and high-level orchestration.
- `pacman.py`: Pac-Man agent (perceive/plan/act), cumulative stats, movement and pellet collection.
- `astar.py`: A* algorithm implementation with metrics collection.
- `bfs.py`, `dfs.py`: Implement BFS and DFS, returning comparable metrics.
- `ghost.py`: Ghost agents and behaviour logic.

4.3 Frontend

Implemented in Pygame; renders the maze, pac-man sprite, ghosts, overlay for explored nodes, and a right-side metrics panel.

4.4 Backend Logic

Game state is updated each tick. Pac-Man executes the agent loop; ghosts update using simple policies. Collision checks and pellet collection occur on each movement step.

4.5 AI / Search Modules

Each search function returns:

- `path`: the sequence of states from start to goal
- `explored`: set of nodes popped from the frontier
- `metrics`: `AlgorithmMetrics` object with nodes_explored, path_length, execution_time, path_cost

4.6 Maze Representation

Grid of cells; walls are boolean masks. Pellet positions are sets of (row, col). Cell size is uniform and converted to pixels for rendering.

4.7 Ghost Behavior

- Blinky / Clyde: direct chase using BFS for next step
- Pinky / Inky: use A* variants (ambush behaviour; Inky alternates modes)
- Frightened mode: ghosts become vulnerable when Pac-Man collects power pellets

4.8 Flowcharts (textual)

Agent planning loop:

1. Perceive environment
2. If (path empty) or (danger) or (replan timer expired): run A* to nearest pellet
3. Execute one step along path
4. Update pellet set, score, and stats
5. Repeat

Game loop:

1. Handle input/events
2. Update Pac-Man (act, power status)
3. Update ghosts
4. Detect collisions
5. Render frame
6. End condition check

---

## 5. ALGORITHMS USED & IMPLEMENTATION

5.1 Breadth-First Search (BFS)

BFS explores the search space level-by-level using a FIFO queue. It is complete and optimal for uniform-cost graphs but can be memory-intensive.

Pseudocode (high level):

```
function BFS(start, goal):
  frontier = Queue([start])
  came_from = {start: None}
  while frontier not empty:
    node = frontier.pop()
    if node == goal: return reconstruct_path(came_from)
    for neighbor in neighbors(node):
      if neighbor not in came_from and not wall:
         frontier.push(neighbor)
         came_from[neighbor] = node
  return []  # no path
```

Time complexity: O(b^d)

Space complexity: O(b^d)

Advantages: Guaranteed shortest path (for unit costs). Disadvantages: high memory for large search trees.

5.2 Depth-First Search (DFS)

DFS explores deep branches first using a LIFO stack. It uses less memory but is not guaranteed to find the shortest path.

Pseudocode (high level):

```
function DFS(start, goal):
  frontier = Stack([start])
  came_from = {start: None}
  while frontier not empty:
    node = frontier.pop()
    if node == goal: return reconstruct_path(came_from)
    for neighbor in neighbors(node):
      if neighbor not in came_from and not wall:
         frontier.push(neighbor)
         came_from[neighbor] = node
  return []
```

Time complexity: O(b^m) where m is maximum depth; space: O(b * m)

Advantages: Low memory. Disadvantages: May return very long paths, not optimal.

5.3 A* Search Algorithm

A* is an informed search algorithm that expands nodes according to f(n) = g(n) + h(n), where g(n) is the cost so far and h(n) is a heuristic estimate of remaining cost.

Formulas:

f(n) = g(n) + h(n)

h(n) = |x1 - x2| + |y1 - y2|  (Manhattan distance)

Pseudocode (high level):

```
function A*(start, goal):
  open = priority_queue([(f=0, g=0, start)])
  came_from = {}
  g_score = {start: 0}
  while open not empty:
    f, g, node = pop_min(open)
    if node == goal: return reconstruct_path(came_from, start, goal)
    for neighbor in neighbors(node):
      tentative_g = g + cost(node, neighbor)
      if tentative_g < g_score.get(neighbor, INF):
         came_from[neighbor] = node
         g_score[neighbor] = tentative_g
         f_score = tentative_g + h(neighbor, goal)
         push(open, (f_score, tentative_g, neighbor))
  return []
```

Time complexity: O(b^d) in worst case, but typically much lower with an effective heuristic.

Space complexity: O(b^d) — it stores open and closed sets.

Why A* was selected

- A* is optimal (for admissible heuristics) and efficient in practice when guided by a good heuristic such as Manhattan distance. It reduces node expansions compared to uninformed search while guaranteeing shortest paths.

Manhattan Distance heuristic

For 4-directional grid movement, Manhattan distance is admissible and consistent:

h(n) = |r_n - r_goal| + |c_n - c_goal|

It never overestimates real path cost and ensures A* re-expansions are not needed when g-scores are managed correctly.

---

## 6. IMPLEMENTATION DETAILS

6.1 Languages & Libraries

- Python 3.10+
- Pygame: rendering and the game loop
- heapq: priority queue for A* open list
- collections: deque for BFS frontier
- time: timing for execution metrics
- Optional: numpy (if array operations used)

6.2 Maze Generation & Representation

The maze is represented as a 2D boolean array (walls vs walkable). Pellet positions are stored in sets of (row, col). The renderer maps grid coordinates to pixels via a fixed `CELL_SIZE`.

Code snippet: Maze cell helpers

```python
def cell_rect(row, col, cell_size):
    return (col * cell_size, row * cell_size, cell_size, cell_size)

def reconstruct_path(came_from, start, goal):
    path = []
    cur = goal
    while cur != start:
        path.append(cur)
        cur = came_from[cur]
    path.append(start)
    path.reverse()
    return path
```

6.3 Pathfinding Implementation (A*)

- Use `heapq` to store tuples `(f_score, g_score, node)`.
- Maintain `g_score` dict and a closed set of expanded nodes.
- Count nodes popped from heap as `nodes_explored`.

Code snippet: core A* loop (simplified)

```python
import heapq

def astar_search(maze, start, goal, heuristic):
    open_heap = []
    heapq.heappush(open_heap, (heuristic(start, goal), 0, start))
    came_from = {}
    g_score = {start: 0}
    explored = set()
    nodes_explored = 0
    while open_heap:
        f, g, node = heapq.heappop(open_heap)
        if node in explored: continue
        explored.add(node)
        nodes_explored += 1
        if node == goal:
            path = reconstruct_path(came_from, start, goal)
            return path, explored, nodes_explored
        for nbr in neighbors(node):
            if maze.is_wall(*nbr): continue
            tentative_g = g + 1
            if tentative_g < g_score.get(nbr, float('inf')):
                g_score[nbr] = tentative_g
                came_from[nbr] = node
                heapq.heappush(open_heap, (tentative_g + heuristic(nbr, goal), tentative_g, nbr))
    return [], explored, nodes_explored
```

6.4 Ghost Movement & Collision Detection

- Each ghost has an update policy (BFS next-step or A*-based ambush). On each tick, ghosts compute a short plan or next step toward the target.
- Collision detection: if a ghost shares Pac-Man's cell and is not frightened, Pac-Man loses a life and triggers a death animation; if the ghost is frightened, Pac-Man eats the ghost and receives score.

6.5 Scoring System

- Normal pellet: +10 points
- Power pellet: +50 points and triggers frightened mode
- Eating frightened ghost: +200 points

6.6 Metrics & Logging

- `AlgorithmMetrics` dataclass stores nodes_explored, path_length, execution_time, path_cost, path_found.
- Cumulative statistics tracked per run: total searches, total nodes explored, total search time, total steps moved, pellets collected, ghosts eaten, lives lost.

---

## 7. TOOLS AND APIS USED

7.1 Why Python

- Rapid prototyping, strong standard library for algorithms, and wide academic usage make Python appropriate for assignments and demonstrations.

7.2 Why Pygame

- Lightweight 2D rendering library; excellent for teaching and visualizing AI algorithms without heavy engine complexity.

7.3 Why A*

- Balances optimality and efficiency via heuristics; well-suited for grid-based pathfinding with unit costs.

7.4 Libraries Summary

- `pygame` — rendering & event loop
- `heapq` — priority queue for A*
- `collections` — `deque` for BFS
- `time` — precise timing for metrics

---

## 8. RESULTS

8.1 Expected Output

- A playable Pac-Man game where the AI agent collects pellets while avoiding ghosts. The UI displays explored nodes overlay, solution path, live metrics, and final-run summary.

8.2 Screenshot Placeholders

- [Figure 1: Running game with overlay showing explored nodes]
- [Figure 2: End-of-run summary screen]

8.3 Performance Metrics (example format)

Per-run metrics to capture (CSV-compatible):

Run,Score,PlayTime_s,Searches,TotalNodes,AvgNodesPerSearch,TotalSearchTime_s,AvgSearch_ms,Steps,Pellets,PowerPellets,GhostsEaten,LivesLost

Measured results (`python benchmark.py`, every ordered pair of the 209 reachable cells, 43,472 searches per algorithm):

| Metric | BFS | DFS | A* |
|--------|----:|----:|---:|
| Mean nodes expanded | 105.5 | 105.5 | 34.4 |
| Shortest path found | 100% | 12% | 100% |
| Path length vs optimal | 1.0x | 4.62x mean, 63x max | 1.0x |

AI agent, 40 seeded games per difficulty: Easy 40/40 wins, Medium 40/40, Hard 23/40.

8.4 Discussion of Results

- A* consistently finds optimal-length paths with far fewer node expansions than BFS, demonstrating effectiveness of the Manhattan heuristic. DFS finds a path faster in some cases but often much longer and unreliable.

---

## 9. NOVELTY OF THE WORK

- Real-time integration of A* planning with reactive re-planning for ghost avoidance.
- Detailed per-run metrics and an evaluation framework packaged with the game for reproducible experiments.
- Visual overlay of explored nodes supporting analysis of search behaviour.

---

## 10. SOCIETAL IMPACT & APPLICATIONS

- Educational tool for teaching search algorithms and agent design.
- Path planning techniques applicable to robotics navigation and autonomous vehicles (grid approximations).
- Game AI practices transferable to NPC behaviour in commercial and academic games.

---

## 11. LEARNING OUTCOMES

- Understanding of informed vs. uninformed search.
- Practical implementation of A* with admissible heuristic.
- Experience integrating algorithms into interactive systems.
- Collecting and reporting experimental metrics for evaluation.

---

## 12. FUTURE IMPROVEMENTS

- Reinforcement Learning (e.g., DQN) for learning policies without explicit planning.
- Adaptive ghost AI employing prediction or learning.
- Multi-agent coordination and cooperative strategies.
- Dynamic maze generation for varied testing.

---

## 13. CONCLUSION

This project demonstrates that A* with Manhattan distance is a practical, efficient solution for grid-based pathfinding in a real-time Pac-Man environment. The agent achieves optimal path lengths while exploring significantly fewer nodes than uninformed methods. The system is a useful teaching platform for search algorithms and provides a reproducible evaluation scaffold for academic assessment.

---

## 14. REFERENCES

1. Russell, S. and Norvig, P., "Artificial Intelligence: A Modern Approach", 4th Edition, Pearson, 2020.
2. Hart, P. E., Nilsson, N. J., & Raphael, B. (1968). "A Formal Basis for the Heuristic Determination of Minimum Cost Paths". IEEE Transactions on Systems Science and Cybernetics.
3. Pygame Documentation — https://www.pygame.org/docs/
4. Python heapq module — https://docs.python.org/3/library/heapq.html
5. LaValle, S. M., "Planning Algorithms", Cambridge University Press, 2006.

---

## 15. VIVA QUESTIONS & ANSWERS (20+)

1. Q: What is a goal-based agent?  
A: An agent that selects actions based on goals it tries to achieve; it plans to reach states that satisfy the goal condition rather than reacting solely to perceptual inputs.

2. Q: Define the state space used in the Pac-Man project.  
A: The state is a grid cell coordinate `(row, col)`. The planning state includes Pac-Man's position and the target pellet. The full environment includes pellet sets and ghost positions for safety checks.

3. Q: What makes Manhattan distance an admissible heuristic?  
A: For 4-direction movement with unit step costs, Manhattan distance never overestimates the true shortest path because it measures the minimum number of orthogonal moves needed in absence of obstacles.

4. Q: Why is A* preferred over BFS in this project?  
A: A* uses a heuristic to focus search towards the goal, reducing node expansions while retaining optimality with an admissible heuristic. BFS explores uniformly across depths and expands many irrelevant nodes.

5. Q: What does f(n) = g(n) + h(n) represent?  
A: `g(n)` is the cost so far to reach node `n`, `h(n)` is the heuristic estimate to the goal, `f(n)` estimates total cost through `n` and is used to prioritize node expansion.

6. Q: How do you ensure A* implementation returns optimal paths?  
A: Use an admissible and consistent heuristic (Manhattan), maintain correct `g_score` values, and use a stable tie-breaking strategy with `(f, g, node)` to push into the priority queue.

7. Q: What are the worst-case time and space complexities of A*?  
A: Worst-case time and space are O(b^d), but with a good heuristic practical performance is much better.

8. Q: Explain BFS properties.  
A: BFS is complete and optimal on unweighted graphs, explores level-by-level, but requires O(b^d) memory.

9. Q: Explain DFS properties.  
A: DFS is memory-efficient (O(b·m)) but not optimal and can get trapped in deep branches; suitable when memory is constrained and any solution is acceptable.

10. Q: How is collision detection implemented?  
A: Compare Pac-Man's cell with each ghost's cell after movement; if equal and ghost not frightened then Pac-Man loses a life, otherwise Pac-Man scores for eating frightened ghosts.

11. Q: What metrics are recorded for each search?  
A: nodes_explored, path_length, execution_time, path_cost, path_found.

12. Q: How do you measure average nodes per search?  
A: Total nodes explored across all searches divided by the number of searches executed in a run.

13. Q: Why does the UI show explored nodes overlay?  
A: To visualise the search process and provide qualitative insight into how many nodes A* expands versus uninformed methods.

14. Q: What is a consistent heuristic and why is it useful?  
A: A heuristic `h` is consistent if `h(n) ≤ cost(n,n') + h(n')`. It guarantees A*'s `f` values are non-decreasing along paths and avoids re-expanding closed nodes.

15. Q: How does ghost frightened mode work?  
A: When Pac-Man consumes a power pellet, ghosts switch to frightened mode for a fixed number of ticks; if Pac-Man collides with frightened ghosts, he eats them for points.

16. Q: How is replanning triggered in the agent?  
A: Replanning occurs when the current path is exhausted, periodically (every N ticks), or if a ghost is detected within a danger radius of the agent or the agent's path.

17. Q: What are some limitations of this project?  
A: Static maze layout (no dynamic reconfiguration), hand-designed ghost behaviours, and no learned policies; A* can be computationally expensive if many replans are run each tick.

18. Q: How would you scale this approach to larger maps?  
A: Use hierarchical pathfinding, reduce search frequency, use incremental search (e.g., D* Lite), or learn policies that approximate planning.

19. Q: Name alternatives to Manhattan heuristic for grid pathfinding.  
A: Euclidean distance (suitable for diagonal moves), Chebyshev distance (for 8-connected grids), or domain-specific heuristics using landmarks.

20. Q: Why is Python suitable for this assignment?  
A: Python enables rapid development, clear algorithmic expression, and good libraries for visualization. It is widely used in education for prototyping AI ideas.

21. Q: How are algorithm comparisons performed in the project?  
A: The `comparison_screen` runs BFS, DFS, and A* on the same start/goal pair and displays nodes, path length, path cost, and time to allow side-by-side evaluation.

22. Q: How do you handle ties when two nodes have equal f(n)?  
A: Use a secondary key. This project pushes `(f, g, node)`, so on equal f the node with the lower g is popped first; pushing `(f, -g, node)` would prefer larger g, which often expands fewer nodes. Either way the path stays optimal.

23. Q: What is the experimental protocol to evaluate algorithms?  
A: Run multiple trials with the same maze and difficulty, record metrics (nodes, time, path length), compute averages and variance, and present tables and plots.

24. Q: How would you integrate reinforcement learning into this project?  
A: Use a DQN or policy gradient to learn a policy mapping states (grid+ghosts) to actions, using reward signals for pellets/ghosts and penalty for death; combine with planning for hybrid methods.

25. Q: What improvements ensure fair comparison between algorithms?  
A: Use identical start/goal pairs, measure wall-clock time and node counts with the same hardware, and average across multiple runs to control for variance.

---

## 16. PPT CONTENT (10 slides)

Slide 1 — Title: Project title, student name, guide, college.

Slide 2 — Motivation: Importance of AI in games and project objectives.

Slide 3 — Problem Statement: Collect pellets, avoid ghosts; constraints.

Slide 4 — Agent Design: Goal-based agent, perceive-plan-act cycle, state space.

Slide 5 — Algorithms: BFS, DFS, A* overview with formulas and pseudocode.

Slide 6 — Heuristic: Manhattan distance, admissibility and consistency.

Slide 7 — System Architecture: modules (`main.py`, `pacman.py`, `astar.py`) and flowchart.

Slide 8 — Results: Example table comparing nodes/time/path length; screenshot placeholder.

Slide 9 — Discussion: Why A* performed best; trade-offs and observations.

Slide 10 — Conclusion & Future Work: Summary, suggested extensions (RL, adaptive ghosts).
