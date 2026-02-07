import { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import StackCard from '../components/StackCard'
import GapCard from '../components/GapCard'
import type { RepoResponse, TechStack } from '../types/api'

type LoadingState = 'loading' | 'error' | 'success'

export default function Analysis() {
  const { repo_id } = useParams<{ repo_id: string }>()
  const [state, setState] = useState<LoadingState>('loading')
  const [data, setData] = useState<RepoResponse | null>(null)
  const [error, setError] = useState('')

  useEffect(() => {
    async function fetchRepo() {
      try {
        const response = await fetch(`/api/repos/${repo_id}`)
        if (!response.ok) {
          const err = await response.json().catch(() => ({}))
          throw new Error(err.detail || 'Failed to load analysis')
        }
        const result: RepoResponse = await response.json()
        setData(result)
        setState('success')
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Something went wrong')
        setState('error')
      }
    }
    fetchRepo()
  }, [repo_id])

  if (state === 'loading') {
    return (
      <div className="min-h-screen bg-gray-100 flex items-center justify-center">
        <div className="text-center">
          <svg className="animate-spin h-12 w-12 text-blue-600 mx-auto mb-4" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
          </svg>
          <p className="text-gray-600">Loading analysis...</p>
        </div>
      </div>
    )
  }

  if (state === 'error') {
    return (
      <div className="min-h-screen bg-gray-100 flex items-center justify-center">
        <div className="text-center">
          <p className="text-red-600 mb-4">{error}</p>
          <Link to="/" className="text-blue-600 hover:underline">
            Go back home
          </Link>
        </div>
      </div>
    )
  }

  const fingerprint = data!.fingerprint
  const stackCategories = Object.entries(fingerprint.stack) as [keyof TechStack, string[]][]

  return (
    <div className="min-h-screen bg-gray-100 p-8">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-800 mb-2">Stack Fingerprint</h1>
          <p className="text-gray-600">{fingerprint.recommendations_context}</p>
        </div>

        {/* Complexity Score */}
        <div className="bg-white p-5 rounded-lg shadow-md mb-8">
          <h2 className="text-lg font-semibold text-gray-800 mb-3">Complexity Score</h2>
          <div className="flex items-center gap-4">
            <div className="flex-1 bg-gray-200 rounded-full h-3">
              <div
                className="bg-blue-600 h-3 rounded-full transition-all"
                style={{ width: `${fingerprint.complexity_score * 10}%` }}
              />
            </div>
            <span className="text-2xl font-bold text-blue-600">{fingerprint.complexity_score}/10</span>
          </div>
        </div>

        {/* Tech Stack */}
        <h2 className="text-xl font-semibold text-gray-800 mb-4">Tech Stack</h2>
        <div className="grid gap-4 md:grid-cols-2 mb-8">
          {stackCategories.map(([category, technologies]) => (
            <StackCard key={category} category={category} technologies={technologies} />
          ))}
        </div>

        {/* Gaps */}
        {fingerprint.gaps.length > 0 && (
          <>
            <h2 className="text-xl font-semibold text-gray-800 mb-4">Gaps & Missing Practices</h2>
            <div className="space-y-3 mb-8">
              {fingerprint.gaps.map((gap, i) => (
                <GapCard key={i} description={gap} severity="medium" />
              ))}
            </div>
          </>
        )}

        {/* Risk Flags */}
        {fingerprint.risk_flags.length > 0 && (
          <>
            <h2 className="text-xl font-semibold text-gray-800 mb-4">Risk Flags</h2>
            <div className="space-y-3 mb-8">
              {fingerprint.risk_flags.map((flag, i) => (
                <GapCard key={i} description={flag} severity="high" />
              ))}
            </div>
          </>
        )}

        {/* CTA */}
        <Link
          to={`/tools/${repo_id}`}
          className="inline-block bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700 transition font-semibold"
        >
          See Recommended Tools
        </Link>
      </div>
    </div>
  )
}
