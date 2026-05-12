import subprocess
import os
import re


def parse_coverage(output: str) -> float:
    """Extract total coverage percentage from pytest-cov output."""
    match = re.search(r'TOTAL\s+\d+\s+\d+\s+(\d+)%', output)
    if match:
        return float(match.group(1))
    match = re.search(r'(\d+)%\s+coverage', output)
    if match:
        return float(match.group(1))
    return 0.0


def run_in_sandbox(repo_path: str) -> dict:
    """
    Run pytest inside an isolated Docker container.
    No network access, limited memory, read-only mount.
    Returns dict with passed, stdout, stderr, coverage_before, coverage_after.
    """
    try:
        # ── STEP 1: Measure coverage BEFORE changes (on original tests) ──
        before_result = subprocess.run([
            "docker", "run", "--rm",
            "--network=none",
            "--memory=512m",
            "--cpus=1",
            "-v", f"{repo_path}:/app",
            "-w", "/app",
            "python:3.11-slim",
            "bash", "-c",
            (
                "pip install pytest pytest-cov bandit -q 2>/dev/null; "
                "pip install -r requirements.txt -q 2>/dev/null || true; "
                "pytest tests/ --cov=. --cov-report=term-missing -q 2>&1 || "
                "pytest --cov=. --cov-report=term-missing -q 2>&1"
            )
        ], capture_output=True, text=True, timeout=120)

        coverage_before = parse_coverage(before_result.stdout)

        # ── STEP 2: Run full test suite WITH coverage AFTER changes ──
        after_result = subprocess.run([
            "docker", "run", "--rm",
            "--network=none",
            "--memory=512m",
            "--cpus=1",
            "-v", f"{repo_path}:/app",
            "-w", "/app",
            "python:3.11-slim",
            "bash", "-c",
            (
                "pip install pytest pytest-cov bandit -q 2>/dev/null; "
                "pip install -r requirements.txt -q 2>/dev/null || true; "
                "pytest tests/ --cov=. --cov-report=term-missing --tb=short -q 2>&1 || "
                "pytest --cov=. --cov-report=term-missing --tb=short -q 2>&1"
            )
        ], capture_output=True, text=True, timeout=120)

        coverage_after = parse_coverage(after_result.stdout)
        passed = after_result.returncode == 0

        return {
            "passed": passed,
            "stdout": after_result.stdout,
            "stderr": after_result.stderr,
            "return_code": after_result.returncode,
            "coverage_before": coverage_before,
            "coverage_after": coverage_after,
            "coverage_delta": round(coverage_after - coverage_before, 1)
        }

    except subprocess.TimeoutExpired:
        return {
            "passed": False,
            "stdout": "",
            "stderr": "Docker sandbox timed out after 120 seconds.",
            "return_code": -1,
            "coverage_before": 0.0,
            "coverage_after": 0.0,
            "coverage_delta": 0.0
        }
    except FileNotFoundError:
        return run_locally(repo_path)
    except Exception as e:
        return {
            "passed": False,
            "stdout": "",
            "stderr": str(e),
            "return_code": -1,
            "coverage_before": 0.0,
            "coverage_after": 0.0,
            "coverage_delta": 0.0
        }


def run_locally(repo_path: str) -> dict:
    """Fallback: run pytest locally if Docker is not available."""
    try:
        result = subprocess.run(
            ["pytest", "tests/", "--cov=.", "--cov-report=term-missing", "--tb=short", "-q"],
            capture_output=True, text=True,
            cwd=repo_path, timeout=60
        )
        coverage = parse_coverage(result.stdout)
        return {
            "passed": result.returncode == 0,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "return_code": result.returncode,
            "coverage_before": 0.0,
            "coverage_after": coverage,
            "coverage_delta": coverage
        }
    except Exception as e:
        return {
            "passed": False,
            "stdout": "",
            "stderr": str(e),
            "return_code": -1,
            "coverage_before": 0.0,
            "coverage_after": 0.0,
            "coverage_delta": 0.0
        }