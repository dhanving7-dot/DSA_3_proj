package com.allocatex.algorithms;

/** Kind of an {@link AlgorithmStep} in an algorithm's live trace. */
public enum StepEvent {
    GRAPH_CREATED,
    PHASE_START,
    SEARCHING_AUGMENTING_PATH,
    AUGMENTING_PATH_FOUND,
    MATCH_FOUND,
    MATCH_UPDATED,
    NO_PATH_FOUND,
    ALGORITHM_COMPLETE
}
