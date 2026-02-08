import { Orb, type AgentState } from '@/components/ui/orb'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { Spinner } from '@/components/ui/spinner'
import AgentTerminal from '@/components/AgentTerminal'
import type { AgentMessage } from '@/hooks/useAnalysisVoice'

interface VoiceAgentProps {
  status: 'connected' | 'disconnected' | 'connecting' | 'disconnecting'
  isSpeaking: boolean
  messages?: AgentMessage[]
  onStart: () => void
  onEnd: () => void
}

export default function VoiceAgent({ status, isSpeaking, messages = [], onStart, onEnd }: VoiceAgentProps) {
  const isConnected = status === 'connected'
  const isConnecting = status === 'connecting'
  const hasActivity = isConnected || isConnecting || messages.length > 0

  // Map to Orb's agentState
  const agentState: AgentState = isConnected
    ? (isSpeaking ? 'talking' : 'listening')
    : null

  return (
    <div className="space-y-4">
      <Card>
        <CardContent className="flex flex-col items-center">
          {/* Orb visualization */}
          <div className="w-32 h-32 mb-4">
            <Orb
              agentState={agentState}
              colors={['hsl(var(--primary))', 'hsl(var(--primary) / 0.7)']}
            />
          </div>

          {/* Status text */}
          <h3 className="text-lg font-semibold text-card-foreground mb-2 text-center">
            {!isConnected && !isConnecting && 'Ready to Start'}
            {isConnecting && 'Connecting...'}
            {isConnected && (isSpeaking ? 'Speaking...' : 'Listening...')}
          </h3>
          <p className="text-muted-foreground text-sm mb-4 text-center">
            {!isConnected && !isConnecting && 'Voice agent will explain your stack analysis'}
            {isConnecting && 'Setting up secure connection...'}
            {isConnected && 'Ask questions about your stack or recommendations'}
          </p>

          {/* Controls */}
          <div className="flex justify-center gap-3">
            {!isConnected && !isConnecting && (
              <Button onClick={onStart} size="lg">
                <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M12 14c1.66 0 3-1.34 3-3V5c0-1.66-1.34-3-3-3S9 3.34 9 5v6c0 1.66 1.34 3 3 3z" />
                  <path d="M17 11c0 2.76-2.24 5-5 5s-5-2.24-5-5H5c0 3.53 2.61 6.43 6 6.92V21h2v-3.08c3.39-.49 6-3.39 6-6.92h-2z" />
                </svg>
                Start Voice Call
              </Button>
            )}

            {isConnecting && (
              <Button disabled className="bg-warning text-warning-foreground hover:bg-warning" size="lg">
                <Spinner className="w-5 h-5" />
                Connecting...
              </Button>
            )}

            {isConnected && (
              <Button onClick={onEnd} variant="destructive" size="lg">
                <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M12 9c-1.6 0-3.15.25-4.6.72v3.1c0 .39-.23.74-.56.9-.98.49-1.87 1.12-2.66 1.85-.18.18-.43.28-.7.28-.28 0-.53-.11-.71-.29L.29 13.08c-.18-.17-.29-.42-.29-.7 0-.28.11-.53.29-.71C3.34 8.78 7.46 7 12 7s8.66 1.78 11.71 4.67c.18.18.29.43.29.71 0 .28-.11.53-.29.71l-2.48 2.48c-.18.18-.43.29-.71.29-.27 0-.52-.11-.7-.28-.79-.74-1.69-1.36-2.67-1.85-.33-.16-.56-.5-.56-.9v-3.1C15.15 9.25 13.6 9 12 9z" />
                </svg>
                End Call
              </Button>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Agent Terminal - shows activity log */}
      {hasActivity && (
        <AgentTerminal messages={messages} className="max-w-full" />
      )}
    </div>
  )
}
