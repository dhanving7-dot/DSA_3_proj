from tests.conftest import register_and_login


def setup_students_and_labs(client, headers):
    lab_ids = []
    for i in range(2):
        resp = client.post(
            "/api/v1/labs",
            json={"code": f"L{i}", "name": f"Lab {i}", "department": "CSE", "capacity": 2},
            headers=headers,
        )
        lab_ids.append(resp.json()["id"])

    student_ids = []
    for i in range(5):
        resp = client.post(
            "/api/v1/students",
            json={
                "roll_number": f"S{i}",
                "full_name": f"Student {i}",
                "email": f"s{i}@example.com",
                "department": "CSE",
                "year": 2,
                "cgpa": 8.0,
            },
            headers=headers,
        )
        student_id = resp.json()["id"]
        student_ids.append(student_id)
        client.put(
            f"/api/v1/students/{student_id}/preferences",
            json=[{"lab_id": lab_ids[0], "rank": 1}, {"lab_id": lab_ids[1], "rank": 2}],
            headers=headers,
        )
    return student_ids, lab_ids


def test_generate_allocation_end_to_end(client):
    headers = register_and_login(client)
    student_ids, lab_ids = setup_students_and_labs(client, headers)

    resp = client.post(
        "/api/v1/allocation/generate",
        json={"algorithm": "HOPCROFT_KARP", "config": {}},
        headers=headers,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["matched_count"] == 4  # 2 labs * capacity 2
    assert body["unmatched_count"] == 1
    assert len(body["allocations"]) == 5
    assert body["metrics"]["time_complexity"] == "O(E * sqrt(V))"

    run_id = body["id"]
    resp = client.get(f"/api/v1/allocation/runs/{run_id}", headers=headers)
    assert resp.status_code == 200

    resp = client.get("/api/v1/allocation/runs", headers=headers)
    assert resp.status_code == 200
    assert len(resp.json()) >= 1


def test_analytics_overview_reflects_run(client):
    headers = register_and_login(client)
    setup_students_and_labs(client, headers)
    client.post("/api/v1/allocation/generate", json={"algorithm": "KUHN", "config": {}}, headers=headers)

    resp = client.get("/api/v1/analytics/overview", headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["overview"]["total_students"] == 5
    assert body["overview"]["matched_students"] == 4
    assert len(body["lab_utilization"]) == 2


def test_matching_playground_run(client):
    headers = register_and_login(client)
    resp = client.post(
        "/api/v1/matching/run",
        json={"algorithm": "KUHN", "num_left": 6, "num_right": 4, "edge_probability": 0.5, "seed": 1},
        headers=headers,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["result"]["algorithm"] == "KUHN"
    assert "steps" in body["result"]
    assert body["result"]["steps"][0]["event"] == "GRAPH_CREATED"


def test_matching_compare_runs_all_four_algorithms(client):
    headers = register_and_login(client)
    setup_students_and_labs(client, headers)
    resp = client.post(
        "/api/v1/matching/compare",
        json={"config": {}, "algorithms": ["KUHN", "HOPCROFT_KARP", "EDMONDS_KARP", "DINIC"]},
        headers=headers,
    )
    assert resp.status_code == 200
    comparisons = resp.json()["comparisons"]
    assert len(comparisons) == 4
    match_sizes = {c["matched_count"] for c in comparisons}
    assert match_sizes == {4}  # all four algorithms must agree on max matching size


def test_simulate_allocation_before_after(client):
    headers = register_and_login(client)
    student_ids, lab_ids = setup_students_and_labs(client, headers)

    resp = client.post(
        "/api/v1/allocation/simulate",
        json={
            "algorithm": "HOPCROFT_KARP",
            "baseline_config": {},
            "modified_config": {},
            "lab_capacity_overrides": {str(lab_ids[0]): 5},
        },
        headers=headers,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["before"]["matched_count"] == 4
    assert body["after"]["matched_count"] == 5  # capacity bump lets everyone in
    assert body["delta"]["matched_count"] == 1


def test_ai_command_parses_without_executing(client):
    headers = register_and_login(client)
    setup_students_and_labs(client, headers)

    resp = client.post(
        "/api/v1/ai/command",
        json={"text": "Allocate second year CSE students prioritizing their first preference", "auto_execute": False},
        headers=headers,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["executed"] is False
    assert body["parsed"]["department_filter"] == "CSE"
    assert body["parsed"]["year_filter"] == 2
    assert body["matched_student_count"] == 5


def test_ai_command_recognizes_lab_acronyms_from_code(client):
    headers = register_and_login(client)
    setup_students_and_labs(client, headers)
    client.post(
        "/api/v1/labs",
        json={"code": "AI-LAB-01", "name": "Artificial Intelligence Laboratory", "department": "AIML", "capacity": 10},
        headers=headers,
    )
    client.post(
        "/api/v1/labs",
        json={"code": "DBMS-LAB-01", "name": "Database Management Systems Laboratory", "department": "CSE", "capacity": 10},
        headers=headers,
    )

    resp = client.post(
        "/api/v1/ai/command",
        json={
            "text": "Allocate second year CSE students to AI and DBMS labs while prioritizing their first preference.",
            "auto_execute": False,
        },
        headers=headers,
    )
    assert resp.status_code == 200
    filters = resp.json()["parsed"]["lab_name_filters"]
    assert "Artificial Intelligence Laboratory" in filters
    assert "Database Management Systems Laboratory" in filters


def test_ai_command_auto_execute_runs_real_engine(client):
    headers = register_and_login(client)
    setup_students_and_labs(client, headers)

    resp = client.post(
        "/api/v1/ai/command",
        json={"text": "Allocate CSE students", "auto_execute": True},
        headers=headers,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["executed"] is True
    assert body["run_id"] is not None


def test_ai_explain_uses_real_allocation_facts(client):
    headers = register_and_login(client)
    student_ids, lab_ids = setup_students_and_labs(client, headers)
    run = client.post("/api/v1/allocation/generate", json={"algorithm": "KUHN", "config": {}}, headers=headers).json()

    resp = client.post(
        "/api/v1/ai/explain",
        json={"student_id": student_ids[0], "run_id": run["id"]},
        headers=headers,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["student_id"] == student_ids[0]
    assert "facts" in body and body["facts"]["run_id"] == run["id"]


def test_ai_analytics_query_why_unmatched(client):
    headers = register_and_login(client)
    setup_students_and_labs(client, headers)
    client.post("/api/v1/allocation/generate", json={"algorithm": "KUHN", "config": {}}, headers=headers)

    resp = client.post(
        "/api/v1/ai/analytics-query",
        json={"question": "Why are students unmatched?"},
        headers=headers,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert "1" in body["answer"] or "unmatched" in body["answer"].lower()
    assert body["facts"]["unmatched_count"] == 1


def test_ai_conflicts_and_report(client):
    headers = register_and_login(client)
    setup_students_and_labs(client, headers)
    client.post("/api/v1/allocation/generate", json={"algorithm": "KUHN", "config": {}}, headers=headers)

    resp = client.get("/api/v1/ai/conflicts", headers=headers)
    assert resp.status_code == 200

    resp = client.get("/api/v1/ai/report", headers=headers)
    assert resp.status_code == 200
    assert "Allocation Report" in resp.json()["report_markdown"]
