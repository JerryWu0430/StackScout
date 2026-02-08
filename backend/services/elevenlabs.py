"""ElevenLabs Conversational AI service for voice interactions."""

import os
import httpx
from typing import Optional
from pydantic import BaseModel
from datetime import datetime


ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
ELEVENLABS_AGENT_ID = os.getenv("ELEVENLABS_AGENT_ID")
ELEVENLABS_BASE_URL = "https://api.elevenlabs.io/v1"
WEBHOOK_BASE_URL = os.getenv("WEBHOOK_BASE_URL", "http://localhost:8000")


# ============ Original StackScout Models ============

class ConversationContext(BaseModel):
    """Context for voice conversation (StackScout scheduling)."""
    tool_name: str
    tool_description: str
    repo_stack: list[str]
    available_times: list[str]


class AnalysisContext(BaseModel):
    """Context for analysis narration voice conversation."""
    repo_stack: list[str]
    gaps: list[str]
    risk_flags: list[str]
    recommendations_context: str = ""


# ============ CallPilot Models ============

class CallPilotContext(BaseModel):
    """Context for CallPilot appointment scheduling calls."""
    provider_name: str
    service_type: str  # 'dentist', 'doctor', 'salon'
    preferred_dates: list[str]
    preferred_times: list[str]  # 'morning', 'afternoon', 'evening'
    user_name: str = "the caller"
    notes: Optional[str] = None


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
    """Build agent system prompt from context (StackScout scheduling)."""
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


def _build_analysis_system_prompt(context: AnalysisContext) -> str:
    """Build system prompt for analysis narration mode."""
    stack_str = ", ".join(context.repo_stack) if context.repo_stack else "no specific technologies detected"
    gaps_str = "\n- ".join(context.gaps) if context.gaps else "None identified"
    risks_str = "\n- ".join(context.risk_flags) if context.risk_flags else "None identified"

    return f"""You are explaining a repository analysis to a developer. Be conversational and helpful.

REPOSITORY ANALYSIS:

Tech Stack Detected:
{stack_str}

Gaps & Missing Practices:
- {gaps_str}

Risk Flags:
- {risks_str}

Context: {context.recommendations_context}

YOUR TASK:
1. Start with a brief greeting and overview of what you found
2. Walk through the tech stack - mention the key technologies detected
3. Discuss the gaps - explain why they matter and how to address them
4. Highlight any risk flags - be constructive, not alarming
5. Briefly mention that there are tool recommendations in the Recommendations tab
6. Ask if they have questions about any specific finding

PERSONA:
- Conversational and helpful, like a senior dev colleague
- Be concise but thorough
- If they ask questions, provide detailed but practical answers
- Avoid jargon unless they use it first
- Be honest about limitations - if something is unclear, say so"""


def build_callpilot_system_prompt(context: CallPilotContext) -> str:
    """Build system prompt for CallPilot appointment scheduling agent."""
    dates_str = ", ".join(context.preferred_dates) if context.preferred_dates else "any available date"
    times_str = ", ".join(context.preferred_times) if context.preferred_times else "any time"

    return f"""You are a professional AI assistant making an outbound phone call to schedule an appointment.

CALLING: {context.provider_name}
SERVICE TYPE: {context.service_type}
CALLER'S PREFERRED DATES: {dates_str}
CALLER'S PREFERRED TIMES: {times_str}
{f"NOTES: {context.notes}" if context.notes else ""}

YOUR TASK:
1. Politely identify yourself as an AI scheduling assistant calling on behalf of a patient/client
2. Request to schedule a {context.service_type} appointment
3. Ask about available times that match the caller's preferences
4. When offered slots, use the record_available_slot tool to save them
5. Select the best matching slot and confirm the booking
6. Use confirm_booking tool when appointment is confirmed
7. Thank them and end the call professionally

CONVERSATION GUIDELINES:
- Be polite, professional, and efficient
- Speak naturally but concisely
- If they ask questions, answer honestly that you're an AI assistant
- If no slots match, ask about alternative dates/times
- If they can't help, thank them and end politely
- Never be pushy or rude

AVAILABLE TOOLS:
- check_user_calendar(datetime): Check if the user is available at a specific time
- record_available_slot(date, time, notes): Record an available appointment slot
- confirm_booking(datetime, confirmation_number): Confirm the final booking

EXAMPLE OPENING:
"Hello, this is an automated scheduling assistant. I'm calling to book a {context.service_type} appointment for one of our users. Do you have any availability in the next few days?"
"""


# Tool definitions for ElevenLabs agent
CALLPILOT_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "check_user_calendar",
            "description": "Check if the user (person we're booking for) is available at a specific date and time",
            "parameters": {
                "type": "object",
                "properties": {
                    "datetime": {
                        "type": "string",
                        "description": "The datetime to check in ISO format (e.g., '2024-01-15T10:00:00')"
                    }
                },
                "required": ["datetime"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "record_available_slot",
            "description": "Record an available appointment slot offered by the provider",
            "parameters": {
                "type": "object",
                "properties": {
                    "date": {
                        "type": "string",
                        "description": "The date of the slot (e.g., '2024-01-15' or 'Monday')"
                    },
                    "time": {
                        "type": "string",
                        "description": "The time of the slot (e.g., '10:00 AM' or '2:30 PM')"
                    },
                    "notes": {
                        "type": "string",
                        "description": "Any additional notes about the slot"
                    }
                },
                "required": ["date", "time"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "confirm_booking",
            "description": "Confirm the final appointment booking",
            "parameters": {
                "type": "object",
                "properties": {
                    "datetime": {
                        "type": "string",
                        "description": "The confirmed appointment datetime"
                    },
                    "confirmation_number": {
                        "type": "string",
                        "description": "Confirmation number if provided by the receptionist"
                    }
                },
                "required": ["datetime"]
            }
        }
    }
]


async def create_conversation(context: ConversationContext) -> ConversationSession:
    """
    Create a new conversation session with signed URL for scheduling mode.

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


async def create_analysis_conversation(context: AnalysisContext) -> ConversationSession:
    """
    Create a new conversation session for analysis narration mode.

    The voice agent will explain the repository analysis to the user.
    """
    if not ELEVENLABS_API_KEY:
        raise ValueError("ELEVENLABS_API_KEY not configured")
    if not ELEVENLABS_AGENT_ID:
        raise ValueError("ELEVENLABS_AGENT_ID not configured")

    # Build system prompt for analysis mode (used by ElevenLabs agent config)
    # Note: The actual prompt is configured in the ElevenLabs dashboard
    # This is just for reference/documentation
    _ = _build_analysis_system_prompt(context)

    async with httpx.AsyncClient() as client:
        # Get signed URL for WebSocket connection
        response = await client.get(
            f"{ELEVENLABS_BASE_URL}/convai/conversation/get-signed-url",
            params={"agent_id": ELEVENLABS_AGENT_ID},
            headers=_get_headers(),
        )
        response.raise_for_status()
        data = response.json()

        signed_url = data["signed_url"]
        session_id = f"analysis_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"

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
