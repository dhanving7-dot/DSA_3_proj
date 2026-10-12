"""Entity search over students and laboratories, powered by the hand-built string algorithms.

All searchable fields are concatenated into one newline-separated corpus
(the way a text engine indexes documents). A single run of the chosen
algorithm finds every occurrence; each match position is mapped back to its
record by binary search over the field start offsets. The suffix array of
the corpus is cached and only rebuilt when the corpus text changes.

When `fuzzy` is on and the exact pass finds nothing for a record, its name
and code tokens are compared with the query by Damerau-Levenshtein (OSA)
distance with an early-exit band - transpositions count as one edit, so
"jonh" still finds "John".
"""
from __future__ import annotations

import time
from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.algorithms.dp import osa_distance
from app.algorithms.strings import SEARCH_ALGORITHMS, find_all, suffix_array, suffix_array_search
from app.models.laboratory import Laboratory
from app.models.student import Student


@dataclass
class _Field:
    start: int
    entity_type: str
    entity_id: int
    field: str
    value: str


_SA_CACHE: dict[str, list[int]] = {}


def _cached_suffix_array(corpus: str) -> tuple[list[int], bool]:
    sa = _SA_CACHE.get(corpus)
    if sa is not None:
        return sa, True
    sa = suffix_array(corpus)
    _SA_CACHE.clear()  # keep only the current corpus
    _SA_CACHE[corpus] = sa
    return sa, False


def _build_corpus(db: Session) -> tuple[str, list[_Field], dict[tuple[str, int], dict]]:
    fields: list[_Field] = []
    entities: dict[tuple[str, int], dict] = {}
    parts: list[str] = []
    offset = 0

    def add(entity_type: str, entity_id: int, field: str, value: str) -> None:
        nonlocal offset
        lowered = value.lower()
        fields.append(_Field(offset, entity_type, entity_id, field, value))
        parts.append(lowered)
        offset += len(lowered) + 1  # newline separator never occurs inside a field

    for s in db.query(Student).order_by(Student.id).all():
        entities[("student", s.id)] = {"type": "student", "id": s.id, "title": s.full_name, "subtitle": f"{s.roll_number} · {s.department} · year {s.year}"}
        add("student", s.id, "name", s.full_name)
        add("student", s.id, "roll_number", s.roll_number)
        add("student", s.id, "email", s.email)
    for lab in db.query(Laboratory).order_by(Laboratory.id).all():
        entities[("lab", lab.id)] = {"type": "lab", "id": lab.id, "title": lab.name, "subtitle": f"{lab.code} · {lab.department} · capacity {lab.capacity}"}
        add("lab", lab.id, "name", lab.name)
        add("lab", lab.id, "code", lab.code)
        add("lab", lab.id, "department", lab.department)
    return "\n".join(parts), fields, entities


def _field_at(fields: list[_Field], position: int) -> _Field:
    lo, hi = 0, len(fields) - 1
    while lo < hi:  # last field whose start <= position
        mid = (lo + hi + 1) // 2
        if fields[mid].start <= position:
            lo = mid
        else:
            hi = mid - 1
    return fields[lo]


def entity_search(db: Session, query: str, algorithm: str = "KMP", fuzzy: bool = True, limit: int = 20) -> dict:
    if algorithm not in SEARCH_ALGORITHMS:
        raise ValueError(f"Unknown search algorithm: {algorithm}")
    pattern = query.strip().lower()
    corpus, fields, entities = _build_corpus(db)

    start = time.perf_counter()
    cache_hit = None
    if algorithm == "SUFFIX_ARRAY":
        sa, cache_hit = _cached_suffix_array(corpus)
        result = suffix_array_search(corpus, pattern, sa)
    else:
        result = find_all(corpus, pattern, algorithm)
    search_ms = (time.perf_counter() - start) * 1000

    hits: dict[tuple[str, int], dict] = {}
    for pos in result.positions:
        f = _field_at(fields, pos)
        key = (f.entity_type, f.entity_id)
        hit = hits.setdefault(key, {**entities[key], "match": "exact", "fields": {}})
        hit["fields"].setdefault(f.field, {"value": f.value, "spans": []})["spans"].append([pos - f.start, pos - f.start + len(pattern)])

    fuzzy_hits: list[dict] = []
    if fuzzy and len(pattern) >= 3 and len(hits) < limit:
        budget = 1 if len(pattern) <= 5 else 2
        for f in fields:
            key = (f.entity_type, f.entity_id)
            if key in hits or f.field not in ("name", "code"):
                continue
            tokens = [t for t in f.value.lower().replace("-", " ").split() if t]
            best = min((osa_distance(pattern, t, budget) for t in tokens), default=budget + 1)
            whole = osa_distance(pattern, f.value.lower(), budget)
            best = min(best, whole)
            if best <= budget:
                previous = next((h for h in fuzzy_hits if (h["type"], h["id"]) == key), None)
                if previous is None:
                    fuzzy_hits.append({**entities[key], "match": "fuzzy", "distance": best, "fields": {f.field: {"value": f.value, "spans": []}}})
                elif best < previous["distance"]:
                    previous["distance"] = best
        fuzzy_hits.sort(key=lambda h: h["distance"])

    ordered = sorted(hits.values(), key=lambda h: (h["type"] != "lab", h["title"]))
    results = (ordered + fuzzy_hits)[:limit]
    return {
        "query": query,
        "algorithm": algorithm,
        "corpus_length": len(corpus),
        "fields_indexed": len(fields),
        "occurrences": len(result.positions),
        "comparisons": result.comparisons,
        "search_time_ms": search_ms,
        "suffix_array_cached": cache_hit,
        "exact_matches": len(hits),
        "fuzzy_matches": len(fuzzy_hits),
        "results": results,
    }
