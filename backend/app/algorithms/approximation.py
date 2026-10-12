"""Module 5 - NP-hard problems: exact exponential algorithms next to polynomial approximations.

Each pair is meant to be run side-by-side so the approximation ratio is
measured, not just quoted.

  vertex_cover_2approx      endpoints of a maximal matching          ratio <= 2
  vertex_cover_exact        bitmask search over vertex subsets       exponential
  greedy_set_cover          most-new-elements-first                  ratio <= H(n) ~ ln n + 1
  exact_set_cover           bitmask DP over subsets of sets          O(2^k)
  knapsack_greedy           density order, can be arbitrarily bad    no guarantee
  knapsack_fptas            value scaling + exact DP                 (1 - eps) OPT in poly(n, 1/eps)
  tsp_nearest_neighbour     greedy tour                              no constant guarantee
  tsp_mst_2approx           preorder walk of an MST (metric TSP)     ratio <= 2
"""
from __future__ import annotations

import math

from app.algorithms.dp import knapsack_01

INF = float("inf")


def harmonic(n: int) -> float:
    return sum(1.0 / i for i in range(1, n + 1))


# --------------------------------------------------------------------------- vertex cover


def vertex_cover_2approx(edges: list[tuple[int, int]]) -> dict:
    """Pick any uncovered edge, take both endpoints. The picked edges form a matching M,
    and any cover needs one endpoint per edge of M, so OPT >= |M| = |cover| / 2."""
    cover: set[int] = set()
    matching: list[tuple[int, int]] = []
    for u, v in edges:
        if u not in cover and v not in cover:
            cover.add(u)
            cover.add(v)
            matching.append((u, v))
    return {"cover": sorted(cover), "size": len(cover), "maximal_matching": matching}


def vertex_cover_exact(n: int, edges: list[tuple[int, int]]) -> dict:
    """Smallest cover by checking subsets in increasing size. Exponential - n is capped by callers."""
    if n > 20:
        raise ValueError("exact vertex cover is limited to 20 vertices")
    edge_masks = [(1 << u) | (1 << v) for u, v in edges]
    best_mask = (1 << n) - 1
    best_size = n
    checked = 0
    for mask in range(1 << n):
        size = bin(mask).count("1")
        if size >= best_size:
            continue
        checked += 1
        if all(mask & em for em in edge_masks):
            best_mask, best_size = mask, size
    return {"cover": [v for v in range(n) if (best_mask >> v) & 1], "size": best_size, "subsets_checked": checked}


# --------------------------------------------------------------------------- set cover


def greedy_set_cover(universe: int, sets: list[int]) -> dict:
    """`universe` and every set are bitmasks over the elements. Returns chosen set indices in pick order."""
    uncovered = universe
    chosen: list[int] = []
    gains: list[int] = []
    while uncovered:
        best_idx, best_gain = -1, 0
        for idx, s in enumerate(sets):
            gain = bin(s & uncovered).count("1")
            if gain > best_gain:
                best_idx, best_gain = idx, gain
        if best_idx == -1:
            break  # remaining elements are in no set
        chosen.append(best_idx)
        gains.append(best_gain)
        uncovered &= ~sets[best_idx]
    return {"chosen": chosen, "gains": gains, "fully_covered": uncovered == 0}


def exact_set_cover(universe: int, sets: list[int]) -> dict:
    """cover[mask] = union of the sets in `mask`, built incrementally from mask without its lowest bit.

    That is the subset-DP trick: each of the 2^k unions costs one OR. Then the
    smallest mask whose union contains the universe wins.
    """
    k = len(sets)
    if k > 22:
        raise ValueError("exact set cover is limited to 22 sets")
    full = 1 << k
    cover = [0] * full
    best_mask, best_size = None, k + 1
    for mask in range(1, full):
        low = mask & -mask
        cover[mask] = cover[mask ^ low] | sets[low.bit_length() - 1]
        if cover[mask] & universe == universe:
            size = bin(mask).count("1")
            if size < best_size:
                best_mask, best_size = mask, size
    if universe == 0:
        return {"chosen": [], "size": 0, "subsets_evaluated": full}
    if best_mask is None:
        return {"chosen": None, "size": None, "subsets_evaluated": full}
    return {"chosen": [i for i in range(k) if (best_mask >> i) & 1], "size": best_size, "subsets_evaluated": full}


# --------------------------------------------------------------------------- knapsack


def knapsack_greedy(weights: list[int], values: list[int], capacity: int) -> dict:
    order = sorted(range(len(weights)), key=lambda i: values[i] / weights[i] if weights[i] else INF, reverse=True)
    chosen, total_w, total_v = [], 0, 0
    for i in order:
        if total_w + weights[i] <= capacity:
            chosen.append(i)
            total_w += weights[i]
            total_v += values[i]
    return {"value": total_v, "items": sorted(chosen)}


def knapsack_fptas(weights: list[int], values: list[int], capacity: int, epsilon: float) -> dict:
    """Scale values by K = eps * vmax / n and round down, then solve exactly with a DP over
    *scaled value* (min weight to reach each value). Rounding loses < K per item, so the
    result is >= (1 - eps) * OPT, in O(n^3 / eps) time - polynomial in n and 1/eps."""
    n = len(weights)
    fitting = [i for i in range(n) if weights[i] <= capacity]
    if not fitting:
        return {"value": 0, "items": [], "scale": None}
    vmax = max(values[i] for i in fitting)
    if vmax == 0:
        return {"value": 0, "items": [], "scale": None}
    k = epsilon * vmax / n
    scaled = [math.floor(values[i] / k) if i in fitting else 0 for i in range(n)]
    total = sum(scaled)
    min_weight = [INF] * (total + 1)
    min_weight[0] = 0
    keep = [[False] * (total + 1) for _ in range(n)]
    for i in fitting:
        sv, wi = scaled[i], weights[i]
        for v in range(total, sv - 1, -1):
            if min_weight[v - sv] + wi < min_weight[v]:
                min_weight[v] = min_weight[v - sv] + wi
                keep[i][v] = True
    best_v = max(v for v in range(total + 1) if min_weight[v] <= capacity)
    items, v = [], best_v
    for i in reversed(range(n)):
        if v >= 0 and keep[i][v]:
            items.append(i)
            v -= scaled[i]
    items.sort()
    return {"value": sum(values[i] for i in items), "items": items, "scale": k}


def knapsack_compare(weights: list[int], values: list[int], capacity: int, epsilon: float) -> dict:
    exact = knapsack_01(weights, values, capacity)
    greedy = knapsack_greedy(weights, values, capacity)
    fptas = knapsack_fptas(weights, values, capacity, epsilon)
    opt = exact["value"]
    return {
        "exact": exact,
        "greedy": {**greedy, "ratio": round(greedy["value"] / opt, 4) if opt else 1.0},
        "fptas": {**fptas, "ratio": round(fptas["value"] / opt, 4) if opt else 1.0, "guarantee": round(1 - epsilon, 4)},
    }


# --------------------------------------------------------------------------- metric TSP


def tour_cost(dist: list[list[float]], tour: list[int]) -> float:
    return sum(dist[tour[i]][tour[i + 1]] for i in range(len(tour) - 1))


def tsp_nearest_neighbour(dist: list[list[float]]) -> dict:
    n = len(dist)
    if n == 0:
        return {"cost": 0, "tour": []}
    visited = [False] * n
    visited[0] = True
    tour = [0]
    for _ in range(n - 1):
        last = tour[-1]
        nxt = min((v for v in range(n) if not visited[v]), key=lambda v: dist[last][v])
        visited[nxt] = True
        tour.append(nxt)
    tour.append(0)
    return {"cost": tour_cost(dist, tour), "tour": tour}


def tsp_mst_2approx(dist: list[list[float]]) -> dict:
    """Prim's MST, then a preorder walk with shortcuts. Shortcutting never increases the cost
    under the triangle inequality, so cost <= 2 * MST <= 2 * OPT."""
    n = len(dist)
    if n == 0:
        return {"cost": 0, "tour": [], "mst_weight": 0}
    in_tree = [False] * n
    best = [INF] * n
    parent = [-1] * n
    best[0] = 0
    children: list[list[int]] = [[] for _ in range(n)]
    mst_weight = 0.0
    for _ in range(n):
        u = min((v for v in range(n) if not in_tree[v]), key=lambda v: best[v])
        in_tree[u] = True
        mst_weight += best[u]
        if parent[u] != -1:
            children[parent[u]].append(u)
        for v in range(n):
            if not in_tree[v] and dist[u][v] < best[v]:
                best[v] = dist[u][v]
                parent[v] = u
    tour, stack = [], [0]
    while stack:
        u = stack.pop()
        tour.append(u)
        stack.extend(reversed(children[u]))
    tour.append(0)
    return {"cost": tour_cost(dist, tour), "tour": tour, "mst_weight": mst_weight}
