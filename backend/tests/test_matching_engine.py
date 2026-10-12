import pytest

from app.algorithms.matching_engine import (
    EngineConstraints,
    LabInput,
    LabRequiredSkill,
    StudentInput,
    run_allocation,
)

ALGORITHMS = ["KUHN", "HOPCROFT_KARP", "EDMONDS_KARP", "DINIC"]


def make_student(id, department="CSE", year=2, cgpa=8.0, priority=0.5, skills=None, preferences=None):
    return StudentInput(
        id=id,
        department=department,
        year=year,
        cgpa=cgpa,
        priority_score=priority,
        skills=skills or {},
        preferences=preferences or {},
    )


def make_lab(id, department="CSE", capacity=1, active=True, required_skills=None, has_slot=True):
    return LabInput(
        id=id,
        department=department,
        capacity=capacity,
        is_active=active,
        required_skills=required_skills or [],
        has_available_slot=has_slot,
    )


@pytest.mark.parametrize("algorithm", ALGORITHMS)
def test_zero_students(algorithm):
    result = run_allocation([], [make_lab(1)], EngineConstraints(), algorithm)
    assert result.matched_count == 0
    assert result.total_students == 0


@pytest.mark.parametrize("algorithm", ALGORITHMS)
def test_zero_labs(algorithm):
    result = run_allocation([make_student(1)], [], EngineConstraints(), algorithm)
    assert result.matched_count == 0
    assert result.unmatched_count == 1
    assert result.assignments[0].status == "UNMATCHED"


@pytest.mark.parametrize("algorithm", ALGORITHMS)
def test_no_possible_matches_due_to_department_rule(algorithm):
    students = [make_student(1, department="ECE")]
    labs = [make_lab(1, department="CSE")]
    constraints = EngineConstraints(same_department_only=True)
    result = run_allocation(students, labs, constraints, algorithm)
    assert result.matched_count == 0
    assert "no eligible laboratory" in result.assignments[0].eligibility_reason


@pytest.mark.parametrize("algorithm", ALGORITHMS)
def test_all_students_choose_same_lab(algorithm):
    students = [make_student(i, preferences={100: 1}) for i in range(1, 6)]
    labs = [make_lab(100, capacity=2)]
    result = run_allocation(students, labs, EngineConstraints(), algorithm)
    assert result.matched_count == 2
    assert result.unmatched_count == 3


@pytest.mark.parametrize("algorithm", ALGORITHMS)
def test_lab_capacity_zero(algorithm):
    students = [make_student(1, preferences={5: 1})]
    labs = [make_lab(5, capacity=0)]
    result = run_allocation(students, labs, EngineConstraints(), algorithm)
    assert result.matched_count == 0


@pytest.mark.parametrize("algorithm", ALGORITHMS)
def test_more_students_than_total_capacity(algorithm):
    students = [make_student(i, preferences={1: 1}) for i in range(1, 11)]
    labs = [make_lab(1, capacity=4)]
    result = run_allocation(students, labs, EngineConstraints(), algorithm)
    assert result.matched_count == 4
    assert result.unmatched_count == 6


@pytest.mark.parametrize("algorithm", ALGORITHMS)
def test_more_capacity_than_students(algorithm):
    students = [make_student(i, preferences={1: 1}) for i in range(1, 4)]
    labs = [make_lab(1, capacity=10)]
    result = run_allocation(students, labs, EngineConstraints(), algorithm)
    assert result.matched_count == 3
    assert result.capacity_utilization == pytest.approx(3 / 10)


@pytest.mark.parametrize("algorithm", ALGORITHMS)
def test_lab_inactive_excluded(algorithm):
    students = [make_student(1, preferences={1: 1})]
    labs = [make_lab(1, capacity=5, active=False)]
    result = run_allocation(students, labs, EngineConstraints(), algorithm)
    assert result.matched_count == 0


@pytest.mark.parametrize("algorithm", ALGORITHMS)
def test_missing_required_skill_excludes_edge(algorithm):
    students = [make_student(1, skills={"Python": 2})]
    labs = [make_lab(1, capacity=1, required_skills=[LabRequiredSkill("Machine Learning", 3, True)])]
    result = run_allocation(students, labs, EngineConstraints(), algorithm)
    assert result.matched_count == 0
    assert "missing required skill" in result.assignments[0].eligibility_reason


@pytest.mark.parametrize("algorithm", ALGORITHMS)
def test_sufficient_skill_allows_match(algorithm):
    students = [make_student(1, skills={"Machine Learning": 4})]
    labs = [make_lab(1, capacity=1, required_skills=[LabRequiredSkill("Machine Learning", 3, True)])]
    result = run_allocation(students, labs, EngineConstraints(), algorithm)
    assert result.matched_count == 1


@pytest.mark.parametrize("algorithm", ALGORITHMS)
def test_disconnected_graph_partial_matching(algorithm):
    students = [make_student(1, preferences={1: 1}), make_student(2, preferences={2: 1})]
    labs = [make_lab(1, capacity=1), make_lab(2, capacity=1), make_lab(3, capacity=1)]
    # student 1 only connects to lab 1, student 2 only connects to lab 2; lab 3 isolated
    result = run_allocation(students, labs, EngineConstraints(require_preference=True), algorithm)
    assert result.matched_count == 2


@pytest.mark.parametrize("algorithm", ALGORITHMS)
def test_preference_satisfaction_is_full_when_everyone_gets_first_choice(algorithm):
    students = [make_student(i, preferences={i: 1}) for i in range(1, 4)]
    labs = [make_lab(i, capacity=1) for i in range(1, 4)]
    result = run_allocation(students, labs, EngineConstraints(require_preference=True), algorithm)
    assert result.matched_count == 3
    assert result.preference_satisfaction == 1.0


def test_duplicate_preference_ranks_do_not_crash_engine():
    # engine itself is tolerant even though the DB layer enforces uniqueness;
    # duplicate ranks should just be treated as whatever dict semantics give.
    student = make_student(1, preferences={1: 1, 2: 1})
    labs = [make_lab(1, capacity=1), make_lab(2, capacity=1)]
    result = run_allocation([student], labs, EngineConstraints(), "HOPCROFT_KARP")
    assert result.matched_count == 1
