from crewai import Agent, Task
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
import os

load_dotenv()

llm = ChatOpenAI(
    model="llama-3.3-70b-versatile",
    openai_api_base="https://api.groq.com/openai/v1",
    openai_api_key=os.getenv("GROQ_API_KEY"),
    api_key=os.getenv("GROQ_API_KEY")
)

qa_tester = Agent(
    role="QA Engineer",
    goal="Ensure all code changes are correct, well-tested, and safe before they ship",
    backstory=(
        "You are a meticulous QA engineer. Nothing ships without your approval. "
        "You write comprehensive pytest test suites and run them in isolated environments. "
        "If anything fails, you produce a clear rejection report so the Coder can fix it."
    ),
    llm=llm,
    verbose=True,
    allow_delegation=False
)

def build_qa_task(changes_summary: str, repo_path: str, sandbox_result: dict) -> Task:
    status = "PASSED" if sandbox_result.get("passed") else "FAILED"
    output = sandbox_result.get("stdout", "")[:1000]

    return Task(
        description=f"""
        Review the following code changes made to the repository at: {repo_path}

        Changes summary:
        {changes_summary}

        Docker sandbox test results — Status: {status}
        Output:
        {output}

        Your job:
        1. Write pytest unit tests for every function that was modified
           - Save them to {repo_path}/tests/test_codesentinel.py
           - Test both happy path and edge cases
           - Each test must have a clear docstring

        2. Evaluate the sandbox results:
           - If PASSED: return APPROVED with the test file content
           - If FAILED: return REJECTED with:
             a. Exactly which test failed and why
             b. What the Coder needs to fix
             c. Specific line numbers if possible

        Return your response in this format:
        {{
            "verdict": "APPROVED" or "REJECTED",
            "test_file": "full content of test_codesentinel.py",
            "coverage_notes": "what is and isn't covered",
            "rejection_reason": "only if REJECTED — exact issues for the Coder to fix"
        }}
        """,
        agent=qa_tester,
        expected_output="APPROVED or REJECTED verdict with test file and reasoning"
    )