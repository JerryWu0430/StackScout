# GitHub API service
import os
import re
import json
import base64
from typing import Optional
import httpx

GITHUB_API_BASE = "https://api.github.com"

# Key dependency files to fetch
DEPENDENCY_FILES = [
    "package.json",
    "requirements.txt",
    "pyproject.toml",
    "Gemfile",
    "go.mod",
    "Cargo.toml",
    "docker-compose.yml",
    "docker-compose.yaml",
    "README.md",
]


def _get_headers() -> dict:
    """Get headers for GitHub API requests."""
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    token = os.getenv("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def parse_repo_url(repo_url: str) -> tuple[str, str]:
    """Parse owner and repo name from GitHub URL.

    Supports:
    - https://github.com/owner/repo
    - https://github.com/owner/repo.git
    - github.com/owner/repo
    - owner/repo
    """
    # Remove .git suffix if present
    url = repo_url.rstrip("/").removesuffix(".git")

    # Try to match full URL pattern
    match = re.match(r"(?:https?://)?(?:www\.)?github\.com/([^/]+)/([^/]+)", url)
    if match:
        return match.group(1), match.group(2)

    # Try owner/repo pattern
    match = re.match(r"^([^/]+)/([^/]+)$", url)
    if match:
        return match.group(1), match.group(2)

    raise ValueError(f"Invalid GitHub repo URL: {repo_url}")


async def _fetch_file_content(
    client: httpx.AsyncClient, owner: str, repo: str, path: str
) -> Optional[str]:
    """Fetch single file content from repo."""
    url = f"{GITHUB_API_BASE}/repos/{owner}/{repo}/contents/{path}"
    resp = await client.get(url, headers=_get_headers())

    if resp.status_code == 404:
        return None
    resp.raise_for_status()

    data = resp.json()
    if data.get("type") != "file":
        return None

    content = data.get("content", "")
    encoding = data.get("encoding", "")

    if encoding == "base64":
        return base64.b64decode(content).decode("utf-8")
    return content


async def _fetch_workflow_files(
    client: httpx.AsyncClient, owner: str, repo: str
) -> dict[str, str]:
    """Fetch all workflow files from .github/workflows/."""
    workflows = {}
    url = f"{GITHUB_API_BASE}/repos/{owner}/{repo}/contents/.github/workflows"
    resp = await client.get(url, headers=_get_headers())

    if resp.status_code == 404:
        return workflows
    resp.raise_for_status()

    files = resp.json()
    for f in files:
        if f.get("type") == "file" and f["name"].endswith((".yml", ".yaml")):
            content = await _fetch_file_content(
                client, owner, repo, f".github/workflows/{f['name']}"
            )
            if content:
                workflows[f".github/workflows/{f['name']}"] = content

    return workflows


async def _fetch_languages(
    client: httpx.AsyncClient, owner: str, repo: str
) -> dict[str, int]:
    """Fetch repo language breakdown from GitHub API."""
    url = f"{GITHUB_API_BASE}/repos/{owner}/{repo}/languages"
    resp = await client.get(url, headers=_get_headers())
    resp.raise_for_status()
    return resp.json()


async def fetch_repo_files(repo_url: str) -> dict:
    """Fetch key files from a GitHub repository.

    Args:
        repo_url: GitHub repo URL (e.g., https://github.com/owner/repo)

    Returns:
        dict with owner, repo, files dict, and languages dict
    """
    owner, repo = parse_repo_url(repo_url)

    files = {}
    async with httpx.AsyncClient(timeout=30.0) as client:
        # Fetch dependency files
        for filepath in DEPENDENCY_FILES:
            content = await _fetch_file_content(client, owner, repo, filepath)
            if content:
                # Parse JSON files
                if filepath.endswith(".json"):
                    try:
                        files[filepath] = json.loads(content)
                    except json.JSONDecodeError:
                        files[filepath] = content
                else:
                    files[filepath] = content

        # Fetch workflow files
        workflow_files = await _fetch_workflow_files(client, owner, repo)
        files.update(workflow_files)

        # Fetch languages
        languages = await _fetch_languages(client, owner, repo)

    return {
        "owner": owner,
        "repo": repo,
        "files": files,
        "languages": languages,
    }
