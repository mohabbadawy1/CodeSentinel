from crewai import Agent, Task
from langchain_openai import ChatOpenAI
from tools.scraper import scrape_cves, scrape_arxiv
from tools.static_analysis import run_static_analysis
from dotenv import load_dotenv
import os

load_dotenv()

llm = ChatOpenAI(
    model="llama-3.3-70b-versatile",
    openai_api_base="https://api.groq.com/openai/v1",
    openai_api_key=os.getenv("GROQ_API_KEY"),
    api_key=os.getenv("GROQ_API_KEY")
)

researcher = Agent(
    role="Security Researcher",
    goal="Identify all vulnerabilities, deprecated patterns, and security issues in a GitHub repository",
    backstory=(
        "You are an expert in CVE databases, security research, and static code analysis. "
        "You methodically analyse codebases, cross-reference known vulnerabilities, and "
        "produce clear, actionable findings reports ordered by priority."
    ),
    tools=[scrape_cves, scrape_arxiv, run_static_analysis],
    llm=llm,
    verbose=True,
    allow_delegation=False
)

def build_research_task(repo_path: str, language: str = "python") -> Task:
    return Task(
        description=f"""
        Analyse the repository at: {repo_path}

        Steps:
        1. Run static analysis on the repo using the Static Analyser tool
        2. Scrape GitHub CVE advisories for '{language}' using the CVE Scraper tool
        3. Scrape arXiv for recent '{language} security' papers using the ArXiv Scraper tool
        4. Combine all findings into a single prioritised list
        5. Score each finding using: Score = (Impact x Exploitability) / Effort
           - Impact: 1-5 (how bad if exploited)
           - Exploitability: 1-5 (how easy to exploit)
           - Effort: 1-5 (how hard to fix, lower = easier)
        6. Sort findings by score descending

        Return a JSON report with this structure:
        {{
            "findings": [
                {{
                    "id": "F001",
                    "type": "security|legacy|missing_tests",
                    "file": "path/to/file.py",
                    "issue": "description of the issue",
                    "fix": "suggested fix",
                    "score": 8.0,
                    "source": "bandit|cve|arxiv|ast"
                }}
            ],
            "summary": "brief overall summary"
        }}
        """,
        agent=researcher,
        expected_output="A JSON findings report with prioritised issues"
    )