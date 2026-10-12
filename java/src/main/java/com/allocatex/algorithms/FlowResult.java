package com.allocatex.algorithms;

/** Value of a maximum flow together with the trace of the algorithm that computed it. */
public record FlowResult(int maxFlow, MatchingResult trace) {}
