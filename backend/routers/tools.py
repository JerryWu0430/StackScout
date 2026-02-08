from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from pydantic import BaseModel

from db.supabase import supabase
from db.models import Tool
from services.recommender import get_recommendations, Recommendation

router = APIRouter(prefix="/api", tags=["tools"])


class MatchReasonResponse(BaseModel):
    type: str  # "industry", "keyword", "gap", "use_case"
    matched: str
    score_contribution: float


class RecommendationResponse(BaseModel):
    tool: Tool
    suitability_score: float
    demo_priority: int
    explanation: str
    match_reasons: list[MatchReasonResponse] = []


@router.get("/tools", response_model=list[Tool])
def list_tools(
    category: Optional[str] = Query(None, description="Filter by category"),
    tags: Optional[str] = Query(None, description="Comma-separated tags to filter"),
):
    """List all tools with optional filtering."""
    query = supabase.table("tools").select("*")

    if category:
        query = query.eq("category", category)

    result = query.execute()

    tools = [Tool(**t) for t in result.data]

    # Filter by tags if provided (post-query since Supabase array filtering is limited)
    if tags:
        tag_list = [t.strip().lower() for t in tags.split(",")]
        tools = [
            t for t in tools
            if any(tag.lower() in [tt.lower() for tt in t.tags] for tag in tag_list)
        ]

    return tools


@router.get("/tools/{tool_id}", response_model=Tool)
def get_tool(tool_id: str):
    """Get single tool details."""
    result = supabase.table("tools").select("*").eq("id", tool_id).execute()

    if not result.data:
        raise HTTPException(status_code=404, detail="Tool not found")

    return Tool(**result.data[0])


@router.get("/repos/{repo_id}/recommendations", response_model=list[RecommendationResponse])
def get_repo_recommendations(repo_id: str, limit: int = Query(10, ge=1, le=30)):
    """Get tool recommendations for a repository."""
    try:
        recommendations = get_recommendations(repo_id, limit=limit)
        return [
            RecommendationResponse(
                tool=rec.tool,
                suitability_score=rec.suitability_score,
                demo_priority=rec.demo_priority,
                explanation=rec.explanation,
                match_reasons=[
                    MatchReasonResponse(
                        type=r.type,
                        matched=r.matched,
                        score_contribution=r.score_contribution,
                    )
                    for r in rec.match_reasons
                ],
            )
            for rec in recommendations
        ]
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
