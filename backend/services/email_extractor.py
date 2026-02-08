"""Email extraction service - scrapes contact emails from tool URLs."""

import re
import httpx
from typing import Optional
from urllib.parse import urljoin, urlparse


COMMON_CONTACT_PAGES = ["/contact", "/demo", "/sales", "/get-started", "/pricing"]
COMMON_EMAIL_PREFIXES = ["sales", "demo", "contact", "hello", "info", "support"]


def _extract_emails_from_html(html: str) -> list[str]:
    """Extract all email addresses from HTML content."""
    # Match mailto: links
    mailto_pattern = r'mailto:([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})'
    mailto_emails = re.findall(mailto_pattern, html, re.IGNORECASE)

    # Match plain email addresses
    email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    plain_emails = re.findall(email_pattern, html)

    # Dedupe + filter common junk
    all_emails = list(set(mailto_emails + plain_emails))
    filtered = [
        e for e in all_emails
        if not e.endswith('.png') and not e.endswith('.jpg')
        and 'example.com' not in e and 'placeholder' not in e.lower()
    ]
    return filtered


def _score_email(email: str) -> int:
    """Score email by preference for sales/demo contacts."""
    email_lower = email.lower()
    local = email_lower.split('@')[0]

    # Prioritize sales/demo/contact emails
    if local in COMMON_EMAIL_PREFIXES or any(p in local for p in ['sales', 'demo']):
        return 100
    if 'contact' in local or 'hello' in local:
        return 80
    if 'info' in local or 'support' in local:
        return 60
    return 40


async def extract_contact_email(url: str) -> Optional[str]:
    """
    Extract best contact email from a tool's website.

    Strategy:
    1. Fetch main page, look for mailto: links
    2. Check common contact pages (/contact, /demo, /sales)
    3. Try common email patterns (sales@domain, demo@domain)
    4. Return best match or None for manual input
    """
    if not url:
        return None

    parsed = urlparse(url)
    base_url = f"{parsed.scheme}://{parsed.netloc}"
    domain = parsed.netloc.replace('www.', '')

    async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
        found_emails: list[str] = []

        # 1. Fetch main page
        try:
            resp = await client.get(url)
            if resp.status_code == 200:
                found_emails.extend(_extract_emails_from_html(resp.text))
        except Exception:
            pass

        # 2. Check common contact pages
        for page in COMMON_CONTACT_PAGES:
            if len(found_emails) >= 5:
                break
            try:
                page_url = urljoin(base_url, page)
                resp = await client.get(page_url)
                if resp.status_code == 200:
                    found_emails.extend(_extract_emails_from_html(resp.text))
            except Exception:
                continue

        # Remove duplicates
        found_emails = list(set(found_emails))

        # 3. If no emails found, try common patterns
        if not found_emails:
            for prefix in COMMON_EMAIL_PREFIXES[:3]:
                guess = f"{prefix}@{domain}"
                found_emails.append(guess)

        # Score and return best
        if found_emails:
            found_emails.sort(key=_score_email, reverse=True)
            return found_emails[0]

        return None


async def extract_company_name(url: str) -> Optional[str]:
    """Extract company name from URL domain."""
    if not url:
        return None

    parsed = urlparse(url)
    domain = parsed.netloc.replace('www.', '')
    # Take first part of domain as company name
    name = domain.split('.')[0]
    return name.capitalize() if name else None
