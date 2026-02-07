"""ElevenLabs Conversational AI service for real-time voice demos."""

import os
import httpx
from typing import Optional
from pydantic import BaseModel
from datetime import datetime


ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
ELEVENLABS_AGENT_ID = os.getenv("ELEVENLABS_AGENT_ID")
ELEVENLABS_BASE_URL = "https://api.elevenlabs.io/v1"


class ConversationContext(BaseModel):
    """Context for voice conversation."""
    tool_name: str
    tool_description: str
    repo_stack: list[str]  # Technologies in user's repo
    available_times: list[str]  # Demo time slots


class ConversationSession(BaseModel):
    """Active conversation session info."""
    session_id: str
    signed_url: str
    agent_id: str
    created_at: datetime


class TranscriptItem(BaseModel):
    """Single transcript entry."""
    speaker: str  # "user" or "agent"
    text: str
    timestamp: Optional[str] = None


class ConversationSummary(BaseModel):
    """Summary of a completed conversation."""
    conversation_id: str
    status: str
    transcript: list[TranscriptItem]
    duration_seconds: Optional[int] = None


def _get_headers() -> dict:
    """Get API headers."""
    return {"xi-api-key": ELEVENLABS_API_KEY}


def _build_system_prompt(context: ConversationContext) -> str:
    """Build agent system prompt from context."""
    stack_str = ", ".join(context.repo_stack) if context.repo_stack else "various technologies"
    times_str = ", ".join(context.available_times) if context.available_times else "flexible times"

    return f"""You are a professional sales development representative for {context.tool_name}.

ABOUT THE TOOL:
{context.tool_description}

USER CONTEXT:
- Their tech stack: {stack_str}
- Available demo times: {times_str}

YOUR GOALS:
1. Greet warmly but concisely
2. Qualify their interest - understand their use case
3. Explain how {context.tool_name} fits their stack
4. Propose a demo time from available slots
5. Confirm booking details

PERSONA:
- Professional, friendly, concise
- Avoid filler words
- Get to the point quickly
- Listen actively, respond relevantly"""


async def create_conversation(context: ConversationContext) -> ConversationSession:
    """
    Create a new conversation session with signed URL.

    The signed URL is used by the frontend to establish a WebSocket
    connection for real-time voice conversation.
    """
    if not ELEVENLABS_API_KEY:
        raise ValueError("ELEVENLABS_API_KEY not configured")
    if not ELEVENLABS_AGENT_ID:
        raise ValueError("ELEVENLABS_AGENT_ID not configured")

    async with httpx.AsyncClient() as client:
        # Get signed URL for WebSocket connection
        response = await client.get(
            f"{ELEVENLABS_BASE_URL}/convai/conversation/get-signed-url",
            params={"agent_id": ELEVENLABS_AGENT_ID},
            headers=_get_headers(),
        )
        response.raise_for_status()
        data = response.json()

        # Extract conversation/session ID from signed URL
        signed_url = data["signed_url"]
        # URL format: wss://...?agent_id=X&conversation_signature=Y
        session_id = f"conv_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"

        return ConversationSession(
            session_id=session_id,
            signed_url=signed_url,
            agent_id=ELEVENLABS_AGENT_ID,
            created_at=datetime.utcnow(),
        )


async def get_conversation_summary(conversation_id: str) -> ConversationSummary:
    """
    Get summary and transcript of a completed conversation.

    Call this after conversation ends to retrieve what was discussed.
    """
    if not ELEVENLABS_API_KEY:
        raise ValueError("ELEVENLABS_API_KEY not configured")

    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{ELEVENLABS_BASE_URL}/convai/conversations/{conversation_id}",
            headers=_get_headers(),
        )
        response.raise_for_status()
        data = response.json()

        transcript = [
            TranscriptItem(
                speaker=item.get("speaker", "unknown"),
                text=item.get("text", ""),
                timestamp=item.get("timestamp"),
            )
            for item in data.get("transcript", [])
        ]

        return ConversationSummary(
            conversation_id=conversation_id,
            status=data.get("status", "unknown"),
            transcript=transcript,
        )


async def get_signed_url(agent_id: Optional[str] = None) -> str:
    """
    Get a signed URL for WebSocket connection.

    Simpler helper when you don't need full session object.
    """
    if not ELEVENLABS_API_KEY:
        raise ValueError("ELEVENLABS_API_KEY not configured")

    target_agent = agent_id or ELEVENLABS_AGENT_ID
    if not target_agent:
        raise ValueError("No agent_id provided and ELEVENLABS_AGENT_ID not configured")

    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{ELEVENLABS_BASE_URL}/convai/conversation/get-signed-url",
            params={"agent_id": target_agent},
            headers=_get_headers(),
        )
        response.raise_for_status()
        return response.json()["signed_url"]
