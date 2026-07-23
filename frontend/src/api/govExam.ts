import { apiClient, unwrap } from './client'

export interface Profile {
  target_exam?: string
  target_region?: string
  education?: string
  degree?: string
  major?: string
  graduation_year?: number
  fresh_graduate_status?: string
  political_status?: string
  household_region?: string
  grassroots_experience?: string
  work_years?: number
  certificates?: string
}

export interface Position {
  id?: string
  exam_year: number
  exam_type: string
  province?: string
  city?: string
  department?: string
  bureau?: string
  position_name: string
  position_code?: string
  recruitment_count?: number
  applicant_count?: number
  competition_ratio?: number
  previous_min_score?: number
  education_requirement?: string
  degree_requirement?: string
  major_requirement?: string
  political_requirement?: string
  grassroots_requirement?: string
  work_years_requirement?: string
  household_requirement?: string
  remarks?: string
  source_name?: string
  source_url?: string
  source_published_at?: string
}

export interface MatchItem {
  position: Position
  tier: string
  score: number
  matched: string[]
  risks: string[]
  verification: string[]
  policy_basis?: {
    source_name?: string
    source_url?: string
    requirement?: string
  }
  rationale: string
}

export function login(username: string, password: string) {
  return unwrap<{
    access_token: string
    expires_in: number
    user_id: string
    username: string
  }>(apiClient.post('/auth/login', { username, password }))
}

export function register(username: string, password: string) {
  return unwrap(apiClient.post('/auth/register', { username, password }))
}

export function getProfile() {
  return unwrap<Profile>(apiClient.get('/profiles/me'))
}

export function saveProfile(profile: Profile) {
  return unwrap<Profile>(apiClient.put('/profiles/me', profile))
}

export function listPositions(params: Record<string, unknown>) {
  return unwrap<Position[]>(apiClient.get('/positions', { params }))
}

export function importPositions(positions: Position[]) {
  return unwrap<{ count: number; items: Position[] }>(
    apiClient.post('/positions/import', { positions }),
  )
}

export function matchPositions(payload: {
  profile?: Profile
  exam_year?: number
  exam_type?: string
  province?: string
  preferred_regions?: string[]
  risk_preference?: string
  limit?: number
}) {
  return unwrap<{ disclaimer: string; strategy: Record<string, unknown>; items: MatchItem[]; report_id: string }>(
    apiClient.post('/positions/match', payload),
  )
}

export function chat(message: string) {
  return unwrap<{ answer: string; agent: string; sources: unknown[] }>(
    apiClient.post('/chat', { message }),
  )
}

export function reviewPractice(payload: {
  practice_type: string
  module_name?: string
  topic?: string
  question?: string
  user_answer: string
  accuracy?: number
  duration_minutes?: number
  question_count?: number
}) {
  return unwrap<{
    score: number
    strengths: string[]
    problems: string[]
    improved_answer: string
    next_steps: string[]
    dimension_scores?: Record<string, number>
    follow_up_question?: string
    disclaimer: string
  }>(apiClient.post('/practice/review', payload))
}

export function buildStudyPlan(payload: {
  target_exam: string
  exam_date?: string
  target_position?: string
  province?: string
  daily_hours: number
  weekly_days: number
  foundation_level: string
  weak_modules: string[]
  strong_modules?: string[]
  preferred_modules?: string[]
  current_scores?: Record<string, number>
  include_interview: boolean
  notes?: string
}) {
  return unwrap<{
    plan: {
      target_exam: string
      exam_date?: string
      days_until_exam?: number
      planned_days: number
      planned_weeks: number
      min_cycle_enforced: boolean
      warning?: string
      weekly_hours: number
      module_weights: Record<string, number>
      phases: Array<Record<string, unknown>>
      weekly_plan: Array<{
        week: number
        phase: string
        focus: string
        weekly_hours: number
        tasks: string[]
        deliverables: string[]
      }>
      daily_template: Array<Record<string, unknown>>
      milestones: Array<Record<string, unknown>>
      adjustment_rules: string[]
      disclaimer: string
    }
    answer: string
    sources: unknown[]
  }>(apiClient.post('/practice/plan', payload))
}

export function getStudyReport(days = 30) {
  return unwrap<{
    days: number
    practice_count: number
    by_type: Record<string, number>
    by_module: Record<string, { count: number; avg_accuracy?: number; avg_duration_minutes?: number }>
    average_score?: number
    top_problem_keywords: Array<{ keyword: string; count: number }>
    suggestions: string[]
    recent: Array<Record<string, unknown>>
  }>(apiClient.post('/practice/report', { days }))
}

export function listWrongQuestions(payload: { status?: string; limit?: number }) {
  return unwrap<Array<Record<string, unknown>>>(apiClient.post('/practice/wrong-questions', payload))
}

export function getKnowledgeStatus() {
  return unwrap<{
    models: Record<string, { exists: boolean; path: string; missing_files: string[]; size_mb: number }>
    vector_rag_ready: boolean
  }>(apiClient.get('/knowledge/status'))
}

export function searchKnowledge(payload: { query: string; top_k?: number }) {
  return unwrap<Array<{
    id?: string
    title?: string
    content?: string
    source_name?: string
    score?: number
    metadata?: Record<string, unknown>
  }>>(apiClient.post('/knowledge/search', payload))
}
