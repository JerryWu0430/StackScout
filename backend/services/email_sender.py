"""Email sending service - Resend API integration."""

import os
from typing import Optional
from dataclasses import dataclass

import resend


FROM_EMAIL = os.getenv("RESEND_FROM_EMAIL", "onboarding@resend.dev")
FROM_NAME = os.getenv("RESEND_FROM_NAME", "StackScout")


@dataclass
class SendResult:
    success: bool
    email_id: Optional[str] = None
    error: Optional[str] = None


def send_email(
    to_email: str,
    subject: str,
    body: str,
    to_name: Optional[str] = None,
    reply_to: Optional[str] = None,
) -> SendResult:
    """
    Send a single email via Resend API.

    Args:
        to_email: Recipient email address
        subject: Email subject line
        body: Plain text email body
        to_name: Optional recipient name
        reply_to: Optional reply-to address
    """
    api_key = os.getenv("RESEND_API_KEY")
    if not api_key:
        return SendResult(success=False, error="RESEND_API_KEY not configured")

    resend.api_key = api_key

    # Override recipient for testing (Resend free tier restriction)
    TEST_EMAIL = os.getenv("RESEND_TEST_EMAIL", "woohaoran@gmail.com")
    to_email = TEST_EMAIL

    try:
        params = {
            "from": f"{FROM_NAME} <{FROM_EMAIL}>",
            "to": [to_email],  # Plain email - name format breaks Resend test mode
            "subject": subject,
            "text": body,
        }

        if reply_to:
            params["reply_to"] = reply_to

        print(f"Sending email to {to_email} with subject: {subject}")
        print(f"Params: {params}")        
        result = resend.Emails.send(params)
        
        print(f"Resend result: {result}")

        # Handle different response formats
        if hasattr(result, 'id'):
            return SendResult(success=True, email_id=result.id)
        elif isinstance(result, dict) and result.get("id"):
            return SendResult(success=True, email_id=result["id"])
        else:
            return SendResult(success=True, email_id=str(result))

    except Exception as e:
        print(f"Resend error: {type(e).__name__}: {e}")
        return SendResult(success=False, error=str(e))


def send_batch_emails(
    emails: list[dict],
    delay_seconds: int = 0,
) -> list[SendResult]:
    """
    Send multiple emails, optionally with delay between them.

    Args:
        emails: List of dicts with to_email, subject, body, to_name (optional)
        delay_seconds: Delay between sends (for rate limiting)

    Returns: List of SendResult for each email
    """
    import time

    results = []
    for i, email in enumerate(emails):
        result = send_email(
            to_email=email["to_email"],
            subject=email["subject"],
            body=email["body"],
            to_name=email.get("to_name"),
            reply_to=email.get("reply_to"),
        )
        results.append(result)

        # Add delay between emails (except last one)
        if delay_seconds > 0 and i < len(emails) - 1:
            time.sleep(delay_seconds)

    return results
