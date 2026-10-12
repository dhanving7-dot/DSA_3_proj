"""Module 6 - Parallel primitives, simulated on a PRAM.

CPython cannot run these rounds truly in parallel (the GIL), so each
primitive is executed round-by-round exactly as a PRAM would: every
operation inside one round is independent of the others in that round. The
simulator counts

  work  T1    = total operations across all rounds
  span  T_inf = number of rounds (the critical-path length)

which are the two quantities Brent's theorem needs:  T_p <= T1/p + T_inf.

The allocation engine uses `blelloch_exclusive_scan` for real: the starting
slot index of every laboratory in the capacity-expanded bipartite graph is
the exclusive prefix sum of the capacities.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable


@dataclass
class ParallelTrace:
    result: list[int] | int
    work: int
    span: int
    rounds: list[dict] = field(default_factory=list)

    def brent_bound(self, processors: int) -> float:
        """Upper bound on running time with p processors: T1/p + T_inf."""
        return self.work / max(processors, 1) + self.span

    def to_dict(self, processors: int = 4) -> dict:
        return {
            "result": self.result,
            "work": self.work,
            "span": self.span,
            "rounds": self.rounds,
            "processors": processors,
            "brent_bound": round(self.brent_bound(processors), 3),
            "parallelism": round(self.work / self.span, 3) if self.span else None,
        }


def _next_pow2(n: int) -> int:
    size = 1
    while size < n:
        size *= 2
    return size


def parallel_reduce(values: list[int], op: Callable[[int, int], int] = lambda a, b: a + b, identity: int = 0) -> ParallelTrace:
    """Balanced binary-tree reduction: n-1 operations, ceil(log2 n) rounds."""
    if not values:
        return ParallelTrace(identity, 0, 0)
    level = list(values)
    rounds: list[dict] = []
    work = 0
    while len(level) > 1:
        nxt = []
        ops = 0
        for i in range(0, len(level) - 1, 2):
            nxt.append(op(level[i], level[i + 1]))
            ops += 1
        if len(level) % 2 == 1:
            nxt.append(level[-1])
        work += ops
        rounds.append({"phase": "reduce", "operations": ops, "values": list(nxt)})
        level = nxt
    return ParallelTrace(level[0], work, len(rounds), rounds)


def blelloch_exclusive_scan(values: list[int]) -> ParallelTrace:
    """Work-efficient exclusive prefix sum (Blelloch 1990).

    Up-sweep builds partial sums in a balanced tree (n-1 additions, log n rounds);
    down-sweep pushes prefixes back down (n-1 additions + swaps, log n rounds).
    Total work O(n), span O(log n). Input is padded with zeros to a power of two.
    """
    n = len(values)
    if n == 0:
        return ParallelTrace([], 0, 0)
    size = _next_pow2(n)
    a = list(values) + [0] * (size - n)
    rounds: list[dict] = []
    work = 0

    d = 1
    while d < size:  # up-sweep (reduce)
        ops = 0
        for i in range(0, size, 2 * d):
            a[i + 2 * d - 1] += a[i + d - 1]
            ops += 1
        work += ops
        rounds.append({"phase": "up-sweep", "stride": d, "operations": ops, "values": a[:n]})
        d *= 2

    a[size - 1] = 0
    d = size // 2
    while d >= 1:  # down-sweep
        ops = 0
        for i in range(0, size, 2 * d):
            left = a[i + d - 1]
            a[i + d - 1] = a[i + 2 * d - 1]
            a[i + 2 * d - 1] += left
            ops += 1
        work += ops
        rounds.append({"phase": "down-sweep", "stride": d, "operations": ops, "values": a[:n]})
        d //= 2

    return ParallelTrace(a[:n], work, len(rounds), rounds)


def sequential_exclusive_scan(values: list[int]) -> list[int]:
    out, running = [], 0
    for v in values:
        out.append(running)
        running += v
    return out
