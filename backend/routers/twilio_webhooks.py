"""Twilio webhook handlers for call events and ElevenLabs connection."""

from fastapi import APIRouter, Form, Request, Response
from fastapi.responses import PlainTextResponse
from typing import Optional
from datetime import datetime

from db.supabase import supabase
from services.twilio_client import generate_connect_twiml

router = APIRouter(prefix="/api/twilio", tags=["twilio"])


@router.post("/connect")
async def connect_to_elevenlabs(
    request: Request,
    call_id: str,
    CallSid: str = Form(None),
    CallStatus: str = Form(None),
):
    """
    TwiML endpoint called when Twilio connects the call.
    Returns TwiML to connect to ElevenLabs Conversational AI.
    """
    # Get call info to build first message
    call_data = None
    if call_id:
        result = supabase.table("calls").select("*, providers(*), booking_requests(*)").eq("id", call_id).single().execute()
        if result.data:
            call_data = result.data

    # Build first message for the AI agent
    first_message = None
    if call_data:
        provider = call_data.get("providers", {})
        request_data = call_data.get("booking_requests", {})
        provider_name = provider.get("name", "your office")
        service_type = request_data.get("service_type", "appointment")

        first_message = f"Hello, this is an automated assistant calling to schedule a {service_type} appointment. Am I speaking with {provider_name}?"

    # Update call status
    if call_id:
        supabase.table("calls").update({
            "twilio_call_sid": CallSid,
            "status": "in_progress",
            "updated_at": datetime.utcnow().isoformat(),
        }).eq("id", call_id).execute()

    # Generate TwiML to connect to ElevenLabs
    twiml = generate_connect_twiml(call_id, first_message)

    return Response(content=twiml, media_type="application/xml")


@router.post("/status")
async def call_status_callback(
    CallSid: str = Form(...),
    CallStatus: str = Form(...),
    CallDuration: Optional[str] = Form(None),
    From: str = Form(None),
    To: str = Form(None),
):
    """
    Twilio status callback for call lifecycle events.
    Updates call status in database.
    """
    # Map Twilio status to our status
    status_map = {
        "initiated": "pending",
        "ringing": "ringing",
        "in-progress": "in_progress",
        "completed": "completed",
        "busy": "failed",
        "no-answer": "no_answer",
        "failed": "failed",
        "canceled": "failed",
    }

    our_status = status_map.get(CallStatus, CallStatus)

    # Find call by Twilio SID and update
    result = supabase.table("calls").select("id").eq("twilio_call_sid", CallSid).single().execute()

    if result.data:
        update_data = {
            "status": our_status,
            "updated_at": datetime.utcnow().isoformat(),
        }
        if CallDuration:
            update_data["duration_seconds"] = int(CallDuration)

        supabase.table("calls").update(update_data).eq("id", result.data["id"]).execute()

    return PlainTextResponse("OK")


@router.post("/elevenlabs-webhook")
async def elevenlabs_webhook(request: Request):
    """
    Webhook endpoint for ElevenLabs Conversational AI events.
    Receives tool calls and conversation updates.
    """
    body = await request.json()
    event_type = body.get("type")

    if event_type == "tool_call":
        return await handle_tool_call(body)
    elif event_type == "conversation_end":
        return await handle_conversation_end(body)

    return {"status": "ok"}


async def handle_tool_call(body: dict) -> dict:
    """
    Handle ElevenLabs tool calls during conversation.
    Supports: check_user_calendar, record_available_slot, confirm_booking
    """
    tool_name = body.get("tool_name")
    tool_input = body.get("tool_input", {})
    conversation_id = body.get("conversation_id")

    if tool_name == "check_user_calendar":
        # Check if user is available at requested time
        # For MVP, always return available
        datetime_str = tool_input.get("datetime")
        return {"available": True, "datetime": datetime_str}

    elif tool_name == "record_available_slot":
        # Record slot offered by provider
        call_result = supabase.table("calls").select("id, available_slots").eq("elevenlabs_conversation_id", conversation_id).single().execute()

        if call_result.data:
            slots = call_result.data.get("available_slots", []) or []
            slots.append({
                "date": tool_input.get("date"),
                "time": tool_input.get("time"),
                "notes": tool_input.get("notes"),
            })
            supabase.table("calls").update({"available_slots": slots}).eq("id", call_result.data["id"]).execute()

        return {"recorded": True}

    elif tool_name == "confirm_booking":
        # Confirm the booking
        call_result = supabase.table("calls").select("id, request_id, provider_id").eq("elevenlabs_conversation_id", conversation_id).single().execute()

        if call_result.data:
            call_id = call_result.data["id"]
            booked_slot = {
                "datetime": tool_input.get("datetime"),
                "confirmation_number": tool_input.get("confirmation_number"),
            }

            # Update call with booking info
            supabase.table("calls").update({
                "booked_slot": booked_slot,
                "outcome": "booked",
            }).eq("id", call_id).execute()

            # Create booking record
            supabase.table("bookings").insert({
                "request_id": call_result.data.get("request_id"),
                "call_id": call_id,
                "provider_id": call_result.data.get("provider_id"),
                "appointment_datetime": tool_input.get("datetime"),
                "confirmation_number": tool_input.get("confirmation_number"),
            }).execute()

        return {"confirmed": True}

    return {"error": "Unknown tool"}


async def handle_conversation_end(body: dict) -> dict:
    """Handle conversation end event - update call record."""
    conversation_id = body.get("conversation_id")
    transcript = body.get("transcript", [])

    call_result = supabase.table("calls").select("id, outcome").eq("elevenlabs_conversation_id", conversation_id).single().execute()

    if call_result.data:
        update_data = {
            "status": "completed",
            "transcript": transcript,
            "updated_at": datetime.utcnow().isoformat(),
        }

        # If no booking was made, set outcome
        if not call_result.data.get("outcome"):
            update_data["outcome"] = "no_booking"

        supabase.table("calls").update(update_data).eq("id", call_result.data["id"]).execute()

    return {"status": "ok"}
