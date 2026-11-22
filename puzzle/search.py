"""Search algorithms. Each returns a Result with the path and how much work it did.

- bfs:   breadth-first; fewest moves, a lot of memory.
- ids:   iterative deepening; fewest moves with very little memory, but repeats work.
- ucs:   uniform-cost; cheapest path under any cost model.
- astar: A* with a heuristic; cheapest path, usually far fewer expansions than UCS.
- beam:  keeps only the best `width` states per level; fast, not guaranteed to
         find the best (or any) solution.
"""
from __future__ import annotations

import heapq
import itertools
import time
from collections import deque
from dataclasses import dataclass, field
from typing import Optional

from .board import Move, Puzzle, State
from .heuristics import HEURISTICS, Heuristic


@dataclass
class Result:
    algorithm: str
    start: State
    path: Optional[list[tuple[Move, State]]]  # None when no solution was found
    expanded: int = 0          # states taken off the frontier and expanded
    max_frontier: int = 0      # the most states held waiting at once
    seconds: float = 0.0
    notes: dict = field(default_factory=dict)

    @property
    def solved(self) -> bool:
        return self.path is not None

    @property
    def moves(self) -> Optional[int]:
        return None if self.path is None else len(self.path)

    @property
    def cost(self) -> Optional[int]:
        return None if self.path is None else sum(m.cost for m, _ in self.path)


def _rebuild(parents: dict, state: State) -> list[tuple[Move, State]]:
    path = []
    while parents[state] is not None:
        move, previous = parents[state]
        path.append((move, state))
        state = previous
    return path[::-1]


def bfs(puzzle: Puzzle, start: State) -> Result:
    began = time.perf_counter()
    result = Result("bfs", start, None)
    parents = {start: None}
    frontier = deque([start])
    while frontier:
        result.max_frontier = max(result.max_frontier, len(frontier))
        state = frontier.popleft()
        if puzzle.is_goal(state):
            result.path = _rebuild(parents, state)
            break
        result.expanded += 1
        for move, nxt in puzzle.successors(state):
            if nxt not in parents:
                parents[nxt] = (move, state)
                frontier.append(nxt)
    result.seconds = time.perf_counter() - began
    return result


def ids(puzzle: Puzzle, start: State, max_depth: int = 40) -> Result:
    """Depth-limited DFS with growing limits. Avoids cycles on the current path only."""
    began = time.perf_counter()
    result = Result("ids", start, None)

    def dls(state: State, depth: int, on_path: set, path: list) -> bool:
        if puzzle.is_goal(state):
            result.path = list(path)
            return True
        if depth == 0:
            return False
        result.expanded += 1
        for move, nxt in puzzle.successors(state):
            if nxt in on_path:
                continue
            on_path.add(nxt)
            path.append((move, nxt))
            if dls(nxt, depth - 1, on_path, path):
                return True
            path.pop()
            on_path.discard(nxt)
        return False

    for limit in range(max_depth + 1):
        result.notes["depth_limit"] = limit
        if dls(start, limit, {start}, []):
            break
    result.max_frontier = (result.moves or max_depth) + 1  # the stack is one path deep
    result.seconds = time.perf_counter() - began
    return result


def astar(puzzle: Puzzle, start: State, heuristic: str | Heuristic = "inversions") -> Result:
    h = HEURISTICS[heuristic] if isinstance(heuristic, str) else heuristic
    name = heuristic if isinstance(heuristic, str) else h.__name__
    began = time.perf_counter()
    result = Result("ucs" if name == "zero" else f"astar[{name}]", start, None)

    tie = itertools.count()  # breaks ties in insertion order, so runs are repeatable
    best_g = {start: 0}
    parents = {start: None}
    frontier = [(h(puzzle, start), next(tie), 0, start)]
    closed = set()
    while frontier:
        result.max_frontier = max(result.max_frontier, len(frontier))
        _, _, g, state = heapq.heappop(frontier)
        if state in closed:
            continue
        if puzzle.is_goal(state):
            result.path = _rebuild(parents, state)
            break
        closed.add(state)
        result.expanded += 1
        for move, nxt in puzzle.successors(state):
            new_g = g + move.cost
            if new_g < best_g.get(nxt, float("inf")):
                best_g[nxt] = new_g
                parents[nxt] = (move, state)
                heapq.heappush(frontier, (new_g + h(puzzle, nxt), next(tie), new_g, nxt))
    result.seconds = time.perf_counter() - began
    return result


def ucs(puzzle: Puzzle, start: State) -> Result:
    return astar(puzzle, start, "zero")


def beam(puzzle: Puzzle, start: State, width: int = 3, heuristic: str = "inversions",
         max_levels: int = 200) -> Result:
    """Level-by-level search keeping the `width` states with the lowest g + h."""
    h = HEURISTICS[heuristic]
    began = time.perf_counter()
    result = Result(f"beam[w={width}]", start, None)
    parents = {start: None}
    g_of = {start: 0}
    level = [start]
    for _ in range(max_levels):
        goal = next((s for s in level if puzzle.is_goal(s)), None)
        if goal is not None:
            result.path = _rebuild(parents, goal)
            break
        candidates = []
        for state in level:
            result.expanded += 1
            for move, nxt in puzzle.successors(state):
                if nxt in parents:  # never revisit, so the beam cannot cycle
                    continue
                parents[nxt] = (move, state)
                g_of[nxt] = g_of[state] + move.cost
                candidates.append(nxt)
        if not candidates:
            break  # the beam ran out of new states: no solution found
        candidates.sort(key=lambda s: (g_of[s] + h(puzzle, s), s))
        level = candidates[:width]
        result.max_frontier = max(result.max_frontier, len(candidates))
    result.seconds = time.perf_counter() - began
    return result


ALGORITHMS = {
    "bfs": bfs,
    "ids": ids,
    "ucs": ucs,
    "astar-misplaced": lambda p, s: astar(p, s, "misplaced"),
    "astar-inversions": lambda p, s: astar(p, s, "inversions"),
    "beam-3": lambda p, s: beam(p, s, width=3),
    "beam-10": lambda p, s: beam(p, s, width=10),
}
