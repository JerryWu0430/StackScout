import { useConversation } from '@elevenlabs/react'
import { useCallback, useEffect, useRef, useState } from 'react'

const AGENT_ID = 'agent_3101kgwzcp5wfwead4c3gqnre1rm'

export interface AgentMessage {
  id: string
  type: 'system' | 'agent' | 'user' | 'thinking'
  content: string
  timestamp: Date
}

interface UseAnalysisVoiceOptions {
  autoStart?: boolean
}

export default function useAnalysisVoice({ autoStart = false }: UseAnalysisVoiceOptions = {}) {
  const hasAutoStarted = useRef(false)
  const [messages, setMessages] = useState<AgentMessage[]>([])
  const messageIdRef = useRef(0)

  const addMessage = useCallback((type: AgentMessage['type'], content: string) => {
    setMessages(prev => [...prev, {
      id: `msg-${++messageIdRef.current}`,
      type,
      content,
      timestamp: new Date(),
    }])
  }, [])

  const conversation = useConversation({
    onConnect: () => {
      console.log('Voice connected')
      addMessage('system', 'Connected to voice agent')
      addMessage('thinking', 'Ready to assist...')
    },
    onDisconnect: () => {
      console.log('Voice disconnected')
      addMessage('system', 'Disconnected from voice agent')
    },
    onError: (error) => {
      console.error('Voice error:', error)
      addMessage('system', `Error: ${String(error)}`)
    },
    onModeChange: (mode) => {
      // Mode changes between 'speaking' and 'listening'
      if (mode.mode === 'speaking') {
        addMessage('thinking', 'Agent is responding...')
      } else if (mode.mode === 'listening') {
        addMessage('thinking', 'Listening for your input...')
      }
    },
  })

  const startCall = useCallback(async () => {
    setMessages([]) // Clear previous messages
    addMessage('system', 'Requesting microphone access...')
    await navigator.mediaDevices.getUserMedia({ audio: true })
    addMessage('system', 'Microphone access granted')
    addMessage('thinking', 'Connecting to ElevenLabs agent...')
    await conversation.startSession({ agentId: AGENT_ID, connectionType: 'webrtc' })
  }, [conversation, addMessage])

  const endCall = useCallback(async () => {
    addMessage('thinking', 'Ending conversation...')
    await conversation.endSession()
  }, [conversation, addMessage])

  // Auto-start
  useEffect(() => {
    if (autoStart && !hasAutoStarted.current) {
      hasAutoStarted.current = true
      startCall()
    }
  }, [autoStart, startCall])

  // Add thinking messages based on state changes
  useEffect(() => {
    if (conversation.isSpeaking) {
      addMessage('thinking', 'Processing response...')
    }
  }, [conversation.isSpeaking, addMessage])

  return {
    status: conversation.status,
    isSpeaking: conversation.isSpeaking,
    messages,
    startCall,
    endCall,
  }
}
