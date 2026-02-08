import { useEffect, useState } from 'react'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Spinner } from '@/components/ui/spinner'

interface BookingInfo {
  toolId: string
  toolName: string
  bookingId: string
}

interface BookingStatus {
  id: string
  status: string
  service_type: string
  calls: Array<{
    id: string
    status: string
    providers?: { name: string; phone: string }
  }>
  booking?: {
    datetime: string
    confirmation_number?: string
    providers?: { name: string; phone: string; address?: string }
  }
}

interface CallStatusTabProps {
  booking: BookingInfo
  onComplete?: () => void
}

export default function CallStatusTab({ booking, onComplete }: CallStatusTabProps) {
  const [status, setStatus] = useState<BookingStatus | null>(null)
  const [error] = useState<string | null>(null)

  // Poll for status updates
  useEffect(() => {
    if (!booking.bookingId) return

    const fetchStatus = async () => {
      try {
        const res = await fetch(`/api/booking/${booking.bookingId}`)
        if (res.ok) {
          const data = await res.json()
          setStatus(data)

          // Check if completed
          if (data.status === 'completed' || data.status === 'confirmed') {
            onComplete?.()
          }
        }
      } catch {
        // Polling error, ignore
      }
    }

    fetchStatus()
    const interval = setInterval(fetchStatus, 3000)

    return () => clearInterval(interval)
  }, [booking.bookingId, onComplete])

  const getStatusIcon = (callStatus: string) => {
    switch (callStatus) {
      case 'ringing':
        return (
          <div className="w-8 h-8 rounded-full bg-warning-muted flex items-center justify-center">
            <svg className="w-4 h-4 text-warning animate-pulse" fill="currentColor" viewBox="0 0 24 24">
              <path d="M6.62 10.79c1.44 2.83 3.76 5.14 6.59 6.59l2.2-2.2c.27-.27.67-.36 1.02-.24 1.12.37 2.33.57 3.57.57.55 0 1 .45 1 1V20c0 .55-.45 1-1 1-9.39 0-17-7.61-17-17 0-.55.45-1 1-1h3.5c.55 0 1 .45 1 1 0 1.25.2 2.45.57 3.57.11.35.03.74-.25 1.02l-2.2 2.2z"/>
            </svg>
          </div>
        )
      case 'in_progress':
        return (
          <div className="w-8 h-8 rounded-full bg-info-muted flex items-center justify-center">
            <svg className="w-4 h-4 text-info" fill="currentColor" viewBox="0 0 24 24">
              <path d="M12 14c1.66 0 3-1.34 3-3V5c0-1.66-1.34-3-3-3S9 3.34 9 5v6c0 1.66 1.34 3 3 3z"/>
              <path d="M17 11c0 2.76-2.24 5-5 5s-5-2.24-5-5H5c0 3.53 2.61 6.43 6 6.92V21h2v-3.08c3.39-.49 6-3.39 6-6.92h-2z"/>
            </svg>
          </div>
        )
      case 'completed':
      case 'confirmed':
        return (
          <div className="w-8 h-8 rounded-full bg-success-muted flex items-center justify-center">
            <svg className="w-4 h-4 text-success" fill="currentColor" viewBox="0 0 24 24">
              <path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z"/>
            </svg>
          </div>
        )
      case 'failed':
        return (
          <div className="w-8 h-8 rounded-full bg-destructive-muted flex items-center justify-center">
            <svg className="w-4 h-4 text-destructive" fill="currentColor" viewBox="0 0 24 24">
              <path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z"/>
            </svg>
          </div>
        )
      default:
        return (
          <div className="w-8 h-8 rounded-full bg-muted flex items-center justify-center">
            <Spinner className="w-4 h-4 text-muted-foreground" />
          </div>
        )
    }
  }

  const getStatusText = (callStatus: string) => {
    switch (callStatus) {
      case 'pending': return 'Preparing call...'
      case 'ringing': return 'Calling provider...'
      case 'in_progress': return 'Speaking with provider'
      case 'completed':
      case 'confirmed': return 'Call completed'
      case 'failed': return 'Call failed'
      default: return 'Processing...'
    }
  }

  if (error) {
    return (
      <Alert variant="destructive">
        <AlertDescription>{error}</AlertDescription>
      </Alert>
    )
  }

  const currentCall = status?.calls?.[0]
  const bookingConfirmed = status?.booking

  return (
    <div className="space-y-6">
      {/* Tool info header */}
      <div className="bg-card rounded-lg p-4">
        <h3 className="font-semibold text-card-foreground mb-1">Booking Demo</h3>
        <p className="text-sm text-muted-foreground">{booking.toolName}</p>
      </div>

      {/* Call status */}
      <div className="bg-card rounded-lg p-6">
        <div className="flex items-center gap-4 mb-4">
          {getStatusIcon(currentCall?.status || status?.status || 'pending')}
          <div>
            <p className="font-medium text-card-foreground">
              {getStatusText(currentCall?.status || status?.status || 'pending')}
            </p>
            {currentCall?.providers?.name && (
              <p className="text-sm text-muted-foreground">
                {currentCall.providers.name}
              </p>
            )}
          </div>
        </div>

        {/* Progress steps */}
        <div className="space-y-3">
          <ProgressStep
            label="Initiating call"
            completed={!!status}
            active={!status}
          />
          <ProgressStep
            label="Ringing"
            completed={['in_progress', 'completed', 'confirmed'].includes(currentCall?.status || '')}
            active={currentCall?.status === 'ringing'}
          />
          <ProgressStep
            label="Speaking with provider"
            completed={['completed', 'confirmed'].includes(currentCall?.status || '')}
            active={currentCall?.status === 'in_progress'}
          />
          <ProgressStep
            label="Booking confirmed"
            completed={!!bookingConfirmed}
            active={false}
          />
        </div>
      </div>

      {/* Confirmed booking details */}
      {bookingConfirmed && (
        <Alert className="bg-success-muted border-success">
          <svg className="w-5 h-5 text-success" fill="currentColor" viewBox="0 0 24 24">
            <path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z"/>
          </svg>
          <AlertDescription>
            <h4 className="font-semibold text-success mb-1">Demo Scheduled!</h4>
            <p className="text-sm text-muted-foreground">
              {bookingConfirmed.datetime}
            </p>
            {bookingConfirmed.confirmation_number && (
              <p className="text-xs text-muted-foreground mt-1">
                Confirmation: {bookingConfirmed.confirmation_number}
              </p>
            )}
          </AlertDescription>
        </Alert>
      )}

      {/* Tip */}
      <p className="text-xs text-muted-foreground text-center">
        You can switch tabs while the call is in progress
      </p>
    </div>
  )
}

function ProgressStep({
  label,
  completed,
  active,
}: {
  label: string
  completed: boolean
  active: boolean
}) {
  return (
    <div className="flex items-center gap-3">
      <div
        className={`w-2 h-2 rounded-full ${
          completed
            ? 'bg-success'
            : active
            ? 'bg-primary animate-pulse'
            : 'bg-muted'
        }`}
      />
      <span
        className={`text-sm ${
          completed
            ? 'text-foreground'
            : active
            ? 'text-foreground font-medium'
            : 'text-muted-foreground'
        }`}
      >
        {label}
      </span>
    </div>
  )
}
