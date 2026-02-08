"""
YC Companies fetcher using yc-oss/api.
Endpoint: https://yc-oss.github.io/api/batches/all.json

No auth required - public JSON API.
"""

from datetime import datetime
from typing import Optional

import httpx

from .models import DiscoveredProduct

YC_API_BASE = "https://yc-oss.github.io/api"
YC_ALL_URL = f"{YC_API_BASE}/companies/all.json"

# Industries relevant to dev tools
DEV_INDUSTRIES = {
    "b2b", "developer-tools", "saas", "infrastructure", "devops",
    "ai", "machine-learning", "analytics", "api", "cloud",
    "data-engineering", "security", "open-source"
}


def _infer_category(industries: list[str], one_liner: str) -> str:
    """Infer tool category from YC industries + description."""
    text = " ".join(industries + [one_liner]).lower()

    if any(k in text for k in ["database", "sql", "data warehouse"]):
        return "Database"
    if any(k in text for k in ["monitor", "observability", "logging"]):
        return "Monitoring"
    if any(k in text for k in ["auth", "identity", "access"]):
        return "Auth"
    if any(k in text for k in ["payment", "fintech", "billing"]):
        return "Payments"
    if any(k in text for k in ["ci/cd", "deploy", "infrastructure"]):
        return "Infrastructure"
    if any(k in text for k in ["ai", "ml", "llm", "machine learning"]):
        return "AI/ML"
    if any(k in text for k in ["analytics", "tracking"]):
        return "Analytics"
    if any(k in text for k in ["api", "integration"]):
        return "API"
    if any(k in text for k in ["security", "compliance"]):
        return "Security"
    if any(k in text for k in ["communication", "messaging", "email"]):
        return "Communications"
    if any(k in text for k in ["search"]):
        return "Search"

    return "Developer Tools"


def _parse_batch_to_date(batch: str) -> Optional[datetime]:
    """Convert YC batch code to approximate date (e.g., 'W24' -> Jan 2024)."""
    if not batch or len(batch) < 2:
        return None

    season = batch[0].upper()
    try:
        year_suffix = int(batch[1:])
        year = 2000 + year_suffix if year_suffix < 100 else year_suffix
    except ValueError:
        return None

    month = 1 if season == "W" else 6  # Winter = Jan, Summer = June
    return datetime(year, month, 1)


async def fetch_yc_companies(
    recent_batches_only: bool = True,
    min_batch_year: int = 2022,
    limit: int = 100
) -> list[DiscoveredProduct]:
    """
    Fetch YC companies, filtered for dev tools.

    Args:
        recent_batches_only: Only include recent batches
        min_batch_year: Earliest batch year to include
        limit: Max companies to return

    Returns:
        List of DiscoveredProduct objects
    """
    async with httpx.AsyncClient(timeout=30) as client:
        try:
            resp = await client.get(YC_ALL_URL)
            resp.raise_for_status()
            companies = resp.json()
        except httpx.HTTPError as e:
            print(f"[YC] API error: {e}")
            return []

    products = []

    for company in companies:
        # Extract batch info
        batch = company.get("batch", "")
        batch_date = _parse_batch_to_date(batch)

        if recent_batches_only and batch_date:
            if batch_date.year < min_batch_year:
                continue

        # Extract industries/tags
        industries = company.get("industries", [])
        if isinstance(industries, str):
            industries = [industries]
        industry_slugs = [i.lower().replace(" ", "-") for i in industries]

        # Filter for dev tools
        if not DEV_INDUSTRIES.intersection(set(industry_slugs)):
            # Check one_liner for keywords
            one_liner = company.get("one_liner", "").lower()
            dev_keywords = ["api", "developer", "infrastructure", "devops", "saas", "b2b", "ai"]
            if not any(k in one_liner for k in dev_keywords):
                continue

        category = _infer_category(industry_slugs, company.get("one_liner", ""))

        # Build URL - prefer website, fallback to YC page
        url = company.get("website")
        if not url:
            slug = company.get("slug", company.get("name", "").lower().replace(" ", "-"))
            url = f"https://www.ycombinator.com/companies/{slug}"

        source_id = company.get("id") or company.get("slug")
        products.append(DiscoveredProduct(
            name=company.get("name", "Unknown"),
            description=company.get("one_liner") or company.get("long_description"),
            url=url,
            category=category,
            tags=industry_slugs[:5],
            source="yc",
            source_id=str(source_id) if source_id else None,
            discovered_at=batch_date
        ))

        if len(products) >= limit:
            break

    print(f"[YC] Found {len(products)} dev tools from YC")
    return products
