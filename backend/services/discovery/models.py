"""Discovery models - kept separate to avoid circular imports."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class DiscoveredProduct(BaseModel):
    """Product discovered from external sources (PH, YC, GitHub)."""
    name: str
    description: Optional[str] = None
    url: Optional[str] = None
    category: str = "Uncategorized"
    tags: list[str] = []
    source: str  # "product_hunt", "yc", "github"
    source_id: Optional[str] = None
    upvotes: Optional[int] = None
    stars: Optional[int] = None
    discovered_at: Optional[datetime] = None
