import ast
import subprocess
import json
import os
from crewai.tools import tool


@tool("Static Analyser")
def run_static_analysis(repo_path: str) -> str:
    """
    Run AST analysis and Bandit security scan on a repository.
    Input: absolute path to the cloned repository
    Returns a JSON string of prioritised findings.
    """
    findings = []

    # ── Bandit security scan ──
    try:
        result = subprocess.run(
            ["bandit", "-r", repo_path, "-f", "json", "-q", "--exit-zero"],
            capture_output=True, text=True, timeout=60
        )
        if result.stdout:
            bandit_data = json.loads(result.stdout)
            for issue in bandit_data.get("results", [])[:20]:
                severity = issue.get("issue_severity", "LOW")
                impact = {"HIGH": 5, "MEDIUM": 3, "LOW": 1}.get(severity, 2)
                findings.append({
                    "id": f"B{len(findings)+1:03d}",
                    "type": "security",
                    "file": issue["filename"].replace(repo_path, "").lstrip("/"),
                    "line": issue["line_number"],
                    "issue": issue["issue_text"],
                    "fix": f"Address {issue.get('test_id', 'security issue')}: {issue['issue_text']}",
                    "impact": impact,
                    "exploitability": 3,
                    "effort": 2,
                    "source": "bandit"
                })
    except Exception as e:
        findings.append({
            "id": "B000", "type": "info",
            "file": "N/A", "issue": f"Bandit scan error: {str(e)}",
            "fix": "Install bandit: pip install bandit",
            "impact": 0, "exploitability": 0, "effort": 0, "source": "bandit"
        })

    # ── AST legacy pattern detection ──
    legacy_count = 0
    for root, dirs, files in os.walk(repo_path):
        dirs[:] = [d for d in dirs if d not in ['venv', '.git', '__pycache__', 'node_modules']]
        for fname in files:
            if not fname.endswith('.py'):
                continue
            fpath = os.path.join(root, fname)
            rel_path = fpath.replace(repo_path, "").lstrip("/")
            try:
                with open(fpath, encoding="utf-8", errors="ignore") as f:
                    source = f.read()
                tree = ast.parse(source)

                for node in ast.walk(tree):
                    # Missing type hints
                    if isinstance(node, ast.FunctionDef):
                        missing_hints = not node.returns or not all(
                            a.annotation for a in node.args.args
                            if a.arg != 'self'
                        )
                        if missing_hints and legacy_count < 10:
                            findings.append({
                                "id": f"L{legacy_count+1:03d}",
                                "type": "legacy",
                                "file": rel_path,
                                "line": node.lineno,
                                "issue": f"Function '{node.name}' missing type annotations",
                                "fix": f"Add type hints to function '{node.name}' parameters and return type",
                                "impact": 2, "exploitability": 1, "effort": 1,
                                "source": "ast"
                            })
                            legacy_count += 1

                    # Bare except clauses
                    if isinstance(node, ast.ExceptHandler) and node.type is None:
                        findings.append({
                            "id": f"L{legacy_count+1:03d}",
                            "type": "legacy",
                            "file": rel_path,
                            "line": node.lineno,
                            "issue": "Bare 'except:' clause catches all exceptions including SystemExit",
                            "fix": "Replace bare 'except:' with specific exception types e.g. 'except Exception:'",
                            "impact": 2, "exploitability": 2, "effort": 1,
                            "source": "ast"
                        })
                        legacy_count += 1

            except SyntaxError:
                pass
            except Exception:
                pass

    # ── Score and sort ──
    for f in findings:
        if f.get("impact", 0) > 0:
            f["score"] = round((f["impact"] * f["exploitability"]) / max(f["effort"], 1), 2)
        else:
            f["score"] = 0

    findings.sort(key=lambda x: x["score"], reverse=True)
    top_findings = findings[:15]

    return json.dumps({
        "total_found": len(findings),
        "findings": top_findings,
        "summary": f"Found {len(findings)} issues: {sum(1 for f in findings if f['type']=='security')} security, {sum(1 for f in findings if f['type']=='legacy')} legacy patterns."
    }, indent=2)
