# Intelligent Pac-Man Agent Using A* Search Algorithm

> **AI Academic Assignment** — Artificial Intelligence | Intelligent Agents | Search Algorithms

---

## 📖 Project Overview

This project implements a **Goal-Based Intelligent Pac-Man Agent** that autonomously navigates a classic maze using the **A\* Search Algorithm** with a **Manhattan Distance heuristic**. The agent collects pellets, avoids ghosts, and demonstrates optimal pathfinding in real time.

Three search algorithms are implemented side-by-side for academic comparison:
- **A\*** (primary agent brain — optimal & efficient)
- **BFS** (complete, optimal, high memory)
- **DFS** (complete, not optimal, low memory)

---

## 🗂️ Project Structure

```
AI AAT 1/
├── main.py          – Game loop, screens, UI renderer, event handler
├── maze.py          – Grid environment: walls, pellets, state space
├── pacman.py        – Goal-based intelligent agent (A* planner)
├── ghost.py         – Ghost agents (BFS / A* chasers, 4 personalities)
├── astar.py         – A* Search with Manhattan Distance heuristic
├── bfs.py           – Breadth-First Search implementation
├── dfs.py           – Depth-First Search implementation
├── utils.py         – Shared helpers: heuristics, metrics, colours
├── requirements.txt – Python dependencies
└── README.md        – This file
```

---

## ⚙️ Installation

### Prerequisites
- Python 3.10 or higher
- pip

### Step 1 — Clone / Download
Place all files inside a single folder (e.g., `AI AAT 1/`).

### Step 2 — Install dependencies

```bash
pip install -r requirements.txt
```

Or install pygame directly:

```bash
pip install pygame
```

### Step 3 — Run the game

```bash
python main.py
```

> Works on Windows, macOS, and Linux. Designed for low/mid-range laptops.

---

## 🎮 Controls

| Key | Action |
|-----|--------|
| `SPACE` | Toggle AI Agent / Manual Mode |
| `Arrow Keys` / `WASD` | Manual movement |
| `V` | Toggle visualisation overlay (explored nodes + path) |
| `C` | Show algorithm comparison screen |
| `R` | Restart game |
| `ESC` | Quit |

---

## 🤖 AI Architecture

### Agent Type: Goal-Based Intelligent Agent

```
┌─────────────────────────────────────────────────────┐
│  ENVIRONMENT  (Maze + Ghost positions)               │
│   → Percept: (position, pellets, ghost_positions)   │
│                                                     │
│  AGENT FUNCTION:  f(percept) → action               │
│   1. Plan path to nearest pellet via A*             │
│   2. Detect if ghost is on current planned path     │
│   3. If danger detected → replan (avoid ghost)      │
│   4. Follow path step-by-step                       │
└─────────────────────────────────────────────────────┘
```

### State Space Representation

| Component | Definition |
|-----------|-----------|
| **State** | `(row, col)` — grid cell position |
| **Initial State** | Pac-Man's spawn cell `(16, 10)` |
| **Goal State** | All pellets collected |
| **Actions** | Move UP / DOWN / LEFT / RIGHT |
| **Transition** | Move to adjacent non-wall cell |
| **Path Cost** | 1 per step (uniform cost) |

### A* Algorithm

```
f(n) = g(n) + h(n)
  g(n) = actual cost from start to n
  h(n) = Manhattan Distance to nearest pellet
       = |row_n - row_goal| + |col_n - col_goal|
```

**Properties of Manhattan Distance heuristic:**
- ✅ **Admissible** — never overestimates (4-directional movement only)
- ✅ **Consistent** — satisfies triangle inequality h(n) ≤ c(n,n') + h(n')
- ✅ **Guarantees optimal path** when heuristic is admissible

---

## 👻 Ghost Agents

| Ghost | Color | Algorithm | Behaviour |
|-------|-------|-----------|-----------|
| Blinky | 🔴 Red | BFS | Direct chase — targets Pac-Man's exact position |
| Pinky | 🩷 Pink | A* | Ambush — targets 4 cells ahead of Pac-Man |
| Inky | 🩵 Cyan | A* | Alternates scatter/chase modes |
| Clyde | 🟠 Orange | BFS | Retreats when within 8 cells; chases when far |

All ghosts enter **frightened mode** (blue) when Pac-Man collects a power pellet.

---

## 📊 Algorithm Comparison

Press `C` in-game to view a live comparison table.

| Metric | BFS | DFS | A* |
|--------|-----|-----|----|
| **Completeness** | ✅ Yes | ✅ Yes (finite) | ✅ Yes |
| **Optimality** | ✅ Yes | ❌ No | ✅ Yes |
| **Time Complexity** | O(b^d) | O(b^m) | O(b^d) guided |
| **Space Complexity** | O(b^d) | O(b·m) | O(b^d) |
| **Heuristic** | None | None | Manhattan Distance |
| **Nodes Explored** | High | Variable | **Lowest** |

> b = branching factor (~4), d = solution depth, m = max depth

---

## 🖥️ Visualisation Features

| Overlay | Colour |
|---------|--------|
| Walls | Deep blue with highlight border |
| Empty path | Near-black |
| Pellets | Warm cream dots |
| Power pellets | Amber glow rings |
| Explored nodes (A*) | Subtle teal |
| Solution path | Bright green |
| Pac-Man | Animated yellow with mouth |
| Ghosts | Personality-specific colours |

---

## 🏆 Win / Lose Conditions

- **Win** — Collect all pellets and power pellets
- **Lose** — A ghost (not frightened) reaches Pac-Man's cell; 3 lives total

---

## 📋 Difficulty Levels

| Level | Ghost Speed |
|-------|-------------|
| Easy | Slow (delay = 14 ticks) |
| Medium | Normal (delay = 10 ticks) |
| Hard | Fast (delay = 6 ticks) |

---

## 📦 Dependencies

```
pygame==2.5.2   – Graphics, windowing, event handling
heapq           – Priority queue for A* open list (stdlib)
collections     – deque for BFS frontier (stdlib)
time            – Execution time measurement (stdlib)
math            – Trigonometry for sprite rendering (stdlib)
```

---

## 🎓 Academic Notes

This project demonstrates:
1. **Informed Search** — A* with admissible heuristic
2. **Uninformed Search** — BFS (optimal), DFS (not optimal)
3. **Goal-Based Agent Architecture** — perceive → plan → act
4. **State Space Representation** — grid as explicit graph
5. **Heuristic Design** — Manhattan distance for 4-directional movement
6. **Multi-Agent Environment** — Pac-Man vs. 4 ghost agents

---

## 👤 Author

**Academic Assignment Submission**  
Subject: Artificial Intelligence  
Algorithm Focus: A* Search, BFS, DFS, Intelligent Agents
