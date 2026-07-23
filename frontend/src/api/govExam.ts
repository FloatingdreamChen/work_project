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
}

export interface MatchItem {
  position: Position
  tier: string
  score: number
  matched: string[]
  risks: string[]
  verification: string[]
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
  limit?: number
}) {
  return unwrap<{ disclaimer: string; items: MatchItem[]; report_id: string }>(
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
  topic?: string
  question?: string
  user_answer: string
}) {
  return unwrap<{
    score: number
    strengths: string[]
    problems: string[]
    improved_answer: string
    next_steps: string[]
    disclaimer: string
  }>(apiClient.post('/practice/review', payload))
}
