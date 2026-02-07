import { useState } from 'react'
import { useNavigate } from 'react-router-dom'

const GITHUB_REPO_REGEX = /^https?:\/\/github\.com\/[\w.-]+\/[\w.-]+\/?$/

export default function Home() {
  const [repoUrl, setRepoUrl] = useState('')
  const [error, setError] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const navigate = useNavigate()

  const validateGitHubUrl = (url: string): boolean => {
    return GITHUB_REPO_REGEX.test(url.trim())
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')

    const trimmedUrl = repoUrl.trim()
    if (!trimmedUrl) {
      setError('Please enter a GitHub repository URL')
      return
    }

    if (!validateGitHubUrl(trimmedUrl)) {
      setError('Please enter a valid GitHub repository URL (e.g., https://github.com/owner/repo)')
      return
    }

    setIsLoading(true)

    try {
      const response = await fetch('/api/repos/analyze', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url: trimmedUrl }),
      })

      if (!response.ok) {
        const data = await response.json().catch(() => ({}))
        throw new Error(data.detail || 'Failed to analyze repository')
      }

      const data = await response.json()
      navigate(`/analysis/${data.repo_id}`)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Something went wrong')
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col items-center justify-center px-4">
      <div className="w-full max-w-xl text-center">
        <h1 className="text-5xl font-bold text-gray-900 mb-4">StackScout</h1>
        <p className="text-lg text-gray-600 mb-10">
          Analyze any GitHub repository's tech stack in seconds
        </p>

        <form onSubmit={handleSubmit} className="w-full">
          <div className="flex flex-col sm:flex-row gap-3">
            <input
              type="url"
              value={repoUrl}
              onChange={(e) => {
                setRepoUrl(e.target.value)
                if (error) setError('')
              }}
              placeholder="https://github.com/owner/repo"
              disabled={isLoading}
              className="flex-1 px-5 py-4 text-lg border border-gray-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-100 disabled:cursor-not-allowed"
            />
            <button
              type="submit"
              disabled={isLoading}
              className="px-8 py-4 text-lg font-semibold bg-blue-600 text-white rounded-xl hover:bg-blue-700 transition disabled:bg-blue-400 disabled:cursor-not-allowed flex items-center justify-center gap-2"
            >
              {isLoading ? (
                <>
                  <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                  </svg>
                  Analyzing...
                </>
              ) : (
                'Analyze Stack'
              )}
            </button>
          </div>

          {error && (
            <p className="mt-3 text-red-600 text-sm text-left">{error}</p>
          )}
        </form>
      </div>
    </div>
  )
}
