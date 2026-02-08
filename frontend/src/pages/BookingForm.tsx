import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { Button } from '@/components/ui/button'
import { Textarea } from '@/components/ui/textarea'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Spinner } from '@/components/ui/spinner'

interface Provider {
  id: string
  name: string
  category: string
  phone: string
  address?: string
  rating?: number
}

const SERVICE_TYPES = [
  { value: 'dentist', label: 'Dentist' },
  { value: 'doctor', label: 'Doctor' },
  { value: 'salon', label: 'Hair Salon' },
  { value: 'mechanic', label: 'Auto Mechanic' },
  { value: 'other', label: 'Other' },
]

const TIME_PREFERENCES = [
  { value: 'morning', label: 'Morning (9am-12pm)' },
  { value: 'afternoon', label: 'Afternoon (12pm-5pm)' },
  { value: 'evening', label: 'Evening (5pm-8pm)' },
]

export default function BookingForm() {
  const navigate = useNavigate()
  const [serviceType, setServiceType] = useState('')
  const [providers, setProviders] = useState<Provider[]>([])
  const [selectedProvider, setSelectedProvider] = useState('')
  const [preferredDates, setPreferredDates] = useState<string[]>([])
  const [preferredTimes, setPreferredTimes] = useState<string[]>([])
  const [notes, setNotes] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState('')

  // Fetch providers when service type changes
  useEffect(() => {
    if (!serviceType) {
      setProviders([])
      return
    }

    fetch(`/api/booking/providers/${serviceType}`)
      .then(res => res.json())
      .then(data => setProviders(data || []))
      .catch(() => setProviders([]))
  }, [serviceType])

  const handleDateToggle = (date: string) => {
    setPreferredDates(prev =>
      prev.includes(date) ? prev.filter(d => d !== date) : [...prev, date]
    )
  }

  const handleTimeToggle = (time: string) => {
    setPreferredTimes(prev =>
      prev.includes(time) ? prev.filter(t => t !== time) : [...prev, time]
    )
  }

  const getNextDays = (count: number): { value: string; label: string }[] => {
    const days = []
    const today = new Date()
    for (let i = 1; i <= count; i++) {
      const date = new Date(today)
      date.setDate(today.getDate() + i)
      days.push({
        value: date.toISOString().split('T')[0],
        label: date.toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' }),
      })
    }
    return days
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')

    if (!serviceType) {
      setError('Please select a service type')
      return
    }

    setIsLoading(true)

    try {
      // Create booking request
      const bookingRes = await fetch('/api/booking/start', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          service_type: serviceType,
          provider_id: selectedProvider || null,
          preferred_dates: preferredDates,
          preferred_times: preferredTimes,
          notes: notes || null,
        }),
      })

      if (!bookingRes.ok) throw new Error('Failed to create booking request')
      const booking = await bookingRes.json()

      // Start the call
      const callRes = await fetch(`/api/booking/${booking.id}/call`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ provider_id: selectedProvider || null }),
      })

      if (!callRes.ok) throw new Error('Failed to initiate call')
      await callRes.json()

      // Navigate to call status page
      navigate(`/calling/${booking.id}`)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Something went wrong')
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-background py-12 px-4">
      <div className="max-w-2xl mx-auto">
        <div className="text-center mb-10">
          <h1 className="text-4xl font-bold text-foreground mb-2">CallPilot</h1>
          <p className="text-muted-foreground">AI-powered appointment scheduling</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-8">
          {/* Service Type */}
          <div>
            <label className="block text-sm font-medium text-foreground mb-3">
              What type of appointment?
            </label>
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
              {SERVICE_TYPES.map(type => (
                <Button
                  key={type.value}
                  type="button"
                  variant="outline"
                  onClick={() => setServiceType(type.value)}
                  className={`h-auto py-3 ${
                    serviceType === type.value
                      ? 'border-primary bg-primary/10 text-primary'
                      : ''
                  }`}
                >
                  {type.label}
                </Button>
              ))}
            </div>
          </div>

          {/* Provider Selection */}
          {providers.length > 0 && (
            <div>
              <label className="block text-sm font-medium text-foreground mb-3">
                Select provider (optional)
              </label>
              <div className="space-y-2">
                {providers.map(provider => (
                  <Button
                    key={provider.id}
                    type="button"
                    variant="outline"
                    onClick={() => setSelectedProvider(provider.id === selectedProvider ? '' : provider.id)}
                    className={`w-full h-auto py-3 justify-start text-left ${
                      selectedProvider === provider.id
                        ? 'border-primary bg-primary/10'
                        : ''
                    }`}
                  >
                    <div>
                      <div className="font-medium text-foreground">{provider.name}</div>
                      {provider.address && (
                        <div className="text-sm text-muted-foreground">{provider.address}</div>
                      )}
                      {provider.rating && (
                        <div className="text-sm text-muted-foreground">Rating: {provider.rating}/5</div>
                      )}
                    </div>
                  </Button>
                ))}
              </div>
            </div>
          )}

          {/* Preferred Dates */}
          <div>
            <label className="block text-sm font-medium text-foreground mb-3">
              Preferred dates
            </label>
            <div className="flex flex-wrap gap-2">
              {getNextDays(7).map(day => (
                <Button
                  key={day.value}
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={() => handleDateToggle(day.value)}
                  className={
                    preferredDates.includes(day.value)
                      ? 'border-primary bg-primary/10 text-primary'
                      : ''
                  }
                >
                  {day.label}
                </Button>
              ))}
            </div>
          </div>

          {/* Preferred Times */}
          <div>
            <label className="block text-sm font-medium text-foreground mb-3">
              Preferred times
            </label>
            <div className="flex flex-wrap gap-2">
              {TIME_PREFERENCES.map(time => (
                <Button
                  key={time.value}
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={() => handleTimeToggle(time.value)}
                  className={
                    preferredTimes.includes(time.value)
                      ? 'border-primary bg-primary/10 text-primary'
                      : ''
                  }
                >
                  {time.label}
                </Button>
              ))}
            </div>
          </div>

          {/* Notes */}
          <div>
            <label className="block text-sm font-medium text-foreground mb-2">
              Additional notes (optional)
            </label>
            <Textarea
              value={notes}
              onChange={e => setNotes(e.target.value)}
              placeholder="Any specific requirements or information..."
              rows={3}
            />
          </div>

          {/* Error */}
          {error && (
            <Alert variant="destructive">
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}

          {/* Submit */}
          <Button
            type="submit"
            disabled={isLoading || !serviceType}
            size="lg"
            className="w-full h-14 text-lg"
          >
            {isLoading ? (
              <>
                <Spinner />
                Starting call...
              </>
            ) : (
              'Start AI Call'
            )}
          </Button>
        </form>
      </div>
    </div>
  )
}
