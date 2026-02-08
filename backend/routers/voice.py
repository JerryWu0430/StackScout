"""Voice router for voice agent integration."""

import json
from datetime import datetime
from typing import Optional, Any
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from db.supabase import supabase
from db.models import Demo
from services import elevenlabs, calendar


router = APIRouter(prefix="/api/voice", tags=["voice"])

# In-memory session tracking (maps elevenlabs conversation_id -> repo_id)
# For production, use Redis or DB table
_session_repo_map: dict[str, str] = {}


# Request/Response models

class StartConversationRequest(BaseModel):
    repo_id: int
    tool_id: Optional[int] = None
    mode: str = 'analysis'  # 'analysis' | 'scheduling'


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
    """Start ElevenLabs conversation session for voice demo or analysis."""
    # Fetch repo fingerprint for stack info
    repo_res = supabase.table("repos").select("*").eq("id", request.repo_id).execute()
    if not repo_res.data:
        raise HTTPException(status_code=404, detail="Repo not found")
    repo = repo_res.data[0]

    # Parse fingerprint data
    stack = []
    gaps = []
    risk_flags = []
    recommendations_context = ""
    if repo.get("fingerprint"):
        import json
        try:
            fp = json.loads(repo["fingerprint"])
            tech = fp.get("tech_stack", fp.get("stack", {}))
            stack = (tech.get("frontend", []) + tech.get("backend", []) +
                    tech.get("database", []) + tech.get("infrastructure", []))
            gaps = fp.get("gaps", [])
            risk_flags = fp.get("risk_flags", [])
            recommendations_context = fp.get("recommendations_context", "")
        except (json.JSONDecodeError, TypeError):
            pass

    # Handle analysis mode
    if request.mode == 'analysis':
        context = elevenlabs.AnalysisContext(
            repo_stack=stack,
            gaps=gaps,
            risk_flags=risk_flags,
            recommendations_context=recommendations_context,
        )
        session = await elevenlabs.create_analysis_conversation(context)
        return StartConversationResponse(
            session_id=session.session_id,
            websocket_url=session.signed_url,
        )

    # Handle scheduling mode (requires tool_id)
    if not request.tool_id:
        raise HTTPException(status_code=400, detail="tool_id required for scheduling mode")

    tool_res = supabase.table("tools").select("*").eq("id", request.tool_id).execute()
    if not tool_res.data:
        raise HTTPException(status_code=404, detail="Tool not found")
    tool = tool_res.data[0]

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


# ============ ElevenLabs Webhook ============

class LinkConversationRequest(BaseModel):
    conversation_id: str
    repo_id: str


@router.post("/webhook/elevenlabs")
async def elevenlabs_webhook(request: Request):
    """
    Receive conversation data from ElevenLabs webhook.

    ElevenLabs sends POST with conversation transcript when call ends.
    Configure webhook URL in ElevenLabs dashboard: {WEBHOOK_BASE_URL}/api/voice/webhook/elevenlabs
    """
    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON")

    print(f"ElevenLabs webhook received: {json.dumps(payload, indent=2)[:500]}")

    conversation_id = payload.get("conversation_id")
    if not conversation_id:
        return {"status": "ignored", "reason": "no conversation_id"}

    # Extract transcript
    transcript = payload.get("transcript", [])
    transcript_text = []
    for item in transcript:
        speaker = item.get("role", item.get("speaker", "unknown"))
        text = item.get("message", item.get("text", ""))
        if text:
            transcript_text.append({"speaker": speaker, "text": text})

    # Extract any analysis/summary from payload
    analysis = payload.get("analysis", {})

    # Store in voice_conversations table (create if needed)
    conversation_data = {
        "conversation_id": conversation_id,
        "transcript": transcript_text,
        "analysis": analysis,
        "raw_payload": payload,
        "status": payload.get("status", "completed"),
    }

    # Try to store - table may not exist yet
    try:
        supabase.table("voice_conversations").upsert(
            conversation_data,
            on_conflict="conversation_id"
        ).execute()
    except Exception as e:
        print(f"Failed to store conversation (table may not exist): {e}")
        # Store in memory as fallback
        _session_repo_map[f"conv_{conversation_id}"] = json.dumps(conversation_data)

    return {"status": "received", "conversation_id": conversation_id}


@router.post("/link-conversation")
async def link_conversation(request: LinkConversationRequest):
    """
    Link a conversation to a repo (called by frontend after conversation ends).
    Stores conversation context for use in email composition.
    """
    # Try to get from voice_conversations table
    conversation_data = None
    try:
        result = supabase.table("voice_conversations").select("*").eq(
            "conversation_id", request.conversation_id
        ).single().execute()
        if result.data:
            conversation_data = result.data
    except Exception:
        pass

    # Fallback: fetch from ElevenLabs API
    if not conversation_data:
        try:
            summary = await elevenlabs.get_conversation_summary(request.conversation_id)
            conversation_data = {
                "conversation_id": request.conversation_id,
                "transcript": [{"speaker": t.speaker, "text": t.text} for t in summary.transcript],
                "status": summary.status,
            }
        except Exception as e:
            print(f"Could not fetch conversation: {e}")

    if not conversation_data:
        raise HTTPException(status_code=404, detail="Conversation not found")

    # Update repo with last conversation
    try:
        supabase.table("repos").update({
            "last_conversation": conversation_data
        }).eq("id", request.repo_id).execute()
    except Exception as e:
        print(f"Failed to update repo (column may not exist): {e}")
        # Store mapping in memory
        _session_repo_map[request.repo_id] = conversation_data

    return {
        "status": "linked",
        "repo_id": request.repo_id,
        "conversation_id": request.conversation_id,
    }


@router.get("/conversation/{repo_id}")
async def get_repo_conversation(repo_id: str):
    """Get the last conversation for a repo."""
    # Try DB first
    try:
        result = supabase.table("repos").select("last_conversation").eq("id", repo_id).single().execute()
        if result.data and result.data.get("last_conversation"):
            return result.data["last_conversation"]
    except Exception:
        pass

    # Fallback to memory
    if repo_id in _session_repo_map:
        data = _session_repo_map[repo_id]
        if isinstance(data, str):
            return json.loads(data)
        return data

    raise HTTPException(status_code=404, detail="No conversation found for repo")


# ============ ElevenLabs Client Tools ============

class GetEmailContextRequest(BaseModel):
    repo_id: str
    tool_id: Optional[str] = None


class CaptureInterestRequest(BaseModel):
    repo_id: str
    interest: str
    tool_name: Optional[str] = None


@router.post("/tool/get-email-context")
async def get_email_context(request: GetEmailContextRequest):
    """
    ElevenLabs client tool: Get context for email drafting discussion.
    Returns repo fingerprint, recommended tools, and match reasons.
    """
    # Get repo
    try:
        repo_result = supabase.table("repos").select("*").eq("id", request.repo_id).single().execute()
        if not repo_result.data:
            return {"error": "Repo not found", "project": None}
        repo = repo_result.data
    except Exception as e:
        print(f"get_email_context error: {e}")
        return {"error": str(e), "project": None}
    fingerprint = repo.get("fingerprint", {})
    if isinstance(fingerprint, str):
        try:
            fingerprint = json.loads(fingerprint)
        except Exception:
            fingerprint = {}

    # Get recommendations if tool_id specified
    tool_info = None
    match_reasons = []
    if request.tool_id:
        tool_result = supabase.table("tools").select("*").eq("id", request.tool_id).single().execute()
        if tool_result.data:
            tool_info = {
                "name": tool_result.data.get("name"),
                "category": tool_result.data.get("category"),
                "description": tool_result.data.get("description"),
            }

    # Build context for agent
    tech_stack = fingerprint.get("tech_stack", fingerprint.get("stack", {}))
    stack_list = []
    if isinstance(tech_stack, dict):
        for category, techs in tech_stack.items():
            if isinstance(techs, list):
                stack_list.extend(techs)

    return {
        "project": {
            "industry": fingerprint.get("industry", "software"),
            "project_type": fingerprint.get("project_type", "application"),
            "tech_stack": stack_list[:10],
            "keywords": fingerprint.get("keywords", [])[:5],
            "use_cases": fingerprint.get("use_cases", [])[:3],
        },
        "tool": tool_info,
        "gaps": fingerprint.get("gaps", [])[:3],
        "suggestions": "Ask the user what specific features they're interested in and what problems they want to solve.",
    }


@router.post("/tool/capture-interest")
async def capture_interest(request: CaptureInterestRequest):
    """
    ElevenLabs client tool: Capture user's expressed interest during conversation.
    Stores for later use in email composition.
    """
    try:
        print(f"Captured interest for repo {request.repo_id}: {request.interest}")

        # Store in memory (keyed by repo_id)
        key = f"interests_{request.repo_id}"
        existing = _session_repo_map.get(key, [])
        if isinstance(existing, str):
            existing = json.loads(existing)
        if not isinstance(existing, list):
            existing = []

        existing.append({
            "interest": request.interest,
            "tool_name": request.tool_name,
            "timestamp": datetime.utcnow().isoformat(),
        })
        _session_repo_map[key] = existing

        # Also try to store in DB
        try:
            repo_result = supabase.table("repos").select("last_conversation").eq("id", request.repo_id).single().execute()
            if repo_result.data:
                conv = repo_result.data.get("last_conversation") or {}
                if isinstance(conv, str):
                    conv = json.loads(conv)
                conv["captured_interests"] = existing
                supabase.table("repos").update({"last_conversation": conv}).eq("id", request.repo_id).execute()
        except Exception as e:
            print(f"Could not persist interest to DB: {e}")

        return {"status": "captured", "interest": request.interest}
    except Exception as e:
        print(f"capture_interest error: {e}")
        return {"status": "error", "error": str(e)}
