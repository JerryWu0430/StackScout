import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Spinner } from '@/components/ui/spinner'

export default function Home() {
  const navigate = useNavigate()
  const [url, setUrl] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!url.trim()) return

    setIsLoading(true)
    setError(null)

    try {
      const res = await fetch('/api/repos/analyze', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ github_url: url.trim() }),
      })

      if (!res.ok) {
        const data = await res.json().catch(() => ({}))
        throw new Error(data.detail || 'Failed to analyze repository')
      }

      const data = await res.json()
      navigate(`/analysis/${data.repo_id}`)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Something went wrong')
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-background flex flex-col items-center justify-center px-4">
      <div className="w-full max-w-2xl text-center">
        {/* Logo/Brand */}
        <div className="mb-8">
          <div className="w-20 h-20 bg-primary/20 rounded-full flex items-center justify-center mx-auto mb-6">
            <svg className="w-10 h-10 text-primary" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
            </svg>
          </div>
          <h1 className="text-5xl font-bold text-foreground mb-4">StackScout</h1>
          <p className="text-xl text-muted-foreground">
            AI-powered repository analysis with voice-guided insights
          </p>
        </div>

        {/* URL Input */}
        <form onSubmit={handleSubmit} className="mb-8">
          <div className="flex gap-3">
            <Input
              type="url"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              placeholder="https://github.com/user/repo"
              className="flex-1 h-12"
              disabled={isLoading}
            />
            <Button
              type="submit"
              disabled={isLoading || !url.trim()}
              size="lg"
              className="h-12"
            >
              {isLoading ? <Spinner /> : 'Analyze'}
            </Button>
          </div>

          {error && (
            <p className="mt-3 text-sm text-destructive">{error}</p>
          )}
        </form>

        {/* Features */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-6">
          <div className="p-6 bg-card border border-border rounded-xl">
            <div className="text-2xl mb-3">1</div>
            <h3 className="font-medium text-foreground mb-1">Paste GitHub URL</h3>
            <p className="text-sm text-muted-foreground">Enter any public repo</p>
          </div>
          <div className="p-6 bg-card border border-border rounded-xl">
            <div className="text-2xl mb-3">2</div>
            <h3 className="font-medium text-foreground mb-1">Voice Analysis</h3>
            <p className="text-sm text-muted-foreground">AI explains your stack</p>
          </div>
          <div className="p-6 bg-card border border-border rounded-xl">
            <div className="text-2xl mb-3">3</div>
            <h3 className="font-medium text-foreground mb-1">Get Recommendations</h3>
            <p className="text-sm text-muted-foreground">Tools to fill gaps</p>
          </div>
        </div>
      </div>
    </div>
  )
}
