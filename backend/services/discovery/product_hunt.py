"""
Product Hunt GraphQL API client.
Fetches daily/weekly launches for dev tools discovery.

API Docs: https://api.producthunt.com/v2/docs
Requires: PRODUCT_HUNT_TOKEN env var (Developer token from PH dashboard)
"""

import os
from datetime import datetime, timedelta
from typing import Optional

import httpx

from .models import DiscoveredProduct

PH_GRAPHQL_URL = "https://api.producthunt.com/v2/api/graphql"

# Dev tool related topics to filter
DEV_TOOL_TOPICS = {
    "developer-tools", "api", "saas", "productivity", "open-source",
    "tech", "software-engineering", "devops", "artificial-intelligence",
    "machine-learning", "databases", "cloud", "infrastructure"
}


def _get_token() -> Optional[str]:
    return os.getenv("PRODUCT_HUNT_TOKEN")


def _infer_category(topics: list[str], tagline: str) -> str:
    """Infer tool category from PH topics + tagline."""
    text = " ".join(topics + [tagline]).lower()

    if any(k in text for k in ["database", "sql", "postgres", "mongo"]):
        return "Database"
    if any(k in text for k in ["monitor", "observability", "logging", "metrics"]):
        return "Monitoring"
    if any(k in text for k in ["auth", "login", "identity", "sso"]):
        return "Auth"
    if any(k in text for k in ["payment", "stripe", "billing", "checkout"]):
        return "Payments"
    if any(k in text for k in ["ci/cd", "deploy", "pipeline", "github action"]):
        return "CI/CD"
    if any(k in text for k in ["ai", "ml", "gpt", "llm", "machine learning"]):
        return "AI/ML"
    if any(k in text for k in ["analytics", "tracking", "insight"]):
        return "Analytics"
    if any(k in text for k in ["api", "integration", "webhook"]):
        return "API"
    if any(k in text for k in ["security", "vulnerability", "pentest"]):
        return "Security"
    if any(k in text for k in ["email", "sms", "notification", "messaging"]):
        return "Communications"
    if any(k in text for k in ["search", "elasticsearch", "algolia"]):
        return "Search"
    if any(k in text for k in ["infrastructure", "cloud", "aws", "hosting"]):
        return "Infrastructure"

    return "Developer Tools"


async def fetch_product_hunt_posts(
    days_back: int = 7,
    min_votes: int = 50,
    limit: int = 50
) -> list[DiscoveredProduct]:
    """
    Fetch recent Product Hunt posts filtered for dev tools.

    Args:
        days_back: How many days back to fetch
        min_votes: Minimum upvotes to include
        limit: Max products to return

    Returns:
        List of DiscoveredProduct objects
    """
    token = _get_token()
    if not token:
        print("[PH] No PRODUCT_HUNT_TOKEN set, skipping")
        return []

    posted_after = (datetime.utcnow() - timedelta(days=days_back)).isoformat()

    query = """
    query($postedAfter: DateTime, $first: Int) {
      posts(postedAfter: $postedAfter, first: $first, order: VOTES) {
        edges {
          node {
            id
            name
            tagline
            description
            url
            website
            votesCount
            createdAt
            topics {
              edges {
                node {
                  slug
                }
              }
            }
          }
        }
      }
    }
    """

    variables = {
        "postedAfter": posted_after,
        "first": min(limit * 2, 100)  # Fetch more to filter
    }

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    async with httpx.AsyncClient(timeout=30) as client:
        try:
            resp = await client.post(
                PH_GRAPHQL_URL,
                json={"query": query, "variables": variables},
                headers=headers
            )
            resp.raise_for_status()
            data = resp.json()
        except httpx.HTTPError as e:
            print(f"[PH] API error: {e}")
            return []

    if "errors" in data:
        print(f"[PH] GraphQL errors: {data['errors']}")
        return []

    products = []
    edges = data.get("data", {}).get("posts", {}).get("edges", [])

    for edge in edges:
        node = edge["node"]
        votes = node.get("votesCount", 0)

        if votes < min_votes:
            continue

        # Extract topics
        topic_edges = node.get("topics", {}).get("edges", [])
        topics = [t["node"]["slug"] for t in topic_edges]

        # Filter for dev tools
        if not DEV_TOOL_TOPICS.intersection(set(topics)):
            continue

        category = _infer_category(topics, node.get("tagline", ""))

        products.append(DiscoveredProduct(
            name=node["name"],
            description=node.get("tagline") or node.get("description"),
            url=node.get("website") or node.get("url"),
            category=category,
            tags=topics[:5],
            source="product_hunt",
            source_id=node["id"],
            upvotes=votes,
            discovered_at=datetime.fromisoformat(node["createdAt"].replace("Z", "+00:00"))
        ))

        if len(products) >= limit:
            break

    print(f"[PH] Found {len(products)} dev tools from Product Hunt")
    return products
