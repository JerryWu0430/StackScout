import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { Button } from '@/components/ui/button'

interface Call {
  id: string
  status: string
  outcome?: string
  providers?: {
    name: string
    phone: string
  }
  transcript?: Array<{ speaker: string; text: string }>
  available_slots?: Array<{ date: string; time: string; notes?: string }>
  booked_slot?: { datetime: string; confirmation_number?: string }
  duration_seconds?: number
}

interface BookingStatus {
  id: string
  status: string
  service_type: string
  calls: Call[]
  booking?: {
    appointment_datetime: string
    confirmation_number?: string
    providers?: {
      name: string
      phone: string
      address?: string
    }
  }
}

const STATUS_DISPLAY: Record<string, { label: string; color: string; icon: string }> = {
  pending: { label: 'Preparing call...', color: 'text-muted-foreground', icon: '' },
  ringing: { label: 'Ringing...', color: 'text-yellow-500', icon: '' },
  in_progress: { label: 'Call in progress', color: 'text-blue-500', icon: '' },
  completed: { label: 'Call completed', color: 'text-green-500', icon: '' },
  failed: { label: 'Call failed', color: 'text-destructive', icon: '' },
  no_answer: { label: 'No answer', color: 'text-orange-500', icon: '' },
}

export default function CallStatus() {
  const { requestId } = useParams<{ requestId: string }>()
  const navigate = useNavigate()
  const [status, setStatus] = useState<BookingStatus | null>(null)
  const [error, setError] = useState('')

  useEffect(() => {
    if (!requestId) return

    const fetchStatus = async () => {
      try {
        const res = await fetch(`/api/booking/${requestId}`)
        if (!res.ok) throw new Error('Failed to fetch status')
        const data = await res.json()
        setStatus(data)

        // If booking is confirmed, stop polling
        if (data.booking || data.status === 'completed') {
          return true
        }
        return false
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Error fetching status')
        return true
      }
    }

    // Initial fetch
    fetchStatus()

    // Poll every 2 seconds
    const interval = setInterval(async () => {
      const shouldStop = await fetchStatus()
      if (shouldStop) clearInterval(interval)
    }, 2000)

    return () => clearInterval(interval)
  }, [requestId])

  const currentCall = status?.calls?.[0]
  const callStatus = currentCall ? STATUS_DISPLAY[currentCall.status] || STATUS_DISPLAY.pending : STATUS_DISPLAY.pending

  if (error) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center px-4">
        <div className="text-center">
          <p className="text-destructive mb-4">{error}</p>
          <Button onClick={() => navigate('/book')}>
            Try Again
          </Button>
        </div>
      </div>
    )
  }

  // Show booking confirmation
  if (status?.booking) {
    return (
      <div className="min-h-screen bg-background py-12 px-4">
        <div className="max-w-lg mx-auto text-center">
          <div className="w-20 h-20 bg-green-500/20 rounded-full flex items-center justify-center mx-auto mb-6">
            <svg className="w-10 h-10 text-green-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
          </div>

          <h1 className="text-3xl font-bold text-foreground mb-2">Appointment Booked!</h1>
          <p className="text-muted-foreground mb-8">Your appointment has been successfully scheduled</p>

          <div className="bg-card border border-border rounded-xl p-6 text-left space-y-4">
            <div>
              <span className="text-sm text-muted-foreground">Provider</span>
              <p className="text-lg font-medium text-foreground">
                {status.booking.providers?.name || 'Provider'}
              </p>
            </div>
            <div>
              <span className="text-sm text-muted-foreground">Date & Time</span>
              <p className="text-lg font-medium text-foreground">
                {new Date(status.booking.appointment_datetime).toLocaleString()}
              </p>
            </div>
            {status.booking.confirmation_number && (
              <div>
                <span className="text-sm text-muted-foreground">Confirmation #</span>
                <p className="text-lg font-medium text-foreground">
                  {status.booking.confirmation_number}
                </p>
              </div>
            )}
            {status.booking.providers?.address && (
              <div>
                <span className="text-sm text-muted-foreground">Address</span>
                <p className="text-foreground">{status.booking.providers.address}</p>
              </div>
            )}
          </div>

          <Button onClick={() => navigate('/book')} className="mt-8">
            Book Another Appointment
          </Button>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-background py-12 px-4">
      <div className="max-w-lg mx-auto">
        <div className="text-center mb-10">
          <h1 className="text-3xl font-bold text-foreground mb-2">AI Making Call</h1>
          <p className="text-muted-foreground">
            CallPilot is calling to schedule your {status?.service_type || 'appointment'}
          </p>
        </div>

        {/* Call Status Indicator */}
        <div className="bg-card border border-border rounded-xl p-8 mb-6">
          <div className="flex items-center justify-center mb-6">
            {/* Pulsing indicator */}
            <div className="relative">
              <div className={`w-16 h-16 rounded-full ${
                currentCall?.status === 'in_progress' ? 'bg-blue-500' :
                currentCall?.status === 'ringing' ? 'bg-yellow-500' :
                currentCall?.status === 'completed' ? 'bg-green-500' :
                'bg-muted'
              } opacity-20`} />
              <div className={`absolute inset-0 w-16 h-16 rounded-full ${
                currentCall?.status === 'in_progress' ? 'bg-blue-500' :
                currentCall?.status === 'ringing' ? 'bg-yellow-500' :
                currentCall?.status === 'completed' ? 'bg-green-500' :
                'bg-muted'
              } opacity-40 animate-ping`} />
              <div className="absolute inset-0 flex items-center justify-center">
                <svg className="w-8 h-8 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z" />
                </svg>
              </div>
            </div>
          </div>

          <p className={`text-center text-lg font-medium ${callStatus.color}`}>
            {callStatus.label}
          </p>

          {currentCall?.providers && (
            <p className="text-center text-muted-foreground mt-2">
              Calling: {currentCall.providers.name}
            </p>
          )}
        </div>

        {/* Available Slots Found */}
        {currentCall?.available_slots && currentCall.available_slots.length > 0 && (
          <div className="bg-card border border-border rounded-xl p-6 mb-6">
            <h3 className="font-medium text-foreground mb-3">Slots Found</h3>
            <div className="space-y-2">
              {currentCall.available_slots.map((slot, i) => (
                <div key={i} className="flex items-center gap-2 text-sm">
                  <span className="text-muted-foreground">{slot.date}</span>
                  <span className="text-foreground">{slot.time}</span>
                  {slot.notes && <span className="text-muted-foreground">({slot.notes})</span>}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Live Transcript */}
        {currentCall?.transcript && currentCall.transcript.length > 0 && (
          <div className="bg-card border border-border rounded-xl p-6">
            <h3 className="font-medium text-foreground mb-3">Conversation</h3>
            <div className="space-y-3 max-h-64 overflow-y-auto">
              {currentCall.transcript.map((item, i) => (
                <div key={i} className={`text-sm ${
                  item.speaker === 'agent' ? 'text-primary' : 'text-foreground'
                }`}>
                  <span className="font-medium">
                    {item.speaker === 'agent' ? 'AI: ' : 'Receptionist: '}
                  </span>
                  {item.text}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Call Failed */}
        {(currentCall?.status === 'failed' || currentCall?.status === 'no_answer') && (
          <div className="text-center mt-6">
            <p className="text-muted-foreground mb-4">
              {currentCall.status === 'no_answer'
                ? "The provider didn't answer. Would you like to try again?"
                : 'The call could not be completed.'}
            </p>
            <Button onClick={() => navigate('/book')}>
              Try Again
            </Button>
          </div>
        )}
      </div>
    </div>
  )
}
