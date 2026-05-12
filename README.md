# 🛡️ CodeSentinel

## Autonomous multi-agent system for vulnerability research, code modernisation, and automated Pull Request delivery

CodeSentinel takes any public GitHub repository as input and produces a fully tested, documented Pull Request as output — with zero human intervention.

Three specialised AI agents collaborate to:
- detect vulnerabilities
- modernise legacy code
- generate and validate tests in a sandbox
- automatically open a PR with full documentation

Built for **GDG EUI x Duckurity AISprint Hackathon 2026 — Challenge 4: Agentic Code Enhancer**

---

# ⚙️ How It Works

## 🔍 Researcher Agent
- Scrapes CVE advisories (GitHub, NVD)
- Pulls research papers from arXiv
- Runs static analysis (AST + Bandit)
- Scores issues by:
  - severity
  - exploitability
  - remediation effort

---

## 🧠 Coder Agent
- Refactors legacy code
- Applies security patches (CVE fixes)
- Adds type hints and documentation
- Prioritises fixes based on severity scoring

---

## 🧪 QA Tester Agent
- Generates full `pytest` test suites
- Runs tests inside isolated Docker sandbox
- On failure:
  - produces structured rejection report
  - sends feedback back to Coder Agent

---

## 🔁 Autonomous Loop
This process repeats until:
- all tests pass
- all critical vulnerabilities are resolved

Then CodeSentinel:
- creates a branch
- opens a Pull Request
- attaches full documentation + changelog + test results

---

# 🧰 Tech Stack

- CrewAI — multi-agent orchestration
- Groq / Llama 3.3 — LLM backbone
- Docker — isolated sandbox execution
- PyGitHub — GitHub automation (branches + PRs)
- BeautifulSoup — CVE + arXiv scraping
- AST + Bandit — static + security analysis
- pytest — automated testing
- FastAPI + React — real-time dashboard (WebSockets)

---

# ✨ Key Features

## 📊 Severity Priority Matrix
Impact × Exploitability ÷ Effort

Every issue is ranked and fully explained inside each PR.

---

## 🛡️ Prompt Injection Guardrails
All repository code is sanitised before entering LLM context to prevent malicious injection via comments or code.

---

## 📡 Real-Time Agent Dashboard
- Live reasoning streams
- Tool call visibility
- Execution tracking
- Fully observable pipeline (no black box)

---

## 📝 Traceable Changelog
Each PR includes:
- Security Fixes 🔐
- Refactors ♻️
- Test Additions 🧪

Each change is linked to:
- CVEs
- arXiv research papers

---

## ⚡ Parallel Repository Processing
- Celery task queue
- multiple repositories at once
- isolated Docker environments per run

---

## 📈 Test Coverage Delta
Each PR includes:
- before vs after coverage
- measurable improvement report

---

# 🚀 Setup

Clone repo, install dependencies, and run dashboard:

git clone <repo-url>
cd codesentinel
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

Copy environment variables:

cp .env.example .env

Add:
- GROQ_API_KEY
- GITHUB_TOKEN

Run the dashboard:

uvicorn dashboard.main:app --reload

Open:
http://localhost:8000

Paste a GitHub repository URL → click **Run Pipeline**

---

# 📁 Project Structure

agents/
  researcher.py
  coder.py
  qa_tester.py

tools/
  scraper.py
  static_analysis.py
  github_tools.py
  sandbox.py
  sanitiser.py

pipeline/
  crew.py

dashboard/
  main.py
  frontend/src/App.jsx

---

# 👥 Team

Built at the GDG EUI AISprint Hackathon 2026, in collaboration with Duckurity
