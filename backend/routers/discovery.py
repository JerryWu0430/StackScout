"""
Discovery API routes for manual sync and status checks.
"""

from fastapi import APIRouter, BackgroundTasks, HTTPException

from services.discovery import run_discovery_sync

router = APIRouter(prefix="/api/discovery", tags=["discovery"])


@router.post("/sync")
async def trigger_sync(background_tasks: BackgroundTasks, dry_run: bool = False):
    """
    Trigger a discovery sync.

    Args:
        dry_run: If True, fetch and dedupe but don't persist

    Returns:
        Status message (sync runs in background)
    """
    background_tasks.add_task(run_discovery_sync, dry_run)
    return {"status": "sync_started", "dry_run": dry_run}


@router.post("/sync/blocking")
async def trigger_sync_blocking(dry_run: bool = False):
    """
    Trigger a discovery sync and wait for results.

    Args:
        dry_run: If True, fetch and dedupe but don't persist

    Returns:
        Sync results with counts
    """
    try:
        result = await run_discovery_sync(dry_run)
        return {"status": "completed", **result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
