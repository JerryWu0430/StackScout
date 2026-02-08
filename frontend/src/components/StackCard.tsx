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
    <Card>
      <CardContent>
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2">
            <div className={`p-1.5 rounded ${config.bg}`}>
              <Icon className="size-4 text-foreground/70" />
            </div>
            <h3 className="text-lg font-semibold text-card-foreground capitalize">{category}</h3>
          </div>
          {technologies.length > 0 && (
            <Badge variant="secondary">{technologies.length}</Badge>
          )}
        </div>
        {technologies.length > 0 ? (
          <div className="flex flex-wrap gap-2">
            {technologies.map((tech) => (
              <span
                key={tech}
                className="px-2 py-1 text-xs bg-muted text-muted-foreground rounded border border-border"
              >
                {tech}
              </span>
            ))}
          </div>
        ) : (
          <p className="text-muted-foreground text-sm italic">None detected</p>
        )}
      </CardContent>
    </Card>
  )
}
