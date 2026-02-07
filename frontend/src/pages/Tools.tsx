import { useSearchParams } from 'react-router-dom'
import { useEffect, useState } from 'react'
import ToolCard from '../components/ToolCard'

interface Tool {
  id: number
  name: string
  category: string
  description?: string
  tags: string[]
}

interface Recommendation {
  tool: Tool
  suitability_score: number
  demo_priority: number
  explanation: string
}

export default function Tools() {
  const [searchParams] = useSearchParams()
  const repoId = searchParams.get('repo_id')

  const [recommendations, setRecommendations] = useState<Recommendation[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!repoId) {
      setError('No repository ID provided')
      setIsLoading(false)
      return
    }

    async function fetchRecommendations() {
      try {
        const response = await fetch(`/api/repos/${repoId}/recommendations`)
        if (!response.ok) {
          const data = await response.json().catch(() => ({}))
          throw new Error(data.detail || 'Failed to fetch recommendations')
        }
        const data = await response.json()
        setRecommendations(data)
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Unknown error')
      } finally {
        setIsLoading(false)
      }
    }

    fetchRecommendations()
  }, [repoId])

  return (
    <div className="min-h-screen bg-gray-100 p-8">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-3xl font-bold text-gray-800 mb-2">Recommended Tools</h1>
        <p className="text-gray-600 mb-6">Based on your repository's tech stack</p>

        {isLoading && (
          <div className="text-center py-12">
            <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-blue-600 border-r-transparent" />
            <p className="mt-4 text-gray-600">Loading recommendations...</p>
          </div>
        )}

        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4">
            <p className="text-red-600">{error}</p>
          </div>
        )}

        {!isLoading && !error && recommendations.length === 0 && (
          <div className="bg-gray-50 border border-gray-200 rounded-lg p-8 text-center">
            <p className="text-gray-600">No recommendations found for this repository.</p>
          </div>
        )}

        {!isLoading && !error && recommendations.length > 0 && (
          <div className="space-y-4">
            {recommendations.map((rec) => (
              <ToolCard
                key={rec.tool.id}
                tool={rec.tool}
                suitabilityScore={rec.suitability_score}
                demoPriority={rec.demo_priority}
                explanation={rec.explanation}
                repoId={repoId!}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
