"""Request bodies for the Concept Lab and Allocation Insights endpoints.

Every size is bounded: several demos are exponential on purpose (Held-Karp,
exact vertex/set cover, bitmask assignment), so the limits keep each request
well under a second.
"""
from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator

from app.models.allocation import AlgorithmName


class PatternSearchRequest(BaseModel):
    text: str = Field(min_length=1, max_length=5000)
    pattern: str = Field(min_length=1, max_length=200)
    seed: int | None = None


class AhoCorasickRequest(BaseModel):
    text: str = Field(min_length=1, max_length=5000)
    patterns: list[str] = Field(min_length=1, max_length=20)

    @field_validator("patterns")
    @classmethod
    def _patterns(cls, value: list[str]) -> list[str]:
        cleaned = [p for p in value if p]
        if not cleaned:
            raise ValueError("at least one non-empty pattern is required")
        if any(len(p) > 50 for p in cleaned):
            raise ValueError("patterns are limited to 50 characters")
        return cleaned


class SuffixArrayRequest(BaseModel):
    text: str = Field(min_length=1, max_length=60)


class EditDistanceRequest(BaseModel):
    a: str = Field(max_length=40)
    b: str = Field(max_length=40)
    variant: Literal["LEVENSHTEIN", "DAMERAU", "WEIGHTED"] = "LEVENSHTEIN"
    insert_cost: float = Field(default=1.0, ge=0, le=10)
    delete_cost: float = Field(default=1.0, ge=0, le=10)
    substitute_cost: float = Field(default=1.0, ge=0, le=10)


class AlignmentRequest(BaseModel):
    a: str = Field(min_length=1, max_length=40)
    b: str = Field(min_length=1, max_length=40)
    mode: Literal["GLOBAL", "LOCAL"] = "GLOBAL"
    match: int = Field(default=1, ge=-10, le=10)
    mismatch: int = Field(default=-1, ge=-10, le=10)
    gap: int = Field(default=-2, ge=-10, le=10)


class MatrixChainRequest(BaseModel):
    dims: list[int] = Field(min_length=2, max_length=13)

    @field_validator("dims")
    @classmethod
    def _dims(cls, value: list[int]) -> list[int]:
        if any(d < 1 or d > 1000 for d in value):
            raise ValueError("dimensions must be between 1 and 1000")
        return value


class OptimalBSTRequest(BaseModel):
    keys: list[str] = Field(default_factory=list, max_length=15)
    freqs: list[int] = Field(default_factory=list, max_length=15)
    from_lab_data: bool = False  # keys = lab codes, freqs = how many students ranked each lab


class TSPRequest(BaseModel):
    num_cities: int = Field(default=8, ge=3, le=11)
    seed: int | None = 7


class HamiltonianRequest(BaseModel):
    num_vertices: int = Field(default=8, ge=2, le=14)
    edge_probability: float = Field(default=0.35, ge=0.0, le=1.0)
    seed: int | None = 3


class TreeRequest(BaseModel):
    num_nodes: int = Field(default=12, ge=2, le=60)
    seed: int | None = 5


class KnapsackRequest(BaseModel):
    weights: list[int] = Field(min_length=1, max_length=25)
    values: list[int] = Field(min_length=1, max_length=25)
    capacity: int = Field(ge=0, le=2000)
    epsilon: float = Field(default=0.2, ge=0.05, le=0.9)

    @field_validator("weights", "values")
    @classmethod
    def _positive(cls, value: list[int]) -> list[int]:
        if any(x < 1 or x > 1000 for x in value):
            raise ValueError("weights and values must be between 1 and 1000")
        return value


class RandomBipartiteRequest(BaseModel):
    num_left: int = Field(default=6, ge=1, le=12)
    num_right: int = Field(default=5, ge=1, le=12)
    edge_probability: float = Field(default=0.4, ge=0.0, le=1.0)
    seed: int | None = 11


class MinCostRequest(BaseModel):
    num_left: int = Field(default=6, ge=1, le=8)
    num_right: int = Field(default=5, ge=1, le=8)
    edge_probability: float = Field(default=0.6, ge=0.0, le=1.0)
    seed: int | None = 11


class ProjectSelectionRequest(BaseModel):
    profits: list[int] = Field(min_length=1, max_length=10)
    costs: list[int] = Field(min_length=1, max_length=10)
    requires: list[tuple[int, int]] = Field(default_factory=list, max_length=100)

    @field_validator("profits", "costs")
    @classmethod
    def _non_negative(cls, value: list[int]) -> list[int]:
        if any(x < 0 or x > 10_000 for x in value):
            raise ValueError("profits and costs must be between 0 and 10000")
        return value


class VertexCoverRequest(BaseModel):
    num_vertices: int = Field(default=10, ge=2, le=16)
    edge_probability: float = Field(default=0.3, ge=0.0, le=1.0)
    seed: int | None = 4


class SetCoverRequest(BaseModel):
    universe_size: int = Field(default=20, ge=1, le=30)
    num_sets: int = Field(default=10, ge=1, le=14)
    seed: int | None = 9


class PrimalityRequest(BaseModel):
    n: str = Field(min_length=1, max_length=40, description="decimal integer, sent as a string to survive JSON")
    rounds: int = Field(default=6, ge=1, le=20)
    seed: int | None = 1

    @field_validator("n")
    @classmethod
    def _numeric(cls, value: str) -> str:
        value = value.strip()
        if not value.isdigit():
            raise ValueError("n must be a non-negative decimal integer")
        return value


class QuicksortRequest(BaseModel):
    n: int = Field(default=500, ge=1, le=2000)
    input_kind: Literal["random", "sorted", "reversed", "few_unique"] = "sorted"
    seed: int | None = 2
    trials: int = Field(default=5, ge=1, le=20)


class ReservoirRequest(BaseModel):
    stream_size: int = Field(default=100, ge=1, le=1000)
    k: int = Field(default=10, ge=1, le=50)
    trials: int = Field(default=2000, ge=1, le=5000)
    seed: int | None = 8

    @model_validator(mode="after")
    def _budget(self) -> "ReservoirRequest":
        if self.stream_size * self.trials > 500_000:
            raise ValueError("stream_size x trials is limited to 500,000")
        return self


class HashingRequest(BaseModel):
    num_keys: int = Field(default=500, ge=1, le=2000)
    table_size: int = Field(default=97, ge=2, le=1000)
    seed: int | None = 6


class ScanRequest(BaseModel):
    values: list[int] = Field(min_length=1, max_length=64)
    processors: int = Field(default=4, ge=1, le=64)


class MonteCarloRequest(BaseModel):
    trials: int = Field(default=100, ge=2, le=300)
    outage_probability: float = Field(default=0.1, ge=0.0, le=1.0)
    seed: int | None = 2024
    algorithm: AlgorithmName = AlgorithmName.HOPCROFT_KARP
    run_id: int | None = None
