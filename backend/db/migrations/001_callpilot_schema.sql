-- CallPilot Schema Migration
-- Run this in Supabase SQL Editor

-- providers table: service providers we can call
CREATE TABLE IF NOT EXISTS providers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    category TEXT NOT NULL, -- 'dentist', 'doctor', 'salon', etc.
    phone TEXT NOT NULL,
    address TEXT,
    lat DOUBLE PRECISION,
    lng DOUBLE PRECISION,
    rating DECIMAL(2,1),
    hours JSONB DEFAULT '{}', -- {"mon": "9:00-17:00", ...}
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- booking_requests table: user booking requests
CREATE TABLE IF NOT EXISTS booking_requests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    service_type TEXT NOT NULL, -- 'dentist', 'doctor', etc.
    preferred_dates JSONB DEFAULT '[]', -- ["2024-01-15", "2024-01-16"]
    preferred_times JSONB DEFAULT '[]', -- ["morning", "afternoon"]
    location_lat DOUBLE PRECISION,
    location_lng DOUBLE PRECISION,
    max_distance_miles INTEGER DEFAULT 10,
    notes TEXT,
    status TEXT DEFAULT 'pending', -- 'pending', 'calling', 'completed', 'failed'
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- calls table: individual call attempts
CREATE TABLE IF NOT EXISTS calls (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    request_id UUID REFERENCES booking_requests(id) ON DELETE CASCADE,
    provider_id UUID REFERENCES providers(id) ON DELETE SET NULL,
    twilio_call_sid TEXT,
    elevenlabs_conversation_id TEXT,
    status TEXT DEFAULT 'pending', -- 'pending', 'ringing', 'in_progress', 'completed', 'failed', 'no_answer'
    outcome TEXT, -- 'booked', 'no_slots', 'callback_requested', 'voicemail', 'failed'
    transcript JSONB DEFAULT '[]',
    available_slots JSONB DEFAULT '[]', -- slots offered by provider
    booked_slot JSONB, -- the slot we booked
    score INTEGER, -- quality score 0-100
    duration_seconds INTEGER,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- bookings table: confirmed appointments
CREATE TABLE IF NOT EXISTS bookings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    request_id UUID REFERENCES booking_requests(id) ON DELETE CASCADE,
    call_id UUID REFERENCES calls(id) ON DELETE SET NULL,
    provider_id UUID REFERENCES providers(id) ON DELETE SET NULL,
    appointment_datetime TIMESTAMPTZ NOT NULL,
    confirmation_number TEXT,
    calendar_event_id TEXT,
    status TEXT DEFAULT 'confirmed', -- 'confirmed', 'cancelled', 'completed'
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for common queries
CREATE INDEX IF NOT EXISTS idx_providers_category ON providers(category);
CREATE INDEX IF NOT EXISTS idx_providers_location ON providers(lat, lng);
CREATE INDEX IF NOT EXISTS idx_booking_requests_status ON booking_requests(status);
CREATE INDEX IF NOT EXISTS idx_calls_request_id ON calls(request_id);
CREATE INDEX IF NOT EXISTS idx_calls_status ON calls(status);
CREATE INDEX IF NOT EXISTS idx_bookings_request_id ON bookings(request_id);

-- Seed some demo providers (your phone for testing)
INSERT INTO providers (name, category, phone, address, rating, hours) VALUES
    ('Demo Dental Clinic', 'dentist', '+1YOURPHONE', '123 Main St', 4.5, '{"mon": "9:00-17:00", "tue": "9:00-17:00", "wed": "9:00-17:00", "thu": "9:00-17:00", "fri": "9:00-17:00"}'),
    ('Demo Family Doctor', 'doctor', '+1YOURPHONE', '456 Oak Ave', 4.8, '{"mon": "8:00-18:00", "tue": "8:00-18:00", "wed": "8:00-18:00", "thu": "8:00-18:00", "fri": "8:00-16:00"}'),
    ('Demo Hair Salon', 'salon', '+1YOURPHONE', '789 Elm Blvd', 4.2, '{"mon": "10:00-19:00", "tue": "10:00-19:00", "wed": "10:00-19:00", "thu": "10:00-19:00", "fri": "10:00-20:00", "sat": "9:00-17:00"}')
ON CONFLICT DO NOTHING;
