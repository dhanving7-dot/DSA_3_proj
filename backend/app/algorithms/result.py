"""Common result / trace types returned by every algorithm implementation.

Keeping one shared shape means the matching engine, the REST layer and the
WebSocket live-progress layer can all treat Kuhn / Hopcroft-Karp /
Edmonds-Karp / Dinic interchangeably.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class StepEvent(str, Enum):
    GRAPH_CREATED = "GRAPH_CREATED"
    PHASE_START = "PHASE_START"
    SEARCHING_AUGMENTING_PATH = "SEARCHING_AUGMENTING_PATH"
    AUGMENTING_PATH_FOUND = "AUGMENTING_PATH_FOUND"
    MATCH_FOUND = "MATCH_FOUND"
    MATCH_UPDATED = "MATCH_UPDATED"
    NO_PATH_FOUND = "NO_PATH_FOUND"
    ALGORITHM_COMPLETE = "ALGORITHM_COMPLETE"


@dataclass
class AlgorithmStep:
    step_number: int
    event: StepEvent
    description: str
    data: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "step_number": self.step_number,
            "event": self.event.value,
            "description": self.description,
            "data": self.data,
        }


@dataclass
class MatchingResult:
    algorithm: str
    matched_pairs: list[tuple[int, int]]
    unmatched_left: list[int]
    unmatched_right: list[int]
    vertices: int
    edges: int
    iterations: int
    augmenting_paths_found: int
    execution_time_ms: float
    time_complexity: str
    space_complexity: str
    steps: list[AlgorithmStep] = field(default_factory=list)

    @property
    def match_size(self) -> int:
        return len(self.matched_pairs)

    def to_dict(self, include_steps: bool = True) -> dict:
        payload = {
            "algorithm": self.algorithm,
            "matched_pairs": self.matched_pairs,
            "match_size": self.match_size,
            "unmatched_left": self.unmatched_left,
            "unmatched_right": self.unmatched_right,
            "vertices": self.vertices,
            "edges": self.edges,
            "iterations": self.iterations,
            "augmenting_paths_found": self.augmenting_paths_found,
            "execution_time_ms": self.execution_time_ms,
            "time_complexity": self.time_complexity,
            "space_complexity": self.space_complexity,
        }
        if include_steps:
            payload["steps"] = [s.to_dict() for s in self.steps]
        return payload
