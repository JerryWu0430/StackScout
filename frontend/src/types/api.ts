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
}

export interface RepoResponse {
  repo_id: number
  fingerprint: RepoFingerprint
}
