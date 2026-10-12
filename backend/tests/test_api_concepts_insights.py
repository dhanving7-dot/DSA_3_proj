import pytest

from tests.conftest import register_and_login
from tests.test_api_allocation import setup_students_and_labs


def test_concept_endpoints_require_auth(client):
    assert client.get("/api/v1/concepts/atlas").status_code == 401
    assert client.get("/api/v1/insights/bottleneck").status_code == 401
    assert client.get("/api/v1/search", params={"q": "lab"}).status_code == 401


def test_atlas_lists_every_module_and_links_demos(client):
    headers = register_and_login(client)
    body = client.get("/api/v1/concepts/atlas", headers=headers).json()
    assert {m["id"] for m in body["modules"]} == {1, 2, 3, 4, 5, 6}
    ids = [a["id"] for a in body["algorithms"]]
    assert len(ids) == len(set(ids))
    for required in ["KMP", "AHO_CORASICK", "SUFFIX_ARRAY", "DAMERAU", "HELD_KARP", "SOS_DP", "MIN_COST_FLOW", "MIN_CUT", "GREEDY_SET_COVER", "MILLER_RABIN", "RESERVOIR", "BLELLOCH_SCAN"]:
        assert required in ids
    assert body["reductions"]


CONCEPT_CALLS = [
    ("/strings/search", {"text": "abracadabra", "pattern": "abra", "seed": 1}),
    ("/strings/aho-corasick", {"text": "ushers", "patterns": ["he", "she", "his", "hers"]}),
    ("/strings/suffix-array", {"text": "banana"}),
    ("/dp/edit-distance", {"a": "kitten", "b": "sitting", "variant": "DAMERAU"}),
    ("/dp/alignment", {"a": "GATTACA", "b": "GCATGCU", "mode": "LOCAL"}),
    ("/dp/matrix-chain", {"dims": [30, 35, 15, 5, 10, 20, 25]}),
    ("/dp/obst", {"keys": ["c", "a", "b"], "freqs": [5, 30, 10]}),
    ("/dp/tsp", {"num_cities": 7, "seed": 2}),
    ("/dp/hamiltonian", {"num_vertices": 7, "edge_probability": 0.5, "seed": 2}),
    ("/dp/tree", {"num_nodes": 15, "seed": 2}),
    ("/flow/min-cut", {"num_left": 6, "num_right": 5, "edge_probability": 0.4, "seed": 3}),
    ("/flow/min-cost", {"num_left": 6, "num_right": 5, "edge_probability": 0.6, "seed": 3}),
    ("/flow/project-selection", {"profits": [10, 8, 5], "costs": [6, 4, 7], "requires": [[0, 0], [0, 1], [1, 1], [2, 2]]}),
    ("/np/vertex-cover", {"num_vertices": 10, "edge_probability": 0.3, "seed": 4}),
    ("/np/set-cover", {"universe_size": 15, "num_sets": 8, "seed": 4}),
    ("/np/knapsack", {"weights": [10, 20, 30], "values": [60, 100, 120], "capacity": 50, "epsilon": 0.2}),
    ("/random/primality", {"n": "561", "rounds": 5, "seed": 1}),
    ("/random/quicksort", {"n": 300, "input_kind": "sorted", "seed": 1, "trials": 3}),
    ("/random/reservoir", {"stream_size": 50, "k": 5, "trials": 500, "seed": 1}),
    ("/random/hashing", {"num_keys": 300, "table_size": 31, "seed": 1}),
    ("/parallel/scan", {"values": [3, 1, 7, 0, 4, 1, 6, 3], "processors": 4}),
]


@pytest.mark.parametrize("path,payload", CONCEPT_CALLS)
def test_concept_demo_endpoints(client, path, payload):
    headers = register_and_login(client)
    resp = client.post(f"/api/v1/concepts{path}", json=payload, headers=headers)
    assert resp.status_code == 200, resp.text


def test_concept_results_are_self_verifying(client):
    headers = register_and_login(client)
    post = lambda path, body: client.post(f"/api/v1/concepts{path}", json=body, headers=headers).json()  # noqa: E731

    search = post("/strings/search", {"text": "abracadabra", "pattern": "abra"})
    assert search["all_agree"] and search["positions"] == [0, 7]

    assert post("/dp/matrix-chain", {"dims": [30, 35, 15, 5, 10, 20, 25]})["min_cost"] == 15125
    obst = post("/dp/obst", {"keys": ["c", "a", "b"], "freqs": [5, 30, 10]})
    assert obst["keys"] == ["a", "b", "c"] and obst["costs_agree"]
    assert post("/dp/tree", {"num_nodes": 30, "seed": 9})["rerooting_matches_bfs"]

    tsp = post("/dp/tsp", {"num_cities": 8, "seed": 3})
    assert tsp["held_karp"]["cost"] <= tsp["mst_2approx"]["cost"] <= 2 * tsp["held_karp"]["cost"] + 0.01

    cut = post("/flow/min-cut", {"num_left": 7, "num_right": 6, "edge_probability": 0.35, "seed": 5})
    assert cut["max_flow"] == cut["cut_capacity"] == cut["konig_cover"]["size"]
    assert post("/flow/min-cost", {"num_left": 7, "num_right": 6, "edge_probability": 0.5, "seed": 5})["optimal_verified"]
    assert post("/flow/project-selection", {"profits": [10, 8, 5], "costs": [6, 4, 7], "requires": [[0, 0], [0, 1], [1, 1], [2, 2]]})["verified"]

    prime = post("/random/primality", {"n": "561"})
    assert prime["carmichael"] is True and prime["fermat"]["probably_prime"] is True
    assert prime["miller_rabin"]["probably_prime"] is False and prime["deterministic"] is False
    big = post("/random/primality", {"n": str(2**89 - 1)})
    assert big["miller_rabin"]["probably_prime"] is True and big["n"] == str(2**89 - 1)

    qs = post("/random/quicksort", {"n": 400, "input_kind": "sorted", "trials": 3})
    assert qs["sorted_correctly"] and qs["deterministic"]["comparisons"] == qs["worst_case"]
    assert qs["randomized"]["mean_comparisons"] < qs["worst_case"] / 5

    scan = post("/parallel/scan", {"values": [3, 1, 7, 0, 4, 1, 6, 3]})
    assert scan["scan_correct"] and scan["scan"]["result"] == [0, 3, 4, 11, 11, 15, 16, 22]


def test_concept_validation_errors(client):
    headers = register_and_login(client)
    assert client.post("/api/v1/concepts/random/primality", json={"n": "12a"}, headers=headers).status_code == 422
    assert client.post("/api/v1/concepts/dp/tsp", json={"num_cities": 30}, headers=headers).status_code == 422
    assert client.post("/api/v1/concepts/dp/obst", json={"keys": ["a", "a"], "freqs": [1, 2]}, headers=headers).status_code == 422
    assert client.post("/api/v1/concepts/random/reservoir", json={"stream_size": 1000, "trials": 5000}, headers=headers).status_code == 422
    resp = client.post("/api/v1/concepts/flow/project-selection", json={"profits": [1], "costs": [1], "requires": [[0, 5]]}, headers=headers)
    assert resp.status_code == 422


def test_obst_from_real_preference_counts(client):
    headers = register_and_login(client)
    setup_students_and_labs(client, headers)
    body = client.post("/api/v1/concepts/dp/obst", json={"from_lab_data": True}, headers=headers).json()
    assert body["keys"] == ["L0", "L1"] and body["freqs"] == [5, 5]


# --------------------------------------------------------------------------- allocation integration


@pytest.mark.parametrize("algorithm", ["FORD_FULKERSON", "MIN_COST_FLOW"])
def test_generate_allocation_with_new_algorithms(client, algorithm):
    headers = register_and_login(client)
    setup_students_and_labs(client, headers)
    resp = client.post("/api/v1/allocation/generate", json={"algorithm": algorithm, "config": {}}, headers=headers)
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["algorithm"] == algorithm and body["matched_count"] == 4 and body["metrics"]["algorithm"] == algorithm


def test_fairness_with_plain_matching_is_a_400_not_a_silent_no_op(client):
    headers = register_and_login(client)
    setup_students_and_labs(client, headers)
    resp = client.post(
        "/api/v1/allocation/generate",
        json={"algorithm": "HOPCROFT_KARP", "config": {"max_share_per_department": 0.5}},
        headers=headers,
    )
    assert resp.status_code == 400 and "laminar" in resp.json()["detail"]
    ok = client.post(
        "/api/v1/allocation/generate", json={"algorithm": "DINIC", "config": {"max_share_per_department": 0.5}}, headers=headers
    )
    assert ok.status_code == 200 and ok.json()["matched_count"] == 2  # one CSE seat per lab of capacity 2


def test_compare_defaults_to_all_six_and_skips_unsupported(client):
    headers = register_and_login(client)
    setup_students_and_labs(client, headers)
    rows = client.post("/api/v1/matching/compare", json={"config": {}}, headers=headers).json()["comparisons"]
    assert [r["algorithm"] for r in rows] == ["KUHN", "HOPCROFT_KARP", "EDMONDS_KARP", "DINIC", "FORD_FULKERSON", "MIN_COST_FLOW"]
    assert len({r["matched_count"] for r in rows}) == 1
    fair = client.post("/api/v1/matching/compare", json={"config": {"max_share_per_department": 0.5}}, headers=headers).json()["comparisons"]
    skipped = [r["algorithm"] for r in fair if "skipped_reason" in r]
    assert skipped == ["KUHN", "HOPCROFT_KARP"]


@pytest.mark.parametrize("algorithm", ["FORD_FULKERSON", "MIN_COST_FLOW", "DINIC"])
def test_playground_reports_matched_pairs_for_flow_algorithms(client, algorithm):
    headers = register_and_login(client)
    body = client.post(
        "/api/v1/matching/run",
        json={"algorithm": algorithm, "num_left": 8, "num_right": 6, "edge_probability": 0.4, "seed": 3},
        headers=headers,
    ).json()
    result = body["result"]
    assert len(result["matched_pairs"]) == result["match_size"] if "match_size" in result else True
    kuhn = client.post(
        "/api/v1/matching/run",
        json={"algorithm": "KUHN", "num_left": 8, "num_right": 6, "edge_probability": 0.4, "seed": 3},
        headers=headers,
    ).json()["result"]
    assert len(result["matched_pairs"]) == kuhn["match_size"]
    edges = {tuple(e) for e in body["input_edges"]}
    assert all(tuple(p) in edges for p in result["matched_pairs"])
    if algorithm == "MIN_COST_FLOW":
        assert len(body["edge_costs"]) == len(body["input_edges"]) and body["total_cost"] is not None


def test_ai_command_typo_and_fairness_switch(client):
    headers = register_and_login(client)
    setup_students_and_labs(client, headers)
    resp = client.post(
        "/api/v1/ai/command", json={"text": "Allocate students fairly using hopcroft", "auto_execute": True}, headers=headers
    ).json()
    assert resp["parsed"]["algorithm"] == "DINIC" and resp["executed"] is True
    assert any("laminar" in n for n in resp["parsed"]["notes"])
    typo = client.post("/api/v1/ai/command", json={"text": "run dinik on electronic students"}, headers=headers).json()
    assert typo["parsed"]["algorithm"] == "DINIC" and typo["parsed"]["department_filter"] == "ECE"
    assert sum("Typo-corrected" in n for n in typo["parsed"]["notes"]) == 2


# --------------------------------------------------------------------------- insights


def test_insights_on_real_data(client):
    headers = register_and_login(client)
    setup_students_and_labs(client, headers)  # 5 students all eligible for 2 labs of capacity 2
    get = lambda path, **params: client.get(f"/api/v1/insights{path}", params=params, headers=headers).json()  # noqa: E731

    bottleneck = get("/bottleneck")
    assert bottleneck["max_flow"] == 4 and bottleneck["unmatched"] == 1
    assert bottleneck["max_flow_equals_min_cut"] is True
    assert bottleneck["hall"]["violator_size"] == 5 and bottleneck["hall"]["reachable_capacity"] == 4
    assert bottleneck["hall"]["deficiency"] == 1
    assert bottleneck["konig"]["min_vertex_cover"] == bottleneck["konig"]["max_matching"] == 4
    assert {b["lab_name"] for b in bottleneck["bottleneck_labs"]} == {"Lab 0", "Lab 1"}

    cover = get("/set-cover")
    assert cover["placeable_students"] == 5 and cover["exact"]["size"] == 1 and cover["greedy"]["size"] == 1

    skills = get("/skill-supply")
    assert skills["students"] == 5

    gap = get("/optimality-gap")
    assert gap["same_cardinality"] and gap["skipped"] == []
    assert [r["algorithm"] for r in gap["algorithms"]][-1] == "MIN_COST_FLOW" and len(gap["algorithms"]) == 6
    assert all(r["gap_to_optimal"] >= 0 for r in gap["algorithms"])

    mc = client.post("/api/v1/insights/monte-carlo", json={"trials": 30, "outage_probability": 0.5, "seed": 1}, headers=headers).json()
    assert mc["baseline_matched"] == 4 and 0 <= mc["mean_matched"] <= 4
    assert mc["ci95"][0] <= mc["mean_matched"] <= mc["ci95"][1]
    assert sum(h["trials"] for h in mc["histogram"]) == 30


def test_audit_sample_uses_reservoir_over_latest_run(client):
    headers = register_and_login(client)
    setup_students_and_labs(client, headers)
    empty = client.get("/api/v1/insights/audit-sample", headers=headers).json()
    assert empty["sample"] == []
    client.post("/api/v1/allocation/generate", json={"algorithm": "KUHN", "config": {}}, headers=headers)
    body = client.get("/api/v1/insights/audit-sample", params={"k": 3, "seed": 1}, headers=headers).json()
    assert body["items_seen"] == 5 and len(body["sample"]) == 3 and body["inclusion_probability"] == 0.6


def test_entity_search_all_algorithms_and_fuzzy(client):
    headers = register_and_login(client)
    setup_students_and_labs(client, headers)
    for algorithm in ["NAIVE", "KMP", "Z_FUNCTION", "RABIN_KARP", "SUFFIX_ARRAY"]:
        body = client.get("/api/v1/search", params={"q": "Student 3", "algorithm": algorithm}, headers=headers).json()
        assert [r["title"] for r in body["results"] if r["match"] == "exact"] == ["Student 3"], algorithm
        assert body["results"][0]["fields"]["name"]["spans"] == [[0, 9]]
    fuzzy = client.get("/api/v1/search", params={"q": "studnet"}, headers=headers).json()
    assert fuzzy["exact_matches"] == 0 and fuzzy["fuzzy_matches"] == 5
    assert all(r["distance"] == 1 for r in fuzzy["results"])  # one transposition under Damerau-Levenshtein
    labs = client.get("/api/v1/search", params={"q": "lab", "fuzzy": False}, headers=headers).json()
    assert {r["title"] for r in labs["results"]} == {"Lab 0", "Lab 1"}
    cached = client.get("/api/v1/search", params={"q": "s1", "algorithm": "SUFFIX_ARRAY"}, headers=headers).json()
    assert cached["suffix_array_cached"] is True
