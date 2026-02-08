#!/usr/bin/env python3
"""
Test discovery module manually.

Usage:
    python scripts/test_discovery.py [source]

Sources: ph (Product Hunt), yc (YC Companies), gh (GitHub), all
"""

import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()


async def test_product_hunt():
    from services.discovery.product_hunt import fetch_product_hunt_posts
    print("\n=== Testing Product Hunt ===")
    products = await fetch_product_hunt_posts(days_back=7, min_votes=30, limit=10)
    for p in products:
        print(f"  [{p.category}] {p.name} - {p.upvotes} upvotes")
        print(f"    {p.url}")
    return products


async def test_yc():
    from services.discovery.yc_companies import fetch_yc_companies
    print("\n=== Testing YC Companies ===")
    products = await fetch_yc_companies(min_batch_year=2023, limit=10)
    for p in products:
        print(f"  [{p.category}] {p.name}")
        print(f"    {p.description[:80] if p.description else 'No description'}...")
    return products


async def test_github():
    from services.discovery.github_trending import fetch_github_trending
    print("\n=== Testing GitHub Trending ===")
    products = await fetch_github_trending(days_back=30, min_stars=50, limit=10)
    for p in products:
        print(f"  [{p.category}] {p.name} - {p.stars} stars")
        print(f"    {p.url}")
    return products


async def test_sync_dry():
    from services.discovery.sync import run_discovery_sync
    print("\n=== Testing Full Sync (Dry Run) ===")
    result = await run_discovery_sync(dry_run=True)
    print(f"  Fetched: {result['fetched']}")
    print(f"  New unique: {result['new']}")
    print(f"  Would persist: {result['new']}")


async def main():
    source = sys.argv[1] if len(sys.argv) > 1 else "all"

    if source in ("ph", "product_hunt", "all"):
        await test_product_hunt()

    if source in ("yc", "all"):
        await test_yc()

    if source in ("gh", "github", "all"):
        await test_github()

    if source in ("sync", "all"):
        await test_sync_dry()


if __name__ == "__main__":
    asyncio.run(main())
