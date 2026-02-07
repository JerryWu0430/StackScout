# Tool recommendation service
import os
import json
from dataclasses import dataclass
from openai import OpenAI

from db.supabase import supabase
from db.models import Tool
from services.embeddings import get_embedding


@dataclass
class Recommendation:
    tool: Tool
    suitability_score: float  # 0-100
    demo_priority: int  # 1-5
    explanation: str


def _cosine_similarity(vec_a: list[float], vec_b: list[float]) -> float:
    """Compute cosine similarity between two vectors."""
    dot = sum(a * b for a, b in zip(vec_a, vec_b))
    norm_a = sum(a * a for a in vec_a) ** 0.5
    norm_b = sum(b * b for b in vec_b) ** 0.5
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def _compute_category_boost(tool_category: str, gaps: list[str]) -> float:
    """Boost score if tool category matches identified gaps."""
    category_lower = tool_category.lower()

    # Map common gap keywords to categories
    gap_category_map = {
        "monitoring": ["monitoring", "observability", "logging", "metrics", "apm"],
        "auth": ["auth", "authentication", "identity", "sso", "security"],
        "database": ["database", "db", "storage", "data", "postgres", "mysql"],
        "payments": ["payments", "billing", "subscriptions", "fintech"],
        "infrastructure": ["infrastructure", "deployment", "hosting", "cloud", "ci-cd"],
        "devops": ["devops", "ci", "cd", "pipeline", "release"],
        "analytics": ["analytics", "tracking", "metrics", "data"],
        "search": ["search", "indexing", "discovery"],
        "communications": ["sms", "email", "notifications", "messaging", "voice"],
        "security": ["security", "vulnerability", "compliance", "encryption"],
    }

    for gap in gaps:
        gap_lower = gap.lower()
        for cat, keywords in gap_category_map.items():
            if cat in category_lower or any(kw in gap_lower for kw in keywords):
                if any(kw in gap_lower for kw in keywords) and cat in category_lower:
                    return 15.0  # Strong category match
    return 0.0


def _compute_tag_boost(tool_tags: list[str], gaps: list[str], context: str) -> float:
    """Boost score based on tag relevance to gaps and context."""
    boost = 0.0
    combined_text = " ".join(gaps).lower() + " " + context.lower()

    for tag in tool_tags:
        tag_lower = tag.lower()
        if tag_lower in combined_text:
            boost += 3.0  # Each matching tag adds points

    return min(boost, 10.0)  # Cap tag boost at 10


def _calculate_demo_priority(score: float) -> int:
    """Convert suitability score to demo priority (1=highest, 5=lowest)."""
    if score >= 85:
        return 1
    elif score >= 70:
        return 2
    elif score >= 55:
        return 3
    elif score >= 40:
        return 4
    else:
        return 5


def _generate_explanation(tool: Tool, gaps: list[str], context: str) -> str:
    """Generate LLM explanation for why this tool is recommended."""
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    prompt = f"""Given a repository with these identified gaps: {', '.join(gaps)}
And this context: {context}

Explain in 1-2 sentences why {tool.name} ({tool.category}) would be a good fit.
Tool description: {tool.description}
Tool tags: {', '.join(tool.tags)}

Be specific about how it addresses the gaps. Keep it concise."""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=100,
        temperature=0.7,
    )
    return response.choices[0].message.content.strip()


def _generate_explanations_batch(
    tools: list[Tool], gaps: list[str], context: str
) -> list[str]:
    """Generate explanations for multiple tools in batch."""
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    tools_info = "\n".join(
        f"- {t.name} ({t.category}): {t.description}" for t in tools
    )

    prompt = f"""Given a repository with these identified gaps: {', '.join(gaps)}
And this context: {context}

For each tool below, write a 1-2 sentence explanation of why it's recommended.
Be specific about how each tool addresses the gaps. Keep each explanation concise.

Tools:
{tools_info}

Respond in JSON format: {{"explanations": ["explanation1", "explanation2", ...]}}"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=500,
        temperature=0.7,
    )

    try:
        content = response.choices[0].message.content.strip()
        # Handle potential markdown code blocks
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
        result = json.loads(content)
        return result.get("explanations", ["" for _ in tools])
    except (json.JSONDecodeError, KeyError):
        # Fallback: generate individually
        return [_generate_explanation(t, gaps, context) for t in tools]


def get_recommendations(repo_id: str, limit: int = 5) -> list[Recommendation]:
    """
    Get tool recommendations for a repository.

    Args:
        repo_id: The repository ID to get recommendations for
        limit: Maximum number of recommendations to return

    Returns:
        List of Recommendation objects sorted by suitability score
    """
    # 1. Get repo fingerprint from DB
    repo_result = supabase.table("repos").select("*").eq("id", repo_id).execute()
    if not repo_result.data:
        raise ValueError(f"Repository {repo_id} not found")

    repo = repo_result.data[0]
    fingerprint_raw = repo.get("fingerprint")

    if not fingerprint_raw:
        raise ValueError(f"Repository {repo_id} has no fingerprint")

    # Parse fingerprint JSON
    fingerprint = json.loads(fingerprint_raw) if isinstance(fingerprint_raw, str) else fingerprint_raw
    gaps = fingerprint.get("gaps", [])
    recommendations_context = fingerprint.get("recommendations_context", "")

    # 2. Create embedding from gaps + recommendations_context
    search_text = " ".join(gaps) + " " + recommendations_context
    query_embedding = get_embedding(search_text)

    # 3. Vector similarity search in tool_embeddings
    # Fetch all tool embeddings (for now - could use pgvector RPC later)
    embeddings_result = supabase.table("tool_embeddings").select("*").execute()
    tools_result = supabase.table("tools").select("*").execute()

    # Build tool lookup
    tools_by_id = {t["id"]: Tool(**t) for t in tools_result.data}

    # 4. Calculate suitability scores
    scored_tools: list[tuple[Tool, float]] = []

    for emb_row in embeddings_result.data:
        tool_id = emb_row["tool_id"]
        tool_embedding = emb_row["embedding"]

        if tool_id not in tools_by_id:
            continue

        tool = tools_by_id[tool_id]

        # Base score: cosine similarity (0-1) -> (0-75)
        similarity = _cosine_similarity(query_embedding, tool_embedding)
        base_score = similarity * 75

        # Boost: category match to gaps (0-15)
        category_boost = _compute_category_boost(tool.category, gaps)

        # Boost: tag relevance (0-10)
        tag_boost = _compute_tag_boost(tool.tags, gaps, recommendations_context)

        # Final score (0-100)
        final_score = min(base_score + category_boost + tag_boost, 100.0)

        scored_tools.append((tool, final_score))

    # Sort by score descending and take top N
    scored_tools.sort(key=lambda x: x[1], reverse=True)
    top_tools = scored_tools[:limit]

    # 5. Generate explanations per tool using LLM (batch)
    if top_tools:
        tools_list = [t for t, _ in top_tools]
        explanations = _generate_explanations_batch(tools_list, gaps, recommendations_context)
    else:
        explanations = []

    # 6. Build and return recommendations
    recommendations = []
    for i, (tool, score) in enumerate(top_tools):
        rec = Recommendation(
            tool=tool,
            suitability_score=round(score, 1),
            demo_priority=_calculate_demo_priority(score),
            explanation=explanations[i] if i < len(explanations) else "",
        )
        recommendations.append(rec)

    return recommendations
