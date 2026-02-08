from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class Tool(BaseModel):
    id: str
    name: str
    category: str
    description: Optional[str] = None
    url: Optional[str] = None
    booking_url: Optional[str] = None
    tags: list[str] = []
    source: Optional[str] = None  # "product_hunt", "yc", "github", or None (seeded)


class ToolEmbedding(BaseModel):
    id: str
    tool_id: str
    embedding: list[float]


class Repo(BaseModel):
    id: str
    github_url: str
    fingerprint: Optional[str] = None


class Demo(BaseModel):
    id: str
    repo_id: str
    tool_id: str
    scheduled_at: Optional[datetime] = None
    status: str = "pending"
