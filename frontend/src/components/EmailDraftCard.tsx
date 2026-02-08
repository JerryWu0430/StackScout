import { Mail, Send, Trash2, Edit2, Clock, CheckCircle, XCircle, AlertCircle } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Checkbox } from '@/components/ui/checkbox'
import { GlowingEffect } from '@/components/ui/glowing-effect'
import type { DraftEmail } from '@/types/api'

interface EmailDraftCardProps {
  draft: DraftEmail
  selected?: boolean
  onSelect?: (selected: boolean) => void
  onEdit?: () => void
  onDelete?: () => void
  onSend?: () => void
  isSending?: boolean
}

function getStatusBadge(status: DraftEmail['status']) {
  switch (status) {
    case 'draft':
      return <Badge variant="outline" className="text-muted-foreground"><Edit2 className="size-3 mr-1" />Draft</Badge>
    case 'ready':
      return <Badge variant="secondary" className="text-primary"><Clock className="size-3 mr-1" />Ready</Badge>
    case 'sent':
      return <Badge className="bg-success text-success-foreground"><CheckCircle className="size-3 mr-1" />Sent</Badge>
    case 'failed':
      return <Badge variant="destructive"><XCircle className="size-3 mr-1" />Failed</Badge>
    default:
      return null
  }
}

export default function EmailDraftCard({
  draft,
  selected = false,
  onSelect,
  onEdit,
  onDelete,
  onSend,
  isSending = false,
}: EmailDraftCardProps) {
  const canSend = draft.status !== 'sent' && draft.to_email

  return (
    <Card className={`relative ${selected ? 'ring-2 ring-primary' : ''}`}>
      <GlowingEffect glow />
      <CardContent className="space-y-3">
        <div className="flex items-start gap-3">
          {onSelect && (
            <Checkbox
              checked={selected}
              onCheckedChange={onSelect}
              disabled={draft.status === 'sent'}
              className="mt-1"
            />
          )}

          <div className="flex-1 min-w-0">
            <div className="flex items-center justify-between gap-2">
              <div className="flex items-center gap-2 min-w-0">
                <Mail className="size-4 text-muted-foreground flex-shrink-0" />
                <span className="font-medium truncate">{draft.tool_name || 'Unknown Tool'}</span>
              </div>
              {getStatusBadge(draft.status)}
            </div>

            <p className="text-sm text-muted-foreground mt-1 truncate">
              To: {draft.to_email || <span className="text-warning">No email set</span>}
              {draft.to_name && ` (${draft.to_name})`}
            </p>
          </div>
        </div>

        <div className="bg-muted/50 rounded-md p-3 space-y-1">
          <p className="text-sm font-medium">{draft.subject}</p>
          <p className="text-xs text-muted-foreground line-clamp-2">{draft.body}</p>
        </div>

        {draft.selected_time && (
          <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
            <Clock className="size-3" />
            <span>Proposed: {draft.selected_time.formatted}</span>
          </div>
        )}

        {!draft.to_email && (
          <div className="flex items-center gap-1.5 text-xs text-warning">
            <AlertCircle className="size-3" />
            <span>Email not found - please add manually</span>
          </div>
        )}

        <div className="flex gap-2 pt-1">
          {draft.status !== 'sent' && (
            <>
              <Button variant="outline" size="sm" onClick={onEdit}>
                <Edit2 className="size-3.5 mr-1" />
                Edit
              </Button>
              {canSend && (
                <Button size="sm" onClick={onSend} disabled={isSending}>
                  <Send className="size-3.5 mr-1" />
                  {isSending ? 'Sending...' : 'Send'}
                </Button>
              )}
              <Button variant="ghost" size="sm" onClick={onDelete} className="ml-auto text-destructive hover:text-destructive">
                <Trash2 className="size-3.5" />
              </Button>
            </>
          )}
          {draft.status === 'sent' && draft.sent_at && (
            <span className="text-xs text-muted-foreground">
              Sent {new Date(draft.sent_at).toLocaleDateString()}
            </span>
          )}
        </div>
      </CardContent>
    </Card>
  )
}
