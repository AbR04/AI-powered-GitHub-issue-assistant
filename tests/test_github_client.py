from backend.github_client import parse_github_repo_url


def test_parse_github_repo_url_basic():
    owner, repo = parse_github_repo_url("https://github.com/facebook/react")
    assert owner == "facebook"
    assert repo == "react"


def test_parse_github_repo_url_with_issues_path():
    owner, repo = parse_github_repo_url("https://github.com/facebook/react/issues/123")
    assert owner == "facebook"
    assert repo == "react"
