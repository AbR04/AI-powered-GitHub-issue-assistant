from typing import List, Optional
from pydantic import BaseModel, HttpUrl, Field


class IssueRequest(BaseModel):
    repo_url: HttpUrl = Field(
        ...,
        description="Public GitHub repository URL, e.g. https://github.com/facebook/react",
    )
    issue_number: int = Field(..., ge=1, description="GitHub issue number")


class IssueComment(BaseModel):
    author: Optional[str]
    body: str


class IssuePayload(BaseModel):
    repo_owner: str
    repo_name: str
    issue_number: int
    title: str
    body: str
    comments: List[IssueComment]


class IssueAnalysis(BaseModel):
    summary: str
    type: str
    priority_score: str
    suggested_labels: List[str]
    potential_impact: str
