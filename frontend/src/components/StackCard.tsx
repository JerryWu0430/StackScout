import { Monitor, Server, Database, Cloud, Package } from 'lucide-react'
import { Card, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'

interface StackCardProps {
  category: string
  technologies: string[]
}

const CATEGORY_CONFIG: Record<string, { icon: typeof Monitor; bg: string }> = {
  frontend: { icon: Monitor, bg: 'bg-info-muted' },
  backend: { icon: Server, bg: 'bg-success-muted' },
  database: { icon: Database, bg: 'bg-warning-muted' },
  infrastructure: { icon: Cloud, bg: 'bg-primary/10' },
}

const DEFAULT_CONFIG = { icon: Package, bg: 'bg-muted' }

export default function StackCard({ category, technologies }: StackCardProps) {
  const config = CATEGORY_CONFIG[category.toLowerCase()] || DEFAULT_CONFIG
  const Icon = config.icon

  return (
    <Card className="p-0">
      <CardContent className="p-3">
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center gap-1.5">
            <div className={`p-1 rounded ${config.bg}`}>
              <Icon className="size-3.5 text-foreground/70" />
            </div>
            <h3 className="text-sm font-semibold text-card-foreground capitalize">{category}</h3>
          </div>
          {technologies.length > 0 && (
            <Badge variant="secondary" className="text-xs">{technologies.length}</Badge>
          )}
        </div>
        {technologies.length > 0 ? (
          <div className="flex flex-wrap gap-1">
            {technologies.map((tech) => (
              <span
                key={tech}
                className="px-2 py-0.5 text-xs bg-muted text-muted-foreground rounded border border-border"
              >
                {tech}
              </span>
            ))}
          </div>
        ) : (
          <p className="text-muted-foreground text-xs italic">None detected</p>
        )}
      </CardContent>
    </Card>
  )
}
