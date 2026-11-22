import random

import pytest

from puzzle import ALGORITHMS, Puzzle, astar, beam, bfs, ids, ucs
from puzzle.heuristics import HEURISTICS


@pytest.fixture
def small():
    return Puzzle(3, 3, max_jump=2)


def replay(puzzle, start, result):
    """Apply the solution's moves from the start and check each one is legal."""
    state = start
    for move, expected in result.path:
        assert move in list(puzzle.moves(state))
        state = puzzle.apply(state, move)
        assert state == expected
    return state


# ------------------------------------------------------------------ rules

def test_goal_ignores_the_blank(small):
    assert small.is_goal(tuple("AAA_BBB"))
    assert small.is_goal(tuple("_AAABBB"))
    assert small.is_goal(tuple("AAABBB_"))
    assert not small.is_goal(tuple("AABA_BB"))


def test_moves_from_the_middle(small):
    moves = list(small.moves(tuple("AAA_BBB")))
    # A tile 1, 2 or 3 cells away on either side can move into the blank.
    assert sorted(m.tile_from for m in moves) == [0, 1, 2, 4, 5, 6]
    assert {m.jumped for m in moves} == {0, 1, 2}


def test_moves_at_the_edge_and_jump_limit():
    puzzle = Puzzle(3, 3, max_jump=1)
    moves = list(puzzle.moves(tuple("_AAABBB")))
    assert [m.tile_from for m in moves] == [1, 2]


def test_distance_costs():
    puzzle = Puzzle(3, 3, max_jump=2, cost_model="distance")
    assert sorted(m.cost for m in puzzle.moves(tuple("AAA_BBB"))) == [1, 1, 2, 2, 3, 3]


def test_parse_rejects_wrong_tiles(small):
    with pytest.raises(ValueError):
        small.parse("AAAABB_")
    with pytest.raises(ValueError):
        small.parse("AAA_BB")
    assert small.parse("b a _ b a a b") == tuple("BA_BAAB")


def test_all_states_count(small):
    states = set(small.all_states())
    assert len(states) == 7 * 20  # blank position x ways to place 3 A among 6 cells
    assert all(s.count("_") == 1 and s.count("A") == 3 for s in states)


# ------------------------------------------------------------------ heuristics

def exact_costs(puzzle):
    """True cost to reach a goal from every state, by searching from each one."""
    return {s: ucs(puzzle, s).cost for s in puzzle.all_states()}


@pytest.mark.parametrize("cost_model", ["unit", "distance"])
@pytest.mark.parametrize("max_jump", [1, 2])
def test_heuristics_never_overestimate(cost_model, max_jump):
    puzzle = Puzzle(3, 3, max_jump=max_jump, cost_model=cost_model)
    for state, true_cost in exact_costs(puzzle).items():
        for name, h in HEURISTICS.items():
            assert h(puzzle, state) <= true_cost, (name, state)


def test_heuristics_are_zero_at_goals(small):
    for state in small.all_states():
        if small.is_goal(state):
            assert all(h(small, state) == 0 for h in HEURISTICS.values())


# ------------------------------------------------------------------ search

def random_starts(puzzle, n=15, seed=1):
    rng = random.Random(seed)
    return [puzzle.random_state(rng) for _ in range(n)]


@pytest.mark.parametrize("name", sorted(ALGORITHMS))
def test_every_algorithm_returns_legal_solutions(small, name):
    for start in random_starts(small):
        result = ALGORITHMS[name](small, start)
        if result.solved:
            assert small.is_goal(replay(small, start, result))
        else:
            assert name.startswith("beam")  # only beam search may give up


def test_optimal_algorithms_agree(small):
    for start in random_starts(small):
        fewest = bfs(small, start).moves
        assert ids(small, start).moves == fewest
        assert ucs(small, start).cost == fewest
        assert astar(small, start, "misplaced").cost == fewest
        assert astar(small, start, "inversions").cost == fewest


def test_astar_is_optimal_with_distance_costs():
    puzzle = Puzzle(3, 3, max_jump=2, cost_model="distance")
    for start in random_starts(puzzle):
        assert astar(puzzle, start, "inversions").cost == ucs(puzzle, start).cost


def test_heuristics_save_work():
    puzzle = Puzzle(4, 4, max_jump=2)
    starts = random_starts(puzzle, n=10, seed=3)
    uniform = sum(ucs(puzzle, s).expanded for s in starts)
    guided = sum(astar(puzzle, s, "inversions").expanded for s in starts)
    assert guided < uniform


def test_already_solved_start(small):
    start = tuple("AAA_BBB")
    for name, algorithm in ALGORITHMS.items():
        result = algorithm(small, start)
        assert result.solved and result.moves == 0, name


def test_unsolvable_puzzle_is_reported():
    # With no jumps a tile can only slide, so the order of the tiles never changes.
    puzzle = Puzzle(1, 1, max_jump=0)
    start = tuple("B_A")
    assert not bfs(puzzle, start).solved
    assert not astar(puzzle, start, "misplaced").solved
    assert not beam(puzzle, start, width=2).solved
