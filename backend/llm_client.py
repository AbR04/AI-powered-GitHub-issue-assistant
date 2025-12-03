import json
import os
from typing import Dict, Any

from fastapi import HTTPException
from dotenv import load_dotenv
import google.generativeai as genai

from .schemas import IssuePayload, IssueAnalysis

# Load variables from .env
load_dotenv()

# Read API key from environment
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    model = None
else:
    genai.configure(api_key=GEMINI_API_KEY)
    # Use a Gemini model that supports text generation
    model = genai.GenerativeModel("gemini-2.5-flash")


def _build_prompt(issue: IssuePayload) -> str:
    """
    Build a detailed prompt with instructions and an inline example
    to encourage the model to output the required JSON structure.
    """

    comments_text = "No comments.\n"
    if issue.comments:
        parts = []
        for idx, c in enumerate(issue.comments, start=1):
            author = c.author or "unknown"
            parts.append(f"Comment {idx} by {author}:\n{c.body}\n")
        comments_text = "\n".join(parts)

    example_section = """
Example Output (IMPORTANT: This is just an example; adapt based on the actual issue):

{
  "summary": "User cannot log in due to a 500 error on the login API.",
  "type": "bug",
  "priority_score": "4 - Login failures affect many users and block access to the app.",
  "suggested_labels": ["bug", "authentication", "login-flow"],
  "potential_impact": "If unresolved, users will be unable to access their accounts, causing frustration and possible churn."
}
"""

    instructions = f"""
You are an AI assistant that reads GitHub issues and classifies them for a product/engineering team.

You will be given:
- Repository owner and name
- Issue number
- Issue title
- Issue body
- Issue comments (if any)

Your job is to analyze the issue and produce a single JSON object with EXACTLY the following fields:

- "summary": A one-sentence summary of the user's problem or request.
- "type": One of the following values ONLY:
    - "bug"
    - "feature_request"
    - "documentation"
    - "question"
    - "other"
- "priority_score": A string that starts with a number from 1 (low) to 5 (critical),
  followed by a hyphen and a brief justification. Example: "3 - Reason here..."
- "suggested_labels": An array of 2-3 short, relevant GitHub-style labels,
  e.g. ["bug", "UI", "performance"].
- "potential_impact": A brief sentence about the potential impact on users,
  especially if the issue describes a bug. If it is not a bug, briefly state the impact or importance.

Important Rules:
- Respond with VALID JSON only.
- Do not include any backticks, markdown, comments, or explanation.
- Do not wrap the JSON in ```json``` or any other formatting.
- The response MUST be a single JSON object.

{example_section}

Now analyze the following issue:

Repository: {issue.repo_owner}/{issue.repo_name}
Issue number: {issue.issue_number}

Title:
{issue.title}

Body:
{issue.body}

Comments:
{comments_text}

Return ONLY the JSON object described above.
"""

    return instructions.strip()


def _extract_json_from_text(text: str) -> str:
    """
    Gemini sometimes returns extra text or formatting around JSON.
    This helper tries to extract the JSON object by finding the first '{'
    and the last '}' and returning that slice.
    """
    text = text.strip()
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        # We didn't find a JSON-looking object
        raise ValueError("No JSON object found in model response.")
    return text[start : end + 1]


def analyze_issue_with_llm(issue: IssuePayload) -> IssueAnalysis:
    if model is None:
        raise HTTPException(
            status_code=500,
            detail="GEMINI_API_KEY is not set. Please configure it before using this endpoint.",
        )

    prompt = _build_prompt(issue)

    try:
        response = model.generate_content(
            prompt,
            generation_config={
                "temperature": 0.2,
            },
        )
        raw_text = response.text or ""
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error while calling Gemini API: {e}",
        )

    try:
        json_str = _extract_json_from_text(raw_text)
        data: Dict[str, Any] = json.loads(json_str)
    except Exception:
        # Keep this generic for the UI; logs would show more detail in a real app
        raise HTTPException(
            status_code=500,
            detail="Gemini did not return valid JSON. Please try again.",
        )

    required_keys = {
        "summary",
        "type",
        "priority_score",
        "suggested_labels",
        "potential_impact",
    }
    missing = required_keys - data.keys()
    if missing:
        raise HTTPException(
            status_code=500,
            detail=f"LLM response is missing fields: {', '.join(missing)}",
        )

    labels = data.get("suggested_labels", [])
    if not isinstance(labels, list):
        labels = [str(labels)]
    labels = [str(l).strip() for l in labels if str(l).strip()]
    if len(labels) == 0:
        labels = ["other"]

    analysis = IssueAnalysis(
        summary=str(data["summary"]).strip(),
        type=str(data["type"]).strip(),
        priority_score=str(data["priority_score"]).strip(),
        suggested_labels=labels,
        potential_impact=str(data["potential_impact"]).strip(),
    )
    return analysis
