package com.allocatex.algorithms;

import java.util.ArrayList;
import java.util.List;
import java.util.NoSuchElementException;

/**
 * Hand-built binary min-heap of (key, value) pairs, used by Dijkstra inside min-cost max-flow.
 *
 * <p>Kept dependency-free in the same spirit as the rest of the package: the engine never leans
 * on a library priority queue. push / pop: O(log n); peek / size: O(1).
 */
public final class MinHeap {
    public record Entry(long key, int value) {}

    private final List<Entry> items = new ArrayList<>();

    public int size() {
        return items.size();
    }

    public boolean isEmpty() {
        return items.isEmpty();
    }

    public void push(long key, int value) {
        items.add(new Entry(key, value));
        int i = items.size() - 1;
        while (i > 0) {
            int parent = (i - 1) / 2;
            if (items.get(parent).key() <= items.get(i).key()) {
                break;
            }
            swap(parent, i);
            i = parent;
        }
    }

    public Entry pop() {
        if (items.isEmpty()) {
            throw new NoSuchElementException("pop from empty heap");
        }
        Entry top = items.get(0);
        Entry last = items.remove(items.size() - 1);
        if (!items.isEmpty()) {
            items.set(0, last);
            int i = 0;
            int n = items.size();
            while (true) {
                int left = 2 * i + 1;
                int right = left + 1;
                int smallest = i;
                if (left < n && items.get(left).key() < items.get(smallest).key()) {
                    smallest = left;
                }
                if (right < n && items.get(right).key() < items.get(smallest).key()) {
                    smallest = right;
                }
                if (smallest == i) {
                    break;
                }
                swap(smallest, i);
                i = smallest;
            }
        }
        return top;
    }

    private void swap(int a, int b) {
        Entry tmp = items.get(a);
        items.set(a, items.get(b));
        items.set(b, tmp);
    }
}
