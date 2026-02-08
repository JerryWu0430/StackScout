import { useConversation } from '@elevenlabs/react'
import { useCallback, useEffect, useRef, useState } from 'react'

const AGENT_ID = 'agent_3101kgwzcp5wfwead4c3gqnre1rm'
const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export interface AgentMessage {
  id: string
  type: 'system' | 'agent' | 'user' | 'thinking'
  content: string
  timestamp: Date
}

interface UseAnalysisVoiceOptions {
  autoStart?: boolean
  repoId?: string
  toolId?: string
  toolName?: string
}

export default function useAnalysisVoice({
  autoStart = false,
  repoId,
  toolId,
  toolName,
}: UseAnalysisVoiceOptions = {}) {
  const hasAutoStarted = useRef(false)
  const [messages, setMessages] = useState<AgentMessage[]>([])
  const [conversationId, setConversationId] = useState<string | null>(null)
  const messageIdRef = useRef(0)

  const addMessage = useCallback((type: AgentMessage['type'], content: string) => {
    setMessages(prev => [...prev, {
      id: `msg-${++messageIdRef.current}`,
      type,
      content,
      timestamp: new Date(),
    }])
  }, [])

  // Link conversation to repo when it ends
  const linkConversation = useCallback(async (convId: string) => {
    if (!repoId || !convId) return
    try {
      await fetch(`${API_BASE}/api/voice/link-conversation`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ conversation_id: convId, repo_id: repoId }),
      })
      console.log('Conversation linked to repo:', repoId)
    } catch (err) {
      console.error('Failed to link conversation:', err)
    }
  }, [repoId])

  const conversation = useConversation({
    onConnect: ({ conversationId: convId }) => {
      console.log('Voice connected, conversation:', convId)
      if (convId) setConversationId(convId)
      addMessage('system', 'Connected to voice agent')
      addMessage('thinking', 'Ready to assist...')
    },
    onDisconnect: () => {
      console.log('Voice disconnected')
      addMessage('system', 'Disconnected from voice agent')
      // Link conversation to repo on disconnect
      if (conversationId && repoId) {
        linkConversation(conversationId)
      }
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
    setConversationId(null)
    addMessage('system', 'Requesting microphone access...')
    await navigator.mediaDevices.getUserMedia({ audio: true })
    addMessage('system', 'Microphone access granted')
    addMessage('thinking', 'Connecting to ElevenLabs agent...')

    // Pass dynamic variables for client tools
    const dynamicVariables: Record<string, string> = {}
    if (repoId) dynamicVariables.repo_id = repoId
    if (toolId) dynamicVariables.tool_id = toolId
    if (toolName) dynamicVariables.tool_name = toolName

    await conversation.startSession({
      agentId: AGENT_ID,
      dynamicVariables,
    })
  }, [conversation, addMessage, repoId, toolId, toolName])

  const endCall = useCallback(async () => {
    addMessage('thinking', 'Ending conversation...')
    // Link before ending (in case onDisconnect doesn't fire)
    if (conversationId && repoId) {
      await linkConversation(conversationId)
    }
    await conversation.endSession()
  }, [conversation, addMessage, conversationId, repoId, linkConversation])

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
    conversationId,
    startCall,
    endCall,
  }
}
