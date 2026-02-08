import { useConversation } from '@elevenlabs/react'
import { useCallback, useEffect, useRef } from 'react'

const AGENT_ID = 'agent_3101kgwzcp5wfwead4c3gqnre1rm'

interface UseAnalysisVoiceOptions {
  autoStart?: boolean
}

export default function useAnalysisVoice({ autoStart = false }: UseAnalysisVoiceOptions = {}) {
  const hasAutoStarted = useRef(false)

  const conversation = useConversation({
    onConnect: () => console.log('Voice connected'),
    onDisconnect: () => console.log('Voice disconnected'),
    onError: (error) => console.error('Voice error:', error),
  })

  const startCall = useCallback(async () => {
    await navigator.mediaDevices.getUserMedia({ audio: true })
    await conversation.startSession({ agentId: AGENT_ID, connectionType: 'webrtc' })
  }, [conversation])

  const endCall = useCallback(async () => {
    await conversation.endSession()
  }, [conversation])

  // Auto-start
  useEffect(() => {
    if (autoStart && !hasAutoStarted.current) {
      hasAutoStarted.current = true
      startCall()
    }
  }, [autoStart, startCall])

  return {
    status: conversation.status,
    isSpeaking: conversation.isSpeaking,
    startCall,
    endCall,
  }
}
