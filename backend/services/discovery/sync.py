"""
Discovery sync orchestrator.
Fetches from all sources, dedupes, generates embeddings, persists to Supabase.
"""

import asyncio
import os
from datetime import datetime
from typing import Optional

from .models import DiscoveredProduct

from .product_hunt import fetch_product_hunt_posts
from .yc_companies import fetch_yc_companies
from .github_trending import fetch_github_trending

# Lazy imports to avoid circular deps
_supabase = None
_embeddings = None


def _get_supabase():
    global _supabase
    if _supabase is None:
        from db.supabase import supabase
        _supabase = supabase
    return _supabase


def _get_embeddings_batch(texts: list[str]) -> list[list[float]]:
    global _embeddings
    if _embeddings is None:
        from services.embeddings import get_embeddings_batch
        _embeddings = get_embeddings_batch
    return _embeddings(texts)


def _create_embedding_text(product: DiscoveredProduct) -> str:
    """Create text for embedding from product."""
    tags_str = ", ".join(product.tags)
    return f"{product.name} - {product.category}: {product.description or ''} Tags: {tags_str}"


def _normalize_url(url: Optional[str]) -> Optional[str]:
    """Normalize URL for deduplication."""
    if not url:
        return None
    url = url.lower().strip().rstrip("/")
    # Remove protocol
    for prefix in ["https://", "http://", "www."]:
        if url.startswith(prefix):
            url = url[len(prefix):]
    return url


async def _fetch_all_sources() -> list[DiscoveredProduct]:
    """Fetch from all sources concurrently."""
    results = await asyncio.gather(
        fetch_product_hunt_posts(days_back=7, min_votes=50, limit=50),
        fetch_yc_companies(recent_batches_only=True, min_batch_year=2022, limit=100),
        fetch_github_trending(days_back=30, min_stars=100, limit=50),
        return_exceptions=True
    )

    products = []
    for result in results:
        if isinstance(result, Exception):
            print(f"[Sync] Source fetch error: {result}")
        elif result:
            products.extend(result)

    return products


def _dedupe_products(
    products: list[DiscoveredProduct],
    existing_urls: set[str],
    existing_names: set[str]
) -> list[DiscoveredProduct]:
    """Remove duplicates by URL and name."""
    seen_urls = set()
    seen_names = set()
    unique = []

    for p in products:
        norm_url = _normalize_url(p.url)
        norm_name = p.name.lower().strip()

        # Skip if matches existing
        if norm_url and norm_url in existing_urls:
            continue
        if norm_name in existing_names:
            continue

        # Skip if duplicate in batch
        if norm_url and norm_url in seen_urls:
            continue
        if norm_name in seen_names:
            continue

        seen_urls.add(norm_url)
        seen_names.add(norm_name)
        unique.append(p)

    return unique


async def run_discovery_sync(dry_run: bool = False) -> dict:
    """
    Run full discovery sync: fetch → dedupe → embed → persist.

    Args:
        dry_run: If True, don't persist to DB

    Returns:
        Summary dict with counts
    """
    print(f"[Sync] Starting discovery sync at {datetime.utcnow().isoformat()}")

    # Fetch from all sources
    products = await _fetch_all_sources()
    print(f"[Sync] Fetched {len(products)} total products")

    if not products:
        return {"fetched": 0, "new": 0, "persisted": 0}

    # Get existing tools for deduplication
    supabase = _get_supabase()
    existing = supabase.table("tools").select("name, url").execute()

    existing_urls = {_normalize_url(t.get("url")) for t in existing.data if t.get("url")}
    existing_names = {t["name"].lower().strip() for t in existing.data}

    # Dedupe
    unique = _dedupe_products(products, existing_urls, existing_names)
    print(f"[Sync] {len(unique)} new unique products after deduplication")

    if dry_run or not unique:
        return {"fetched": len(products), "new": len(unique), "persisted": 0}

    # Generate embeddings in batches
    BATCH_SIZE = 20
    persisted = 0

    for i in range(0, len(unique), BATCH_SIZE):
        batch = unique[i:i + BATCH_SIZE]
        texts = [_create_embedding_text(p) for p in batch]

        try:
            embeddings = _get_embeddings_batch(texts)
        except Exception as e:
            print(f"[Sync] Embedding error: {e}")
            continue

        # Insert tools and embeddings
        for product, embedding in zip(batch, embeddings):
            try:
                # Insert tool
                tool_data = {
                    "name": product.name,
                    "category": product.category,
                    "description": product.description,
                    "url": product.url,
                    "tags": product.tags,
                    "source": product.source,
                    "source_id": product.source_id
                }

                result = supabase.table("tools").insert(tool_data).execute()

                if result.data:
                    tool_id = result.data[0]["id"]

                    # Insert embedding
                    supabase.table("tool_embeddings").insert({
                        "tool_id": tool_id,
                        "embedding": embedding
                    }).execute()

                    persisted += 1
                    print(f"[Sync] Inserted: {product.name} ({product.source})")

            except Exception as e:
                print(f"[Sync] Insert error for {product.name}: {e}")

    print(f"[Sync] Completed: {persisted}/{len(unique)} new tools persisted")
    return {"fetched": len(products), "new": len(unique), "persisted": persisted}


# Scheduler instance
_scheduler = None


def schedule_daily_sync(hour: int = 3, minute: int = 0):
    """
    Schedule daily discovery sync.

    Args:
        hour: Hour to run (UTC)
        minute: Minute to run
    """
    global _scheduler

    if _scheduler is not None:
        print("[Sync] Scheduler already running")
        return

    from apscheduler.schedulers.asyncio import AsyncIOScheduler
    from apscheduler.triggers.cron import CronTrigger

    _scheduler = AsyncIOScheduler()
    _scheduler.add_job(
        run_discovery_sync,
        CronTrigger(hour=hour, minute=minute),
        id="discovery_sync",
        name="Daily discovery sync",
        replace_existing=True
    )
    _scheduler.start()
    print(f"[Sync] Scheduled daily sync at {hour:02d}:{minute:02d} UTC")


def stop_scheduler():
    """Stop the scheduler."""
    global _scheduler
    if _scheduler:
        _scheduler.shutdown()
        _scheduler = None
        print("[Sync] Scheduler stopped")
