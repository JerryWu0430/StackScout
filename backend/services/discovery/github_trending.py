"""
GitHub trending repos fetcher using GitHub Search API.
Uses GITHUB_TOKEN env var for higher rate limits.
"""

import os
from datetime import datetime, timedelta
from typing import Optional

import httpx

from .models import DiscoveredProduct

GH_SEARCH_URL = "https://api.github.com/search/repositories"

# Topics indicating dev tools / SaaS
DEV_TOOL_TOPICS = {
    "cli", "api", "sdk", "framework", "library", "devops", "infrastructure",
    "monitoring", "logging", "database", "orm", "authentication", "security",
    "ai", "machine-learning", "llm", "analytics", "testing", "deployment",
    "saas", "developer-tools", "automation"
}

# Keywords in description indicating dev tools
DEV_KEYWORDS = {
    "api", "sdk", "cli", "framework", "library", "tool", "platform",
    "infrastructure", "deploy", "monitor", "database", "auth", "security"
}


def _get_headers() -> dict:
    headers = {"Accept": "application/vnd.github.v3+json"}
    token = os.getenv("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"token {token}"
    return headers


def _infer_category(topics: list[str], description: str, language: str) -> str:
    """Infer category from repo metadata."""
    text = " ".join(topics + [description, language]).lower()

    if any(k in text for k in ["database", "sql", "orm", "postgres", "mysql"]):
        return "Database"
    if any(k in text for k in ["monitor", "observability", "logging", "metrics", "tracing"]):
        return "Monitoring"
    if any(k in text for k in ["auth", "oauth", "jwt", "identity"]):
        return "Auth"
    if any(k in text for k in ["payment", "stripe", "billing"]):
        return "Payments"
    if any(k in text for k in ["ci", "cd", "deploy", "pipeline", "github-actions"]):
        return "CI/CD"
    if any(k in text for k in ["ai", "ml", "llm", "gpt", "machine-learning", "neural"]):
        return "AI/ML"
    if any(k in text for k in ["analytics", "tracking", "data-viz"]):
        return "Analytics"
    if any(k in text for k in ["api", "rest", "graphql", "grpc"]):
        return "API"
    if any(k in text for k in ["security", "vulnerability", "pentest", "crypto"]):
        return "Security"
    if any(k in text for k in ["messaging", "email", "notification", "queue"]):
        return "Communications"
    if any(k in text for k in ["search", "elasticsearch", "algolia"]):
        return "Search"
    if any(k in text for k in ["cli", "terminal", "command-line"]):
        return "CLI Tools"
    if any(k in text for k in ["testing", "test", "mock", "e2e"]):
        return "Testing"
    if any(k in text for k in ["infrastructure", "cloud", "kubernetes", "docker"]):
        return "Infrastructure"

    return "Open Source"


def _is_dev_tool(topics: list[str], description: str) -> bool:
    """Check if repo is likely a dev tool."""
    text = " ".join(topics + [description]).lower()

    # Check topics
    if DEV_TOOL_TOPICS.intersection(set(topics)):
        return True

    # Check description keywords
    if any(k in text for k in DEV_KEYWORDS):
        return True

    return False


async def fetch_github_trending(
    days_back: int = 30,
    min_stars: int = 100,
    limit: int = 50,
    language: Optional[str] = None
) -> list[DiscoveredProduct]:
    """
    Fetch trending GitHub repos (recently created with high star growth).

    Args:
        days_back: How far back to look for new repos
        min_stars: Minimum stars to include
        limit: Max repos to return
        language: Filter by programming language

    Returns:
        List of DiscoveredProduct objects
    """
    created_after = (datetime.utcnow() - timedelta(days=days_back)).strftime("%Y-%m-%d")

    # Build search query
    query_parts = [f"created:>{created_after}", f"stars:>={min_stars}"]
    if language:
        query_parts.append(f"language:{language}")

    query = " ".join(query_parts)

    params = {
        "q": query,
        "sort": "stars",
        "order": "desc",
        "per_page": min(limit * 2, 100)  # Fetch more to filter
    }

    async with httpx.AsyncClient(timeout=30) as client:
        try:
            resp = await client.get(GH_SEARCH_URL, params=params, headers=_get_headers())
            resp.raise_for_status()
            data = resp.json()
        except httpx.HTTPError as e:
            print(f"[GH] API error: {e}")
            return []

    products = []
    repos = data.get("items", [])

    for repo in repos:
        topics = repo.get("topics", [])
        description = repo.get("description") or ""
        lang = repo.get("language") or ""

        # Filter for dev tools
        if not _is_dev_tool(topics, description):
            continue

        category = _infer_category(topics, description, lang)

        # Use homepage if available, else GitHub URL
        url = repo.get("homepage") or repo.get("html_url")

        products.append(DiscoveredProduct(
            name=repo["name"],
            description=description[:200] if description else None,
            url=url,
            category=category,
            tags=topics[:5] if topics else [lang.lower()] if lang else [],
            source="github",
            source_id=str(repo["id"]),
            stars=repo.get("stargazers_count"),
            discovered_at=datetime.fromisoformat(repo["created_at"].replace("Z", "+00:00"))
        ))

        if len(products) >= limit:
            break

    print(f"[GH] Found {len(products)} dev tools from GitHub")
    return products
