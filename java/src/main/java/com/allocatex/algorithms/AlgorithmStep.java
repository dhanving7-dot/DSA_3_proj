package com.allocatex.algorithms;

import java.util.Map;

/** One entry of an algorithm's step-by-step trace. */
public record AlgorithmStep(int stepNumber, StepEvent event, String description, Map<String, Object> data) {}
