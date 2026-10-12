"""Hand-built binary min-heap used by Dijkstra inside min-cost max-flow.

Kept dependency-free in the same spirit as the rest of `app.algorithms`: the
engine never leans on a library priority queue, every structure it relies on
is implemented (and therefore explainable) here.

push / pop: O(log n)   peek / len: O(1)
"""
from __future__ import annotations


class MinHeap:
    """Array-backed binary heap of (key, value) pairs ordered by key."""

    def __init__(self) -> None:
        self._items: list[tuple[float, int]] = []

    def __len__(self) -> int:
        return len(self._items)

    def push(self, key: float, value: int) -> None:
        items = self._items
        items.append((key, value))
        i = len(items) - 1
        while i > 0:
            parent = (i - 1) // 2
            if items[parent][0] <= items[i][0]:
                break
            items[parent], items[i] = items[i], items[parent]
            i = parent

    def pop(self) -> tuple[float, int]:
        items = self._items
        if not items:
            raise IndexError("pop from empty heap")
        top = items[0]
        last = items.pop()
        if items:
            items[0] = last
            i = 0
            n = len(items)
            while True:
                left = 2 * i + 1
                right = left + 1
                smallest = i
                if left < n and items[left][0] < items[smallest][0]:
                    smallest = left
                if right < n and items[right][0] < items[smallest][0]:
                    smallest = right
                if smallest == i:
                    break
                items[smallest], items[i] = items[i], items[smallest]
                i = smallest
        return top
