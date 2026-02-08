"""Email drafts API endpoints for demo booking."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import uuid

from db.supabase import supabase
from db.models import DraftEmail, TimeSlot, Tool
from services.email_extractor import extract_contact_email, extract_company_name
from services.email_composer import compose_demo_email
from services.email_sender import send_email, send_batch_emails
from services.calendar import get_available_slots, get_optimal_demo_slots, TimeSlot as CalendarTimeSlot
from services.recommender import get_recommendations


router = APIRouter(prefix="/api/email-drafts", tags=["email-drafts"])


class CreateDraftRequest(BaseModel):
    repo_id: str
    tool_id: str


class UpdateDraftRequest(BaseModel):
    subject: Optional[str] = None
    body: Optional[str] = None
    to_email: Optional[str] = None
    to_name: Optional[str] = None
    selected_time: Optional[dict] = None  # TimeSlot as dict


class BatchSendRequest(BaseModel):
    draft_ids: list[str]


class DraftResponse(BaseModel):
    id: str
    repo_id: str
    tool_id: str
    to_email: Optional[str]
    to_name: Optional[str]
    subject: str
    body: str
    context: dict
    suggested_times: list[dict]
    selected_time: Optional[dict]
    status: str
    created_at: Optional[str]
    sent_at: Optional[str]
    tool_name: Optional[str] = None
    tool_url: Optional[str] = None


class AvailabilityResponse(BaseModel):
    slots: list[dict]


def _calendar_slot_to_dict(slot: CalendarTimeSlot) -> dict:
    return {
        "start": slot.start.isoformat(),
        "end": slot.end.isoformat(),
        "formatted": slot.formatted,
    }


@router.post("/", response_model=DraftResponse)
async def create_draft(request: CreateDraftRequest):
    """Create a draft email for a tool recommendation."""
    # Get tool info
    tool_result = supabase.table("tools").select("*").eq("id", request.tool_id).single().execute()
    if not tool_result.data:
        raise HTTPException(status_code=404, detail="Tool not found")

    tool_data = tool_result.data
    tool = Tool(**tool_data)

    # Get repo fingerprint and conversation context
    repo_result = supabase.table("repos").select("*").eq("id", request.repo_id).single().execute()
    if not repo_result.data:
        raise HTTPException(status_code=404, detail="Repo not found")

    fingerprint = repo_result.data.get("fingerprint", {})
    if isinstance(fingerprint, str):
        import json
        fingerprint = json.loads(fingerprint)

    # Get conversation context if available
    conversation_context = repo_result.data.get("last_conversation")
    if isinstance(conversation_context, str):
        import json
        try:
            conversation_context = json.loads(conversation_context)
        except Exception:
            conversation_context = None

    # Get recommendation context from recommender service
    match_reasons = []
    explanation = ""
    try:
        recommendations = get_recommendations(request.repo_id, limit=20)
        for rec in recommendations:
            if rec.tool.id == request.tool_id:
                match_reasons = [{"type": r.type, "matched": r.matched, "score_contribution": r.score_contribution} for r in rec.match_reasons]
                explanation = rec.explanation
                break
    except Exception as e:
        # If recommender fails, continue with empty match_reasons
        print(f"Warning: Could not get recommendations: {e}")

    # Extract contact email from tool URL
    to_email = await extract_contact_email(tool.url or tool.booking_url)
    to_name = await extract_company_name(tool.url) if tool.url else None

    # Get suggested meeting times (optional - skip if calendar not configured)
    calendar_slots = []
    suggested_times = []
    model_slots = []
    try:
        calendar_slots = get_available_slots(days_ahead=7)[:6]
        suggested_times = [_calendar_slot_to_dict(s) for s in calendar_slots]
        model_slots = [
            TimeSlot(start=s.start, end=s.end, formatted=s.formatted)
            for s in calendar_slots[:3]
        ]
    except Exception as e:
        # Calendar not configured - continue without time slots
        print(f"Calendar not available: {e}")

    # Compose email using LLM (include conversation context if available)
    subject, body = compose_demo_email(
        tool=tool,
        fingerprint=fingerprint,
        match_reasons=match_reasons,
        explanation=explanation,
        suggested_times=model_slots,
        conversation_context=conversation_context,
    )

    # Build context for storage
    context = {
        "tool": tool_data,
        "fingerprint": fingerprint,
        "match_reasons": match_reasons,
        "explanation": explanation,
        "conversation_context": conversation_context,
    }

    # Save draft to DB
    draft_id = str(uuid.uuid4())
    draft_data = {
        "id": draft_id,
        "repo_id": request.repo_id,
        "tool_id": request.tool_id,
        "to_email": to_email,
        "to_name": to_name,
        "subject": subject,
        "body": body,
        "context": context,
        "suggested_times": suggested_times,
        "selected_time": None,
        "status": "draft",
    }

    result = supabase.table("draft_emails").insert(draft_data).execute()
    if not result.data:
        raise HTTPException(status_code=500, detail="Failed to create draft")

    return DraftResponse(
        **result.data[0],
        tool_name=tool.name,
        tool_url=tool.url,
    )


@router.get("/repo/{repo_id}", response_model=list[DraftResponse])
async def list_drafts(repo_id: str):
    """List all drafts for a repo."""
    result = supabase.table("draft_emails").select("*, tools(name, url)").eq("repo_id", repo_id).order("created_at", desc=True).execute()

    drafts = []
    for row in result.data or []:
        tool_info = row.pop("tools", {}) or {}
        drafts.append(DraftResponse(
            **row,
            tool_name=tool_info.get("name"),
            tool_url=tool_info.get("url"),
        ))

    return drafts


@router.get("/{draft_id}", response_model=DraftResponse)
async def get_draft(draft_id: str):
    """Get a single draft by ID."""
    result = supabase.table("draft_emails").select("*, tools(name, url)").eq("id", draft_id).single().execute()

    if not result.data:
        raise HTTPException(status_code=404, detail="Draft not found")

    tool_info = result.data.pop("tools", {}) or {}
    return DraftResponse(
        **result.data,
        tool_name=tool_info.get("name"),
        tool_url=tool_info.get("url"),
    )


@router.patch("/{draft_id}", response_model=DraftResponse)
async def update_draft(draft_id: str, request: UpdateDraftRequest):
    """Update a draft's subject, body, email, or selected time."""
    update_data = {}
    if request.subject is not None:
        update_data["subject"] = request.subject
    if request.body is not None:
        update_data["body"] = request.body
    if request.to_email is not None:
        update_data["to_email"] = request.to_email
    if request.to_name is not None:
        update_data["to_name"] = request.to_name
    if request.selected_time is not None:
        update_data["selected_time"] = request.selected_time
        update_data["status"] = "ready"

    if not update_data:
        raise HTTPException(status_code=400, detail="No fields to update")

    result = supabase.table("draft_emails").update(update_data).eq("id", draft_id).execute()

    if not result.data:
        raise HTTPException(status_code=404, detail="Draft not found")

    # Fetch full draft with tool info
    return await get_draft(draft_id)


@router.delete("/{draft_id}")
async def delete_draft(draft_id: str):
    """Delete a draft."""
    result = supabase.table("draft_emails").delete().eq("id", draft_id).execute()

    if not result.data:
        raise HTTPException(status_code=404, detail="Draft not found")

    return {"deleted": True}


@router.post("/{draft_id}/send")
async def send_single(draft_id: str):
    """Send a single draft email."""
    # Get draft
    draft_result = supabase.table("draft_emails").select("*").eq("id", draft_id).single().execute()

    if not draft_result.data:
        raise HTTPException(status_code=404, detail="Draft not found")

    draft = draft_result.data

    if not draft.get("to_email"):
        raise HTTPException(status_code=400, detail="No recipient email set")

    # Send email
    result = send_email(
        to_email=draft["to_email"],
        subject=draft["subject"],
        body=draft["body"],
        to_name=draft.get("to_name"),
    )

    if result.success:
        # Update draft status
        supabase.table("draft_emails").update({
            "status": "sent",
            "sent_at": datetime.utcnow().isoformat(),
        }).eq("id", draft_id).execute()

        return {"success": True, "email_id": result.email_id}
    else:
        # Check if it's a config error vs send error
        if "not configured" in (result.error or ""):
            raise HTTPException(status_code=503, detail="Email service not configured. Set RESEND_API_KEY in .env")

        # Mark as failed
        supabase.table("draft_emails").update({
            "status": "failed",
        }).eq("id", draft_id).execute()

        raise HTTPException(status_code=500, detail=f"Failed to send: {result.error}")


@router.post("/batch-send")
async def batch_send(request: BatchSendRequest):
    """Send multiple draft emails with optimized timing."""
    if not request.draft_ids:
        raise HTTPException(status_code=400, detail="No drafts specified")

    # Get all drafts
    result = supabase.table("draft_emails").select("*").in_("id", request.draft_ids).execute()

    if not result.data:
        raise HTTPException(status_code=404, detail="No drafts found")

    # Filter drafts with valid emails
    valid_drafts = [d for d in result.data if d.get("to_email")]

    if not valid_drafts:
        raise HTTPException(status_code=400, detail="No drafts with valid recipient emails")

    # Prepare emails for batch send
    emails = [
        {
            "to_email": d["to_email"],
            "subject": d["subject"],
            "body": d["body"],
            "to_name": d.get("to_name"),
        }
        for d in valid_drafts
    ]

    # Send with 2-second delay between emails (rate limiting)
    results = send_batch_emails(emails, delay_seconds=2)

    # Update statuses
    sent_ids = []
    failed_ids = []

    for draft, send_result in zip(valid_drafts, results):
        if send_result.success:
            supabase.table("draft_emails").update({
                "status": "sent",
                "sent_at": datetime.utcnow().isoformat(),
            }).eq("id", draft["id"]).execute()
            sent_ids.append(draft["id"])
        else:
            supabase.table("draft_emails").update({
                "status": "failed",
            }).eq("id", draft["id"]).execute()
            failed_ids.append(draft["id"])

    return {
        "sent": len(sent_ids),
        "failed": len(failed_ids),
        "sent_ids": sent_ids,
        "failed_ids": failed_ids,
    }


@router.get("/availability", response_model=AvailabilityResponse)
async def get_availability(tool_count: int = 1, days_ahead: int = 7):
    """Get optimal calendar slots for demo scheduling."""
    try:
        if tool_count > 1:
            slots = get_optimal_demo_slots(tool_count, days_ahead)
        else:
            slots = get_available_slots(days_ahead)[:10]
        return AvailabilityResponse(slots=[_calendar_slot_to_dict(s) for s in slots])
    except Exception:
        # Calendar not configured
        return AvailabilityResponse(slots=[])
