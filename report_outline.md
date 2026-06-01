# AI Project Report Outline
## Intelligent Pac-Man Agent Using A* Search Algorithm

---

## Title Page

- **Project Title:** Intelligent Pac-Man Agent Using A\* Search Algorithm
- **Subject:** Artificial Intelligence
- **Topic Area:** Intelligent Agents | Search Algorithms | Problem Solving
- **Tools Used:** Python 3.10+, Pygame 2.5
- **Date:** [Submission Date]

---

## 1. Introduction

### 1.1 Motivation
- Classic Pac-Man as a testbed for AI decision-making and search
- Real-world parallel: autonomous navigation, robotics path planning

### 1.2 Objectives
- Implement a Goal-Based Intelligent Agent
- Apply A\*, BFS, and DFS to maze navigation
- Compare algorithm performance with real-time metrics
- Visualise search exploration and solution paths

### 1.3 Scope
- 2D grid maze environment
- Single agent (Pac-Man) vs. multi-agent (4 ghosts)
- Three search algorithms with live comparison dashboard

---

## 2. Background & Literature Review

### 2.1 Intelligent Agents (Russell & Norvig)
- Agent types: Simple Reflex, Model-Based, Goal-Based, Utility-Based
- This project: **Goal-Based Agent** — acts to achieve defined goals

### 2.2 Search Algorithms Overview
| Algorithm | Type | Optimal? | Complete? | Key Data Structure |
|-----------|------|----------|-----------|-------------------|
| BFS | Uninformed | Yes | Yes | Queue (FIFO) |
| DFS | Uninformed | No | Yes | Stack (LIFO) |
| A* | Informed | Yes | Yes | Priority Queue (Min-Heap) |

### 2.3 Heuristic Functions
- Admissibility requirement: h(n) ≤ h*(n)
- Manhattan Distance for 4-directional grid movement
- Consistency: h(n) ≤ c(n,n') + h(n') — guarantees optimal A*

---

## 3. Problem Formulation

### 3.1 Task Environment Properties
| Property | Value |
|----------|-------|
| Observable | Fully (agent knows full maze) |
| Deterministic | Yes |
| Episodic/Sequential | Sequential |
| Static/Dynamic | Dynamic (ghosts move) |
| Discrete | Yes (grid cells) |
| Single/Multi-Agent | Multi-Agent |

### 3.2 State Space Definition
- **State:** `(row, col)` — Pac-Man's grid position
- **Initial State:** Spawn cell `(16, 10)`
- **Goal State:** Set of all pellets = empty
- **Actions:** {UP, DOWN, LEFT, RIGHT}
- **Transition Model:** Move to adjacent non-wall cell
- **Path Cost:** 1 per step (uniform cost)
- **State Space Size:** 21 × 21 grid = 441 cells (approx. 300 walkable)

### 3.3 Maze Environment
- 21 × 21 grid
- Cell types: Wall, Empty, Pellet (+10 pts), Power Pellet (+50 pts)
- Total pellets: ~150

---

## 4. Algorithm Implementations

### 4.1 A\* Search (`astar.py`)

**Formula:** `f(n) = g(n) + h(n)`
- `g(n)` = actual cost from start to n
- `h(n)` = Manhattan Distance to goal
- `f(n)` = total estimated cost

**Pseudocode:**
```
OPEN  ← priority queue, initial = {start: f=h(start)}
CLOSED← empty set

while OPEN not empty:
    n ← node with lowest f(n) in OPEN
    if n == goal: return reconstruct_path()
    CLOSED ← CLOSED ∪ {n}
    for each neighbour m of n:
        if m in CLOSED: skip
        tentative_g = g(n) + 1
        if tentative_g < g(m):
            came_from[m] = n
            g(m) = tentative_g
            f(m) = tentative_g + h(m)
            OPEN ← OPEN ∪ {m}
return FAILURE
```

**Time Complexity:** O(b^d) — guided by heuristic, much less in practice  
**Space Complexity:** O(b^d) — stores frontier and closed set

### 4.2 BFS (`bfs.py`)

**Pseudocode:**
```
FRONTIER ← queue [{start}]
EXPLORED ← {}
while FRONTIER not empty:
    node ← FRONTIER.dequeue()
    if node == goal: return path
    for each neighbour of node:
        if not visited: FRONTIER.enqueue(neighbour)
return FAILURE
```

**Time Complexity:** O(b^d)  
**Space Complexity:** O(b^d)

### 4.3 DFS (`dfs.py`)

**Pseudocode:**
```
FRONTIER ← stack [{start}]
VISITED  ← {}
while FRONTIER not empty:
    node ← FRONTIER.pop()
    if node == goal: return path
    for each neighbour of node:
        if not visited: FRONTIER.push(neighbour)
return FAILURE
```

**Time Complexity:** O(b^m)  
**Space Complexity:** O(b·m) — only stores current path

---

## 5. Agent Design

### 5.1 Pac-Man: Goal-Based Agent
```
perceive() → plan() → act()
```
1. **Perceive:** Get current position, pellet positions, ghost positions
2. **Plan:** Run A\* to nearest pellet (considering ghost proximity)
3. **Act:** Move one step along the A\* path
4. **Replan:** Trigger replanning if ghost is within 4 cells or path exhausted

### 5.2 Ghost Agents

| Ghost | Algorithm | Targeting Strategy |
|-------|-----------|-------------------|
| Blinky (Red) | BFS | Direct: Pac-Man's exact cell |
| Pinky (Pink) | A\* | Ambush: 4 cells ahead of Pac-Man |
| Inky (Cyan) | A\* | Scatter/chase alternation |
| Clyde (Orange) | BFS | Chase if dist > 8, scatter if close |

### 5.3 Collision Detection
- Each tick: check if any ghost occupies Pac-Man's cell
- If frightened ghost: Pac-Man eats ghost (+200 pts), ghost respawns
- If normal ghost: Pac-Man loses life; game over at 0 lives

---

## 6. Results & Analysis

### 6.1 Performance Comparison Table
*(Fill in with actual values from the C-key comparison screen)*

| Metric | BFS | DFS | A\* |
|--------|-----|-----|-----|
| Nodes Explored | ~280 | ~200–450 | ~60–120 |
| Path Length (steps) | Optimal | Suboptimal | Optimal |
| Execution Time (ms) | ~0.8 ms | ~0.5 ms | ~0.3 ms |
| Path Optimality | ✅ | ❌ | ✅ |

### 6.2 Observations
- A\* explores **3–5× fewer nodes** than BFS due to heuristic guidance
- DFS finds paths that can be **2–3× longer** than optimal
- Execution times are all sub-millisecond on a standard laptop
- A\* provides the best balance of speed + optimality for this domain

---

## 7. Visualisation & UI

### 7.1 Colour Scheme
- Deep blue walls with highlighted borders
- Teal overlay for explored nodes
- Bright green for A\* solution path
- Amber power pellets with glow rings

### 7.2 Real-Time Metrics Panel
- Algorithm name, nodes explored, path length, path cost, execution time
- Ghost status (mode: chase/scatter/frightened, algorithm used)
- h(n) value updated every tick

---

## 8. Conclusion

### 8.1 Key Findings
- A\* Search with Manhattan Distance heuristic provides **optimal** and **efficient** pathfinding for Pac-Man
- Goal-Based Agent architecture cleanly separates perception, planning, and action
- BFS and DFS serve as useful baselines to demonstrate A\*'s advantage

### 8.2 Limitations
- Ghost avoidance is reactive (proximity check), not predictive
- DFS path quality depends on neighbour expansion order
- Single-level maze (extension: multi-level possible)

### 8.3 Future Work
- Implement **Minimax** or **Expectimax** for adversarial ghost search
- Add **Q-Learning** or **MCTS** for adaptive agent behaviour
- Multiple maze levels with increasing complexity

---

## 9. References

1. Russell, S. & Norvig, P. (2020). *Artificial Intelligence: A Modern Approach* (4th ed.)
2. Hart, P., Nilsson, N., & Raphael, B. (1968). *A Formal Basis for Heuristic Determination of Minimum Cost Paths*
3. Pygame Documentation: https://www.pygame.org/docs/
4. Wikipedia: *A\* search algorithm* — https://en.wikipedia.org/wiki/A*_search_algorithm
