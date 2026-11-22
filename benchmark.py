"""Compare every algorithm on the same random start states and write the results.

    python benchmark.py                 # 3+3 up to 7+7 tiles, 30 starts each
    python benchmark.py --starts 50 --sizes 3 4

Writes results/benchmark.md (tables for the README) and results/benchmark.png.
"""
from __future__ import annotations

import argparse
import random
import statistics
from pathlib import Path

from puzzle import ALGORITHMS, Puzzle

ROOT = Path(__file__).resolve().parent
SKIP_ABOVE = {"ids": 3}  # IDS re-searches every level; beyond 3+3 it takes minutes per start


def run(sizes: list[int], starts: int, seed: int, max_jump: int) -> list[dict]:
    rows = []
    for n in sizes:
        puzzle = Puzzle(n, n, max_jump=max_jump)
        rng = random.Random(seed + n)
        states = [s for s in (puzzle.random_state(rng) for _ in range(starts * 3)) if not puzzle.is_goal(s)][:starts]
        optimal = {s: ALGORITHMS["astar-inversions"](puzzle, s).moves for s in states}
        for name, algorithm in ALGORITHMS.items():
            if n > SKIP_ABOVE.get(name, 99):
                continue
            results = [algorithm(puzzle, s) for s in states]
            solved = [r for r in results if r.solved]
            rows.append({
                "tiles": f"{n}+{n}",
                "algorithm": name,
                "solved": f"{len(solved)}/{len(results)}",
                "optimal": sum(r.moves == optimal[r.start] for r in solved),
                "avg_moves": statistics.mean(r.moves for r in solved) if solved else float("nan"),
                "avg_expanded": statistics.mean(r.expanded for r in results),
                "avg_frontier": statistics.mean(r.max_frontier for r in results),
                "avg_ms": statistics.mean(r.seconds for r in results) * 1000,
            })
            print(f"  {rows[-1]['tiles']:<5} {name:<17} expanded {rows[-1]['avg_expanded']:>10.1f}")
    return rows


def write_markdown(rows: list[dict], path: Path, starts: int, seed: int, max_jump: int) -> None:
    lines = [
        f"Random start states per size: {starts} (seed {seed}); moves may jump over up to {max_jump} tiles; every move costs 1.",
        "",
        "| Tiles | Algorithm | Solved | Optimal | Avg moves | Avg states expanded | Avg max frontier | Avg time (ms) |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for r in rows:
        lines.append(
            f"| {r['tiles']} | {r['algorithm']} | {r['solved']} | {r['optimal']} | {r['avg_moves']:.2f} | "
            f"{r['avg_expanded']:,.0f} | {r['avg_frontier']:,.0f} | {r['avg_ms']:.2f} |"
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_chart(rows: list[dict], path: Path) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    sizes = list(dict.fromkeys(r["tiles"] for r in rows))
    algorithms = list(dict.fromkeys(r["algorithm"] for r in rows))
    fig, ax = plt.subplots(figsize=(9, 4.8))
    for algorithm in algorithms:
        points = [(sizes.index(r["tiles"]), r["avg_expanded"]) for r in rows if r["algorithm"] == algorithm]
        ax.plot([p[0] for p in points], [p[1] for p in points], marker="o", label=algorithm)
    ax.set_yscale("log")
    ax.set_xticks(range(len(sizes)), [f"{s} tiles" for s in sizes])
    ax.set_ylabel("Average states expanded (log scale)")
    ax.set_title("How much each algorithm searches as the board grows")
    ax.legend(fontsize=8, ncol=2)
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--sizes", type=int, nargs="+", default=[3, 4, 5, 6, 7], help="Tiles of each kind")
    parser.add_argument("--starts", type=int, default=30)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--max-jump", type=int, default=2)
    args = parser.parse_args()

    out = ROOT / "results"
    out.mkdir(exist_ok=True)
    rows = run(args.sizes, args.starts, args.seed, args.max_jump)
    write_markdown(rows, out / "benchmark.md", args.starts, args.seed, args.max_jump)
    write_chart(rows, out / "benchmark.png")
    print(f"Wrote {out / 'benchmark.md'} and {out / 'benchmark.png'}")


if __name__ == "__main__":
    main()
