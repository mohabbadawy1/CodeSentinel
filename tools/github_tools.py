import os
import tempfile
import subprocess
import json
from github import Github
from dotenv import load_dotenv

load_dotenv()


def clone_repo(repo_url: str) -> tuple[str, str]:
    """Clone a GitHub repo to a temp directory. Returns (local_path, repo_name)"""
    token = os.getenv("GITHUB_TOKEN")
    repo_name = repo_url.replace("https://github.com/", "").rstrip("/")
    auth_url = repo_url.replace("https://", f"https://{token}@")

    tmp_dir = tempfile.mkdtemp(prefix="codesentinel_")
    result = subprocess.run(
        ["git", "clone", auth_url, tmp_dir],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        raise RuntimeError(f"Git clone failed: {result.stderr}")

    return tmp_dir, repo_name


def get_default_branch(repo_name: str) -> str:
    g = Github(os.getenv("GITHUB_TOKEN"))
    repo = g.get_repo(repo_name)
    return repo.default_branch


def create_branch(repo_name: str, branch_name: str) -> bool:
    """Create a new branch on GitHub. Returns True if created."""
    try:
        g = Github(os.getenv("GITHUB_TOKEN"))
        repo = g.get_repo(repo_name)
        default = repo.default_branch
        base_sha = repo.get_branch(default).commit.sha
        repo.create_git_ref(f"refs/heads/{branch_name}", base_sha)
        return True
    except Exception as e:
        print(f"Branch creation note: {e}")
        return False


def push_changes(repo_path: str, branch_name: str, commit_message: str) -> bool:
    """Stage all changes, commit, and push to the remote branch."""
    try:
        subprocess.run(["git", "config", "user.email", "codesentinel@hackathon.dev"], cwd=repo_path)
        subprocess.run(["git", "config", "user.name", "CodeSentinel"], cwd=repo_path)
        subprocess.run(["git", "checkout", "-B", branch_name], cwd=repo_path, capture_output=True)
        subprocess.run(["git", "add", "-A"], cwd=repo_path)

        result = subprocess.run(
            ["git", "commit", "-m", commit_message],
            cwd=repo_path, capture_output=True, text=True
        )
        if "nothing to commit" in result.stdout:
            return False

        subprocess.run(["git", "push", "-f", "origin", branch_name], cwd=repo_path, capture_output=True)
        return True
    except Exception as e:
        print(f"Push failed: {e}")
        return False


def create_pull_request(
    repo_name: str,
    branch_name: str,
    changes_summary: str,
    findings: str,
    sandbox_result: dict,
    coverage_before: float = 0.0,
    coverage_after: float = 0.0
) -> str:
    """Create a Pull Request and return its URL."""
    g = Github(os.getenv("GITHUB_TOKEN"))
    repo = g.get_repo(repo_name)
    default = repo.default_branch

    status_emoji = "✅" if sandbox_result.get("passed") else "⚠️"

    security_fixes_md = ""
    refactors_md = ""
    files_modified_md = ""

    try:
        raw = changes_summary
        if "```" in raw:
            raw = raw.split("```")[1].replace("json", "").strip()
        data = json.loads(raw)

        changelog = data.get("changelog", {})
        for fix in changelog.get("security_fixes", []):
            security_fixes_md += f"- {fix}\n"
        for ref in changelog.get("refactors", []):
            refactors_md += f"- {ref}\n"
        for f in data.get("files_modified", []):
            files_modified_md += f"- `{f}`\n"
    except Exception:
        security_fixes_md = "_See summary below_"
        refactors_md = "_See summary below_"
        files_modified_md = "_Could not parse file list_"

    findings_md = ""
    try:
        fdata = json.loads(findings) if isinstance(findings, str) else findings
        for f in fdata.get("findings", [])[:5]:
            findings_md += f"| {f.get('id')} | {f.get('type')} | {f.get('score')} | {f.get('source')} | {f.get('issue', '')[:60]} |\n"
    except Exception:
        findings_md = "| — | — | — | — | Could not parse findings |\n"

    sandbox_stdout = sandbox_result.get("stdout", "No output")[:600]
    passed_str = "PASSED" if sandbox_result.get("passed") else "PARTIAL"
    delta = max(0, coverage_after - coverage_before)

    body = (
        "## 🤖 CodeSentinel — Autonomous Security Enhancement\n\n"
        "> Generated autonomously by **CodeSentinel**, a multi-agent AI pipeline built for the "
        "**GDG EUI × Duckurity AISprint Hackathon 2026** — Challenge 4: Agentic Code Enhancer.\n\n"
        "---\n\n"
        f"## 🔒 Security Fixes\n{security_fixes_md or '_No security fixes parsed_'}\n\n"
        f"## ♻️ Refactoring\n{refactors_md or '_No refactors parsed_'}\n\n"
        f"## 📁 Files Modified\n{files_modified_md or '_No files parsed_'}\n\n"
        "---\n\n"
        "## 📊 Findings (Top 5 by Priority Score)\n\n"
        "| ID | Type | Score | Source | Issue |\n"
        "|----|------|-------|--------|-------|\n"
        f"{findings_md}\n"
        "---\n\n"
        f"## 🧪 Test Results\n{status_emoji} **Status: {passed_str}**\n\n"
        f"```\n{sandbox_stdout}\n```\n\n"
        "## 📈 Coverage Delta\n"
        "| | Coverage |\n|---|---|\n"
        f"| Before | {coverage_before:.1f}% |\n"
        f"| After | {coverage_after:.1f}% |\n"
        f"| Delta | +{delta:.1f}% |\n\n"
        "---\n\n"
        "## 🤖 Agent Pipeline\n"
        "| Step | Agent | Action |\n|------|-------|--------|\n"
        "| 1 | 🔍 Researcher | Scraped CVEs, arXiv papers, ran Bandit static analysis, scored findings |\n"
        "| 2 | 💻 Coder | Applied fixes in priority order, added type hints and docstrings |\n"
        "| 3 | ✅ QA Tester | Generated pytest suite, validated in Docker sandbox, approved changes |\n\n"
        "---\n*🦆 CodeSentinel — GDG EUI × Duckurity AISprint Hackathon 2026*\n"
    )

    pr = repo.create_pull(
        title="[CodeSentinel] 🤖 Automated security patches and code modernisation",
        body=body,
        head=branch_name,
        base=default
    )
    return pr.html_url