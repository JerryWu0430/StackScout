from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class Tool(BaseModel):
    id: int
    name: str
    category: str
    description: Optional[str] = None
    url: Optional[str] = None
    booking_url: Optional[str] = None
    tags: list[str] = []


class ToolEmbedding(BaseModel):
    id: int
    tool_id: int
    embedding: list[float]


class Repo(BaseModel):
    id: int
    github_url: str
    fingerprint: Optional[str] = None


class Demo(BaseModel):
    id: int
    repo_id: int
    tool_id: int
    scheduled_at: Optional[datetime] = None
    status: str = "pending"
