"""Solve one puzzle from the command line.

    python -m puzzle BA_BAAB
    python -m puzzle "B B A _ A B A" --algorithm bfs --max-jump 2
    python -m puzzle BBBB_AAAA --algorithm astar-inversions --cost distance
"""
from __future__ import annotations

import argparse

from .board import Puzzle, show
from .search import ALGORITHMS


def main() -> None:
    parser = argparse.ArgumentParser(description="Sort A tiles to the left of B tiles.")
    parser.add_argument("start", help="Start state, e.g. BA_BAAB (_ is the blank)")
    parser.add_argument("--algorithm", "-a", default="astar-inversions", choices=sorted(ALGORITHMS))
    parser.add_argument("--max-jump", type=int, default=2, help="Most tiles one move may jump over")
    parser.add_argument("--cost", choices=["unit", "distance"], default="unit")
    args = parser.parse_args()

    text = "".join(args.start.upper().split())
    puzzle = Puzzle(text.count("A"), text.count("B"), args.max_jump, args.cost)
    start = puzzle.parse(text)
    result = ALGORITHMS[args.algorithm](puzzle, start)

    print(f"Start: {show(start)}   algorithm: {result.algorithm}")
    if not result.solved:
        print(f"No solution found ({result.expanded} states expanded).")
        return
    for i, (move, state) in enumerate(result.path, 1):
        kind = "slide" if move.jumped == 0 else f"jump over {move.jumped}"
        print(f"{i:>3}. {show(state)}   tile {move.tile_from} -> {move.tile_to} ({kind}, cost {move.cost})")
    print(f"Solved in {result.moves} moves, cost {result.cost}, {result.expanded} states expanded, "
          f"{result.seconds * 1000:.1f} ms.")


if __name__ == "__main__":
    main()
