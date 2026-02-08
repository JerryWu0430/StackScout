"""Twilio client for outbound PSTN calls with ElevenLabs integration."""

import os
from twilio.rest import Client
from twilio.twiml.voice_response import VoiceResponse, Connect
from typing import Optional
from pydantic import BaseModel


TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER")
WEBHOOK_BASE_URL = os.getenv("WEBHOOK_BASE_URL", "http://localhost:8000")
ELEVENLABS_AGENT_ID = os.getenv("ELEVENLABS_AGENT_ID")


class CallRequest(BaseModel):
    """Request to initiate an outbound call."""
    provider_phone: str
    provider_name: str
    service_type: str
    preferred_dates: list[str]
    preferred_times: list[str]
    call_id: str  # Our internal call ID for tracking


class CallResult(BaseModel):
    """Result of call initiation."""
    call_sid: str
    status: str
    call_id: str


def get_twilio_client() -> Client:
    """Get Twilio client instance."""
    if not TWILIO_ACCOUNT_SID or not TWILIO_AUTH_TOKEN:
        raise ValueError("TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN required")
    return Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)


def initiate_call(request: CallRequest) -> CallResult:
    """
    Initiate outbound call to provider.

    Twilio will call the provider's phone, then connect to ElevenLabs
    via the TwiML webhook response.
    """
    client = get_twilio_client()

    if not TWILIO_PHONE_NUMBER:
        raise ValueError("TWILIO_PHONE_NUMBER not configured")

    # Status callback URL for call events
    status_callback = f"{WEBHOOK_BASE_URL}/api/twilio/status"

    # TwiML URL that returns instructions to connect to ElevenLabs
    twiml_url = f"{WEBHOOK_BASE_URL}/api/twilio/connect?call_id={request.call_id}"

    call = client.calls.create(
        to=request.provider_phone,
        from_=TWILIO_PHONE_NUMBER,
        url=twiml_url,
        status_callback=status_callback,
        status_callback_event=["initiated", "ringing", "answered", "completed"],
        status_callback_method="POST",
        method="POST",
    )

    return CallResult(
        call_sid=call.sid,
        status=call.status,
        call_id=request.call_id,
    )


def generate_connect_twiml(call_id: str, first_message: Optional[str] = None) -> str:
    """
    Generate TwiML to connect Twilio call to ElevenLabs Conversational AI.

    Uses the <Connect><Stream> approach for real-time audio streaming.
    """
    if not ELEVENLABS_AGENT_ID:
        raise ValueError("ELEVENLABS_AGENT_ID not configured")

    response = VoiceResponse()

    # Connect to ElevenLabs via WebSocket stream
    connect = Connect()

    # ElevenLabs WebSocket URL for Twilio integration
    # Docs: https://elevenlabs.io/docs/conversational-ai/guides/conversational-ai-twilio
    stream_url = f"wss://api.elevenlabs.io/v1/convai/conversation?agent_id={ELEVENLABS_AGENT_ID}"

    # Add custom parameters for context
    stream = connect.stream(url=stream_url)
    stream.parameter(name="call_id", value=call_id)

    if first_message:
        stream.parameter(name="first_message", value=first_message)

    response.append(connect)

    return str(response)


def end_call(call_sid: str) -> bool:
    """End an active call."""
    client = get_twilio_client()
    try:
        client.calls(call_sid).update(status="completed")
        return True
    except Exception:
        return False


def get_call_status(call_sid: str) -> dict:
    """Get current status of a call."""
    client = get_twilio_client()
    call = client.calls(call_sid).fetch()
    return {
        "sid": call.sid,
        "status": call.status,
        "duration": call.duration,
        "direction": call.direction,
    }
