import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Spinner } from '@/components/ui/spinner'
import { Features1 } from '@/components/blocks/features-1'
import FaultyTerminal from '@/components/FaultyTerminal'
import asciiDarkImg from '@/assets/ascii-dark.png'

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
    <div className="min-h-screen bg-background flex flex-col items-center justify-center px-4 relative overflow-hidden">
      {/* FaultyTerminal Background */}
      <div className="absolute inset-0 opacity-30">
        <FaultyTerminal
          scale={1}
          digitSize={1.5}
          scanlineIntensity={0.3}
          glitchAmount={1}
          flickerAmount={1}
          noiseAmp={0.3}
          chromaticAberration={0}
          dither={0}
          curvature={0.2}
          tint="#ffffff"
          mouseReact
          mouseStrength={0.2}
          brightness={1}
        />
      </div>
      <div className="w-full max-w-2xl text-center relative z-10">
        {/* Logo/Brand */}
        <div className="mb-8">
          {/* Large ASCII art with soft, blurred corners */}
          <div
            className="w-full max-w-xl mx-auto aspect-[4/3] max-h-80 relative"
            style={{
              maskImage: 'radial-gradient(ellipse 65% 65% at 50% 50%, black 35%, transparent 65%)',
              WebkitMaskImage: 'radial-gradient(ellipse 65% 65% at 50% 50%, black 35%, transparent 65%)',
            }}
          >
            <img
              src={asciiDarkImg}
              alt=""
              className="w-full h-full object-cover object-center opacity-80"
            />
          </div>
          <h1 className="text-5xl font-bold text-foreground mb-4 -mt-20 relative z-10">StackScout</h1>
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
        <Features1 />
      </div>
    </div>
  )
}
