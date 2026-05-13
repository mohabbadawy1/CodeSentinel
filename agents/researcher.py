from crewai import Agent, Task
from langchain_groq import ChatGroq
from dotenv import load_dotenv
import os

load_dotenv()

llm = ChatGroq(
    model="groq/llama-3.1-8b-instant",
    temperature=0,
    api_key=os.getenv("GROQ_API_KEY")
)

researcher = Agent(
    role="Security Researcher",
    goal="Identify vulnerabilities",
    backstory="Expert security researcher",
    tools=[],
    llm="groq/llama-3.1-8b-instant",
    verbose=False,
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
