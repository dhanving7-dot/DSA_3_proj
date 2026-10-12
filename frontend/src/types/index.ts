export type UserRole = "ADMIN" | "FACULTY" | "STUDENT"

export interface User {
  id: number
  email: string
  full_name: string
  role: UserRole
  is_active: boolean
  created_at: string
}

export interface StudentSkill {
  id: number
  skill_name: string
  proficiency_level: number
}

export interface StudentPreference {
  id: number
  lab_id: number
  rank: number
}

export interface Student {
  id: number
  roll_number: string
  full_name: string
  email: string
  department: string
  year: number
  cgpa: number
  priority_score: number
  created_at: string
  skills: StudentSkill[]
  preferences: StudentPreference[]
}

export type LabStatus = "ACTIVE" | "INACTIVE" | "MAINTENANCE"

export interface LabRequiredSkill {
  id: number
  skill_name: string
  min_proficiency: number
  required: boolean
}

export interface LabEquipment {
  id: number
  equipment_name: string
  quantity: number
}

export interface LabTimeSlot {
  id: number
  day_of_week: number
  start_time: string
  end_time: string
  is_available: boolean
}

export interface Laboratory {
  id: number
  code: string
  name: string
  department: string
  capacity: number
  location: string
  status: LabStatus
  created_at: string
  required_skills: LabRequiredSkill[]
  equipment: LabEquipment[]
  time_slots: LabTimeSlot[]
}

export type AlgorithmName =
  | "KUHN"
  | "HOPCROFT_KARP"
  | "FORD_FULKERSON"
  | "EDMONDS_KARP"
  | "DINIC"
  | "MIN_COST_FLOW"

export interface AllocationConfig {
  same_department_only: boolean
  require_preference: boolean
  min_preference_score: number
  preference_weight: number
  skill_weight: number
  priority_weight: number
  max_share_per_department: number | null
}

export const DEFAULT_ALLOCATION_CONFIG: AllocationConfig = {
  same_department_only: false,
  require_preference: false,
  min_preference_score: 0.3,
  preference_weight: 0.5,
  skill_weight: 0.3,
  priority_weight: 0.2,
  max_share_per_department: null,
}

export interface AlgorithmMetric {
  algorithm: AlgorithmName
  vertices: number
  edges: number
  iterations: number
  augmenting_paths_found: number
  time_complexity: string
  space_complexity: string
  execution_time_ms: number
}

export interface Allocation {
  id: number
  run_id: number
  student_id: number
  lab_id: number | null
  algorithm: AlgorithmName
  preference_rank: number | null
  match_score: number
  eligibility_reason: string
  status: "MATCHED" | "UNMATCHED"
  created_at: string
}

export interface AllocationRun {
  id: number
  algorithm: AlgorithmName
  status: "PENDING" | "RUNNING" | "COMPLETED" | "FAILED"
  total_students: number
  total_labs: number
  total_edges: number
  matched_count: number
  unmatched_count: number
  execution_time_ms: number
  preference_satisfaction: number
  capacity_utilization: number
  created_at: string
  metrics: AlgorithmMetric | null
}

export interface AllocationRunDetail extends AllocationRun {
  allocations: Allocation[]
}

export interface AlgorithmStep {
  step_number: number
  event: string
  description: string
  data: Record<string, unknown>
}

export interface MatchingResult {
  algorithm: AlgorithmName
  matched_pairs: [number, number][]
  match_size: number
  unmatched_left: number[]
  unmatched_right: number[]
  vertices: number
  edges: number
  iterations: number
  augmenting_paths_found: number
  execution_time_ms: number
  time_complexity: string
  space_complexity: string
  steps: AlgorithmStep[]
}

export interface OverviewStats {
  total_students: number
  total_labs: number
  total_capacity: number
  matched_students: number
  unmatched_students: number
  matching_percentage: number
  capacity_utilization: number
  preference_satisfaction: number
  latest_run_id: number | null
  latest_algorithm: string | null
}

export interface LabUtilization {
  lab_id: number
  lab_name: string
  department: string
  capacity: number
  allocated: number
  utilization: number
}

export interface DepartmentAllocation {
  department: string
  total_students: number
  matched: number
  unmatched: number
}

export interface AlgorithmPerformance {
  algorithm: string
  run_id: number
  vertices: number
  edges: number
  execution_time_ms: number
  matched_count: number
  iterations: number
}

export interface HistoricalRun {
  run_id: number
  algorithm: string
  status: string
  matched_count: number
  unmatched_count: number
  execution_time_ms: number
  created_at: string
}

export interface AnalyticsOverview {
  overview: OverviewStats
  lab_utilization: LabUtilization[]
  department_allocation: DepartmentAllocation[]
  algorithm_performance: AlgorithmPerformance[]
  historical_runs: HistoricalRun[]
}

export interface ParsedConstraints {
  algorithm: string
  config: AllocationConfig
  department_filter: string | null
  year_filter: number | null
  lab_name_filters: string[]
  notes: string[]
}

export interface AICommandResponse {
  original_text: string
  parsed: ParsedConstraints
  matched_student_count: number
  matched_lab_count: number
  executed: boolean
  run_id: number | null
  message: string
}

export interface AIExplainResponse {
  student_id: number
  lab_id: number | null
  status: string
  explanation: string
  facts: Record<string, unknown>
}

export interface AIAnalyticsQueryResponse {
  question: string
  answer: string
  facts: Record<string, unknown>
}

export interface Conflict {
  type: string
  severity: "high" | "medium" | "low"
  message: string
  lab_id?: number
  department?: string
}

export interface SimulationMetrics {
  matched_count: number
  unmatched_count: number
  total_students: number
  total_labs: number
  preference_satisfaction: number
  capacity_utilization: number
  execution_time_ms: number
}

export interface SimulationResult {
  algorithm: string
  before: SimulationMetrics
  after: SimulationMetrics
  delta: Record<string, number>
  changes_applied: Record<string, unknown>
}

export interface AlgorithmInfo {
  name: string
  category: string
  description: string
  time_complexity: string
  space_complexity: string
  steps: string[]
}
