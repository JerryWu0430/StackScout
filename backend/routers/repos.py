from typing import Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from db.supabase import supabase
from services.github import fetch_repo_files
from services.analyzer import analyze_repo, RepoFingerprint

router = APIRouter(prefix="/repos", tags=["repos"])


class AnalyzeRequest(BaseModel):
    github_url: str


class AnalyzeResponse(BaseModel):
    repo_id: str
    github_url: Optional[str] = None
    fingerprint: RepoFingerprint


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze_repository(req: AnalyzeRequest):
    """Analyze a GitHub repo and save fingerprint.

    1. Fetch repo files via GitHub API
    2. Analyze stack with LLM
    3. Save to repos table
    4. Return fingerprint + repo_id
    """
    # Fetch repo files
    repo_files = await fetch_repo_files(req.github_url)

    # Analyze stack
    fingerprint = analyze_repo(repo_files)

    # Save to DB (upsert by github_url)
    result = (
        supabase.table("repos")
        .upsert(
            {"github_url": req.github_url, "fingerprint": fingerprint.model_dump_json()},
            on_conflict="github_url",
        )
        .execute()
    )

    repo_id = result.data[0]["id"]
    return AnalyzeResponse(repo_id=repo_id, github_url=req.github_url, fingerprint=fingerprint)


@router.get("/{repo_id}", response_model=AnalyzeResponse)
async def get_repo(repo_id: str):
    """Get saved repo fingerprint by ID."""
    result = supabase.table("repos").select("*").eq("id", repo_id).execute()

    if not result.data:
        raise HTTPException(status_code=404, detail="Repo not found")

    repo = result.data[0]
    if not repo.get("fingerprint"):
        raise HTTPException(status_code=404, detail="Fingerprint not found")

    fingerprint = RepoFingerprint.model_validate_json(repo["fingerprint"])
    return AnalyzeResponse(repo_id=repo["id"], github_url=repo.get("github_url"), fingerprint=fingerprint)
