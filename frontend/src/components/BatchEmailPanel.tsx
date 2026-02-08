import { useState } from 'react'
import { Send, Mail, CheckCircle, XCircle } from 'lucide-react'
import { motion } from 'framer-motion'
import { Button } from '@/components/ui/button'
import { Spinner } from '@/components/ui/spinner'
import EmailDraftCard from './EmailDraftCard'
import EmailDraftModal from './EmailDraftModal'
import { useEmailDrafts } from '@/hooks/useEmailDrafts'
import type { DraftEmail, TimeSlot } from '@/types/api'

interface BatchEmailPanelProps {
  repoId: string
}

export default function BatchEmailPanel({ repoId }: BatchEmailPanelProps) {
  const {
    drafts,
    isLoading,
    updateDraft,
    deleteDraft,
    sendDraft,
    batchSend,
    isSending,
  } = useEmailDrafts(repoId)

  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set())
  const [editingDraft, setEditingDraft] = useState<DraftEmail | null>(null)
  const [isSaving, setIsSaving] = useState(false)
  const [batchResult, setBatchResult] = useState<{ sent: number; failed: number } | null>(null)

  const pendingDrafts = drafts.filter((d) => d.status !== 'sent')
  const sentDrafts = drafts.filter((d) => d.status === 'sent')

  const selectedDrafts = pendingDrafts.filter((d) => selectedIds.has(d.id) && d.to_email)
  const canBatchSend = selectedDrafts.length > 0

  const toggleSelect = (draftId: string, selected: boolean) => {
    setSelectedIds((prev) => {
      const next = new Set(prev)
      if (selected) {
        next.add(draftId)
      } else {
        next.delete(draftId)
      }
      return next
    })
  }

  const selectAll = () => {
    const ids = pendingDrafts.filter((d) => d.to_email).map((d) => d.id)
    setSelectedIds(new Set(ids))
  }

  const deselectAll = () => {
    setSelectedIds(new Set())
  }

  const handleSave = async (data: {
    subject: string
    body: string
    to_email: string
    to_name: string
    selected_time?: TimeSlot
  }) => {
    if (!editingDraft) return
    setIsSaving(true)
    try {
      await updateDraft({ draftId: editingDraft.id, data })
    } finally {
      setIsSaving(false)
    }
  }

  const handleSendSingle = async (draftId: string) => {
    try {
      await sendDraft(draftId)
    } catch (err) {
      console.error('Send failed:', err)
    }
  }

  const handleBatchSend = async () => {
    if (!canBatchSend) return
    setBatchResult(null)
    try {
      const result = await batchSend(Array.from(selectedIds))
      setBatchResult({ sent: result.sent, failed: result.failed })
      setSelectedIds(new Set())
    } catch (err) {
      console.error('Batch send failed:', err)
    }
  }

  const handleDelete = async (draftId: string) => {
    try {
      await deleteDraft(draftId)
      setSelectedIds((prev) => {
        const next = new Set(prev)
        next.delete(draftId)
        return next
      })
    } catch (err) {
      console.error('Delete failed:', err)
    }
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Spinner className="size-8" />
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {/* Batch Actions Header */}
      {pendingDrafts.length > 0 && (
        <div className="flex items-center justify-between bg-muted/50 rounded-lg p-3">
          <div className="flex items-center gap-3">
            <Mail className="size-5 text-muted-foreground" />
            <span className="text-sm">
              {selectedIds.size} of {pendingDrafts.length} selected
            </span>
            <Button variant="link" size="sm" onClick={selectAll} className="text-xs px-0">
              Select All
            </Button>
            {selectedIds.size > 0 && (
              <Button variant="link" size="sm" onClick={deselectAll} className="text-xs px-0">
                Clear
              </Button>
            )}
          </div>

          <Button onClick={handleBatchSend} disabled={!canBatchSend || isSending} size="sm">
            <Send className="size-4 mr-1.5" />
            {isSending ? 'Sending...' : `Send ${selectedIds.size} Email${selectedIds.size !== 1 ? 's' : ''}`}
          </Button>
        </div>
      )}

      {/* Batch Result */}
      {batchResult && (
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className="flex items-center gap-4 bg-muted rounded-lg p-3"
        >
          <CheckCircle className="size-5 text-success" />
          <span className="text-sm">{batchResult.sent} sent successfully</span>
          {batchResult.failed > 0 && (
            <>
              <XCircle className="size-5 text-destructive" />
              <span className="text-sm text-destructive">{batchResult.failed} failed</span>
            </>
          )}
        </motion.div>
      )}

      {/* Empty State */}
      {drafts.length === 0 && (
        <div className="text-center py-12 text-muted-foreground">
          <Mail className="size-12 mx-auto mb-4 opacity-50" />
          <p>No email drafts yet</p>
          <p className="text-sm mt-1">Click "Draft Email" on a tool to create one</p>
        </div>
      )}

      {/* Pending Drafts */}
      {pendingDrafts.length > 0 && (
        <div className="space-y-3">
          <h3 className="text-sm font-medium text-muted-foreground">Pending ({pendingDrafts.length})</h3>
          {pendingDrafts.map((draft) => (
            <motion.div
              key={draft.id}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
            >
              <EmailDraftCard
                draft={draft}
                selected={selectedIds.has(draft.id)}
                onSelect={(sel) => toggleSelect(draft.id, sel)}
                onEdit={() => setEditingDraft(draft)}
                onDelete={() => handleDelete(draft.id)}
                onSend={() => handleSendSingle(draft.id)}
                isSending={isSending}
              />
            </motion.div>
          ))}
        </div>
      )}

      {/* Sent Drafts */}
      {sentDrafts.length > 0 && (
        <div className="space-y-3 mt-6">
          <h3 className="text-sm font-medium text-muted-foreground">Sent ({sentDrafts.length})</h3>
          {sentDrafts.map((draft) => (
            <EmailDraftCard
              key={draft.id}
              draft={draft}
            />
          ))}
        </div>
      )}

      {/* Edit Modal */}
      <EmailDraftModal
        draft={editingDraft}
        open={!!editingDraft}
        onOpenChange={(open) => !open && setEditingDraft(null)}
        onSave={handleSave}
        onSend={editingDraft ? () => handleSendSingle(editingDraft.id) : undefined}
        isSaving={isSaving}
        isSending={isSending}
      />
    </div>
  )
}
