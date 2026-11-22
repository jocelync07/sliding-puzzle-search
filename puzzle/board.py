"""The tile-sorting puzzle: states, legal moves and the goal test.

A board is a row of cells holding two kinds of tiles, "A" and "B", and one
blank "_". A move takes a tile and puts it in the blank. The tile can slide
from the next cell, or jump over up to `max_jump` other tiles. The goal is
every "A" to the left of every "B"; the blank may end up anywhere.

    start  B A _ B A A B        goal  A A A _ B B B   (or A A A B _ B B, ...)
"""
from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Iterator, NamedTuple, Tuple

BLANK = "_"
State = Tuple[str, ...]


class Move(NamedTuple):
    tile_from: int    # where the tile was
    tile_to: int      # where it lands (the old blank)
    jumped: int       # how many tiles it jumped over (0 = a slide)
    cost: int


@dataclass(frozen=True)
class Puzzle:
    """Rules for one puzzle size. `cost_model` decides what a move costs.

    - "unit":     every move costs 1, so the best solution has the fewest moves.
    - "distance": a move costs how far the tile travels (slide 1, jump over k = k + 1).
    """

    n_a: int = 3
    n_b: int = 3
    max_jump: int = 2
    cost_model: str = "unit"

    def __post_init__(self):
        if self.n_a < 1 or self.n_b < 1:
            raise ValueError("Need at least one tile of each kind")
        if self.max_jump < 0:
            raise ValueError("max_jump cannot be negative")
        if self.cost_model not in ("unit", "distance"):
            raise ValueError("cost_model must be 'unit' or 'distance'")

    @property
    def size(self) -> int:
        return self.n_a + self.n_b + 1

    def parse(self, text: str) -> State:
        """'BA_BAAB' or 'B A _ B A A B' -> a state, checked against this puzzle."""
        state = tuple(c for c in text.upper() if not c.isspace())
        self.validate(state)
        return state

    def validate(self, state: State) -> None:
        if len(state) != self.size:
            raise ValueError(f"Expected {self.size} cells, got {len(state)}")
        counts = {c: state.count(c) for c in set(state)}
        expected = {"A": self.n_a, "B": self.n_b, BLANK: 1}
        if counts != expected:
            raise ValueError(f"Expected {expected}, got {counts}")

    def is_goal(self, state: State) -> bool:
        tiles = [c for c in state if c != BLANK]
        return tiles == ["A"] * self.n_a + ["B"] * self.n_b

    def moves(self, state: State) -> Iterator[Move]:
        """Every legal move, nearest tiles first."""
        blank = state.index(BLANK)
        for distance in range(1, self.max_jump + 2):
            for source in (blank - distance, blank + distance):
                if 0 <= source < self.size:
                    cost = 1 if self.cost_model == "unit" else distance
                    yield Move(source, blank, distance - 1, cost)

    def apply(self, state: State, move: Move) -> State:
        cells = list(state)
        cells[move.tile_to], cells[move.tile_from] = cells[move.tile_from], BLANK
        return tuple(cells)

    def successors(self, state: State) -> Iterator[tuple[Move, State]]:
        for move in self.moves(state):
            yield move, self.apply(state, move)

    def random_state(self, rng: random.Random) -> State:
        cells = ["A"] * self.n_a + ["B"] * self.n_b + [BLANK]
        rng.shuffle(cells)
        return tuple(cells)

    def all_states(self) -> Iterator[State]:
        """Every arrangement of this puzzle's tiles (fine for small boards)."""
        from itertools import combinations

        positions = range(self.size)
        for blank in positions:
            rest = [p for p in positions if p != blank]
            for a_cells in combinations(rest, self.n_a):
                cells = ["B"] * self.size
                cells[blank] = BLANK
                for p in a_cells:
                    cells[p] = "A"
                yield tuple(cells)


def show(state: State) -> str:
    return " ".join(state)
