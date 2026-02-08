"""Booking API endpoints for CallPilot."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import uuid

from db.supabase import supabase
from services.twilio_client import CallRequest, initiate_call

router = APIRouter(prefix="/api/booking", tags=["booking"])


class BookingRequestCreate(BaseModel):
    """Request to start a booking process."""
    service_type: str  # 'dentist', 'doctor', 'salon', etc.
    provider_id: Optional[str] = None  # Specific provider, or None for auto-select
    preferred_dates: list[str] = []  # ["2024-01-15", "2024-01-16"]
    preferred_times: list[str] = []  # ["morning", "afternoon", "evening"]
    notes: Optional[str] = None


class BookingRequestResponse(BaseModel):
    """Response with booking request info."""
    id: str
    status: str
    service_type: str
    created_at: str


class CallStartResponse(BaseModel):
    """Response when call is initiated."""
    call_id: str
    call_sid: str
    status: str
    provider_name: str
    provider_phone: str


class BookingStatus(BaseModel):
    """Current status of a booking request."""
    id: str
    status: str
    service_type: str
    calls: list[dict]
    booking: Optional[dict] = None


@router.post("/start", response_model=BookingRequestResponse)
async def create_booking_request(request: BookingRequestCreate):
    """Create a new booking request."""
    booking_id = str(uuid.uuid4())

    result = supabase.table("booking_requests").insert({
        "id": booking_id,
        "service_type": request.service_type,
        "preferred_dates": request.preferred_dates,
        "preferred_times": request.preferred_times,
        "notes": request.notes,
        "status": "pending",
    }).execute()

    if not result.data:
        raise HTTPException(status_code=500, detail="Failed to create booking request")

    return BookingRequestResponse(
        id=booking_id,
        status="pending",
        service_type=request.service_type,
        created_at=result.data[0]["created_at"],
    )


@router.post("/{request_id}/call", response_model=CallStartResponse)
async def start_call(request_id: str, provider_id: Optional[str] = None):
    """
    Initiate a call to a provider for a booking request.
    If provider_id not specified, selects best available provider.
    """
    # Get booking request
    booking_result = supabase.table("booking_requests").select("*").eq("id", request_id).single().execute()

    if not booking_result.data:
        raise HTTPException(status_code=404, detail="Booking request not found")

    booking = booking_result.data

    # Get provider (specified or auto-select)
    if provider_id:
        provider_result = supabase.table("providers").select("*").eq("id", provider_id).single().execute()
    else:
        # Auto-select provider by category
        provider_result = supabase.table("providers").select("*").eq("category", booking["service_type"]).limit(1).execute()
        if provider_result.data:
            provider_result.data = provider_result.data[0]

    if not provider_result.data:
        raise HTTPException(status_code=404, detail="No provider found")

    provider = provider_result.data

    # Create call record
    call_id = str(uuid.uuid4())
    supabase.table("calls").insert({
        "id": call_id,
        "request_id": request_id,
        "provider_id": provider["id"],
        "status": "pending",
    }).execute()

    # Update booking request status
    supabase.table("booking_requests").update({
        "status": "calling",
        "updated_at": datetime.utcnow().isoformat(),
    }).eq("id", request_id).execute()

    # Initiate the call via Twilio
    try:
        call_request = CallRequest(
            provider_phone=provider["phone"],
            provider_name=provider["name"],
            service_type=booking["service_type"],
            preferred_dates=booking.get("preferred_dates", []),
            preferred_times=booking.get("preferred_times", []),
            call_id=call_id,
        )
        result = initiate_call(call_request)

        # Update call record with Twilio SID
        supabase.table("calls").update({
            "twilio_call_sid": result.call_sid,
            "status": "ringing",
        }).eq("id", call_id).execute()

        return CallStartResponse(
            call_id=call_id,
            call_sid=result.call_sid,
            status="ringing",
            provider_name=provider["name"],
            provider_phone=provider["phone"],
        )

    except Exception as e:
        # Update call as failed
        supabase.table("calls").update({
            "status": "failed",
            "outcome": str(e),
        }).eq("id", call_id).execute()
        raise HTTPException(status_code=500, detail=f"Failed to initiate call: {str(e)}")


@router.get("/{request_id}", response_model=BookingStatus)
async def get_booking_status(request_id: str):
    """Get current status of a booking request including all calls."""
    # Get booking request
    booking_result = supabase.table("booking_requests").select("*").eq("id", request_id).single().execute()

    if not booking_result.data:
        raise HTTPException(status_code=404, detail="Booking request not found")

    booking = booking_result.data

    # Get all calls for this request
    calls_result = supabase.table("calls").select("*, providers(name, phone)").eq("request_id", request_id).order("created_at", desc=True).execute()

    # Get confirmed booking if exists
    booking_confirm = supabase.table("bookings").select("*, providers(name, phone, address)").eq("request_id", request_id).single().execute()

    return BookingStatus(
        id=request_id,
        status=booking["status"],
        service_type=booking["service_type"],
        calls=calls_result.data or [],
        booking=booking_confirm.data if booking_confirm.data else None,
    )


@router.get("/{request_id}/call/{call_id}")
async def get_call_details(request_id: str, call_id: str):
    """Get details of a specific call."""
    result = supabase.table("calls").select("*, providers(*)").eq("id", call_id).eq("request_id", request_id).single().execute()

    if not result.data:
        raise HTTPException(status_code=404, detail="Call not found")

    return result.data


@router.get("/providers/{category}")
async def list_providers(category: str):
    """List available providers by category."""
    result = supabase.table("providers").select("*").eq("category", category).execute()
    return result.data or []


@router.get("/providers")
async def list_all_providers():
    """List all available providers."""
    result = supabase.table("providers").select("*").execute()
    return result.data or []
