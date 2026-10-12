package com.allocatex.algorithms;

import java.util.ArrayList;
import java.util.Comparator;
import java.util.HashMap;
import java.util.HashSet;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;

/**
 * Domain-aware orchestration layer on top of the graph algorithms.
 *
 * <p>Accepts plain records ({@link StudentInput} / {@link LabInput} / {@link EngineConstraints})
 * so the algorithms and the eligibility/scoring logic can be tested without a database.
 *
 * <p>Pipeline:
 * <ol>
 *   <li>Determine eligibility for every (student, lab) pair given skills, department rules, lab
 *       status and preference-only constraints.</li>
 *   <li>Score every eligible edge (preference rank, skill fit, priority/fairness).</li>
 *   <li>Build the appropriate graph representation for the requested algorithm and run it
 *       (Kuhn/Hopcroft-Karp -> BipartiteGraph with lab-capacity "slot" expansion;
 *       Ford-Fulkerson/Edmonds-Karp/Dinic -> a source/sink FlowNetwork; min-cost flow -> the same
 *       network with edge costs).</li>
 *   <li>Translate the raw matching/flow result back into student-lab assignments with
 *       explainable reasons and aggregate statistics.</li>
 * </ol>
 *
 * <p>Fairness caps (at most a share of a lab's seats per department) are a <em>laminar</em>
 * capacity constraint: department quotas nested inside each lab's total. Plain bipartite matching
 * cannot express that, the flow formulation can - each (lab, department) pair gets a gadget node
 * whose edge into the lab carries the quota. So the matching-only algorithms reject a fairness cap
 * rather than silently ignoring it.
 */
public final class MatchingEngine {
    public static final List<String> MATCHING_ALGORITHMS = List.of("KUHN", "HOPCROFT_KARP");
    public static final List<String> FLOW_ALGORITHMS = List.of("FORD_FULKERSON", "EDMONDS_KARP", "DINIC");
    public static final List<String> COST_FLOW_ALGORITHMS = List.of("MIN_COST_FLOW");
    public static final List<String> ALL_ALGORITHMS = List.of(
            "KUHN", "HOPCROFT_KARP", "FORD_FULKERSON", "EDMONDS_KARP", "DINIC", "MIN_COST_FLOW");

    /** Match scores are rounded to 4 decimals, so this scale turns them into exact integer costs. */
    static final int COST_SCALE = 10_000;

    private MatchingEngine() {}

    /** A configuration the requested algorithm cannot honour. */
    public static final class AllocationConfigException extends IllegalArgumentException {
        public AllocationConfigException(String message) {
            super(message);
        }
    }

    /**
     * @param skills      skill name -> proficiency (1-5)
     * @param preferences lab id -> rank (1 = best)
     */
    public record StudentInput(int id, String department, int year, double cgpa, double priorityScore,
                               Map<String, Integer> skills, Map<Integer, Integer> preferences) {}

    public record LabRequiredSkill(String skillName, int minProficiency, boolean required) {}

    /** @param hasAvailableSlot scheduling/availability constraint */
    public record LabInput(int id, String department, int capacity, boolean isActive,
                           List<LabRequiredSkill> requiredSkills, boolean hasAvailableSlot) {
        public LabInput(int id, String department, int capacity, boolean isActive, List<LabRequiredSkill> requiredSkills) {
            this(id, department, capacity, isActive, requiredSkills, true);
        }
    }

    /** @param maxSharePerDepartment fairness: cap fraction of a lab's capacity per department, or null for none */
    public record EngineConstraints(boolean sameDepartmentOnly, boolean requirePreference, double minPreferenceScore,
                                    double preferenceWeight, double skillWeight, double priorityWeight,
                                    Double maxSharePerDepartment) {
        public static EngineConstraints defaults() {
            return new EngineConstraints(false, false, 0.3, 0.5, 0.3, 0.2, null);
        }

        public EngineConstraints withSameDepartmentOnly(boolean value) {
            return new EngineConstraints(value, requirePreference, minPreferenceScore, preferenceWeight,
                    skillWeight, priorityWeight, maxSharePerDepartment);
        }

        public EngineConstraints withRequirePreference(boolean value) {
            return new EngineConstraints(sameDepartmentOnly, value, minPreferenceScore, preferenceWeight,
                    skillWeight, priorityWeight, maxSharePerDepartment);
        }

        public EngineConstraints withMaxSharePerDepartment(Double value) {
            return new EngineConstraints(sameDepartmentOnly, requirePreference, minPreferenceScore, preferenceWeight,
                    skillWeight, priorityWeight, value);
        }
    }

    public record EligibleEdge(int studentId, int labId, double score, Integer preferenceRank, String reason) {}

    /** @param status MATCHED | UNMATCHED */
    public record AssignmentResult(int studentId, Integer labId, Integer preferenceRank, double matchScore,
                                   String eligibilityReason, String status) {}

    /** @param totalScore sum of match scores over matched students (what min-cost flow maximises) */
    public record EngineResult(String algorithm, List<AssignmentResult> assignments, int matchedCount,
                               int unmatchedCount, int totalStudents, int totalLabs, int totalEdges,
                               double preferenceSatisfaction, double capacityUtilization,
                               MatchingResult algorithmTrace, double totalScore) {}

    private record SkillFit(boolean eligible, double score, String reason) {}

    static double round4(double x) {
        return Math.round(x * 10_000.0) / 10_000.0;
    }

    private static SkillFit skillFit(StudentInput student, LabInput lab) {
        if (lab.requiredSkills().isEmpty()) {
            return new SkillFit(true, 1.0, "no specific skill requirements");
        }
        int satisfied = 0;
        int totalRequired = 0;
        List<String> missing = new ArrayList<>();
        for (LabRequiredSkill req : lab.requiredSkills()) {
            if (!req.required()) {
                continue;
            }
            totalRequired++;
            int proficiency = student.skills().getOrDefault(req.skillName(), 0);
            if (proficiency >= req.minProficiency()) {
                satisfied++;
            } else {
                missing.add(req.skillName());
            }
        }
        if (totalRequired == 0) {
            return new SkillFit(true, 1.0, "no mandatory skill requirements");
        }
        if (!missing.isEmpty()) {
            return new SkillFit(false, 0.0, "missing required skill(s): " + String.join(", ", missing));
        }
        return new SkillFit(true, (double) satisfied / totalRequired,
                "satisfies " + satisfied + "/" + totalRequired + " required skills");
    }

    private static boolean isUsable(LabInput lab) {
        return lab.isActive() && lab.hasAvailableSlot() && lab.capacity() > 0;
    }

    /**
     * Picks the most informative reason a student has zero eligible edges. Skill mismatches are
     * reported before department/preference mismatches since they are usually the more actionable
     * piece of feedback.
     */
    private static String bestRejectionReason(StudentInput student, List<LabInput> labs, EngineConstraints constraints) {
        if (labs.isEmpty()) {
            return "no laboratories are currently registered in the system";
        }
        String fallbackReason = "no eligible laboratory found for this student under current constraints";
        for (LabInput lab : labs) {
            if (!isUsable(lab)) {
                continue;
            }
            if (constraints.sameDepartmentOnly() && !student.department().equals(lab.department())) {
                continue;
            }
            SkillFit fit = skillFit(student, lab);
            if (!fit.eligible()) {
                return fit.reason() + " (lab " + lab.id() + ")";
            }
            if (constraints.requirePreference() && student.preferences().get(lab.id()) == null) {
                fallbackReason = "not eligible: lab requires a stated preference, none of student's preferences matched any active lab";
            }
        }
        return fallbackReason;
    }

    public static List<EligibleEdge> buildEligibleEdges(List<StudentInput> students, List<LabInput> labs,
                                                        EngineConstraints constraints) {
        List<EligibleEdge> edges = new ArrayList<>();
        List<LabInput> activeLabs = labs.stream().filter(MatchingEngine::isUsable).toList();

        for (StudentInput student : students) {
            for (LabInput lab : activeLabs) {
                if (constraints.sameDepartmentOnly() && !student.department().equals(lab.department())) {
                    continue;
                }
                Integer prefRank = student.preferences().get(lab.id());
                if (constraints.requirePreference() && prefRank == null) {
                    continue;
                }
                SkillFit fit = skillFit(student, lab);
                if (!fit.eligible()) {
                    continue;
                }

                double preferenceScore;
                String prefReason;
                if (prefRank != null) {
                    int maxRank = Math.max(student.preferences().size(), 1);
                    preferenceScore = 1.0 - (double) (prefRank - 1) / maxRank;
                    prefReason = "ranked #" + prefRank + " preference";
                } else {
                    preferenceScore = constraints.minPreferenceScore();
                    prefReason = "not in stated preferences (baseline score applied)";
                }

                double priorityScore = Math.min(Math.max(student.priorityScore(), 0.0), 1.0);
                double score = constraints.preferenceWeight() * preferenceScore
                        + constraints.skillWeight() * fit.score()
                        + constraints.priorityWeight() * priorityScore;

                String deptReason = student.department().equals(lab.department())
                        ? "same department as lab"
                        : "cross-department (" + student.department() + " -> " + lab.department() + ")";
                String reason = prefReason + "; " + fit.reason() + "; " + deptReason;

                edges.add(new EligibleEdge(student.id(), lab.id(), round4(score), prefRank, reason));
            }
        }
        return edges;
    }

    /** Per-student edge lists, best score first (the order augmenting-path searches try them in). */
    private static Map<Integer, List<EligibleEdge>> groupEdgesByStudent(List<EligibleEdge> edges) {
        Map<Integer, List<EligibleEdge>> grouped = new LinkedHashMap<>();
        for (EligibleEdge edge : edges) {
            grouped.computeIfAbsent(edge.studentId(), k -> new ArrayList<>()).add(edge);
        }
        for (List<EligibleEdge> studentEdges : grouped.values()) {
            studentEdges.sort(Comparator.comparingDouble(EligibleEdge::score).reversed());
        }
        return grouped;
    }

    private static Map<Integer, Integer> indexById(List<Integer> ids) {
        Map<Integer, Integer> index = new HashMap<>();
        for (int i = 0; i < ids.size(); i++) {
            index.put(ids.get(i), i);
        }
        return index;
    }

    private record IndexPairs(List<MatchingResult.MatchedPair> pairs, MatchingResult trace) {}

    /** Returns matched (student index, lab index) pairs and the algorithm trace. */
    private static IndexPairs runKuhnOrHopcroftKarp(List<StudentInput> students, List<LabInput> labs,
                                                    List<EligibleEdge> edges, String algorithm) {
        Map<Integer, Integer> studentIndex = indexById(students.stream().map(StudentInput::id).toList());
        Map<Integer, Integer> labIndex = indexById(labs.stream().map(LabInput::id).toList());

        // expand each lab into `capacity` slot-vertices on the right side; lab j's slots start at the
        // exclusive prefix sum of the capacities before it (computed with the work-efficient Blelloch scan)
        int[] capacities = labs.stream().mapToInt(LabInput::capacity).toArray();
        int[] slotOffsets = Parallel.blellochExclusiveScan(capacities).result();
        int slotCount = 0;
        for (int c : capacities) {
            slotCount += c;
        }
        int[] slotToLabIdx = new int[slotCount];
        for (int labIdx = 0; labIdx < labs.size(); labIdx++) {
            for (int slot = slotOffsets[labIdx]; slot < slotOffsets[labIdx] + capacities[labIdx]; slot++) {
                slotToLabIdx[slot] = labIdx;
            }
        }

        BipartiteGraph graph = new BipartiteGraph(students.size(), slotCount);
        for (Map.Entry<Integer, List<EligibleEdge>> entry : groupEdgesByStudent(edges).entrySet()) {
            int left = studentIndex.get(entry.getKey());
            for (EligibleEdge edge : entry.getValue()) {
                int labIdx = labIndex.get(edge.labId());
                for (int slot = slotOffsets[labIdx]; slot < slotOffsets[labIdx] + capacities[labIdx]; slot++) {
                    graph.addEdge(left, slot);
                }
            }
        }

        MatchingResult trace = algorithm.equals("KUHN") ? Kuhn.maxMatching(graph) : HopcroftKarp.maxMatching(graph);
        List<MatchingResult.MatchedPair> pairs = trace.matchedPairs().stream()
                .map(p -> new MatchingResult.MatchedPair(p.left(), slotToLabIdx[p.right()]))
                .toList();
        return new IndexPairs(pairs, trace);
    }

    /** Seats one department may take in a lab under a fairness cap (at least one, never above capacity). */
    public static int departmentQuota(int capacity, double share) {
        return Math.min(capacity, Math.max(1, (int) Math.floor(share * capacity)));
    }

    /** @param edge the EligibleEdge for student arcs, null otherwise */
    record Arc(int u, int v, int capacity, EligibleEdge edge) {}

    /**
     * Node numbering and arcs of the flow formulation, shared by plain and min-cost flow.
     *
     * <p>source(0) -> student nodes -> [ (lab, department) quota gadgets ] -> lab nodes -> sink.
     * Gadget nodes only exist when a fairness cap is active; they are numbered after the sink.
     */
    record FlowLayout(int numNodes, int source, int sink, int studentOffset, Map<Integer, Integer> nodeToLab,
                      List<Arc> arcs) {}

    private record GadgetKey(int labIdx, String department) {}

    static FlowLayout buildFlowLayout(List<StudentInput> students, List<LabInput> labs, List<EligibleEdge> edges,
                                      Double share) {
        Map<Integer, Integer> studentIndex = indexById(students.stream().map(StudentInput::id).toList());
        Map<Integer, Integer> labIndex = indexById(labs.stream().map(LabInput::id).toList());
        Map<Integer, String> departmentOf = new HashMap<>();
        for (StudentInput s : students) {
            departmentOf.put(s.id(), s.department());
        }

        int source = 0;
        int studentOffset = 1;
        int labOffset = studentOffset + students.size();
        int sink = labOffset + labs.size();
        int nextNode = sink + 1;

        List<Arc> arcs = new ArrayList<>();
        for (int i = 0; i < students.size(); i++) {
            arcs.add(new Arc(source, studentOffset + i, 1, null));
        }
        for (int j = 0; j < labs.size(); j++) {
            arcs.add(new Arc(labOffset + j, sink, labs.get(j).capacity(), null));
        }

        Map<Integer, Integer> nodeToLab = new HashMap<>();
        for (int j = 0; j < labs.size(); j++) {
            nodeToLab.put(labOffset + j, j);
        }
        Map<GadgetKey, Integer> gadgets = new LinkedHashMap<>();
        for (Map.Entry<Integer, List<EligibleEdge>> entry : groupEdgesByStudent(edges).entrySet()) {
            int sid = entry.getKey();
            int studentNode = studentOffset + studentIndex.get(sid);
            for (EligibleEdge edge : entry.getValue()) {
                int labIdx = labIndex.get(edge.labId());
                int target;
                if (share == null) {
                    target = labOffset + labIdx;
                } else {
                    GadgetKey key = new GadgetKey(labIdx, departmentOf.get(sid));
                    Integer node = gadgets.get(key);
                    if (node == null) {
                        node = nextNode++;
                        gadgets.put(key, node);
                        nodeToLab.put(node, labIdx);
                    }
                    target = node;
                }
                arcs.add(new Arc(studentNode, target, 1, edge));
            }
        }
        for (Map.Entry<GadgetKey, Integer> gadget : gadgets.entrySet()) {
            int labIdx = gadget.getKey().labIdx();
            arcs.add(new Arc(gadget.getValue(), labOffset + labIdx,
                    departmentQuota(labs.get(labIdx).capacity(), share), null));
        }

        return new FlowLayout(nextNode, source, sink, studentOffset, nodeToLab, arcs);
    }

    private static List<MatchingResult.MatchedPair> extractFlowPairs(List<? extends List<? extends Edge>> adjacency,
                                                                     FlowLayout layout, int numStudents) {
        List<MatchingResult.MatchedPair> pairs = new ArrayList<>();
        for (int i = 0; i < numStudents; i++) {
            for (Edge edge : adjacency.get(layout.studentOffset() + i)) {
                Integer labIdx = layout.nodeToLab().get(edge.to);
                if (edge.flow > 0 && labIdx != null) {
                    pairs.add(new MatchingResult.MatchedPair(i, labIdx));
                    break;
                }
            }
        }
        return pairs;
    }

    private static IndexPairs runFlowAlgorithm(List<StudentInput> students, List<LabInput> labs,
                                               List<EligibleEdge> edges, String algorithm, Double share) {
        FlowLayout layout = buildFlowLayout(students, labs, edges, share);
        FlowNetwork network = new FlowNetwork(layout.numNodes());
        for (Arc arc : layout.arcs()) {
            network.addEdge(arc.u(), arc.v(), arc.capacity());
        }

        FlowResult result = switch (algorithm) {
            case "EDMONDS_KARP" -> EdmondsKarp.maxFlow(network, layout.source(), layout.sink(), "EDMONDS_KARP");
            case "FORD_FULKERSON" -> FordFulkerson.maxFlow(network, layout.source(), layout.sink());
            default -> Dinic.maxFlow(network, layout.source(), layout.sink());
        };
        return new IndexPairs(extractFlowPairs(network.adjacency(), layout, students.size()), result.trace());
    }

    /**
     * Cheapest maximum flow where a student->lab arc costs (best score - score): among all maximum
     * matchings this picks one with the largest total match score.
     */
    private static IndexPairs runMinCostFlow(List<StudentInput> students, List<LabInput> labs,
                                             List<EligibleEdge> edges, Double share) {
        FlowLayout layout = buildFlowLayout(students, labs, edges, share);
        double bestScore = edges.stream().mapToDouble(EligibleEdge::score).max().orElse(0.0);
        MinCostFlow.CostFlowNetwork network = new MinCostFlow.CostFlowNetwork(layout.numNodes());
        for (Arc arc : layout.arcs()) {
            int cost = arc.edge() != null ? (int) Math.round((bestScore - arc.edge().score()) * COST_SCALE) : 0;
            network.addEdge(arc.u(), arc.v(), arc.capacity(), cost);
        }
        MinCostFlow.Result result = MinCostFlow.minCostMaxFlow(network, layout.source(), layout.sink());
        return new IndexPairs(extractFlowPairs(network.adjacency(), layout, students.size()), result.trace());
    }

    public static EngineResult runAllocation(List<StudentInput> students, List<LabInput> labs,
                                             EngineConstraints constraints, String algorithm) {
        if (!ALL_ALGORITHMS.contains(algorithm)) {
            throw new AllocationConfigException("Unknown algorithm: " + algorithm);
        }
        Double share = constraints.maxSharePerDepartment();
        if (share != null) {
            if (!(share > 0 && share <= 1)) {
                throw new AllocationConfigException("max_share_per_department must be in (0, 1]");
            }
            if (MATCHING_ALGORITHMS.contains(algorithm)) {
                throw new AllocationConfigException(algorithm + " solves plain bipartite matching, which cannot "
                        + "express a per-department fairness cap (department quotas nested inside each lab's capacity "
                        + "form a laminar constraint). Use a flow formulation - FORD_FULKERSON, EDMONDS_KARP, DINIC or "
                        + "MIN_COST_FLOW - which models each quota as a gadget node.");
            }
        }

        List<EligibleEdge> edges = buildEligibleEdges(students, labs, constraints);

        if (students.isEmpty() || labs.isEmpty() || edges.isEmpty()) {
            List<AssignmentResult> assignments = new ArrayList<>();
            for (StudentInput s : students) {
                assignments.add(new AssignmentResult(s.id(), null, null, 0.0,
                        bestRejectionReason(s, labs, constraints), "UNMATCHED"));
            }
            List<Integer> allLeft = new ArrayList<>();
            for (int i = 0; i < students.size(); i++) {
                allLeft.add(i);
            }
            List<Integer> allRight = new ArrayList<>();
            for (int j = 0; j < labs.size(); j++) {
                allRight.add(j);
            }
            MatchingResult emptyTrace = new MatchingResult(algorithm, List.of(), allLeft, allRight,
                    students.size() + labs.size(), 0, 0, 0, 0.0, "N/A", "N/A", List.of());
            return new EngineResult(algorithm, assignments, 0, students.size(), students.size(), labs.size(), 0,
                    0.0, 0.0, emptyTrace, 0.0);
        }

        Map<Long, EligibleEdge> edgeLookup = new HashMap<>();
        for (EligibleEdge e : edges) {
            edgeLookup.put(pairKey(e.studentId(), e.labId()), e);
        }

        IndexPairs run;
        if (MATCHING_ALGORITHMS.contains(algorithm)) {
            run = runKuhnOrHopcroftKarp(students, labs, edges, algorithm);
        } else if (FLOW_ALGORITHMS.contains(algorithm)) {
            run = runFlowAlgorithm(students, labs, edges, algorithm, share);
        } else {
            run = runMinCostFlow(students, labs, edges, share);
        }
        Set<Integer> studentsWithEdges = new HashSet<>();
        for (EligibleEdge e : edges) {
            studentsWithEdges.add(e.studentId());
        }

        Map<Integer, Integer> matchedStudentIds = new HashMap<>(); // student id -> lab id
        for (MatchingResult.MatchedPair pair : run.pairs()) {
            matchedStudentIds.put(students.get(pair.left()).id(), labs.get(pair.right()).id());
        }

        List<AssignmentResult> assignments = new ArrayList<>();
        int preferenceHits = 0;
        double totalScore = 0.0;
        for (StudentInput student : students) {
            Integer labId = matchedStudentIds.get(student.id());
            if (labId != null) {
                EligibleEdge edge = edgeLookup.get(pairKey(student.id(), labId));
                assignments.add(new AssignmentResult(student.id(), labId, edge.preferenceRank(), edge.score(),
                        edge.reason(), "MATCHED"));
                totalScore += edge.score();
                if (edge.preferenceRank() != null) {
                    preferenceHits++;
                }
            } else {
                String reason;
                if (studentsWithEdges.contains(student.id())) {
                    String quotaClause = share != null ? " or department quota" : "";
                    reason = "eligible for one or more labs, but capacity" + quotaClause + " was exhausted: "
                            + "no augmenting path reaches a free seat, so no larger matching includes this student";
                } else {
                    reason = bestRejectionReason(student, labs, constraints);
                }
                assignments.add(new AssignmentResult(student.id(), null, null, 0.0, reason, "UNMATCHED"));
            }
        }

        int matchedCount = matchedStudentIds.size();
        int unmatchedCount = students.size() - matchedCount;
        int totalCapacity = labs.stream().mapToInt(LabInput::capacity).sum();
        double capacityUtilization = totalCapacity > 0 ? round4((double) matchedCount / totalCapacity) : 0.0;
        double preferenceSatisfaction = matchedCount > 0 ? round4((double) preferenceHits / matchedCount) : 0.0;

        return new EngineResult(algorithm, assignments, matchedCount, unmatchedCount, students.size(), labs.size(),
                edges.size(), preferenceSatisfaction, capacityUtilization, run.trace(), round4(totalScore));
    }

    private static long pairKey(int studentId, int labId) {
        return ((long) studentId << 32) | (labId & 0xFFFFFFFFL);
    }
}
