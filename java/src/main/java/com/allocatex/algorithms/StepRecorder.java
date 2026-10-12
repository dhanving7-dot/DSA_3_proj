package com.allocatex.algorithms;

import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

/** Collects numbered {@link AlgorithmStep}s; shared by every algorithm instead of a per-algorithm emit closure. */
final class StepRecorder {
    private final List<AlgorithmStep> steps = new ArrayList<>();

    /** @param keyValues alternating key / value pairs for the step's data payload */
    void emit(StepEvent event, String description, Object... keyValues) {
        Map<String, Object> data = new LinkedHashMap<>();
        for (int i = 0; i + 1 < keyValues.length; i += 2) {
            data.put((String) keyValues[i], keyValues[i + 1]);
        }
        steps.add(new AlgorithmStep(steps.size() + 1, event, description, data));
    }

    List<AlgorithmStep> steps() {
        return steps;
    }
}
