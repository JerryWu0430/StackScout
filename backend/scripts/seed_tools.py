#!/usr/bin/env python3
"""
Seed tools from JSON into Supabase with OpenAI embeddings.

Usage:
    python scripts/seed_tools.py

Requires:
    SUPABASE_URL, SUPABASE_KEY, OPENAI_API_KEY in environment
"""

import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# Check required env vars
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not all([SUPABASE_URL, SUPABASE_KEY, OPENAI_API_KEY]):
    print("Error: Missing required env vars (SUPABASE_URL, SUPABASE_KEY, OPENAI_API_KEY)")
    sys.exit(1)

try:
    from openai import OpenAI
    from supabase import create_client
except ImportError:
    print("Error: Install dependencies: pip install supabase openai")
    sys.exit(1)

# Init clients
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
openai_client = OpenAI(api_key=OPENAI_API_KEY)

EMBEDDING_MODEL = "text-embedding-3-small"
BATCH_SIZE = 20  # OpenAI batch limit


def load_tools_json() -> list[dict]:
    """Load tools from seed JSON file."""
    json_path = Path(__file__).parent.parent / "data" / "tools_seed.json"
    with open(json_path) as f:
        data = json.load(f)
    return data["tools"]


def create_embedding_text(tool: dict) -> str:
    """Create text for embedding from tool data."""
    tags_str = ", ".join(tool.get("tags", []))
    return f"{tool['name']} - {tool['category']}: {tool['description']} Tags: {tags_str}"


def generate_embeddings(texts: list[str]) -> list[list[float]]:
    """Generate embeddings for a batch of texts."""
    response = openai_client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=texts
    )
    return [item.embedding for item in response.data]


def seed_tools():
    """Main seeding function."""
    tools = load_tools_json()
    print(f"Loaded {len(tools)} tools from JSON")

    # Insert tools into Supabase
    inserted_tools = []
    for tool in tools:
        # Check if tool already exists
        existing = supabase.table("tools").select("id").eq("name", tool["name"]).execute()
        if existing.data:
            print(f"  Skipping {tool['name']} (already exists)")
            inserted_tools.append({"id": existing.data[0]["id"], **tool})
            continue

        # Insert tool
        result = supabase.table("tools").insert({
            "name": tool["name"],
            "category": tool["category"],
            "description": tool["description"],
            "url": tool["url"],
            "booking_url": tool.get("booking_url"),
            "tags": tool.get("tags", [])
        }).execute()

        if result.data:
            inserted_tools.append(result.data[0])
            print(f"  Inserted: {tool['name']}")
        else:
            print(f"  Failed to insert: {tool['name']}")

    print(f"\nInserted {len(inserted_tools)} tools into database")

    # Generate and insert embeddings in batches
    print("\nGenerating embeddings...")
    for i in range(0, len(inserted_tools), BATCH_SIZE):
        batch = inserted_tools[i:i + BATCH_SIZE]
        texts = [create_embedding_text(t) for t in batch]

        embeddings = generate_embeddings(texts)

        for tool, embedding in zip(batch, embeddings):
            # Check if embedding exists
            existing = supabase.table("tool_embeddings").select("id").eq("tool_id", tool["id"]).execute()
            if existing.data:
                print(f"  Skipping embedding for {tool['name']} (already exists)")
                continue

            # Insert embedding
            supabase.table("tool_embeddings").insert({
                "tool_id": tool["id"],
                "embedding": embedding
            }).execute()
            print(f"  Created embedding for: {tool['name']}")

        print(f"  Processed batch {i // BATCH_SIZE + 1}/{(len(inserted_tools) + BATCH_SIZE - 1) // BATCH_SIZE}")

    print("\nSeeding complete!")


if __name__ == "__main__":
    seed_tools()
