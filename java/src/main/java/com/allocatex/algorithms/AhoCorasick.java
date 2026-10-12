package com.allocatex.algorithms;

import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.Collections;
import java.util.HashSet;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;

/**
 * Multi-pattern matcher: a trie of all patterns plus BFS-built failure links.
 *
 * <p>fail[v] -> node for the longest proper suffix of v's string that is also a trie path;
 * dictLink -> nearest node along the failure chain that ends a pattern (so reporting all matches at
 * a position costs O(matches), not O(depth)).
 *
 * <p>Time complexity: O(n + sum|P| + z).
 */
public final class AhoCorasick {
    public record Match(int position, int patternIndex) implements Comparable<Match> {
        @Override
        public int compareTo(Match other) {
            int byPosition = Integer.compare(position, other.position);
            return byPosition != 0 ? byPosition : Integer.compare(patternIndex, other.patternIndex);
        }
    }

    public record NodeInfo(int node, String label, int fail, String failLabel, List<String> outputs) {}

    private final List<String> patterns;
    private final List<Map<Character, Integer>> children = new ArrayList<>();
    private final List<Integer> fail = new ArrayList<>();
    private final List<List<Integer>> ends = new ArrayList<>(); // pattern indices ending exactly at this node
    private final List<Integer> dictLink = new ArrayList<>();

    public AhoCorasick(List<String> patterns) {
        this.patterns = List.copyOf(patterns);
        addNode();

        for (int idx = 0; idx < this.patterns.size(); idx++) {
            String pattern = this.patterns.get(idx);
            if (pattern.isEmpty()) {
                continue;
            }
            int node = 0;
            for (int i = 0; i < pattern.length(); i++) {
                char ch = pattern.charAt(i);
                Integer next = children.get(node).get(ch);
                if (next == null) {
                    next = addNode();
                    children.get(node).put(ch, next);
                }
                node = next;
            }
            ends.get(node).add(idx);
        }

        ArrayDeque<Integer> queue = new ArrayDeque<>(children.get(0).values()); // depth-1 nodes fail to the root
        while (!queue.isEmpty()) {
            int node = queue.poll();
            for (Map.Entry<Character, Integer> entry : children.get(node).entrySet()) {
                char ch = entry.getKey();
                int child = entry.getValue();
                int f = fail.get(node);
                while (f != 0 && !children.get(f).containsKey(ch)) {
                    f = fail.get(f);
                }
                int candidate = children.get(f).getOrDefault(ch, 0);
                fail.set(child, candidate != child ? candidate : 0);
                int target = fail.get(child);
                dictLink.set(child, !ends.get(target).isEmpty() ? target : dictLink.get(target));
                queue.add(child);
            }
        }
    }

    private int addNode() {
        children.add(new LinkedHashMap<>());
        fail.add(0);
        ends.add(new ArrayList<>());
        dictLink.add(-1);
        return children.size() - 1;
    }

    public int numNodes() {
        return children.size();
    }

    /** Every occurrence as (start position, pattern index), in text order. */
    public List<Match> search(String text) {
        List<Match> matches = new ArrayList<>();
        int node = 0;
        for (int i = 0; i < text.length(); i++) {
            char ch = text.charAt(i);
            while (node != 0 && !children.get(node).containsKey(ch)) {
                node = fail.get(node);
            }
            node = children.get(node).getOrDefault(ch, 0);
            for (int out = node; out > 0; out = dictLink.get(out)) {
                for (int idx : ends.get(out)) {
                    matches.add(new Match(i - patterns.get(idx).length() + 1, idx));
                }
            }
        }
        Collections.sort(matches);
        return matches;
    }

    public Set<Integer> foundSet(String text) {
        Set<Integer> found = new HashSet<>();
        for (Match match : search(text)) {
            found.add(match.patternIndex());
        }
        return found;
    }

    /** Node table for visualisation: string spelled by each node, its failure target, outputs. */
    public List<NodeInfo> describe() {
        String[] labels = new String[numNodes()];
        labels[0] = "";
        ArrayDeque<Integer> queue = new ArrayDeque<>();
        queue.add(0);
        while (!queue.isEmpty()) {
            int node = queue.poll();
            for (Map.Entry<Character, Integer> entry : children.get(node).entrySet()) {
                labels[entry.getValue()] = labels[node] + entry.getKey();
                queue.add(entry.getValue());
            }
        }
        List<NodeInfo> table = new ArrayList<>();
        for (int v = 0; v < numNodes(); v++) {
            List<String> outputs = new ArrayList<>();
            for (int i : ends.get(v)) {
                outputs.add(patterns.get(i));
            }
            table.add(new NodeInfo(v, labels[v], fail.get(v), labels[fail.get(v)], outputs));
        }
        return table;
    }
}
