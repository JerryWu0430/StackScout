# Repository analyzer service
import os
import json
from pydantic import BaseModel, Field
from openai import OpenAI
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
    # New fields for better matching
    industry: str = Field(default="general", description="Industry: fintech, ecommerce, healthcare, devtools, saas, ai-ml, media, education, general")
    project_type: str = Field(default="web_app", description="Type: api, web_app, mobile, cli, library, data_pipeline, ml_model")
    keywords: list[str] = Field(default_factory=list, description="Key domain terms extracted from README/code")
    use_cases: list[str] = Field(default_factory=list, description="What the project does/solves")


def _get_client() -> OpenAI:
    """Get OpenAI-compatible client (LiteLLM or OpenAI)."""
    base_url = os.getenv("LITELLM_BASE_URL")
    api_key = os.getenv("LITELLM_API_KEY") or os.getenv("OPENAI_API_KEY")

    if base_url:
        return OpenAI(base_url=base_url, api_key=api_key)
    return OpenAI(api_key=api_key)


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

5. **Recommendations Context**: 2-3 sentence summary of what tools/services would help

6. **Industry**: Detect the business domain. Choose ONE from:
   - fintech (payments, banking, trading, crypto)
   - ecommerce (retail, marketplace, shopping)
   - healthcare (medical, health tech, fitness)
   - devtools (developer tools, SDKs, APIs for developers)
   - saas (B2B software, productivity tools)
   - ai-ml (AI/ML products, data science)
   - media (content, streaming, social)
   - education (learning, courses, edtech)
   - general (other/unclear)

7. **Project Type**: What kind of software. Choose ONE from:
   - api (REST/GraphQL API service)
   - web_app (full-stack web application)
   - mobile (iOS/Android app)
   - cli (command-line tool)
   - library (reusable package/SDK)
   - data_pipeline (ETL, data processing)
   - ml_model (ML training/inference)

8. **Keywords**: Extract 5-10 domain-specific keywords that describe what this project does.
   Examples: "payments", "authentication", "real-time chat", "image processing", "api gateway"

9. **Use Cases**: 2-4 specific things this project enables/solves.
   Examples: "process credit card payments", "manage user sessions", "analyze customer data"

Be specific about versions and technologies detected. Focus on actionable insights.

Respond with valid JSON matching this schema:
{schema}

Return ONLY the JSON, no markdown or explanation."""


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


RESPONSE_SCHEMA = """{
  "stack": {
    "frontend": ["list of frontend techs"],
    "backend": ["list of backend techs"],
    "database": ["list of database techs"],
    "infrastructure": ["list of infra techs"]
  },
  "gaps": ["list of missing best practices"],
  "risk_flags": ["list of potential issues"],
  "complexity_score": 1-10,
  "recommendations_context": "summary string",
  "industry": "one of: fintech, ecommerce, healthcare, devtools, saas, ai-ml, media, education, general",
  "project_type": "one of: api, web_app, mobile, cli, library, data_pipeline, ml_model",
  "keywords": ["domain", "specific", "keywords"],
  "use_cases": ["what the project does"]
}"""


@retry(
    retry=retry_if_exception_type(Exception),
    wait=wait_exponential(multiplier=1, min=1, max=60),
    stop=stop_after_attempt(3),
)
def analyze_repo(repo_files: dict) -> RepoFingerprint:
    """Analyze repository files and return structured fingerprint."""
    files = repo_files.get("files", {})
    languages = repo_files.get("languages", {})

    prompt = ANALYSIS_PROMPT.format(
        files_content=_format_files_for_prompt(files),
        languages=json.dumps(languages, indent=2),
        schema=RESPONSE_SCHEMA,
    )

    client = _get_client()
    model = os.getenv("LITELLM_MODEL", "gpt-4o")

    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "You are a senior software architect analyzing repositories. Always respond with valid JSON only."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.1,
    )

    result_text = response.choices[0].message.content
    # Strip markdown code blocks if present
    if result_text.startswith("```"):
        result_text = result_text.split("```")[1]
        if result_text.startswith("json"):
            result_text = result_text[4:]
    result_text = result_text.strip()

    result = json.loads(result_text)
    return RepoFingerprint(**result)
