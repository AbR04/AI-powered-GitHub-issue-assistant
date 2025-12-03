# AI-Powered GitHub Issue Assistant

A simple AI agent that analyzes a GitHub issue and returns a structured JSON summary
including type, priority, suggested labels, and potential impact.

This project is built as part of the Seedling Labs Engineering Intern Craft Case.

---

## ✨ Features

- Input:
  - Public GitHub repository URL (e.g. `https://github.com/facebook/react`)
  - GitHub issue number
- Backend (FastAPI):
  - Fetches issue title, body, and comments via GitHub REST API
  - Uses an LLM (OpenAI) to:
    - Summarize the issue
    - Classify type (bug, feature_request, documentation, question, other)
    - Assign a priority score (1–5) with justification
    - Suggest GitHub-style labels
    - Describe potential impact
- Frontend (Streamlit):
  - Clean UI for input and display
  - Structured view of the analysis
  - Raw JSON view
  - Copyable JSON block (extra UX touch)
- Engineering:
  - Clear project structure
  - Typed models with Pydantic
  - Basic edge case handling (invalid URL, missing issue, long content)

---

## 🚀 Quick Start (Under 5 Minutes)

### 1. Clone the repository

```bash
git clone https://github.com/<your-username>/ai-github-issue-assistant.git
cd ai-github-issue-assistant
