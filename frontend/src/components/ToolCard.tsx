import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'

interface Tool {
  id: number | string
  name: string
  category: string
  description?: string
  tags: string[]
}

interface ToolCardProps {
  tool: Tool
  suitabilityScore: number
  demoPriority: number
  explanation: string
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

export default function ToolCard({
  tool,
  suitabilityScore,
  demoPriority,
  explanation,
  onBookDemo,
}: ToolCardProps) {
  return (
    <Card>
      <CardContent className="space-y-4">
        <div className="flex justify-between items-start">
          <div>
            <h3 className="text-lg font-semibold text-card-foreground">{tool.name}</h3>
            <p className="text-muted-foreground text-sm">{tool.description}</p>
          </div>
          <div className="flex gap-2">
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

        <p className="text-muted-foreground text-sm italic">{explanation}</p>

        <Button onClick={onBookDemo} size="sm">
          Book Demo
        </Button>
      </CardContent>
    </Card>
  )
}
