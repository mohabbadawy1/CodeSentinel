from crewai import Agent, Task
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
import os

load_dotenv()

llm = ChatOpenAI(
    model="llama-3.3-70b-versatile", openai_api_base="https://api.groq.com/openai/v1", openai_api_key=os.getenv("GROQ_API_KEY"),
    api_key=os.getenv("GROQ_API_KEY")
)

coder = Agent(
    role="Senior Software Engineer",
    goal="Fix all identified vulnerabilities and modernise legacy code to production quality",
    backstory=(
        "You are a senior engineer specialising in security patches and code modernisation. "
        "You write clean, well-documented Python code with type hints. "
        "You address issues in order of priority score and always explain your changes clearly."
    ),
    llm=llm,
    verbose=True,
    allow_delegation=False
)

def build_coder_task(findings_report: str, repo_path: str, rejection_feedback: str = "") -> Task:
    feedback_section = ""
    if rejection_feedback:
        feedback_section = f"""
        IMPORTANT — Previous attempt was REJECTED by QA Tester:
        {rejection_feedback}
        Fix the above issues before proceeding.
        """

    return Task(
        description=f"""
        You are fixing a Python repository located at: {repo_path}
        {feedback_section}

        Findings report (address in order of score, highest first):
        {findings_report}

        For each finding:
        1. Open the relevant file
        2. Apply the fix — patch the CVE, replace deprecated API, or modernise the code
        3. Add type hints to every function you modify
        4. Add or update the docstring for every function you modify
        5. Do NOT break existing functionality

        After making all changes, return a structured summary:
        {{
            "files_modified": ["list of files changed"],
            "changes": [
                {{
                    "file": "path/to/file.py",
                    "function": "function_name",
                    "change": "what was changed and why",
                    "finding_id": "F001"
                }}
            ],
            "changelog": {{
                "security_fixes": ["list of security fixes made"],
                "refactors": ["list of refactors made"],
                "test_additions": []
            }}
        }}
        """,
        agent=coder,
        expected_output="JSON summary of all code changes made"
    )
