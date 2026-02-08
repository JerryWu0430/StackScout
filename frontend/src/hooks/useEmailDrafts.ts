import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import type { DraftEmail, TimeSlot } from '@/types/api'

const API_BASE = '/api/email-drafts'

async function fetchDrafts(repoId: string): Promise<DraftEmail[]> {
  const res = await fetch(`${API_BASE}/repo/${repoId}`)
  if (!res.ok) throw new Error('Failed to fetch drafts')
  return res.json()
}

async function createDraft(repoId: string, toolId: string): Promise<DraftEmail> {
  const res = await fetch(API_BASE, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ repo_id: repoId, tool_id: toolId }),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(err.detail || 'Failed to create draft')
  }
  return res.json()
}

async function updateDraft(
  draftId: string,
  data: Partial<{ subject: string; body: string; to_email: string; to_name: string; selected_time: TimeSlot }>
): Promise<DraftEmail> {
  const res = await fetch(`${API_BASE}/${draftId}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  })
  if (!res.ok) throw new Error('Failed to update draft')
  return res.json()
}

async function deleteDraft(draftId: string): Promise<void> {
  const res = await fetch(`${API_BASE}/${draftId}`, { method: 'DELETE' })
  if (!res.ok) throw new Error('Failed to delete draft')
}

async function sendDraft(draftId: string): Promise<{ success: boolean; email_id?: string }> {
  const res = await fetch(`${API_BASE}/${draftId}/send`, { method: 'POST' })
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(err.detail || 'Failed to send email')
  }
  return res.json()
}

async function batchSend(draftIds: string[]): Promise<{ sent: number; failed: number; sent_ids: string[]; failed_ids: string[] }> {
  const res = await fetch(`${API_BASE}/batch-send`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ draft_ids: draftIds }),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(err.detail || 'Failed to send emails')
  }
  return res.json()
}

export function useEmailDrafts(repoId: string | undefined) {
  const queryClient = useQueryClient()
  const queryKey = ['email-drafts', repoId]

  const draftsQuery = useQuery({
    queryKey,
    queryFn: () => fetchDrafts(repoId!),
    enabled: !!repoId,
    staleTime: 30_000,
  })

  const createMutation = useMutation({
    mutationFn: ({ toolId }: { toolId: string }) => createDraft(repoId!, toolId),
    onSuccess: () => queryClient.invalidateQueries({ queryKey }),
  })

  const updateMutation = useMutation({
    mutationFn: ({ draftId, data }: { draftId: string; data: Parameters<typeof updateDraft>[1] }) =>
      updateDraft(draftId, data),
    onSuccess: () => queryClient.invalidateQueries({ queryKey }),
  })

  const deleteMutation = useMutation({
    mutationFn: deleteDraft,
    onSuccess: () => queryClient.invalidateQueries({ queryKey }),
  })

  const sendMutation = useMutation({
    mutationFn: sendDraft,
    onSuccess: () => queryClient.invalidateQueries({ queryKey }),
  })

  const batchSendMutation = useMutation({
    mutationFn: batchSend,
    onSuccess: () => queryClient.invalidateQueries({ queryKey }),
  })

  return {
    drafts: draftsQuery.data ?? [],
    isLoading: draftsQuery.isLoading,
    error: draftsQuery.error,
    createDraft: createMutation.mutateAsync,
    updateDraft: updateMutation.mutateAsync,
    deleteDraft: deleteMutation.mutateAsync,
    sendDraft: sendMutation.mutateAsync,
    batchSend: batchSendMutation.mutateAsync,
    isCreating: createMutation.isPending,
    isSending: sendMutation.isPending || batchSendMutation.isPending,
  }
}
