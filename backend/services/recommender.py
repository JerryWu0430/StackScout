# Tool recommendation service
import os
import json
from dataclasses import dataclass, field
from openai import OpenAI

from db.supabase import supabase
from db.models import Tool
from services.embeddings import get_embedding


def _get_client() -> OpenAI:
    """Get OpenAI-compatible client (LiteLLM or OpenAI)."""
    base_url = os.getenv("LITELLM_BASE_URL")
    api_key = os.getenv("LITELLM_API_KEY") or os.getenv("OPENAI_API_KEY")
    if base_url:
        return OpenAI(base_url=base_url, api_key=api_key)
    return OpenAI(api_key=api_key)


@dataclass
class MatchReason:
    type: str  # "industry", "keyword", "gap", "use_case", "category"
    matched: str  # what was matched
    score_contribution: float


@dataclass
class Recommendation:
    tool: Tool
    suitability_score: float  # 0-100
    demo_priority: int  # 1-5
    explanation: str
    match_reasons: list[MatchReason] = field(default_factory=list)


# Industry -> relevant tool tags mapping
INDUSTRY_TAG_MAP = {
    "fintech": ["payments", "fintech", "billing", "subscriptions", "banking", "crypto"],
    "ecommerce": ["payments", "ecommerce", "checkout", "subscriptions", "search", "analytics"],
    "healthcare": ["hipaa", "compliance", "security", "auth", "data"],
    "devtools": ["api", "sdk", "developer", "ci-cd", "devops", "infrastructure"],
    "saas": ["auth", "billing", "subscriptions", "analytics", "monitoring"],
    "ai-ml": ["ai", "ml", "data", "gpu", "inference", "training"],
    "media": ["cdn", "streaming", "storage", "media", "video"],
    "education": ["auth", "video", "analytics", "notifications"],
    "general": [],
}

# Project type -> relevant categories
PROJECT_TYPE_CATEGORY_MAP = {
    "api": ["API", "Auth", "Monitoring", "Database", "Security"],
    "web_app": ["Auth", "Database", "Infrastructure", "Analytics", "Search"],
    "mobile": ["Auth", "Analytics", "Notifications", "Database"],
    "cli": ["DevOps", "CI/CD", "Infrastructure"],
    "library": ["CI/CD", "DevOps", "Monitoring"],
    "data_pipeline": ["Database", "Monitoring", "Infrastructure"],
    "ml_model": ["Infrastructure", "Monitoring", "Database"],
}

# Existing tech -> tool categories to penalize
# If project already has these, don't recommend similar tools
EXISTING_TECH_PENALTIES = {
    # CI/CD tools
    "github actions": ["ci/cd", "ci-cd", "devops", "deployment"],
    "circleci": ["ci/cd", "ci-cd", "devops", "deployment"],
    "gitlab ci": ["ci/cd", "ci-cd", "devops", "deployment"],
    "jenkins": ["ci/cd", "ci-cd", "devops", "deployment"],
    "travis": ["ci/cd", "ci-cd", "devops", "deployment"],
    # Monitoring
    "datadog": ["monitoring", "observability", "apm"],
    "new relic": ["monitoring", "observability", "apm"],
    "sentry": ["monitoring", "error tracking", "apm"],
    "grafana": ["monitoring", "observability"],
    "prometheus": ["monitoring", "observability"],
    # Auth
    "auth0": ["auth", "authentication", "identity"],
    "firebase auth": ["auth", "authentication", "identity"],
    "clerk": ["auth", "authentication", "identity"],
    "supabase auth": ["auth", "authentication", "identity"],
    "nextauth": ["auth", "authentication", "identity"],
    # Payments
    "stripe": ["payments", "billing", "subscriptions"],
    "braintree": ["payments", "billing"],
    "paypal": ["payments", "billing"],
    # Analytics
    "google analytics": ["analytics", "tracking"],
    "mixpanel": ["analytics", "tracking"],
    "amplitude": ["analytics", "tracking"],
    "posthog": ["analytics", "tracking"],
    # Database
    "postgresql": ["database"],
    "mysql": ["database"],
    "mongodb": ["database"],
    "supabase": ["database", "backend"],
    "firebase": ["database", "backend"],
}


def _cosine_similarity(vec_a: list[float], vec_b: list[float]) -> float:
    """Compute cosine similarity between two vectors."""
    dot = sum(a * b for a, b in zip(vec_a, vec_b))
    norm_a = sum(a * a for a in vec_a) ** 0.5
    norm_b = sum(b * b for b in vec_b) ** 0.5
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def _compute_industry_boost(tool_tags: list[str], industry: str) -> tuple[float, list[str]]:
    """Boost score if tool tags match project industry."""
    industry_tags = INDUSTRY_TAG_MAP.get(industry.lower(), [])
    if not industry_tags:
        return 0.0, []

    matched = []
    tool_tags_lower = [t.lower() for t in tool_tags]

    for tag in industry_tags:
        if tag in tool_tags_lower:
            matched.append(tag)

    # Up to 15 points for industry match
    boost = min(len(matched) * 5, 15.0)
    return boost, matched


def _compute_keyword_boost(tool: Tool, keywords: list[str]) -> tuple[float, list[str]]:
    """Boost score if tool matches project keywords."""
    tool_text = f"{tool.name} {tool.description} {' '.join(tool.tags)}".lower()
    matched = []

    for kw in keywords:
        if kw.lower() in tool_text:
            matched.append(kw)

    # Up to 10 points for keyword matches
    boost = min(len(matched) * 3, 10.0)
    return boost, matched


def _compute_category_boost(tool_category: str, gaps: list[str], project_type: str) -> tuple[float, list[str]]:
    """Boost score if tool category matches gaps or project type."""
    category_lower = tool_category.lower()
    matched = []

    # Map gap keywords to categories
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

    # Check gaps
    for gap in gaps:
        gap_lower = gap.lower()
        for cat, keywords in gap_category_map.items():
            if cat in category_lower and any(kw in gap_lower for kw in keywords):
                matched.append(f"gap:{gap[:30]}")
                break

    # Check project type relevance
    relevant_categories = PROJECT_TYPE_CATEGORY_MAP.get(project_type, [])
    if any(cat.lower() in category_lower for cat in relevant_categories):
        matched.append(f"type:{project_type}")

    boost = min(len(matched) * 5, 10.0)
    return boost, matched


def _compute_use_case_boost(tool: Tool, use_cases: list[str]) -> tuple[float, list[str]]:
    """Boost if tool description matches use cases."""
    tool_text = f"{tool.description} {' '.join(tool.tags)}".lower()
    matched = []

    for uc in use_cases:
        # Check if key words from use case appear in tool
        uc_words = [w for w in uc.lower().split() if len(w) > 3]
        matches = sum(1 for w in uc_words if w in tool_text)
        if matches >= 2:  # At least 2 words match
            matched.append(uc[:40])

    boost = min(len(matched) * 4, 8.0)
    return boost, matched


def _compute_redundancy_penalty(tool: Tool, stack: dict) -> tuple[float, str]:
    """Penalize tool if project already has similar tech in stack."""
    # Flatten all stack items
    all_stack_items = []
    for category_items in stack.values():
        if isinstance(category_items, list):
            all_stack_items.extend([item.lower() for item in category_items])

    stack_text = " ".join(all_stack_items)
    tool_category_lower = tool.category.lower()
    tool_tags_lower = [t.lower() for t in tool.tags]
    tool_name_lower = tool.name.lower()

    # Check if any existing tech triggers a penalty for this tool's category
    for existing_tech, penalized_categories in EXISTING_TECH_PENALTIES.items():
        if existing_tech in stack_text:
            # Check if tool falls into penalized category
            for penalized_cat in penalized_categories:
                if (penalized_cat in tool_category_lower or
                    penalized_cat in tool_name_lower or
                    any(penalized_cat in tag for tag in tool_tags_lower)):
                    return -25.0, f"Already has {existing_tech}"

    return 0.0, ""


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


def _generate_explanation(
    tool: Tool, gaps: list[str], context: str, industry: str, keywords: list[str]
) -> str:
    """Generate LLM explanation for why this tool is recommended."""
    client = _get_client()
    model = os.getenv("LITELLM_MODEL", "gpt-4o-mini")

    prompt = f"""A {industry} project with keywords [{', '.join(keywords[:5])}] has these gaps: {', '.join(gaps[:3])}
Context: {context}

Explain in 1-2 sentences why {tool.name} ({tool.category}) is recommended.
Tool: {tool.description}
Be specific about the industry/project fit. Keep it concise."""

    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=100,
        temperature=0.7,
    )
    return response.choices[0].message.content.strip()


def _generate_explanations_batch(
    tools: list[Tool], gaps: list[str], context: str, industry: str, keywords: list[str]
) -> list[str]:
    """Generate explanations for multiple tools in batch."""
    client = _get_client()
    model = os.getenv("LITELLM_MODEL", "gpt-4o-mini")

    tools_info = "\n".join(
        f"- {t.name} ({t.category}): {t.description}" for t in tools
    )

    prompt = f"""A {industry} project with keywords [{', '.join(keywords[:5])}] has these gaps: {', '.join(gaps[:3])}
Context: {context}

For each tool, write 1 sentence explaining why it fits this specific project.
Focus on industry relevance and how it addresses their needs.

Tools:
{tools_info}

Respond in JSON: {{"explanations": ["explanation1", "explanation2", ...]}}"""

    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=500,
        temperature=0.7,
    )

    try:
        content = response.choices[0].message.content.strip()
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
        result = json.loads(content)
        return result.get("explanations", ["" for _ in tools])
    except (json.JSONDecodeError, KeyError):
        return [_generate_explanation(t, gaps, context, industry, keywords) for t in tools]


def get_recommendations(repo_id: str, limit: int = 5) -> list[Recommendation]:
    """Get tool recommendations for a repository."""
    # 1. Get repo fingerprint from DB
    repo_result = supabase.table("repos").select("*").eq("id", repo_id).execute()
    if not repo_result.data:
        raise ValueError(f"Repository {repo_id} not found")

    repo = repo_result.data[0]
    fingerprint_raw = repo.get("fingerprint")

    if not fingerprint_raw:
        raise ValueError(f"Repository {repo_id} has no fingerprint")

    # Parse fingerprint JSON
    fp = json.loads(fingerprint_raw) if isinstance(fingerprint_raw, str) else fingerprint_raw
    gaps = fp.get("gaps", [])
    context = fp.get("recommendations_context", "")
    industry = fp.get("industry", "general")
    project_type = fp.get("project_type", "web_app")
    keywords = fp.get("keywords", [])
    use_cases = fp.get("use_cases", [])
    stack = fp.get("stack", {})

    # 2. Create rich embedding from all context
    search_parts = [
        f"Industry: {industry}",
        f"Project type: {project_type}",
        f"Keywords: {' '.join(keywords)}",
        f"Gaps: {' '.join(gaps)}",
        f"Use cases: {' '.join(use_cases)}",
        context,
    ]
    search_text = " ".join(search_parts)
    query_embedding = get_embedding(search_text)

    # 3. Fetch all tools and embeddings
    embeddings_result = supabase.table("tool_embeddings").select("*").execute()
    tools_result = supabase.table("tools").select("*").execute()
    tools_by_id = {t["id"]: Tool(**t) for t in tools_result.data}

    # 4. Score each tool
    scored_tools: list[tuple[Tool, float, list[MatchReason]]] = []

    for emb_row in embeddings_result.data:
        tool_id = emb_row["tool_id"]
        tool_embedding = emb_row["embedding"]

        if isinstance(tool_embedding, str):
            tool_embedding = json.loads(tool_embedding)

        if tool_id not in tools_by_id:
            continue

        tool = tools_by_id[tool_id]
        reasons = []

        # Base: cosine similarity (0-50)
        similarity = _cosine_similarity(query_embedding, tool_embedding)
        base_score = similarity * 50

        # Industry boost (0-15)
        industry_boost, industry_matched = _compute_industry_boost(tool.tags, industry)
        if industry_matched:
            reasons.append(MatchReason("industry", f"{industry}: {', '.join(industry_matched)}", industry_boost))

        # Keyword boost (0-10)
        keyword_boost, keyword_matched = _compute_keyword_boost(tool, keywords)
        if keyword_matched:
            reasons.append(MatchReason("keyword", ', '.join(keyword_matched[:3]), keyword_boost))

        # Category/gap boost (0-10)
        category_boost, category_matched = _compute_category_boost(tool.category, gaps, project_type)
        if category_matched:
            reasons.append(MatchReason("gap", ', '.join(category_matched[:2]), category_boost))

        # Use case boost (0-8)
        usecase_boost, usecase_matched = _compute_use_case_boost(tool, use_cases)
        if usecase_matched:
            reasons.append(MatchReason("use_case", usecase_matched[0], usecase_boost))

        # Tag relevance (0-7)
        combined_text = " ".join(gaps + keywords + use_cases).lower()
        tag_boost = sum(2 for tag in tool.tags if tag.lower() in combined_text)
        tag_boost = min(tag_boost, 7.0)

        # Redundancy penalty (-25 if project already has similar tech)
        redundancy_penalty, redundancy_reason = _compute_redundancy_penalty(tool, stack)
        if redundancy_penalty < 0:
            reasons.append(MatchReason("redundant", redundancy_reason, redundancy_penalty))

        final_score = max(0, min(base_score + industry_boost + keyword_boost + category_boost + usecase_boost + tag_boost + redundancy_penalty, 100.0))
        scored_tools.append((tool, final_score, reasons))

    # Sort and take top N
    scored_tools.sort(key=lambda x: x[1], reverse=True)
    top_tools = scored_tools[:limit]

    # 5. Generate explanations
    if top_tools:
        tools_list = [t for t, _, _ in top_tools]
        explanations = _generate_explanations_batch(tools_list, gaps, context, industry, keywords)
    else:
        explanations = []

    # 6. Build recommendations
    recommendations = []
    for i, (tool, score, reasons) in enumerate(top_tools):
        rec = Recommendation(
            tool=tool,
            suitability_score=round(score, 1),
            demo_priority=_calculate_demo_priority(score),
            explanation=explanations[i] if i < len(explanations) else "",
            match_reasons=reasons,
        )
        recommendations.append(rec)

    return recommendations
