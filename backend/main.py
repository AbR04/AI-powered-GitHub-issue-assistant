from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .schemas import IssueRequest, IssueAnalysis
from .github_client import fetch_issue_data
from .llm_client import analyze_issue_with_llm

app = FastAPI(
    title="AI-Powered GitHub Issue Assistant",
    description="Backend API that analyzes GitHub issues using an LLM",
    version="1.0.0",
)

# Allow local frontend to call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # in production you would restrict this
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.post("/analyze", response_model=IssueAnalysis)
def analyze_issue(request: IssueRequest):
    """
    Takes a GitHub repository URL and issue number, fetches the issue,
    and returns an AI-generated structured analysis.
    """
    issue_payload = fetch_issue_data(request)
    analysis = analyze_issue_with_llm(issue_payload)
    return analysis
