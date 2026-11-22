"""Heuristics: estimates of the remaining cost that never overestimate it.

Both look only at the order of the tiles, ignoring the blank. In that order the
goal is A...AB...B. One move takes one tile past at most `max_jump` others, so
it can only change the order a little; that is what makes both admissible
(they never overestimate) for the "unit" cost model. Under the "distance" cost
model every move costs at least 1, so they stay admissible there too.
"""
from __future__ import annotations

import math
from typing import Callable

from .board import BLANK, Puzzle, State

Heuristic = Callable[[Puzzle, State], int]


def tile_order(state: State) -> list[str]:
    return [c for c in state if c != BLANK]


def misplaced(puzzle: Puzzle, state: State) -> int:
    """How many B tiles sit among the first n_a tiles.

    One move moves one tile, so it can take at most one B out of that zone.
    Each such B needs at least one move.
    """
    return tile_order(state)[: puzzle.n_a].count("B")


def inversions(puzzle: Puzzle, state: State) -> int:
    """Pairs in the wrong order (a B before an A), divided by the most one move can fix.

    A tile that jumps over k tiles swaps its order with exactly those k tiles
    (and a slide swaps with none). So one move removes at most max(1, max_jump)
    inversions, and the remaining moves are at least inversions / max_jump.
    """
    order = tile_order(state)
    count, bs_seen = 0, 0
    for tile in order:
        if tile == "B":
            bs_seen += 1
        else:
            count += bs_seen
    return math.ceil(count / max(1, puzzle.max_jump))


def zero(puzzle: Puzzle, state: State) -> int:
    """No information: A* with this is uniform-cost search."""
    return 0


HEURISTICS: dict[str, Heuristic] = {
    "misplaced": misplaced,
    "inversions": inversions,
    "zero": zero,
}
