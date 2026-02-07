# Repository analyzer service
import os
import json
from pydantic import BaseModel, Field
from openai import OpenAI, RateLimitError
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type


class TechStack(BaseModel):
    frontend: list[str] = Field(default_factory=list, description="Frontend frameworks/libs")
    backend: list[str] = Field(default_factory=list, description="Backend frameworks/libs")
    database: list[str] = Field(default_factory=list, description="Database technologies")
    infrastructure: list[str] = Field(default_factory=list, description="Infra/DevOps tools")


class RepoFingerprint(BaseModel):
    stack: TechStack = Field(description="Detected tech stack by category")
    gaps: list[str] = Field(default_factory=list, description="Missing best practices")
    risk_flags: list[str] = Field(default_factory=list, description="Potential issues")
    complexity_score: int = Field(ge=1, le=10, description="Complexity rating 1-10")
    recommendations_context: str = Field(description="Summary for embedding/matching")


def _get_client() -> OpenAI:
    """Get OpenAI client (lazy init)."""
    return OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


ANALYSIS_PROMPT = """Analyze this repository and provide a detailed fingerprint.

Repository files:
{files_content}

Languages (bytes):
{languages}

Based on the files, identify:
1. **Stack**: Categorize technologies into frontend, backend, database, infrastructure
2. **Gaps**: Missing best practices (CI/CD, testing, monitoring, security, docs, etc.)
3. **Risk Flags**: Potential issues (outdated deps, security concerns, missing configs)
4. **Complexity Score**: 1-10 based on project size, tech diversity, architecture complexity
5. **Recommendations Context**: 2-3 sentence summary of what tools/services would help this project

Be specific about versions and technologies detected. Focus on actionable insights."""


def _format_files_for_prompt(files: dict) -> str:
    """Format files dict for LLM prompt, truncating large files."""
    parts = []
    for path, content in files.items():
        if isinstance(content, dict):
            content_str = json.dumps(content, indent=2)
        else:
            content_str = str(content)

        # Truncate large files
        if len(content_str) > 3000:
            content_str = content_str[:3000] + "\n... [truncated]"

        parts.append(f"=== {path} ===\n{content_str}")

    return "\n\n".join(parts)


@retry(
    retry=retry_if_exception_type(RateLimitError),
    wait=wait_exponential(multiplier=1, min=1, max=60),
    stop=stop_after_attempt(5),
)
def analyze_repo(repo_files: dict) -> RepoFingerprint:
    """Analyze repository files and return structured fingerprint.

    Args:
        repo_files: Dict from github.fetch_repo_files() with keys:
            - owner: str
            - repo: str
            - files: dict[str, str|dict]
            - languages: dict[str, int]

    Returns:
        RepoFingerprint with stack analysis, gaps, risks, and recommendations
    """
    files = repo_files.get("files", {})
    languages = repo_files.get("languages", {})

    prompt = ANALYSIS_PROMPT.format(
        files_content=_format_files_for_prompt(files),
        languages=json.dumps(languages, indent=2),
    )

    response = _get_client().beta.chat.completions.parse(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are a senior software architect analyzing repositories."},
            {"role": "user", "content": prompt},
        ],
        response_format=RepoFingerprint,
    )

    return response.choices[0].message.parsed
