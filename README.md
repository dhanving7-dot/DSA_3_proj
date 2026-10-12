# AllocateX — Automated Student-to-Laboratory Allocation Using Maximum Bipartite Matching

A full-stack academic systems project that solves real laboratory-allocation
constraints (eligibility, preferences, skills, capacity, scheduling,
fairness) using **hand-implemented graph algorithms** — Kuhn's algorithm,
Hopcroft-Karp, Edmonds-Karp and Dinic's algorithm — wrapped in a production-style
FastAPI + PostgreSQL backend and a React + TypeScript frontend. An AI layer
parses natural language into structured constraints and explains real
results; it never fabricates or replaces the algorithmic decision.

---

## Table of Contents

1. [Problem Statement](#1-problem-statement)
2. [Objectives](#2-objectives)
3. [System Architecture](#3-system-architecture)
4. [Database Architecture](#4-database-architecture)
5. [Algorithm Explanation & Mathematical Formulation](#5-algorithm-explanation--mathematical-formulation)
6. [Time & Space Complexity](#6-time--space-complexity)
7. [API Documentation](#7-api-documentation)
8. [Setup Instructions](#8-setup-instructions)
9. [Seed Data](#9-seed-data)
10. [Testing](#10-testing)
11. [Screenshots](#11-screenshots)
12. [Security](#12-security)
13. [AI Layer — Design Contract](#13-ai-layer--design-contract)
14. [Future Enhancements](#14-future-enhancements)

---

## 1. Problem Statement

A college must assign `N` students to `M` laboratories every semester.
Every assignment is constrained by:

- **Eligibility** — department rules, prerequisite skills, lab status.
- **Preferences** — each student ranks the labs they want.
- **Capacity** — every lab can only hold a fixed number of students.
- **Skills / equipment / subject requirements** — a lab may require a
  minimum proficiency in one or more skills.
- **Scheduling / availability** — a lab may be under maintenance or have no
  open time slots.
- **Fairness & priority** — no single department should be able to crowd
  out every seat in a lab; some students carry priority weight (CGPA-linked
  or administrative).

This is the textbook **assignment problem on a bipartite graph**, and its
optimal (maximum-cardinality) solution is exactly **Maximum Bipartite
Matching** — equivalently, **Maximum Flow** on a source→student→lab→sink
network where lab capacity becomes edge capacity.

## 2. Objectives

- Implement Kuhn's, Hopcroft-Karp, Edmonds-Karp and Dinic's algorithms
  **from scratch** (no `networkx`, no third-party graph/matching library).
- Build a real, persisted allocation pipeline: constraints → eligible-edge
  graph → algorithm → explainable assignments → analytics.
- Make every algorithm's execution observable: vertex/edge counts,
  iteration counts, measured execution time, and a full step-by-step trace
  streamed live over WebSockets.
- Add an AI layer that **enhances** the deterministic engine (natural
  language → structured constraints, explanations from real stored facts,
  conflict detection, report generation) without ever fabricating a result.
- Package it as a real, running full-stack application with authentication,
  role-based access, a relational schema, and test coverage — not a static
  mockup.

## 3. System Architecture

```
┌─────────────────────────────┐        ┌──────────────────────────────────┐
│           Frontend           │        │              Backend              │
│  React 19 + TypeScript + Vite│        │      FastAPI + SQLAlchemy 2.0      │
│  Tailwind v4 · shadcn-style  │  REST  │                                    │
│  primitives · Framer Motion  │◄──────►│  app/api/v1/*  (routers)           │
│  React Flow · Recharts       │  JSON  │  app/services/*  (business logic)  │
│  TanStack Query · Zustand    │        │  app/algorithms/*  (Kuhn, HK, EK,   │
│                              │  WS    │             Dinic, matching engine)│
│  useAlgorithmSocket ─────────┼───────►│  app/ws/manager.py  (pub/sub)      │
└─────────────────────────────┘        └───────────────┬────────────────────┘
                                                         │ SQLAlchemy ORM
                                                         ▼
                                            ┌─────────────────────────┐
                                            │       PostgreSQL         │
                                            │ (SQLite fallback for     │
                                            │  local dev / tests)      │
                                            └─────────────────────────┘
```

**Backend layering** (`backend/app/`):

| Layer | Responsibility |
|---|---|
| `algorithms/` | Pure-Python, dependency-free graph algorithms. Testable with zero database. |
| `services/` | Bridges ORM rows ⇄ algorithm inputs; owns AI parsing, analytics aggregation, simulation. |
| `api/v1/` | Thin FastAPI routers: validate, call a service, return a schema. No business logic here. |
| `models/` | SQLAlchemy 2.0 declarative models (the relational schema). |
| `schemas/` | Pydantic request/response contracts. |
| `ws/` | WebSocket connection manager + step-replay broadcaster. |

This separation is what makes the algorithms unit-testable in isolation
(see [`tests/test_kuhn.py`](backend/tests/test_kuhn.py) etc., which import
nothing from the database layer at all).

## 4. Database Architecture

```
users ──1:1── students ──1:N── student_skills
  │                │
  │                └──1:N── student_preferences ──N:1── laboratories
  │
  └──1:N── allocation_runs ──1:N── allocations ──N:1── students
                  │                     │
                  │                     └──N:1── laboratories
                  └──1:1── algorithm_metrics

laboratories ──1:N── lab_skills
             ──1:N── lab_equipment
             ──1:N── lab_time_slots

constraints        (standalone configurable rule rows)
audit_logs          (user_id nullable FK, action, entity, details JSON)
```

Key design choices:

- **`allocation_runs` + `allocations` + `algorithm_metrics`** together give
  full historical auditability: every run remembers its algorithm, its
  config snapshot, its aggregate stats, *and* the per-student reasoning
  (`eligibility_reason`, `preference_rank`, `match_score`) for every
  assignment — matched or not.
- **Lab capacity is a first-class column**, consumed two different ways by
  the matching engine: as `capacity`-many expanded "slot" vertices for
  Kuhn/Hopcroft-Karp, and as direct edge capacity for the flow algorithms.
- Foreign keys use `ON DELETE CASCADE` (child rows) or `SET NULL` (audit
  trail / optional links) as appropriate; unique constraints prevent
  duplicate preference ranks or duplicate lab preferences per student.
- Timestamps (`created_at` / `updated_at`) are server-side defaults.

## 5. Algorithm Explanation & Mathematical Formulation

Let `S` = students (left vertices), `L` = labs (right vertices). An edge
`(s, l)` exists iff `s` is *eligible* for `l` under the active constraints
(department rule, skill fit, lab active + available). Each edge carries a
`match_score ∈ [0,1]`:

```
match_score(s,l) = w_pref · pref(s,l) + w_skill · skill(s,l) + w_priority · priority(s)
```

where `pref(s,l) = 1 - (rank-1)/max_rank` (or a configurable baseline if
unranked), `skill(s,l)` is the fraction of required skills satisfied at
sufficient proficiency, and `priority(s)` is the student's normalized
priority score. Weights are configurable per run.

**Two equivalent formulations are implemented, deliberately, to demonstrate
the theoretical equivalence taught in the course:**

1. **Simple bipartite matching** (Kuhn / Hopcroft-Karp): each lab is
   expanded into `capacity` "slot" vertices, reducing many-to-one
   b-matching to plain 1-to-1 bipartite matching. Adjacency lists are
   sorted by descending `match_score` so that, among the (possibly many)
   maximum matchings, the algorithm tends to prefer higher-scoring edges —
   a standard, honest heuristic that never changes the *size* of the
   maximum matching, only which one is picked among ties.
2. **Maximum flow** (Edmonds-Karp / Dinic): `source → student` (capacity
   1), `student → lab` (capacity 1 per eligible edge), `lab → sink`
   (capacity = lab capacity). By the max-flow/min-cut theorem and
   integrality of flow on this network, the value of the maximum flow
   equals the size of the maximum matching, and every unit of flow on a
   `student → lab` edge is a real assignment.

See [`app/algorithms/matching_engine.py`](backend/app/algorithms/matching_engine.py)
for the exact graph-construction code, and
[`app/algorithms/kuhn.py`](backend/app/algorithms/kuhn.py),
[`hopcroft_karp.py`](backend/app/algorithms/hopcroft_karp.py),
[`edmonds_karp.py`](backend/app/algorithms/edmonds_karp.py),
[`dinic.py`](backend/app/algorithms/dinic.py) for the algorithms themselves.
Every implementation emits a step-by-step trace (`GRAPH_CREATED`,
`SEARCHING_AUGMENTING_PATH`, `PHASE_START`, `MATCH_UPDATED`,
`ALGORITHM_COMPLETE`, ...) that the frontend replays live over a
WebSocket — the Algorithm Playground and Allocation Config pages animate
the *actual* recorded trace, not a fabricated one.

## 6. Time & Space Complexity

| Algorithm | Time | Space | Notes |
|---|---|---|---|
| Kuhn's | `O(V·E)` | `O(V+E)` | One DFS (`O(E)`) per left vertex. |
| Hopcroft-Karp | `O(E·√V)` | `O(V+E)` | `O(√V)` phases, each an `O(E)` BFS + restricted DFS. |
| Edmonds-Karp | `O(V·E²)` | `O(V+E)` | Ford-Fulkerson with BFS-shortest augmenting paths. |
| Dinic's | `O(V²·E)` general, `O(E·√V)` on unit-capacity bipartite graphs | `O(V+E)` | Matches Hopcroft-Karp's bound in our exact use case. |

These are surfaced live in the UI (Algorithm Playground metrics panel,
`algorithm_metrics` table) alongside the *measured* wall-clock time for
that specific run, so complexity claims are always checked against real
data. Cross-algorithm agreement is enforced by tests (`test_hopcroft_karp.py`,
`test_max_flow.py`): Kuhn and Hopcroft-Karp always produce equal-size
matchings on identical randomized graphs, and Edmonds-Karp / Dinic always
produce equal max-flow values.

## 7. API Documentation

Interactive OpenAPI docs are auto-generated at **`/docs`** once the backend
is running. Summary of the resources:

| Prefix | Purpose |
|---|---|
| `POST /api/v1/auth/register`, `/login`, `GET /me` | JWT auth, role-based (`ADMIN` / `FACULTY` / `STUDENT`) |
| `GET/POST/PUT/DELETE /api/v1/students` | CRUD, search/filter, `/export` + `/import` CSV, `/skills`, `/preferences` |
| `GET/POST/PUT/DELETE /api/v1/labs` | CRUD, `/skills`, `/equipment`, `/time-slots` |
| `GET/POST/DELETE /api/v1/preferences` | Standalone preference management |
| `GET/POST/PUT/DELETE /api/v1/constraints` | Configurable rule rows |
| `POST /api/v1/allocation/generate` | Runs the real engine, persists an `AllocationRun`, optionally streams progress |
| `GET /api/v1/allocation/runs`, `/runs/{id}` | Historical runs + full assignment detail |
| `POST /api/v1/allocation/simulate` | What-If: runs the engine twice (before/after), never persisted |
| `GET /api/v1/matching/algorithms` | Static algorithm metadata (complexity, description, steps) |
| `POST /api/v1/matching/run` | Algorithm Playground: synthetic graph, any of the 4 algorithms |
| `POST /api/v1/matching/compare` | Runs all 4 algorithms on identical real input, persists each |
| `GET /api/v1/analytics/overview`, `/lab-utilization`, `/departments`, `/algorithm-performance`, `/history` | Real aggregates only |
| `POST /api/v1/ai/command` | NL → structured `AllocationConfig` (+ optional auto-execute on the real engine) |
| `POST /api/v1/ai/explain` | Per-assignment explanation from stored facts |
| `POST /api/v1/ai/analytics-query` | NL question → answer computed from real run data |
| `GET /api/v1/ai/conflicts` | Deterministic conflict detection (capacity, availability, department supply) |
| `GET /api/v1/ai/report` | Markdown report generated from stored statistics |
| `WS /api/v1/ws/algorithm/{channel}` | Live algorithm-progress event stream |

## 8. Setup Instructions

### Option A — Docker Compose (recommended)

```bash
cp backend/.env.example backend/.env      # edit SECRET_KEY for anything beyond local use
docker compose up --build
# backend:  http://localhost:8000/docs
# frontend: http://localhost:8080
```

Seed the database once the stack is up:

```bash
docker compose exec backend python -m scripts.seed_data
```

### Option B — Run locally

**Backend** (Python 3.12+; SQLite is used automatically if `DATABASE_URL`
is left at its default):

```bash
cd backend
python -m venv venv
source venv/bin/activate        # venv\Scripts\activate on Windows
pip install -r requirements.txt
python -m scripts.seed_data     # 220 students, 10 active labs + 1 under maintenance
uvicorn app.main:app --reload --port 8000
```

**Frontend** (Node 20+):

```bash
cd frontend
npm install
npm run dev                     # http://localhost:5173, proxies /api to :8000
```

Demo accounts created by the seed script:

| Role | Email | Password |
|---|---|---|
| Admin | `admin@campus.edu` | `Admin@123` |
| Faculty | `faculty@campus.edu` | `Faculty@123` |
| Student (a few, every 40th seeded student) | `student40@campus.edu`, `student80@campus.edu`, ... | `Student@123` |

## 9. Seed Data

`backend/scripts/seed_data.py` generates:

- **220 students** across 7 departments (CSE, ECE, EEE, MECH, CIVIL, IT,
  AIML), randomized year (1–4), CGPA, priority score, 1–4 department-relevant
  skills each, and 1–3 ranked lab preferences (mostly in-department, some
  cross-department).
- **11 laboratories**: 10 active with realistic capacity/equipment/skill
  requirements/time-slots, plus one deliberately set to `MAINTENANCE` status
  to exercise the "unavailable laboratory" path end-to-end.

## 10. Testing

```bash
cd backend
source venv/bin/activate
pytest -v
```

**92 tests, all passing**, covering:

- `test_kuhn.py`, `test_hopcroft_karp.py`, `test_max_flow.py` — correctness
  of all four algorithms individually, plus **cross-validation**: Kuhn vs.
  Hopcroft-Karp match-size agreement and Edmonds-Karp vs. Dinic flow-value
  agreement on 30+ randomized graphs.
- `test_matching_engine.py` — every required edge case: zero students, zero
  labs, all students choosing the same lab, lab capacity = 0, more students
  than total capacity, more capacity than students, disconnected graph
  components, missing/sufficient skill requirements, inactive labs,
  duplicate preference ranks.
- `test_api_auth.py`, `test_api_students_labs.py`, `test_api_allocation.py`
  — full HTTP-level integration tests (registration/login/RBAC, student &
  lab CRUD, CSV import/export, end-to-end allocation generation, analytics,
  algorithm comparison, What-If simulation, and every AI endpoint) against
  an in-memory SQLite database via `TestClient`.

The application was also driven end-to-end in a real browser (Playwright
against the actual running dev servers) to verify every page renders real
data with zero console/network errors — this process caught and fixed
three real bugs during development (see commit history / code comments):
a SQLite timestamp tie-break in "latest run" queries, a WebSocket
connect-race that dropped early algorithm steps on the Allocation Config
page, and an acronym-matching gap in the AI command parser.

## 11. Screenshots

*(Add screenshots of the Landing page, Dashboard, Algorithm Playground, and
Graph Visualization page here before submission — e.g. `docs/screenshots/*.png`.)*

## 12. Security

- Passwords hashed with bcrypt (`passlib`).
- JWT bearer tokens (`python-jose`), role claim embedded, role-based
  dependency guards (`require_admin`, `require_admin_or_faculty`) on every
  mutating endpoint.
- Pydantic validates every request body; SQLAlchemy's parameterized ORM
  queries prevent SQL injection.
- CORS restricted to the configured frontend origin(s).
- Rate limiting via `slowapi` (`RATE_LIMIT_PER_MINUTE`).
- `audit_logs` records who did what (register/login/create/update/delete/
  generate-allocation) with a timestamp and IP.
- Secrets are read from environment variables (`.env`, never committed —
  see `.gitignore`); `.env.example` documents every variable without real
  values.

## 13. AI Layer — Design Contract

The spec for this project explicitly forbids letting an LLM replace the
DSA algorithm. The AI layer (`app/services/ai_service.py`) is built to make
that contract structural, not just a promise:

1. **Parsing** (`parse_command`) is a transparent, rule-based NLP pipeline
   (department/year/algorithm/lab-acronym extraction + weight heuristics).
   It outputs a plain `AllocationConfig` — the *same* schema every other
   allocation entry point uses.
2. **Execution** always goes through `matching_engine.run_allocation` /
   `allocation_service.generate_and_persist_allocation` — identical code
   path to a human manually configuring a run. The AI can request
   `auto_execute=true`, but it never computes or invents the assignments
   itself.
3. **Explanation** (`explain_assignment`) and **analytics Q&A**
   (`answer_analytics_question`) only ever read real, already-persisted
   `Allocation` / `AllocationRun` rows and format them — no numbers are
   invented.
4. **Conflict detection** (`detect_conflicts`) and **report generation**
   (`generate_report`) are pure aggregation over the real schema.

The rule-based parser runs fully offline and deterministically (useful for
grading/demo reliability). `AI_MODEL` / `ANTHROPIC_API_KEY` are wired into
`app/core/config.py` so a real LLM call could be dropped in later purely to
*improve parsing quality* — it would still hand off to the exact same
structured config and the exact same deterministic engine.

## 14. Future Enhancements

- Alembic migrations (currently `Base.metadata.create_all` for simplicity).
- Redis-backed caching for analytics aggregates on very large datasets.
- A true incremental/streaming algorithm execution (today's WebSocket
  replay re-broadcasts the real, already-computed trace at a paced
  interval — accurate but not "live" in the sense of the algorithm
  blocking on network I/O per step).
- Weighted/many-to-many b-matching relaxations (e.g. a student allowed in
  multiple labs across time slots) via a fuller time-indexed flow network.
- Optional Dinic-with-scaling or Hopcroft-Karp parallelization for very
  large institutional datasets (10,000+ students).

---

## Advanced algorithms (course modules 2-6)

Every algorithm below is hand-built in `backend/app/algorithms/` (standard library only) and listed, with complexity and
where the product uses it, on the **Algorithm Atlas** page (`/app/atlas`, served by `GET /api/v1/concepts/atlas`).

| Module | Algorithms | Used in the product for |
|---|---|---|
| 2 Strings | naive, KMP, Z-function, Rabin-Karp (Miller-Rabin primes), Aho-Corasick, suffix array + Kasai LCP | entity search (`GET /search`, Ctrl/Cmd+K), AI command keyword extraction |
| 3 DP | Levenshtein / Damerau / weighted edit distance, Needleman-Wunsch, Smith-Waterman, matrix chain, optimal BST (+Knuth), Held-Karp, Hamiltonian path, tree DP + rerooting, SOS DP, knapsack, bitmask assignment | typo tolerance in search and AI parsing, skill-supply analysis |
| 4 Flow | Kuhn, Hopcroft-Karp, **Ford-Fulkerson**, Edmonds-Karp, Dinic, **min-cost max-flow**, min cut, König cover, Hall certificate, project selection | allocation engine (6 algorithms), fairness quotas as flow gadgets, bottleneck analysis |
| 5 NP & approximation | vertex cover 2-approx / exact, greedy / exact set cover, knapsack greedy / FPTAS, metric TSP 2-approx, nearest neighbour | "which labs must stay open" |
| 6 Randomised & parallel | Miller-Rabin, Fermat, Las Vegas prime generation, universal hashing, reservoir sampling, randomised quicksort, Monte Carlo simulation, Blelloch scan, parallel reduce | audit sampling, outage-risk simulation, lab slot offsets |

New pages: **Allocation Insights** (`/app/insights`), **Algorithm Atlas** (`/app/atlas`), **Concept Lab** (`/app/concepts`,
interactive demos for every module, most verified against brute-force oracles). The What-If Simulator gains a Monte Carlo
outage panel and Allocation Results a reservoir-sampled audit.

Behaviour changes worth knowing:

- `MIN_COST_FLOW` places the same maximum number of students as the other algorithms but returns the maximum matching
  with the highest total match score.
- `max_share_per_department` (fairness cap) is now actually enforced, by the flow algorithms. Kuhn and Hopcroft-Karp
  cannot express it and return HTTP 400 instead of silently ignoring it.
- New enum values `FORD_FULKERSON` and `MIN_COST_FLOW`: an existing **Postgres** database needs
  `ALTER TYPE algorithmname ADD VALUE 'FORD_FULKERSON'; ALTER TYPE algorithmname ADD VALUE 'MIN_COST_FLOW';`
  (SQLite needs nothing).
