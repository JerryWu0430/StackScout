"""Google Calendar integration service for demo scheduling."""

import os
from datetime import datetime, timedelta
from typing import Optional
from dataclasses import dataclass

from google.oauth2 import service_account
from googleapiclient.discovery import build


SCOPES = ["https://www.googleapis.com/auth/calendar"]
CALENDAR_ID = os.getenv("GOOGLE_CALENDAR_ID", "primary")
SERVICE_ACCOUNT_FILE = os.getenv("GOOGLE_SERVICE_ACCOUNT_FILE", "credentials.json")


@dataclass
class TimeSlot:
    start: datetime
    end: datetime
    formatted: str


@dataclass
class Event:
    id: str
    summary: str
    start: datetime
    end: datetime
    meet_link: Optional[str]
    attendees: list[str]


def _get_calendar_service():
    """Build authenticated Calendar API service."""
    credentials = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES
    )
    return build("calendar", "v3", credentials=credentials)


def _format_slot(dt: datetime) -> str:
    """Format datetime as 'Tuesday, Feb 10 at 2:00 PM'."""
    return dt.strftime("%A, %b %d at %-I:%M %p")


def get_available_slots(days_ahead: int = 7, slot_duration_minutes: int = 30) -> list[TimeSlot]:
    """Get available time slots for demo scheduling.

    Queries freebusy API to find open slots during business hours (9am-5pm).
    """
    service = _get_calendar_service()

    now = datetime.utcnow()
    time_min = now.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
    time_max = time_min + timedelta(days=days_ahead)

    # Query freebusy
    body = {
        "timeMin": time_min.isoformat() + "Z",
        "timeMax": time_max.isoformat() + "Z",
        "items": [{"id": CALENDAR_ID}],
    }

    freebusy = service.freebusy().query(body=body).execute()
    busy_periods = freebusy["calendars"][CALENDAR_ID]["busy"]

    # Parse busy times
    busy_times = []
    for period in busy_periods:
        start = datetime.fromisoformat(period["start"].replace("Z", "+00:00"))
        end = datetime.fromisoformat(period["end"].replace("Z", "+00:00"))
        busy_times.append((start.replace(tzinfo=None), end.replace(tzinfo=None)))

    # Generate available slots during business hours
    available = []
    current_day = time_min

    while current_day < time_max:
        # Business hours: 9am-5pm
        slot_start = current_day.replace(hour=9, minute=0)
        day_end = current_day.replace(hour=17, minute=0)

        while slot_start + timedelta(minutes=slot_duration_minutes) <= day_end:
            slot_end = slot_start + timedelta(minutes=slot_duration_minutes)

            # Check if slot overlaps any busy period
            is_busy = any(
                not (slot_end <= busy_start or slot_start >= busy_end)
                for busy_start, busy_end in busy_times
            )

            if not is_busy and slot_start > now:
                available.append(TimeSlot(
                    start=slot_start,
                    end=slot_end,
                    formatted=_format_slot(slot_start)
                ))

            slot_start = slot_end

        current_day += timedelta(days=1)

    return available


def create_demo_event(
    tool_name: str,
    slot: TimeSlot,
    attendee_email: str,
    description: str = ""
) -> Event:
    """Create a demo event with Google Meet link.

    Args:
        tool_name: Name of tool being demoed
        slot: TimeSlot for the event
        attendee_email: Email of attendee to invite
        description: Optional event description
    """
    service = _get_calendar_service()

    event_body = {
        "summary": f"StackScout Demo: {tool_name}",
        "description": description or f"Demo session for {tool_name} via StackScout",
        "start": {
            "dateTime": slot.start.isoformat(),
            "timeZone": "UTC",
        },
        "end": {
            "dateTime": slot.end.isoformat(),
            "timeZone": "UTC",
        },
        "attendees": [{"email": attendee_email}],
        "conferenceData": {
            "createRequest": {
                "requestId": f"stackscout-{slot.start.timestamp()}",
                "conferenceSolutionKey": {"type": "hangoutsMeet"},
            }
        },
    }

    created = service.events().insert(
        calendarId=CALENDAR_ID,
        body=event_body,
        conferenceDataVersion=1,
        sendUpdates="all",
    ).execute()

    return Event(
        id=created["id"],
        summary=created["summary"],
        start=slot.start,
        end=slot.end,
        meet_link=created.get("hangoutLink"),
        attendees=[attendee_email],
    )
