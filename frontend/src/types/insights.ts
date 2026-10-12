import type { AllocationConfig } from "@/types"

export interface AtlasModule {
  id: number
  title: string
  summary: string
}

export interface AtlasAlgorithm {
  id: string
  name: string
  module: number
  category: string
  time_complexity: string
  space_complexity: string
  summary: string
  source: string
  used_in: { label: string; path: string }[]
  demo: string | null // "tab:anchor" inside the Concept Lab
}

export interface Reduction {
  from: string
  to: string
  idea: string
}

export interface AtlasResponse {
  modules: AtlasModule[]
  algorithms: AtlasAlgorithm[]
  reductions: Reduction[]
}

export interface BottleneckInsight {
  config: AllocationConfig
  config_from_run: number | null
  total_students: number
  max_flow: number
  unmatched: number
  min_cut_capacity: number
  max_flow_equals_min_cut: boolean
  hall: {
    violator_size: number
    reachable_capacity: number
    deficiency: number
    students_with_no_eligible_lab: number
    by_department: Record<string, number>
  }
  konig: { students_in_cover: number; lab_seats_in_cover: number; min_vertex_cover: number; max_matching: number }
  bottleneck_labs: { lab_id: number; lab_name: string; capacity: number; students_competing: number }[]
  binding_quotas: { lab_id: number; lab_name: string; department: string; quota: number }[]
  labs_outside_bottleneck: { lab_id: number; lab_name: string }[]
  execution_time_ms: number
}

export interface SetCoverLab {
  lab_id: number
  lab_name: string
  covers: number
  students_only_eligible_here?: number
}

export interface SetCoverInsight {
  config_from_run: number | null
  placeable_students: number
  students_with_no_eligible_lab: number
  candidate_labs: number
  greedy: { labs: SetCoverLab[]; new_students_per_pick: number[]; size: number; time_ms: number }
  exact: { labs: SetCoverLab[]; size: number; subsets_evaluated: number; time_ms: number } | null
  approximation_ratio: number | null
  harmonic_bound: number
  essential_labs: SetCoverLab[]
}

export interface SkillSupplyInsight {
  items: string[]
  k: number
  masks: number
  sos_operations: number
  sos_time_ms: number
  bruteforce_operations: number
  students: number
  per_lab: {
    lab_id: number
    lab_name: string
    capacity: number
    requirements: string[]
    qualified_sos: number | null
    qualified_bruteforce: number
  }[]
  pair_matrix: number[][]
  qualified_for_none: number
}

export interface AlgorithmSummary {
  algorithm: string
  matched: number
  total_score: number
  average_score: number
  preference_satisfaction: number
  rank_distribution: Record<string, number>
  execution_time_ms: number
  gap_to_optimal: number
  students_placed_differently: number
}

export interface OptimalityInsight {
  config_from_run: number | null
  skipped: string[]
  algorithms: AlgorithmSummary[]
  optimal_total_score: number
  same_cardinality: boolean
}

export interface MonteCarloResult {
  config_from_run: number | null
  algorithm: string
  trials: number
  outage_probability: number
  seed: number | null
  baseline_matched: number
  mean_matched: number
  std_matched: number
  ci95: [number, number]
  min_matched: number
  max_matched: number
  histogram: { matched: number; trials: number }[]
  at_risk_students: { student_id: number; student: string; p_unmatched: number }[]
  students_ever_displaced: number
  never_placeable: number
  lab_criticality: { lab_id: number; lab_name: string; trials_down: number; expected_matched_when_down: number; loss_vs_baseline: number }[]
  execution_time_ms: number
}

export interface AuditSample {
  run_id: number | null
  k: number
  items_seen: number
  inclusion_probability: number
  sample: {
    allocation_id: number
    student_id: number
    student: string
    lab: string | null
    status: "MATCHED" | "UNMATCHED"
    preference_rank: number | null
    match_score: number
    reason: string
  }[]
}

export type SearchAlgorithm = "NAIVE" | "KMP" | "Z_FUNCTION" | "RABIN_KARP" | "SUFFIX_ARRAY"

export interface SearchHit {
  type: "student" | "lab"
  id: number
  title: string
  subtitle: string
  match: "exact" | "fuzzy"
  distance?: number
  fields: Record<string, { value: string; spans: [number, number][] }>
}

export interface SearchResponse {
  query: string
  algorithm: SearchAlgorithm
  corpus_length: number
  fields_indexed: number
  occurrences: number
  comparisons: number
  search_time_ms: number
  suffix_array_cached: boolean | null
  exact_matches: number
  fuzzy_matches: number
  results: SearchHit[]
}
