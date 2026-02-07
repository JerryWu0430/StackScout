import { useState, useEffect } from 'react'
import { useParams, Link } from 'react-router-dom'
import VoiceAgent from '../components/VoiceAgent'

interface Tool {
  id: number
  name: string
  description: string
  category: string
}

interface ConversationSummary {
  session_id: string
  status: string
  key_points: string[]
  booking_status?: string
  next_steps: string[]
}

type CallState = 'idle' | 'connecting' | 'active' | 'ended'

export default function Schedule() {
  const { repo_id: repoId, tool_id: toolId } = useParams()

  const [tool, setTool] = useState<Tool | null>(null)
  const [callState, setCallState] = useState<CallState>('idle')
  const [sessionId, setSessionId] = useState<string | null>(null)
  const [websocketUrl, setWebsocketUrl] = useState<string | null>(null)
  const [summary, setSummary] = useState<ConversationSummary | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [audioUrl, setAudioUrl] = useState<string | null>(null)

  // Fetch tool info
  useEffect(() => {
    if (!toolId) return
    fetch(`/api/tools/${toolId}`)
      .then((res) => res.json())
      .then(setTool)
      .catch(() => setError('Failed to load tool info'))
  }, [toolId])

  const startVoiceCall = async () => {
    if (!repoId || !toolId) {
      setError('Missing repo or tool ID')
      return
    }

    setCallState('connecting')
    setError(null)

    try {
      const res = await fetch('/api/voice/start', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          repo_id: parseInt(repoId),
          tool_id: parseInt(toolId),
        }),
      })

      if (!res.ok) {
        const data = await res.json().catch(() => ({}))
        throw new Error(data.detail || 'Failed to start voice session')
      }

      const data = await res.json()
      setSessionId(data.session_id)
      setWebsocketUrl(data.websocket_url)
      setCallState('active')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to start call')
      setCallState('idle')
    }
  }

  const endVoiceCall = async () => {
    setCallState('ended')

    if (sessionId) {
      try {
        const res = await fetch(`/api/voice/${sessionId}/summary`)
        if (res.ok) {
          const data = await res.json()
          setSummary(data)
        }
      } catch {
        // Summary fetch optional
      }
    }
  }

  const handleCallEnded = (recordingUrl?: string) => {
    if (recordingUrl) setAudioUrl(recordingUrl)
    endVoiceCall()
  }

  // Show summary view after call ends
  if (callState === 'ended' && summary) {
    return (
      <div className="min-h-screen bg-gray-100 p-8">
        <div className="max-w-2xl mx-auto">
          <h1 className="text-3xl font-bold text-gray-800 mb-2">Call Summary</h1>
          {tool && <p className="text-gray-600 mb-6">{tool.name} Demo Scheduling</p>}

          {/* Booking status */}
          <div className="bg-white rounded-lg shadow-md p-6 mb-6">
            <div className="flex items-center gap-3 mb-4">
              <div
                className={`w-3 h-3 rounded-full ${
                  summary.booking_status === 'confirmed' ? 'bg-green-500' : 'bg-yellow-500'
                }`}
              />
              <span className="font-medium text-gray-800">
                {summary.booking_status === 'confirmed'
                  ? 'Demo Scheduled!'
                  : 'Booking Pending'}
              </span>
            </div>

            {/* Key points */}
            {summary.key_points.length > 0 && (
              <div className="mb-4">
                <h3 className="text-sm font-semibold text-gray-700 mb-2">Key Points</h3>
                <ul className="space-y-2">
                  {summary.key_points.map((point, i) => (
                    <li key={i} className="text-sm text-gray-600 flex gap-2">
                      <span className="text-blue-500">•</span>
                      {point}
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* Next steps */}
            <div>
              <h3 className="text-sm font-semibold text-gray-700 mb-2">Next Steps</h3>
              <ul className="space-y-2">
                {summary.next_steps.map((step, i) => (
                  <li key={i} className="text-sm text-gray-600 flex gap-2">
                    <span className="text-green-500">{i + 1}.</span>
                    {step}
                  </li>
                ))}
              </ul>
            </div>
          </div>

          {/* Audio playback */}
          {audioUrl && (
            <div className="bg-white rounded-lg shadow-md p-6 mb-6">
              <h3 className="text-sm font-semibold text-gray-700 mb-3">Call Recording</h3>
              <audio controls className="w-full" src={audioUrl}>
                Your browser does not support audio playback.
              </audio>
            </div>
          )}

          {/* Actions */}
          <div className="flex gap-4">
            <button
              onClick={() => {
                setCallState('idle')
                setSummary(null)
                setSessionId(null)
              }}
              className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition"
            >
              Schedule Another Call
            </button>
            <Link
              to={`/tools?repo_id=${repoId}`}
              className="px-6 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition"
            >
              Back to Recommendations
            </Link>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-100 p-8">
      <div className="max-w-2xl mx-auto">
        <h1 className="text-3xl font-bold text-gray-800 mb-2">Schedule Demo</h1>

        {/* Tool info */}
        {tool ? (
          <div className="bg-white rounded-lg shadow-md p-4 mb-6">
            <div className="flex justify-between items-start">
              <div>
                <h2 className="text-xl font-semibold text-gray-800">{tool.name}</h2>
                <p className="text-gray-600 text-sm mt-1">{tool.description}</p>
              </div>
              <span className="text-xs px-2 py-1 bg-blue-100 text-blue-700 rounded">
                {tool.category}
              </span>
            </div>
          </div>
        ) : toolId ? (
          <div className="bg-white rounded-lg shadow-md p-4 mb-6 animate-pulse">
            <div className="h-6 bg-gray-200 rounded w-1/3 mb-2" />
            <div className="h-4 bg-gray-200 rounded w-2/3" />
          </div>
        ) : null}

        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg mb-6">
            {error}
          </div>
        )}

        {/* Voice agent */}
        <VoiceAgent
          callState={callState}
          websocketUrl={websocketUrl}
          onStart={startVoiceCall}
          onEnd={handleCallEnded}
        />

        {/* Back link */}
        <Link
          to={`/tools?repo_id=${repoId || ''}`}
          className="inline-block mt-6 text-blue-600 hover:text-blue-700 transition"
        >
          ← Back to recommendations
        </Link>
      </div>
    </div>
  )
}
