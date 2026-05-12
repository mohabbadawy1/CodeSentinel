from crewai import Crew, Process
from agents.researcher import researcher, build_research_task
from agents.coder import coder, build_coder_task
from agents.qa_tester import qa_tester, build_qa_task
from tools.github_tools import clone_repo, create_branch, push_changes, create_pull_request
from tools.sandbox import run_in_sandbox
from tools.sanitiser import sanitise_findings
from dotenv import load_dotenv
import os
import json

load_dotenv()

MAX_RETRIES = 3


def run_pipeline(repo_url: str, log_callback=None) -> dict:
    """
    Run the full CodeSentinel pipeline on a GitHub repository.

    Args:
        repo_url: Full GitHub URL e.g. https://github.com/owner/repo
        log_callback: Optional function(str) called with each log message

    Returns:
        dict with pr_url, approved, changes
    """

    def log(msg: str):
        print(msg)
        if log_callback:
            log_callback(msg)

    result = {
        "pr_url": None,
        "approved": False,
        "changes": "",
        "error": None
    }

    try:
        # ── STEP 1: Clone repo ──
        log(f"[PIPELINE] Starting CodeSentinel on {repo_url}")
        log("[STEP 1/5] Cloning repository...")
        repo_path, repo_name = clone_repo(repo_url)
        branch_name = "codesentinel/auto-patch"
        log(f"[STEP 1/5] Cloned to {repo_path}")

        # ── STEP 2: Researcher agent ──
        log("[STEP 2/5] Researcher agent starting — scraping CVEs and running static analysis...")
        research_task = build_research_task(repo_path)
        research_crew = Crew(
            agents=[researcher],
            tasks=[research_task],
            process=Process.sequential,
            verbose=True
        )
        findings_raw = str(research_crew.kickoff())
        findings_safe = sanitise_findings(findings_raw)
        log(f"[STEP 2/5] Research complete. Preview: {findings_safe[:200]}...")

        # ── STEP 3: Coder + QA debate loop ──
        approved = False
        changes_summary = ""
        sandbox_result = {"passed": False, "stdout": "", "stderr": ""}
        rejection_feedback = ""

        for attempt in range(1, MAX_RETRIES + 1):
            log(f"[STEP 3/5] Coder agent — attempt {attempt}/{MAX_RETRIES}")
            coder_task = build_coder_task(findings_safe, repo_path, rejection_feedback)
            coder_crew = Crew(
                agents=[coder],
                tasks=[coder_task],
                process=Process.sequential,
                verbose=True
            )
            changes_summary = str(coder_crew.kickoff())
            log(f"[STEP 3/5] Coder finished. Changes: {changes_summary[:150]}...")

            # Run sandbox
            log(f"[STEP 4/5] QA Tester — running tests in Docker sandbox (attempt {attempt}/{MAX_RETRIES})...")
            sandbox_result = run_in_sandbox(repo_path)

            # QA agent evaluates
            qa_task = build_qa_task(changes_summary, repo_path, sandbox_result)
            qa_crew = Crew(
                agents=[qa_tester],
                tasks=[qa_task],
                process=Process.sequential,
                verbose=True
            )
            qa_result = str(qa_crew.kickoff())

            if sandbox_result["passed"] or "APPROVED" in qa_result.upper():
                log(f"[STEP 4/5] QA APPROVED — all tests passed on attempt {attempt}")
                approved = True
                break
            else:
                log(f"[STEP 4/5] QA REJECTED — attempt {attempt}. Sending feedback to Coder...")
                rejection_feedback = f"QA Rejection (attempt {attempt}):\n{qa_result}\n\nSandbox output:\n{sandbox_result['stdout'][:500]}"

        if not approved:
            log("[STEP 4/5] Max retries reached — submitting best attempt")

        # ── STEP 5: Create PR ──
        log("[STEP 5/5] Creating Pull Request on GitHub...")
        create_branch(repo_name, branch_name)
        push_changes(repo_path, branch_name, "[CodeSentinel] Automated security patches and modernisation")

        pr_url = create_pull_request(
            repo_name=repo_name,
            branch_name=branch_name,
            changes_summary=changes_summary,
            findings=findings_safe,
            sandbox_result=sandbox_result,
            coverage_before=sandbox_result.get("coverage_before", 0.0),
            coverage_after=sandbox_result.get("coverage_after", 0.0),
)

        log(f"[PIPELINE] Done! Pull Request created: {pr_url}")

        result["pr_url"] = pr_url
        result["approved"] = approved
        result["changes"] = changes_summary

    except Exception as e:
        error_msg = f"[PIPELINE ERROR] {str(e)}"
        log(error_msg)
        result["error"] = str(e)

    return result


if __name__ == "__main__":
    # Quick test — run from terminal: python -m pipeline.crew
    import sys
    repo = sys.argv[1] if len(sys.argv) > 1 else os.getenv("TARGET_REPO", "")
    if not repo:
        print("Usage: python -m pipeline.crew https://github.com/owner/repo")
    else:
        run_pipeline(repo)
