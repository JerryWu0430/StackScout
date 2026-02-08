// API types matching backend models

export interface TechStack {
  frontend: string[]
  backend: string[]
  database: string[]
  infrastructure: string[]
}

export interface RepoFingerprint {
  stack: TechStack
  gaps: string[]
  risk_flags: string[]
  complexity_score: number
  recommendations_context: string
  // New fields
  industry: string
  project_type: string
  keywords: string[]
  use_cases: string[]
}

export interface RepoResponse {
  repo_id: string
  github_url?: string | null
  fingerprint: RepoFingerprint
}

export interface Tool {
  id: string
  name: string
  category: string
  description?: string
  url?: string
  booking_url?: string
  tags: string[]
  source?: 'product_hunt' | 'yc' | 'github' | null  // null = seeded tool
}

export interface MatchReason {
  type: 'industry' | 'keyword' | 'gap' | 'use_case'
  matched: string
  score_contribution: number
}

export interface Recommendation {
  tool: Tool
  suitability_score: number
  demo_priority: number
  explanation: string
  match_reasons: MatchReason[]
}

export interface TimeSlot {
  start: string
  end: string
  formatted: string
}

export interface DraftEmail {
  id: string
  repo_id: string
  tool_id: string
  to_email: string | null
  to_name: string | null
  subject: string
  body: string
  context: {
    tool?: Tool
    fingerprint?: RepoFingerprint
    match_reasons?: MatchReason[]
    explanation?: string
  }
  suggested_times: TimeSlot[]
  selected_time: TimeSlot | null
  status: 'draft' | 'ready' | 'sent' | 'failed'
  created_at: string | null
  sent_at: string | null
  tool_name?: string
  tool_url?: string
}
