"""
Product discovery module - fetches tools/products from external sources.
Sources: Product Hunt, YC Companies, GitHub Trending
"""

from .models import DiscoveredProduct
from .product_hunt import fetch_product_hunt_posts
from .yc_companies import fetch_yc_companies
from .github_trending import fetch_github_trending
from .sync import run_discovery_sync, schedule_daily_sync

__all__ = [
    "DiscoveredProduct",
    "fetch_product_hunt_posts",
    "fetch_yc_companies",
    "fetch_github_trending",
    "run_discovery_sync",
    "schedule_daily_sync",
]
