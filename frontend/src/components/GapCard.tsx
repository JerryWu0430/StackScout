interface GapCardProps {
  description: string
  severity?: 'low' | 'medium' | 'high'
}

const SEVERITY_STYLES = {
  low: 'bg-yellow-50 border-yellow-200 text-yellow-800',
  medium: 'bg-orange-50 border-orange-200 text-orange-800',
  high: 'bg-red-50 border-red-200 text-red-800',
}

const SEVERITY_ICONS = {
  low: '⚡',
  medium: '⚠️',
  high: '🚨',
}

export default function GapCard({ description, severity = 'medium' }: GapCardProps) {
  return (
    <div className={`p-4 rounded-lg border ${SEVERITY_STYLES[severity]}`}>
      <div className="flex items-start gap-3">
        <span className="text-lg">{SEVERITY_ICONS[severity]}</span>
        <p className="text-sm">{description}</p>
      </div>
    </div>
  )
}
