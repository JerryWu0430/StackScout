"""Voice router for voice agent integration."""

from datetime import datetime
from typing import Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from db.supabase import supabase
from db.models import Demo
from services import elevenlabs, calendar


router = APIRouter(prefix="/api/voice", tags=["voice"])


# Request/Response models

class StartConversationRequest(BaseModel):
    repo_id: int
    tool_id: int


class StartConversationResponse(BaseModel):
    session_id: str
    websocket_url: str


class ConversationSummaryResponse(BaseModel):
    session_id: str
    status: str
    key_points: list[str]
    booking_status: Optional[str] = None
    next_steps: list[str]


class CreateDemoRequest(BaseModel):
    repo_id: int
    tool_id: int
    scheduled_at: datetime


class DemoResponse(BaseModel):
    id: int
    repo_id: int
    tool_id: int
    scheduled_at: Optional[datetime]
    status: str
    meet_link: Optional[str] = None


# Endpoints

@router.post("/start", response_model=StartConversationResponse)
async def start_conversation(request: StartConversationRequest):
    """Start ElevenLabs conversation session for voice demo."""
    # Fetch tool info
    tool_res = supabase.table("tools").select("*").eq("id", request.tool_id).execute()
    if not tool_res.data:
        raise HTTPException(status_code=404, detail="Tool not found")
    tool = tool_res.data[0]

    # Fetch repo fingerprint for stack info
    repo_res = supabase.table("repos").select("*").eq("id", request.repo_id).execute()
    if not repo_res.data:
        raise HTTPException(status_code=404, detail="Repo not found")
    repo = repo_res.data[0]

    # Parse stack from fingerprint
    stack = []
    if repo.get("fingerprint"):
        import json
        try:
            fp = json.loads(repo["fingerprint"])
            tech = fp.get("tech_stack", {})
            stack = tech.get("frontend", []) + tech.get("backend", []) + tech.get("database", [])
        except (json.JSONDecodeError, TypeError):
            pass

    # Get available demo times
    try:
        slots = calendar.get_available_slots(days_ahead=7)
        available_times = [s.formatted for s in slots[:5]]
    except Exception:
        available_times = []

    # Build context and start conversation
    context = elevenlabs.ConversationContext(
        tool_name=tool["name"],
        tool_description=tool.get("description", ""),
        repo_stack=stack,
        available_times=available_times,
    )

    session = await elevenlabs.create_conversation(context)

    return StartConversationResponse(
        session_id=session.session_id,
        websocket_url=session.signed_url,
    )


@router.get("/{session_id}/summary", response_model=ConversationSummaryResponse)
async def get_summary(session_id: str):
    """Get post-call summary including key points and booking status."""
    try:
        summary = await elevenlabs.get_conversation_summary(session_id)
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Conversation not found: {e}")

    # Extract key points from transcript
    key_points = []
    for item in summary.transcript:
        if item.speaker == "agent" and len(item.text) > 20:
            key_points.append(item.text[:100])
    key_points = key_points[:5]  # Limit to 5

    # Determine booking status from transcript
    booking_keywords = ["booked", "scheduled", "confirmed", "appointment"]
    transcript_text = " ".join(t.text.lower() for t in summary.transcript)
    booking_status = "confirmed" if any(k in transcript_text for k in booking_keywords) else "pending"

    # Next steps based on status
    next_steps = ["Review conversation transcript"]
    if booking_status == "confirmed":
        next_steps.append("Check calendar for demo invite")
    else:
        next_steps.append("Schedule demo manually if interested")

    return ConversationSummaryResponse(
        session_id=session_id,
        status=summary.status,
        key_points=key_points,
        booking_status=booking_status,
        next_steps=next_steps,
    )


# Demo booking endpoints

demos_router = APIRouter(prefix="/api/demos", tags=["demos"])


@demos_router.post("", response_model=DemoResponse)
async def create_demo(request: CreateDemoRequest):
    """Create demo booking with calendar event."""
    # Verify tool exists
    tool_res = supabase.table("tools").select("*").eq("id", request.tool_id).execute()
    if not tool_res.data:
        raise HTTPException(status_code=404, detail="Tool not found")
    tool = tool_res.data[0]

    # Verify repo exists
    repo_res = supabase.table("repos").select("*").eq("id", request.repo_id).execute()
    if not repo_res.data:
        raise HTTPException(status_code=404, detail="Repo not found")

    # Create calendar event
    meet_link = None
    try:
        slot = calendar.TimeSlot(
            start=request.scheduled_at,
            end=request.scheduled_at,  # Duration handled by calendar service
            formatted=request.scheduled_at.strftime("%A, %b %d at %-I:%M %p"),
        )
        # TODO: Get attendee email from request or user context
        event = calendar.create_demo_event(
            tool_name=tool["name"],
            slot=slot,
            attendee_email="demo@stackscout.io",  # Placeholder
        )
        meet_link = event.meet_link
    except Exception:
        pass  # Calendar event creation optional

    # Save to demos table
    demo_data = {
        "repo_id": request.repo_id,
        "tool_id": request.tool_id,
        "scheduled_at": request.scheduled_at.isoformat(),
        "status": "scheduled",
    }

    result = supabase.table("demos").insert(demo_data).execute()
    if not result.data:
        raise HTTPException(status_code=500, detail="Failed to create demo")

    demo = result.data[0]
    return DemoResponse(
        id=demo["id"],
        repo_id=demo["repo_id"],
        tool_id=demo["tool_id"],
        scheduled_at=demo.get("scheduled_at"),
        status=demo["status"],
        meet_link=meet_link,
    )


@demos_router.get("", response_model=list[DemoResponse])
async def list_demos(repo_id: int):
    """List scheduled demos for a repo."""
    result = supabase.table("demos").select("*").eq("repo_id", repo_id).execute()

    return [
        DemoResponse(
            id=d["id"],
            repo_id=d["repo_id"],
            tool_id=d["tool_id"],
            scheduled_at=d.get("scheduled_at"),
            status=d["status"],
        )
        for d in result.data
    ]
