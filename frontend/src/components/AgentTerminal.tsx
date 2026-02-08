import { useEffect, useRef } from 'react'
import { Terminal, TypingAnimation, AnimatedSpan } from '@/components/ui/terminal'
import type { AgentMessage } from '@/hooks/useAnalysisVoice'

interface AgentTerminalProps {
  messages: AgentMessage[]
  className?: string
}

function getMessagePrefix(type: AgentMessage['type']): string {
  switch (type) {
    case 'system': return '>'
    case 'agent': return '[agent]'
    case 'user': return '[you]'
    case 'thinking': return '...'
  }
}

function getMessageStyle(type: AgentMessage['type']): string {
  switch (type) {
    case 'system': return 'text-muted-foreground'
    case 'agent': return 'text-primary'
    case 'user': return 'text-foreground'
    case 'thinking': return 'text-muted-foreground italic'
  }
}

export default function AgentTerminal({ messages, className }: AgentTerminalProps) {
  const scrollRef = useRef<HTMLDivElement>(null)

  // Auto-scroll to bottom on new messages
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight
    }
  }, [messages])

  if (messages.length === 0) {
    return (
      <Terminal sequence={false} className={className}>
        <AnimatedSpan className="text-muted-foreground">
          {'> Waiting to start...'}
        </AnimatedSpan>
      </Terminal>
    )
  }

  return (
    <Terminal sequence={false} className={className}>
      <div ref={scrollRef} className="max-h-[300px] overflow-y-auto space-y-1">
        {messages.map((msg, idx) => {
          const isLatest = idx === messages.length - 1
          const prefix = getMessagePrefix(msg.type)
          const style = getMessageStyle(msg.type)
          const content = `${prefix} ${msg.content}`

          // Use typing animation for the latest thinking message
          if (isLatest && msg.type === 'thinking') {
            return (
              <TypingAnimation
                key={msg.id}
                className={style}
                duration={30}
                delay={0}
                startOnView={false}
              >
                {content}
              </TypingAnimation>
            )
          }

          return (
            <AnimatedSpan key={msg.id} className={style}>
              {content}
            </AnimatedSpan>
          )
        })}
      </div>
    </Terminal>
  )
}
