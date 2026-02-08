import { ExternalLink } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import type { Tool, MatchReason } from '@/types/api'

interface ToolCardProps {
  tool: Tool
  suitabilityScore: number
  demoPriority: number
  explanation: string
  matchReasons?: MatchReason[]
  onBookDemo?: () => void
}

function getScoreColor(score: number): string {
  if (score >= 80) return 'bg-success'
  if (score >= 60) return 'bg-warning'
  return 'bg-destructive'
}

function getPriorityLabel(priority: number): string {
  if (priority <= 2) return 'High Priority'
  if (priority <= 3) return 'Medium Priority'
  return 'Low Priority'
}

function getPriorityColor(priority: number): string {
  if (priority <= 2) return 'bg-destructive-muted text-destructive'
  if (priority <= 3) return 'bg-warning-muted text-warning-foreground'
  return 'bg-muted text-muted-foreground'
}

function getReasonIcon(type: string): string {
  switch (type) {
    case 'industry': return '🏢'
    case 'keyword': return '🔑'
    case 'gap': return '🎯'
    case 'use_case': return '💡'
    default: return '✓'
  }
}

function getReasonLabel(type: string): string {
  switch (type) {
    case 'industry': return 'Industry fit'
    case 'keyword': return 'Keyword match'
    case 'gap': return 'Addresses gap'
    case 'use_case': return 'Use case match'
    default: return 'Match'
  }
}

function getSourceLabel(source: string | null | undefined): { label: string; color: string } | null {
  switch (source) {
    case 'product_hunt':
      return { label: 'Product Hunt', color: 'bg-orange-100 text-orange-700 dark:bg-orange-900 dark:text-orange-300' }
    case 'yc':
      return { label: 'Y Combinator', color: 'bg-orange-100 text-orange-600 dark:bg-orange-900 dark:text-orange-400' }
    case 'github':
      return { label: 'GitHub', color: 'bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-300' }
    default:
      return null
  }
}

function formatUrl(url: string): string {
  return url.replace(/^https?:\/\/(www\.)?/, '').replace(/\/$/, '')
}

export default function ToolCard({
  tool,
  suitabilityScore,
  demoPriority,
  explanation,
  matchReasons = [],
  onBookDemo,
}: ToolCardProps) {
  const sourceInfo = getSourceLabel(tool.source)

  return (
    <Card>
      <CardContent className="space-y-4">
        <div className="flex justify-between items-start">
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 flex-wrap">
              <h3 className="text-lg font-semibold text-card-foreground">{tool.name}</h3>
              {sourceInfo && (
                <span className={`text-xs px-2 py-0.5 rounded ${sourceInfo.color}`}>
                  {sourceInfo.label}
                </span>
              )}
            </div>
            <p className="text-muted-foreground text-sm mt-1">{tool.description}</p>
            {tool.url && (
              <a
                href={tool.url}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-1 text-sm text-primary hover:underline mt-1"
              >
                <ExternalLink className="size-3" />
                {formatUrl(tool.url)}
              </a>
            )}
          </div>
          <div className="flex gap-2 flex-shrink-0 ml-4">
            <span className={`text-xs px-2 py-1 rounded font-medium ${getPriorityColor(demoPriority)}`}>
              {getPriorityLabel(demoPriority)}
            </span>
            <span className="text-xs bg-muted text-muted-foreground px-2 py-1 rounded">
              {tool.category}
            </span>
          </div>
        </div>

        <div>
          <div className="flex justify-between text-sm mb-1">
            <span className="text-muted-foreground">Suitability Score</span>
            <span className="font-medium text-card-foreground">{Math.round(suitabilityScore)}%</span>
          </div>
          <div className="w-full bg-muted rounded-full h-2">
            <div
              className={`h-2 rounded-full ${getScoreColor(suitabilityScore)}`}
              style={{ width: `${suitabilityScore}%` }}
            />
          </div>
        </div>

        {/* Match Reasons */}
        {matchReasons.length > 0 && (
          <div className="flex flex-wrap gap-2">
            {matchReasons.map((reason, idx) => (
              <Badge
                key={idx}
                variant="outline"
                className="text-xs font-normal"
                title={`+${reason.score_contribution.toFixed(1)} points`}
              >
                <span className="mr-1">{getReasonIcon(reason.type)}</span>
                <span className="text-muted-foreground mr-1">{getReasonLabel(reason.type)}:</span>
                <span className="font-medium">{reason.matched}</span>
              </Badge>
            ))}
          </div>
        )}

        <p className="text-muted-foreground text-sm italic">{explanation}</p>

        <div className="flex gap-2">
          <Button onClick={onBookDemo} size="sm">
            Book Demo
          </Button>
          {tool.url && (
            <Button
              variant="outline"
              size="sm"
              asChild
            >
              <a href={tool.url} target="_blank" rel="noopener noreferrer">
                Visit Website
              </a>
            </Button>
          )}
        </div>
      </CardContent>
    </Card>
  )
}
