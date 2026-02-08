import { useState, useEffect } from 'react'
import { Clock, Send } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'
import { Badge } from '@/components/ui/badge'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from '@/components/ui/dialog'
import type { DraftEmail, TimeSlot } from '@/types/api'

interface EmailDraftModalProps {
  draft: DraftEmail | null
  open: boolean
  onOpenChange: (open: boolean) => void
  onSave: (data: { subject: string; body: string; to_email: string; to_name: string; selected_time?: TimeSlot }) => Promise<void>
  onSend?: () => Promise<void>
  isSaving?: boolean
  isSending?: boolean
}

export default function EmailDraftModal({
  draft,
  open,
  onOpenChange,
  onSave,
  onSend,
  isSaving = false,
  isSending = false,
}: EmailDraftModalProps) {
  const [subject, setSubject] = useState('')
  const [body, setBody] = useState('')
  const [toEmail, setToEmail] = useState('')
  const [toName, setToName] = useState('')
  const [selectedTime, setSelectedTime] = useState<TimeSlot | null>(null)

  useEffect(() => {
    if (draft) {
      setSubject(draft.subject)
      setBody(draft.body)
      setToEmail(draft.to_email || '')
      setToName(draft.to_name || '')
      setSelectedTime(draft.selected_time)
    }
  }, [draft])

  const handleSave = async () => {
    await onSave({
      subject,
      body,
      to_email: toEmail,
      to_name: toName,
      selected_time: selectedTime || undefined,
    })
  }

  const handleSaveAndSend = async () => {
    await onSave({
      subject,
      body,
      to_email: toEmail,
      to_name: toName,
      selected_time: selectedTime || undefined,
    })
    if (onSend) {
      await onSend()
    }
  }

  if (!draft) return null

  const canSend = toEmail && draft.status !== 'sent'

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl" onClose={() => onOpenChange(false)}>
        <DialogHeader>
          <DialogTitle>Edit Email Draft</DialogTitle>
          <DialogDescription>
            Demo request for {draft.tool_name || 'Unknown Tool'}
          </DialogDescription>
        </DialogHeader>

        <div className="px-6 space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-1.5">
              <label className="text-sm font-medium">Recipient Email</label>
              <Input
                value={toEmail}
                onChange={(e) => setToEmail(e.target.value)}
                placeholder="sales@example.com"
                type="email"
              />
            </div>
            <div className="space-y-1.5">
              <label className="text-sm font-medium">Recipient Name (optional)</label>
              <Input
                value={toName}
                onChange={(e) => setToName(e.target.value)}
                placeholder="Sales Team"
              />
            </div>
          </div>

          <div className="space-y-1.5">
            <label className="text-sm font-medium">Subject</label>
            <Input
              value={subject}
              onChange={(e) => setSubject(e.target.value)}
              placeholder="Demo request..."
            />
          </div>

          <div className="space-y-1.5">
            <label className="text-sm font-medium">Body</label>
            <Textarea
              value={body}
              onChange={(e) => setBody(e.target.value)}
              rows={10}
              className="font-mono text-sm"
            />
          </div>

          {/* Time Slot Selection */}
          {draft.suggested_times.length > 0 && (
            <div className="space-y-2">
              <label className="text-sm font-medium flex items-center gap-1.5">
                <Clock className="size-4" />
                Suggested Meeting Times
              </label>
              <div className="flex flex-wrap gap-2">
                {draft.suggested_times.slice(0, 6).map((slot, idx) => (
                  <Badge
                    key={idx}
                    variant={selectedTime?.start === slot.start ? 'default' : 'outline'}
                    className="cursor-pointer hover:bg-muted"
                    onClick={() => setSelectedTime(slot)}
                  >
                    {slot.formatted}
                  </Badge>
                ))}
              </div>
              {selectedTime && (
                <p className="text-xs text-muted-foreground">
                  Selected: {selectedTime.formatted}
                </p>
              )}
            </div>
          )}
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Cancel
          </Button>
          <Button variant="secondary" onClick={handleSave} disabled={isSaving}>
            {isSaving ? 'Saving...' : 'Save Draft'}
          </Button>
          {canSend && onSend && (
            <Button onClick={handleSaveAndSend} disabled={isSaving || isSending}>
              <Send className="size-4 mr-1.5" />
              {isSending ? 'Sending...' : 'Save & Send'}
            </Button>
          )}
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
