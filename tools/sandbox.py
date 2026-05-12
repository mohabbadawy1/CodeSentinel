import subprocess
import re

CMD = (
    "pip install pytest pytest-cov -q && "
    "pip install -e . -q 2>/dev/null || true; "
    "python -m pytest tests/ --cov=. --cov-report=term-missing --tb=short -q 2>&1 || "
    "python -m pytest --cov=. --cov-report=term-missing --tb=short -q 2>&1"
)


def parse_coverage(output: str) -> float:
    match = re.search(r'TOTAL\s+\d+\s+\d+\s+(\d+)%', output)
    if match:
        return float(match.group(1))
    return 0.0


def run_in_sandbox(repo_path: str) -> dict:
    try:
        before_result = subprocess.run([
            "docker", "run", "--rm", "--network=none", "--memory=512m", "--cpus=1",
            "-v", f"{repo_path}:/app", "-w", "/app", "python:3.11-slim",
            "bash", "-c", CMD
        ], capture_output=True, text=True, timeout=180)
        coverage_before = parse_coverage(before_result.stdout)

        after_result = subprocess.run([
            "docker", "run", "--rm", "--network=none", "--memory=512m", "--cpus=1",
            "-v", f"{repo_path}:/app", "-w", "/app", "python:3.11-slim",
            "bash", "-c", CMD
        ], capture_output=True, text=True, timeout=180)
        coverage_after = parse_coverage(after_result.stdout)

        return {
            "passed": after_result.returncode == 0,
            "stdout": after_result.stdout,
            "stderr": after_result.stderr,
            "return_code": after_result.returncode,
            "coverage_before": coverage_before,
            "coverage_after": coverage_after,
            "coverage_delta": round(coverage_after - coverage_before, 1)
        }
    except subprocess.TimeoutExpired:
        return {"passed": False, "stdout": "", "stderr": "Timed out.", "return_code": -1,
                "coverage_before": 0.0, "coverage_after": 0.0, "coverage_delta": 0.0}
    except FileNotFoundError:
        return run_locally(repo_path)
    except Exception as e:
        return {"passed": False, "stdout": "", "stderr": str(e), "return_code": -1,
                "coverage_before": 0.0, "coverage_after": 0.0, "coverage_delta": 0.0}


def run_locally(repo_path: str) -> dict:
    try:
        result = subprocess.run(
            ["python", "-m", "pytest", "tests/", "--cov=.", "--cov-report=term-missing", "--tb=short", "-q"],
            capture_output=True, text=True, cwd=repo_path, timeout=60
        )
        coverage = parse_coverage(result.stdout)
        return {"passed": result.returncode == 0, "stdout": result.stdout, "stderr": result.stderr,
                "return_code": result.returncode, "coverage_before": 0.0,
                "coverage_after": coverage, "coverage_delta": coverage}
    except Exception as e:
        return {"passed": False, "stdout": "", "stderr": str(e), "return_code": -1,
                "coverage_before": 0.0, "coverage_after": 0.0, "coverage_delta": 0.0}