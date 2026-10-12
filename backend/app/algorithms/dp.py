"""Module 3 - Advanced dynamic programming, hand-built.

Every routine here either returns its full DP table (so the Concept Lab can
render it with the traceback path highlighted) or is the lean, table-free
version used on hot paths (entity fuzzy search, AI command typo tolerance).

Contents
  edit_distance            Wagner-Fischer: Levenshtein / Damerau (OSA) / weighted, with traceback
  levenshtein_distance     O(min(n,m)) memory, early-exit band for fuzzy search
  osa_distance             Damerau-Levenshtein (optimal string alignment), 3 rolling rows
  needleman_wunsch         global alignment
  smith_waterman           local alignment
  matrix_chain_order       interval DP, O(n^3)
  optimal_bst              interval DP, O(n^3) and Knuth-optimised O(n^2)
  held_karp_tsp            bitmask DP, O(2^n * n^2)
  hamiltonian_path         bitmask DP, O(2^n * n^2)
  tree_dp                  diameter, centroid(s), max independent set, rerooting sum of distances
  sos_superset_sums        sum over supersets, O(k * 2^k)
  knapsack_01 / subset_sum pseudo-polynomial O(n * W)
  bitmask_assignment       exact max-cardinality, max-score assignment (verifies min-cost flow)
"""
from __future__ import annotations

from collections import deque

INF = float("inf")


# --------------------------------------------------------------------------- edit distance


def edit_distance(
    a: str,
    b: str,
    variant: str = "LEVENSHTEIN",
    insert_cost: float = 1.0,
    delete_cost: float = 1.0,
    substitute_cost: float = 1.0,
    transpose_cost: float = 1.0,
) -> dict:
    """Wagner-Fischer table D[i][j] = cost of turning a[:i] into b[:j].

    LEVENSHTEIN  insert / delete / substitute (unit costs)
    DAMERAU      + transposition of two adjacent characters (OSA variant: no
                 substring is edited twice, which keeps it a simple DP)
    WEIGHTED     Levenshtein with caller-supplied operation costs
    """
    variant = variant.upper()
    if variant not in ("LEVENSHTEIN", "DAMERAU", "WEIGHTED"):
        raise ValueError(f"Unknown edit-distance variant: {variant}")
    if variant != "WEIGHTED":
        insert_cost = delete_cost = substitute_cost = transpose_cost = 1.0

    n, m = len(a), len(b)
    D = [[0.0] * (m + 1) for _ in range(n + 1)]
    for i in range(1, n + 1):
        D[i][0] = D[i - 1][0] + delete_cost
    for j in range(1, m + 1):
        D[0][j] = D[0][j - 1] + insert_cost

    for i in range(1, n + 1):
        for j in range(1, m + 1):
            same = a[i - 1] == b[j - 1]
            best = min(
                D[i - 1][j] + delete_cost,
                D[i][j - 1] + insert_cost,
                D[i - 1][j - 1] + (0 if same else substitute_cost),
            )
            if variant == "DAMERAU" and i > 1 and j > 1 and a[i - 1] == b[j - 2] and a[i - 2] == b[j - 1]:
                best = min(best, D[i - 2][j - 2] + transpose_cost)
            D[i][j] = best

    # traceback: walk back from (n, m) choosing any move consistent with the table
    ops: list[dict] = []
    path: list[list[int]] = [[n, m]]
    i, j = n, m
    eps = 1e-9
    while i > 0 or j > 0:
        if i > 0 and j > 0 and a[i - 1] == b[j - 1] and abs(D[i][j] - D[i - 1][j - 1]) < eps:
            ops.append({"op": "match", "a": a[i - 1], "b": b[j - 1]})
            i, j = i - 1, j - 1
        elif i > 0 and j > 0 and abs(D[i][j] - (D[i - 1][j - 1] + substitute_cost)) < eps:
            ops.append({"op": "substitute", "a": a[i - 1], "b": b[j - 1]})
            i, j = i - 1, j - 1
        elif (
            variant == "DAMERAU" and i > 1 and j > 1 and a[i - 1] == b[j - 2] and a[i - 2] == b[j - 1]
            and abs(D[i][j] - (D[i - 2][j - 2] + transpose_cost)) < eps
        ):
            ops.append({"op": "transpose", "a": a[i - 2: i], "b": b[j - 2: j]})
            i, j = i - 2, j - 2
        elif i > 0 and abs(D[i][j] - (D[i - 1][j] + delete_cost)) < eps:
            ops.append({"op": "delete", "a": a[i - 1], "b": ""})
            i -= 1
        else:
            ops.append({"op": "insert", "a": "", "b": b[j - 1]})
            j -= 1
        path.append([i, j])
    ops.reverse()
    path.reverse()

    return {
        "variant": variant,
        "distance": D[n][m],
        "table": D,
        "operations": ops,
        "path": path,
        "cells_computed": n * m,
    }


def levenshtein_distance(a: str, b: str, max_distance: int | None = None) -> int:
    """Two-row Wagner-Fischer. If max_distance is given, returns max_distance + 1 as soon as
    every cell in a row exceeds it (the answer can only grow from there)."""
    if len(a) < len(b):
        a, b = b, a
    if not b:
        return len(a)
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, start=1):
        cur = [i] + [0] * len(b)
        for j, cb in enumerate(b, start=1):
            cur[j] = min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb))
        if max_distance is not None and min(cur) > max_distance:
            return max_distance + 1
        prev = cur
    return prev[-1]


def osa_distance(a: str, b: str, max_distance: int | None = None) -> int:
    """Damerau-Levenshtein (optimal string alignment) with three rolling rows.

    With max_distance, returns max_distance + 1 once two consecutive rows both
    exceed it: every later cell builds on one of the previous two rows (the
    transposition looks two rows back), so the answer can no longer fit.
    """
    n, m = len(a), len(b)
    if n == 0:
        return m
    if m == 0:
        return n
    two_back = [0] * (m + 1)
    prev = list(range(m + 1))
    for i in range(1, n + 1):
        cur = [i] + [0] * m
        for j in range(1, m + 1):
            cost = 0 if a[i - 1] == b[j - 1] else 1
            cur[j] = min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + cost)
            if i > 1 and j > 1 and a[i - 1] == b[j - 2] and a[i - 2] == b[j - 1]:
                cur[j] = min(cur[j], two_back[j - 2] + 1)
        if max_distance is not None and min(cur) > max_distance and min(prev) > max_distance:
            return max_distance + 1
        two_back, prev = prev, cur
    return prev[m]


# --------------------------------------------------------------------------- sequence alignment


def _alignment_table(a: str, b: str, match: int, mismatch: int, gap: int, local: bool) -> list[list[int]]:
    n, m = len(a), len(b)
    H = [[0] * (m + 1) for _ in range(n + 1)]
    if not local:
        for i in range(1, n + 1):
            H[i][0] = i * gap
        for j in range(1, m + 1):
            H[0][j] = j * gap
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            diag = H[i - 1][j - 1] + (match if a[i - 1] == b[j - 1] else mismatch)
            best = max(diag, H[i - 1][j] + gap, H[i][j - 1] + gap)
            H[i][j] = max(0, best) if local else best
    return H


def _trace_alignment(a, b, H, i, j, match, mismatch, gap, local):
    top: list[str] = []
    bottom: list[str] = []
    path = [[i, j]]
    while i > 0 or j > 0:
        if local and H[i][j] == 0:
            break
        if i > 0 and j > 0 and H[i][j] == H[i - 1][j - 1] + (match if a[i - 1] == b[j - 1] else mismatch):
            top.append(a[i - 1])
            bottom.append(b[j - 1])
            i, j = i - 1, j - 1
        elif i > 0 and H[i][j] == H[i - 1][j] + gap:
            top.append(a[i - 1])
            bottom.append("-")
            i -= 1
        else:
            top.append("-")
            bottom.append(b[j - 1])
            j -= 1
        path.append([i, j])
    path.reverse()
    return "".join(reversed(top)), "".join(reversed(bottom)), path, (i, j)


def needleman_wunsch(a: str, b: str, match: int = 1, mismatch: int = -1, gap: int = -2) -> dict:
    """Global alignment: every character of both strings takes part. O(n*m) time and space."""
    H = _alignment_table(a, b, match, mismatch, gap, local=False)
    top, bottom, path, _ = _trace_alignment(a, b, H, len(a), len(b), match, mismatch, gap, local=False)
    return {"mode": "GLOBAL", "score": H[len(a)][len(b)], "table": H, "aligned_a": top, "aligned_b": bottom, "path": path}


def smith_waterman(a: str, b: str, match: int = 2, mismatch: int = -1, gap: int = -2) -> dict:
    """Local alignment: scores are clamped at 0 so the best-scoring *substring pair* wins."""
    H = _alignment_table(a, b, match, mismatch, gap, local=True)
    best, bi, bj = 0, 0, 0
    for i in range(len(H)):
        for j in range(len(H[0])):
            if H[i][j] > best:
                best, bi, bj = H[i][j], i, j
    top, bottom, path, (si, sj) = _trace_alignment(a, b, H, bi, bj, match, mismatch, gap, local=True)
    return {
        "mode": "LOCAL",
        "score": best,
        "table": H,
        "aligned_a": top,
        "aligned_b": bottom,
        "path": path,
        "a_range": [si, bi],
        "b_range": [sj, bj],
    }


# --------------------------------------------------------------------------- interval DP


def matrix_chain_order(dims: list[int]) -> dict:
    """Matrix i has shape dims[i-1] x dims[i]. cost[i][j] = min scalar multiplications for A_i..A_j."""
    n = len(dims) - 1
    if n < 1:
        raise ValueError("need at least two dimensions (one matrix)")
    cost = [[0] * (n + 1) for _ in range(n + 1)]
    split = [[0] * (n + 1) for _ in range(n + 1)]
    for length in range(2, n + 1):
        for i in range(1, n - length + 2):
            j = i + length - 1
            cost[i][j] = INF
            for k in range(i, j):
                candidate = cost[i][k] + cost[k + 1][j] + dims[i - 1] * dims[k] * dims[j]
                if candidate < cost[i][j]:
                    cost[i][j] = candidate
                    split[i][j] = k

    def paren(i: int, j: int) -> str:
        if i == j:
            return f"A{i}"
        k = split[i][j]
        return f"({paren(i, k)} x {paren(k + 1, j)})"

    naive = 0  # left-to-right evaluation, for contrast
    rows = dims[0]
    for k in range(1, n):
        naive += rows * dims[k] * dims[k + 1]
    return {
        "min_cost": cost[1][n],
        "parenthesization": paren(1, n),
        "left_to_right_cost": naive,
        "cost_table": [[None if (i == 0 or j == 0 or j < i) else cost[i][j] for j in range(n + 1)] for i in range(n + 1)],
        "split_table": split,
    }


def _obst_tree(root: list[list[int]], keys: list, i: int, j: int):
    if i > j:
        return None
    r = root[i][j]
    return {"key": keys[r], "left": _obst_tree(root, keys, i, r - 1), "right": _obst_tree(root, keys, r + 1, j)}


def optimal_bst(keys: list, freqs: list[int], knuth: bool = True) -> dict:
    """Sorted keys with access frequencies; cost = sum(freq * depth), root depth 1.

    e[i][j] = min_r ( e[i][r-1] + e[r+1][j] ) + w(i, j).  The plain recurrence
    tries every root: O(n^3). Knuth's monotonicity root[i][j-1] <= root[i][j] <=
    root[i+1][j] shrinks the search range and telescopes to O(n^2).
    """
    n = len(keys)
    if n != len(freqs):
        raise ValueError("keys and freqs must have the same length")
    if n == 0:
        return {"cost": 0, "tree": None, "root_evaluations": 0}
    prefix = [0]
    for f in freqs:
        prefix.append(prefix[-1] + f)

    def w(i: int, j: int) -> int:
        return prefix[j + 1] - prefix[i]

    e = [[0] * (n + 1) for _ in range(n + 1)]  # e[i][j] for i..j inclusive, e[i][i-1] = 0
    root = [[0] * n for _ in range(n)]
    evaluations = 0

    def cost(i: int, j: int) -> int:
        return e[i][j] if i <= j else 0

    for i in range(n):
        e[i][i] = freqs[i]
        root[i][i] = i
    for length in range(2, n + 1):
        for i in range(n - length + 1):
            j = i + length - 1
            lo, hi = (root[i][j - 1], root[i + 1][j]) if knuth else (i, j)
            best, best_r = INF, lo
            for r in range(lo, hi + 1):
                evaluations += 1
                candidate = cost(i, r - 1) + cost(r + 1, j)
                if candidate < best:
                    best, best_r = candidate, r
            e[i][j] = best + w(i, j)
            root[i][j] = best_r
    return {"cost": e[0][n - 1], "tree": _obst_tree(root, keys, 0, n - 1), "root_evaluations": evaluations}


# --------------------------------------------------------------------------- bitmask DP


def held_karp_tsp(dist: list[list[float]]) -> dict:
    """dp[mask][v] = shortest path that starts at city 0, visits exactly `mask`, ends at v."""
    n = len(dist)
    if n == 0:
        return {"cost": 0, "tour": [], "states": 0}
    if n == 1:
        return {"cost": 0, "tour": [0, 0], "states": 1}
    full = 1 << n
    dp = [[INF] * n for _ in range(full)]
    parent = [[-1] * n for _ in range(full)]
    dp[1][0] = 0
    states = 0
    for mask in range(1, full):
        if not mask & 1:
            continue
        for v in range(n):
            cur = dp[mask][v]
            if cur == INF or not (mask >> v) & 1:
                continue
            states += 1
            for u in range(n):
                if (mask >> u) & 1:
                    continue
                nmask = mask | (1 << u)
                candidate = cur + dist[v][u]
                if candidate < dp[nmask][u]:
                    dp[nmask][u] = candidate
                    parent[nmask][u] = v
    best, last = INF, -1
    for v in range(1, n):
        candidate = dp[full - 1][v] + dist[v][0]
        if candidate < best:
            best, last = candidate, v
    tour = [0]
    mask, v = full - 1, last
    while v != 0:
        tour.append(v)
        prev = parent[mask][v]
        mask ^= 1 << v
        v = prev
    tour.append(0)
    tour.reverse()
    return {"cost": best, "tour": tour, "states": states}


def hamiltonian_path(n: int, adjacency: list[list[int]]) -> dict:
    """reach[mask] = bitset of vertices v such that some path covers exactly `mask` and ends at v."""
    if n == 0:
        return {"exists": False, "path": []}
    full = 1 << n
    reach = [0] * full
    parent: dict[tuple[int, int], int] = {}
    for v in range(n):
        reach[1 << v] |= 1 << v
    for mask in range(1, full):
        ends = reach[mask]
        if not ends:
            continue
        for v in range(n):
            if not (ends >> v) & 1:
                continue
            for u in adjacency[v]:
                if (mask >> u) & 1:
                    continue
                nmask = mask | (1 << u)
                if not (reach[nmask] >> u) & 1:
                    reach[nmask] |= 1 << u
                    parent[(nmask, u)] = v
    last = next((v for v in range(n) if (reach[full - 1] >> v) & 1), None)
    if last is None:
        return {"exists": False, "path": []}
    path = [last]
    mask = full - 1
    while mask & (mask - 1):  # more than one bit set
        prev = parent[(mask, last)]
        mask ^= 1 << last
        last = prev
        path.append(last)
    path.reverse()
    return {"exists": True, "path": path}


def sos_superset_sums(f: list[int], k: int) -> list[int]:
    """g[mask] = sum of f[s] over all s that are supersets of mask. O(k * 2^k).

    Processes one bit at a time: after handling bit i, g[mask] sums every s that
    agrees with mask on bits > i and is a superset on bits <= i.
    """
    if len(f) != 1 << k:
        raise ValueError("f must have length 2^k")
    g = list(f)
    for bit in range(k):
        for mask in range(1 << k):
            if not (mask >> bit) & 1:
                g[mask] += g[mask | (1 << bit)]
    return g


def sos_subset_sums(f: list[int], k: int) -> list[int]:
    """g[mask] = sum of f[s] over all s that are subsets of mask."""
    if len(f) != 1 << k:
        raise ValueError("f must have length 2^k")
    g = list(f)
    for bit in range(k):
        for mask in range(1 << k):
            if (mask >> bit) & 1:
                g[mask] += g[mask ^ (1 << bit)]
    return g


def bitmask_assignment(scores: list[list[float | None]]) -> dict:
    """Exact assignment of rows (students) to columns (slots), each used at most once.

    Objective is lexicographic: maximum number of assigned rows, then maximum
    total score - the same objective min-cost max-flow optimises. dp over
    (row index, mask of used columns): O(rows * 2^cols * cols). Only meant for
    small instances, where it acts as an independent correctness oracle.
    """
    rows = len(scores)
    cols = len(scores[0]) if rows else 0
    if cols > 16:
        raise ValueError("bitmask assignment is limited to 16 columns")
    NEG = (-1, -INF)
    # best[mask] after processing a prefix of rows -> (count, score)
    best: dict[int, tuple[int, float]] = {0: (0, 0.0)}
    choice: list[dict[int, tuple[int, int]]] = []
    for r in range(rows):
        nxt: dict[int, tuple[int, float]] = {}
        back: dict[int, tuple[int, int]] = {}
        for mask, (cnt, sc) in best.items():
            if (cnt, sc) > nxt.get(mask, NEG):  # leave row r unassigned
                nxt[mask] = (cnt, sc)
                back[mask] = (mask, -1)
            for c in range(cols):
                s = scores[r][c]
                if s is None or (mask >> c) & 1:
                    continue
                nmask = mask | (1 << c)
                cand = (cnt + 1, sc + s)
                if cand > nxt.get(nmask, NEG):
                    nxt[nmask] = cand
                    back[nmask] = (mask, c)
        best = nxt
        choice.append(back)
    final_mask = max(best, key=lambda m: best[m])
    count, total = best[final_mask]
    assignment = [-1] * rows
    mask = final_mask
    for r in range(rows - 1, -1, -1):
        prev_mask, c = choice[r][mask]
        assignment[r] = c
        mask = prev_mask
    return {"matched": count, "total_score": total, "assignment": assignment}


# --------------------------------------------------------------------------- knapsack / subset sum


def knapsack_01(weights: list[int], values: list[int], capacity: int) -> dict:
    """best[w] = best value with total weight <= w. O(n * W) - pseudo-polynomial: W is a
    number in the input, so the table is exponential in the *bit length* of W."""
    n = len(weights)
    best = [[0] * (capacity + 1) for _ in range(n + 1)]
    for i in range(1, n + 1):
        wi, vi = weights[i - 1], values[i - 1]
        for w in range(capacity + 1):
            best[i][w] = best[i - 1][w]
            if wi <= w and best[i - 1][w - wi] + vi > best[i][w]:
                best[i][w] = best[i - 1][w - wi] + vi
    chosen = []
    w = capacity
    for i in range(n, 0, -1):
        if best[i][w] != best[i - 1][w]:
            chosen.append(i - 1)
            w -= weights[i - 1]
    chosen.reverse()
    return {"value": best[n][capacity], "items": chosen, "cells": (n + 1) * (capacity + 1)}


def subset_sum(numbers: list[int], target: int) -> dict:
    reachable = [False] * (target + 1)
    reachable[0] = True
    came_from = [-1] * (target + 1)
    for idx, x in enumerate(numbers):
        for s in range(target, x - 1, -1):
            if not reachable[s] and reachable[s - x]:
                reachable[s] = True
                came_from[s] = idx
    if not reachable[target]:
        return {"possible": False, "subset": []}
    subset, s = [], target
    while s > 0:
        idx = came_from[s]
        subset.append(numbers[idx])
        s -= numbers[idx]
    return {"possible": True, "subset": sorted(subset)}


# --------------------------------------------------------------------------- DP on trees


def tree_dp(n: int, edges: list[tuple[int, int]]) -> dict:
    """All four classic tree DPs in two DFS passes (iterative, so deep trees are safe).

    down pass (post-order): subtree sizes, longest downward path, MIS take/skip
    up pass (pre-order, the rerooting technique): sum of distances from every
    node, from  ans[child] = ans[parent] - size[child] + (n - size[child]).
    """
    if n == 0:
        return {"diameter": 0, "centroids": [], "max_independent_set": 0, "sum_of_distances": []}
    adj: list[list[int]] = [[] for _ in range(n)]
    for u, v in edges:
        adj[u].append(v)
        adj[v].append(u)

    parent = [-1] * n
    order: list[int] = []
    seen = [False] * n
    seen[0] = True
    stack = [0]
    while stack:  # pre-order
        u = stack.pop()
        order.append(u)
        for v in adj[u]:
            if not seen[v]:
                seen[v] = True
                parent[v] = u
                stack.append(v)
    if len(order) != n:
        raise ValueError("edges do not form a connected tree")

    size = [1] * n
    down = [0] * n  # longest downward path length (edges)
    take = [1] * n  # MIS of subtree with u included
    skip = [0] * n  # MIS of subtree with u excluded
    depth_sum = [0] * n  # sum of distances from u to nodes in its subtree
    diameter = 0
    for u in reversed(order):
        best1 = best2 = 0
        for v in adj[u]:
            if v == parent[u]:
                continue
            size[u] += size[v]
            depth_sum[u] += depth_sum[v] + size[v]
            take[u] += skip[v]
            skip[u] += max(take[v], skip[v])
            length = down[v] + 1
            if length > best1:
                best1, best2 = length, best1
            elif length > best2:
                best2 = length
        down[u] = best1
        diameter = max(diameter, best1 + best2)

    total = [0] * n
    total[0] = depth_sum[0]
    for u in order:  # rerooting
        for v in adj[u]:
            if v != parent[u]:
                total[v] = total[u] - size[v] + (n - size[v])

    centroids = []
    for u in range(n):
        largest = n - size[u]
        for v in adj[u]:
            if v != parent[u]:
                largest = max(largest, size[v])
        if largest <= n // 2:
            centroids.append(u)

    return {
        "diameter": diameter,
        "centroids": centroids,
        "max_independent_set": max(take[0], skip[0]),
        "sum_of_distances": total,
        "subtree_sizes": size,
        "parent": parent,
    }


def bfs_distances(n: int, edges: list[tuple[int, int]], source: int) -> list[int]:
    """Plain BFS, used by tests as an oracle for the rerooting DP."""
    adj: list[list[int]] = [[] for _ in range(n)]
    for u, v in edges:
        adj[u].append(v)
        adj[v].append(u)
    dist = [-1] * n
    dist[source] = 0
    queue = deque([source])
    while queue:
        u = queue.popleft()
        for v in adj[u]:
            if dist[v] == -1:
                dist[v] = dist[u] + 1
                queue.append(v)
    return dist
