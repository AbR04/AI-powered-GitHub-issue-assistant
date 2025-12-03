import re
from typing import Tuple, List
import os

import requests
from fastapi import HTTPException

from .schemas import IssuePayload, IssueComment, IssueRequest


GITHUB_API_BASE = "https://api.github.com"


def parse_github_repo_url(repo_url: str) -> Tuple[str, str]:
    """
    Parse URLs like:
      - https://github.com/owner/repo
      - https://github.com/owner/repo/
      - https://github.com/owner/repo/issues/123
    and return (owner, repo).
    """
    pattern = r"https?://github\.com/([^/]+)/([^/]+)"
    match = re.match(pattern, repo_url.strip())
    if not match:
        raise HTTPException(
            status_code=400,
            detail="Invalid GitHub repository URL. Expected format like https://github.com/owner/repo",
        )
    owner = match.group(1)
    repo = match.group(2).replace(".git", "")
    return owner, repo


def _build_github_headers() -> dict:
    """
    Use an optional GitHub token for higher rate limits, if provided.
    """
    token = os.getenv("GITHUB_TOKEN")
    headers = {"Accept": "application/vnd.github+json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def fetch_issue_data(request: IssueRequest) -> IssuePayload:
    owner, repo = parse_github_repo_url(str(request.repo_url))
    issue_number = request.issue_number

    headers = _build_github_headers()

    # Fetch main issue
    issue_url = f"{GITHUB_API_BASE}/repos/{owner}/{repo}/issues/{issue_number}"
    issue_resp = requests.get(issue_url, headers=headers, timeout=15)

    if issue_resp.status_code == 404:
        raise HTTPException(
            status_code=404,
            detail="Issue not found. Please check the repository URL and issue number.",
        )
    if not issue_resp.ok:
        raise HTTPException(
            status_code=issue_resp.status_code,
            detail=f"Failed to fetch issue from GitHub: {issue_resp.text}",
        )

    issue_json = issue_resp.json()
    title = issue_json.get("title", "")
    body = issue_json.get("body") or ""
    comments_count = issue_json.get("comments", 0)

    # Fetch comments if any
    comments: List[IssueComment] = []
    if comments_count > 0:
        comments_url = issue_json.get("comments_url")
        if comments_url:
            comments_resp = requests.get(comments_url, headers=headers, timeout=15)
            if comments_resp.ok:
                for c in comments_resp.json():
                    author = c.get("user", {}).get("login")
                    body_text = c.get("body") or ""
                    if body_text.strip():
                        comments.append(IssueComment(author=author, body=body_text))

    # Handle very long body/comments (truncate to keep LLM context reasonable)
    max_chars = 4000

    def _truncate(text: str, limit: int = max_chars) -> str:
        return text if len(text) <= limit else text[: limit - 3] + "..."

    body = _truncate(body)
    truncated_comments: List[IssueComment] = []
    for c in comments:
        truncated_comments.append(
            IssueComment(author=c.author, body=_truncate(c.body))
        )

    return IssuePayload(
        repo_owner=owner,
        repo_name=repo,
        issue_number=issue_number,
        title=title,
        body=body,
        comments=truncated_comments,
    )
