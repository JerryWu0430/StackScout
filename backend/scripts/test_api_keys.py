#!/usr/bin/env python3
"""
Test API keys and service connectivity.

Usage:
    python scripts/test_api_keys.py
"""

import os
import sys
from pathlib import Path
from typing import Optional, Tuple

from dotenv import load_dotenv

load_dotenv()


def test_supabase() -> Tuple[bool, str]:
    """Test Supabase connection by querying tools table."""
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")

    if not url or not key:
        return False, "Missing SUPABASE_URL or SUPABASE_KEY"

    try:
        from supabase import create_client
        client = create_client(url, key)
        result = client.table("tools").select("id").limit(1).execute()
        return True, "Connected (tools table accessible)"
    except Exception as e:
        return False, str(e)


def test_github() -> Tuple[bool, str]:
    """Test GitHub token via rate limit endpoint."""
    token = os.getenv("GITHUB_TOKEN")

    if not token:
        return False, "Missing GITHUB_TOKEN"

    try:
        import requests
        resp = requests.get(
            "https://api.github.com/rate_limit",
            headers={"Authorization": f"token {token}"},
            timeout=10
        )
        if resp.status_code == 200:
            remaining = resp.json()["rate"]["remaining"]
            return True, f"Valid ({remaining} requests remaining)"
        return False, f"{resp.status_code} {resp.reason}"
    except Exception as e:
        return False, str(e)


def test_openai() -> Tuple[bool, str]:
    """Test OpenAI by generating embedding."""
    key = os.getenv("OPENAI_API_KEY")

    if not key:
        return False, "Missing OPENAI_API_KEY"

    try:
        from openai import OpenAI
        client = OpenAI(api_key=key)
        resp = client.embeddings.create(
            model="text-embedding-3-small",
            input="test"
        )
        dims = len(resp.data[0].embedding)
        return True, f"Valid (embedding returned {dims} dims)"
    except Exception as e:
        return False, str(e)


def test_elevenlabs() -> Tuple[bool, str]:
    """Test ElevenLabs via user info endpoint."""
    key = os.getenv("ELEVENLABS_API_KEY")

    if not key:
        return False, "Missing ELEVENLABS_API_KEY"

    try:
        import requests
        resp = requests.get(
            "https://api.elevenlabs.io/v1/user",
            headers={"xi-api-key": key},
            timeout=10
        )
        if resp.status_code == 200:
            return True, "Valid (user info retrieved)"
        return False, f"{resp.status_code} {resp.reason}"
    except Exception as e:
        return False, str(e)


def test_google_calendar() -> Tuple[Optional[bool], str]:
    """Test Google Calendar (optional)."""
    creds_path = os.getenv("GOOGLE_CALENDAR_CREDENTIALS")

    if not creds_path:
        return None, "Skipped (no credentials file)"

    if not Path(creds_path).exists():
        return None, f"Skipped (file not found: {creds_path})"

    try:
        from google.oauth2 import service_account
        from googleapiclient.discovery import build
        from datetime import datetime, timedelta

        creds = service_account.Credentials.from_service_account_file(
            creds_path,
            scopes=["https://www.googleapis.com/auth/calendar.readonly"]
        )
        service = build("calendar", "v3", credentials=creds)

        now = datetime.utcnow()
        body = {
            "timeMin": now.isoformat() + "Z",
            "timeMax": (now + timedelta(days=1)).isoformat() + "Z",
            "items": [{"id": "primary"}]
        }
        service.freebusy().query(body=body).execute()
        return True, "Valid (freebusy query succeeded)"
    except Exception as e:
        return False, str(e)


def main():
    print("Testing API Keys...\n")

    tests = [
        ("Supabase", test_supabase),
        ("GitHub", test_github),
        ("OpenAI", test_openai),
        ("ElevenLabs", test_elevenlabs),
        ("Google Calendar", test_google_calendar),
    ]

    results = []
    for name, test_fn in tests:
        success, msg = test_fn()
        results.append((name, success, msg))

        if success is True:
            print(f"✓ {name}: {msg}")
        elif success is False:
            print(f"✗ {name}: {msg}")
        else:  # None = skipped
            print(f"⚠ {name}: {msg}")

    # Summary
    passed = sum(1 for _, s, _ in results if s is True)
    failed = sum(1 for _, s, _ in results if s is False)
    skipped = sum(1 for _, s, _ in results if s is None)

    print(f"\n{passed} passed, {failed} failed, {skipped} skipped")

    if failed > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
