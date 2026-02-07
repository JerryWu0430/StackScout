import { useState, useEffect, useRef } from 'react'

type CallState = 'idle' | 'connecting' | 'active' | 'ended'

interface TranscriptEntry {
  speaker: 'user' | 'agent'
  text: string
  timestamp: number
}

interface VoiceAgentProps {
  callState: CallState
  websocketUrl: string | null
  onStart: () => void
  onEnd: (recordingUrl?: string) => void
}

export default function VoiceAgent({ callState, websocketUrl, onStart, onEnd }: VoiceAgentProps) {
  const [isMuted, setIsMuted] = useState(false)
  const [transcript, setTranscript] = useState<TranscriptEntry[]>([])
  const [audioLevels, setAudioLevels] = useState<number[]>(Array(12).fill(0))

  const wsRef = useRef<WebSocket | null>(null)
  const audioContextRef = useRef<AudioContext | null>(null)
  const analyserRef = useRef<AnalyserNode | null>(null)
  const mediaStreamRef = useRef<MediaStream | null>(null)
  const animationFrameRef = useRef<number | null>(null)
  const transcriptEndRef = useRef<HTMLDivElement>(null)

  // Scroll transcript to bottom
  useEffect(() => {
    transcriptEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [transcript])

  // Setup audio stream and WebSocket
  useEffect(() => {
    if (callState !== 'active' || !websocketUrl) return

    let isCancelled = false

    const updateAudioLevels = () => {
      if (isCancelled || !analyserRef.current) return

      const dataArray = new Uint8Array(analyserRef.current.frequencyBinCount)
      analyserRef.current.getByteFrequencyData(dataArray)

      // Sample 12 frequency bands
      const bands = 12
      const bandSize = Math.floor(dataArray.length / bands)
      const levels = Array(bands)
        .fill(0)
        .map((_, i) => {
          const start = i * bandSize
          const slice = dataArray.slice(start, start + bandSize)
          const avg = slice.reduce((a, b) => a + b, 0) / slice.length
          return Math.min(1, avg / 128) // Normalize to 0-1
        })

      setAudioLevels(levels)
      animationFrameRef.current = requestAnimationFrame(updateAudioLevels)
    }

    const setupAudio = async () => {
      try {
        // Get microphone access
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
        if (isCancelled) {
          stream.getTracks().forEach((t) => t.stop())
          return
        }
        mediaStreamRef.current = stream

        // Setup audio analyzer for visualization
        audioContextRef.current = new AudioContext()
        analyserRef.current = audioContextRef.current.createAnalyser()
        analyserRef.current.fftSize = 256

        const source = audioContextRef.current.createMediaStreamSource(stream)
        source.connect(analyserRef.current)

        // Start visualization
        updateAudioLevels()

        // Connect WebSocket
        const ws = new WebSocket(websocketUrl)
        wsRef.current = ws

        ws.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data)

            // Handle transcript messages
            if (data.type === 'transcript') {
              setTranscript((prev) => [
                ...prev,
                {
                  speaker: data.speaker || 'agent',
                  text: data.text,
                  timestamp: Date.now(),
                },
              ])
            }

            // Handle audio data from agent (for playback)
            if (data.type === 'audio' && data.audio) {
              // In production, decode and play audio
              // For now, handled by ElevenLabs client
            }

            // Handle call ended
            if (data.type === 'end') {
              onEnd(data.recording_url)
            }
          } catch {
            // Non-JSON message, ignore
          }
        }

        ws.onerror = () => {
          console.error('WebSocket error')
        }

        ws.onclose = () => {
          if (!isCancelled) {
            onEnd()
          }
        }
      } catch (err) {
        console.error('Failed to setup audio:', err)
        if (!isCancelled) {
          onEnd()
        }
      }
    }

    setupAudio()

    return () => {
      isCancelled = true
      // Cleanup
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current)
      }
      if (wsRef.current) {
        wsRef.current.close()
      }
      if (mediaStreamRef.current) {
        mediaStreamRef.current.getTracks().forEach((track) => track.stop())
      }
      if (audioContextRef.current) {
        audioContextRef.current.close()
      }
    }
  }, [callState, websocketUrl, onEnd])

  // Handle mute toggle
  useEffect(() => {
    if (mediaStreamRef.current) {
      mediaStreamRef.current.getAudioTracks().forEach((track) => {
        track.enabled = !isMuted
      })
    }
  }, [isMuted])

  const handleEndCall = () => {
    if (wsRef.current) {
      wsRef.current.send(JSON.stringify({ type: 'end' }))
      wsRef.current.close()
    }
    onEnd()
  }

  return (
    <div className="bg-white p-6 rounded-lg shadow-md">
      {/* Audio visualization */}
      <div className="flex items-end justify-center gap-1 h-24 mb-4">
        {callState === 'active' ? (
          audioLevels.map((level, i) => (
            <div
              key={i}
              className="w-2 bg-blue-500 rounded-full transition-all duration-75"
              style={{ height: `${Math.max(8, level * 80)}px` }}
            />
          ))
        ) : (
          <div
            className={`w-24 h-24 rounded-full flex items-center justify-center ${
              callState === 'connecting' ? 'bg-yellow-100 animate-pulse' : 'bg-gray-100'
            }`}
          >
            <svg
              className={`w-12 h-12 ${
                callState === 'connecting' ? 'text-yellow-500' : 'text-gray-400'
              }`}
              fill="currentColor"
              viewBox="0 0 24 24"
            >
              <path d="M12 14c1.66 0 3-1.34 3-3V5c0-1.66-1.34-3-3-3S9 3.34 9 5v6c0 1.66 1.34 3 3 3z" />
              <path d="M17 11c0 2.76-2.24 5-5 5s-5-2.24-5-5H5c0 3.53 2.61 6.43 6 6.92V21h2v-3.08c3.39-.49 6-3.39 6-6.92h-2z" />
            </svg>
          </div>
        )}
      </div>

      {/* Status text */}
      <h3 className="text-lg font-semibold text-gray-800 mb-2 text-center">
        {callState === 'idle' && 'Ready to Start'}
        {callState === 'connecting' && 'Connecting...'}
        {callState === 'active' && (isMuted ? 'Muted' : 'Listening...')}
        {callState === 'ended' && 'Call Ended'}
      </h3>
      <p className="text-gray-600 text-sm mb-4 text-center">
        {callState === 'idle' && 'Start a voice call with our AI to schedule your demo'}
        {callState === 'connecting' && 'Setting up secure connection...'}
        {callState === 'active' && 'Speak naturally to schedule your demo'}
        {callState === 'ended' && 'Processing your conversation...'}
      </p>

      {/* Transcript */}
      {callState === 'active' && transcript.length > 0 && (
        <div className="bg-gray-50 rounded-lg p-3 mb-4 max-h-48 overflow-y-auto">
          <h4 className="text-xs font-semibold text-gray-500 mb-2 uppercase">Transcript</h4>
          <div className="space-y-2">
            {transcript.map((entry, i) => (
              <div
                key={i}
                className={`text-sm ${
                  entry.speaker === 'user' ? 'text-blue-700' : 'text-gray-700'
                }`}
              >
                <span className="font-medium">
                  {entry.speaker === 'user' ? 'You: ' : 'Agent: '}
                </span>
                {entry.text}
              </div>
            ))}
            <div ref={transcriptEndRef} />
          </div>
        </div>
      )}

      {/* Controls */}
      <div className="flex justify-center gap-3">
        {callState === 'idle' && (
          <button
            onClick={onStart}
            className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition flex items-center gap-2"
          >
            <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
              <path d="M12 14c1.66 0 3-1.34 3-3V5c0-1.66-1.34-3-3-3S9 3.34 9 5v6c0 1.66 1.34 3 3 3z" />
              <path d="M17 11c0 2.76-2.24 5-5 5s-5-2.24-5-5H5c0 3.53 2.61 6.43 6 6.92V21h2v-3.08c3.39-.49 6-3.39 6-6.92h-2z" />
            </svg>
            Start Voice Call
          </button>
        )}

        {callState === 'connecting' && (
          <button disabled className="px-6 py-2 bg-yellow-500 text-white rounded-lg flex items-center gap-2">
            <svg className="animate-spin w-5 h-5" viewBox="0 0 24 24">
              <circle
                className="opacity-25"
                cx="12"
                cy="12"
                r="10"
                stroke="currentColor"
                strokeWidth="4"
                fill="none"
              />
              <path
                className="opacity-75"
                fill="currentColor"
                d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
              />
            </svg>
            Connecting...
          </button>
        )}

        {callState === 'active' && (
          <>
            {/* Mute button */}
            <button
              onClick={() => setIsMuted(!isMuted)}
              className={`px-4 py-2 rounded-lg transition flex items-center gap-2 ${
                isMuted
                  ? 'bg-yellow-100 text-yellow-700 hover:bg-yellow-200'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              {isMuted ? (
                <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M19 11h-1.7c0 .74-.16 1.43-.43 2.05l1.23 1.23c.56-.98.9-2.09.9-3.28zm-4.02.17c0-.06.02-.11.02-.17V5c0-1.66-1.34-3-3-3S9 3.34 9 5v.18l5.98 5.99zM4.27 3L3 4.27l6.01 6.01V11c0 1.66 1.33 3 2.99 3 .22 0 .44-.03.65-.08l1.66 1.66c-.71.33-1.5.52-2.31.52-2.76 0-5.3-2.1-5.3-5.1H5c0 3.41 2.72 6.23 6 6.72V21h2v-3.28c.91-.13 1.77-.45 2.54-.9L19.73 21 21 19.73 4.27 3z" />
                </svg>
              ) : (
                <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M12 14c1.66 0 3-1.34 3-3V5c0-1.66-1.34-3-3-3S9 3.34 9 5v6c0 1.66 1.34 3 3 3z" />
                  <path d="M17 11c0 2.76-2.24 5-5 5s-5-2.24-5-5H5c0 3.53 2.61 6.43 6 6.92V21h2v-3.08c3.39-.49 6-3.39 6-6.92h-2z" />
                </svg>
              )}
              {isMuted ? 'Unmute' : 'Mute'}
            </button>

            {/* End call button */}
            <button
              onClick={handleEndCall}
              className="px-4 py-2 bg-red-500 text-white rounded-lg hover:bg-red-600 transition flex items-center gap-2"
            >
              <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                <path d="M12 9c-1.6 0-3.15.25-4.6.72v3.1c0 .39-.23.74-.56.9-.98.49-1.87 1.12-2.66 1.85-.18.18-.43.28-.7.28-.28 0-.53-.11-.71-.29L.29 13.08c-.18-.17-.29-.42-.29-.7 0-.28.11-.53.29-.71C3.34 8.78 7.46 7 12 7s8.66 1.78 11.71 4.67c.18.18.29.43.29.71 0 .28-.11.53-.29.71l-2.48 2.48c-.18.18-.43.29-.71.29-.27 0-.52-.11-.7-.28-.79-.74-1.69-1.36-2.67-1.85-.33-.16-.56-.5-.56-.9v-3.1C15.15 9.25 13.6 9 12 9z" />
              </svg>
              End Call
            </button>
          </>
        )}
      </div>
    </div>
  )
}
