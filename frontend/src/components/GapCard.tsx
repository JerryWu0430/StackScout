import { motion } from 'framer-motion'
import { Zap, AlertCircle, ShieldAlert } from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip'

interface GapCardProps {
  description: string
  severity?: 'low' | 'medium' | 'high'
}

const SEVERITY_CONFIG = {
  low: {
    icon: Zap,
    badge: 'info' as const,
    label: 'Low',
    border: 'border-l-info',
    bg: 'bg-info-muted',
  },
  medium: {
    icon: AlertCircle,
    badge: 'warning' as const,
    label: 'Medium',
    border: 'border-l-warning',
    bg: 'bg-warning-muted',
  },
  high: {
    icon: ShieldAlert,
    badge: 'destructive' as const,
    label: 'High',
    border: 'border-l-destructive',
    bg: 'bg-destructive-muted',
  },
}

export default function GapCard({ description, severity = 'medium' }: GapCardProps) {
  const config = SEVERITY_CONFIG[severity]
  const Icon = config.icon

  return (
    <TooltipProvider>
      <Tooltip>
        <TooltipTrigger asChild>
          <motion.div
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.2 }}
            className={`p-2.5 rounded border border-l-2 ${config.border} ${config.bg} cursor-default`}
          >
            <div className="flex items-start gap-2">
              <Icon className="size-3.5 shrink-0 mt-0.5 text-foreground/70" />
              <div className="flex-1 min-w-0">
                <p className="text-xs text-foreground">{description}</p>
              </div>
              <Badge variant={config.badge} className="shrink-0 text-xs">
                {config.label}
              </Badge>
            </div>
          </motion.div>
        </TooltipTrigger>
        <TooltipContent side="top" className="max-w-xs">
          <p className="text-xs">{description}</p>
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  )
}
