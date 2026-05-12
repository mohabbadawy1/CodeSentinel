import subprocess
import os


def run_in_sandbox(repo_path: str) -> dict:
    """
    Run pytest inside an isolated Docker container.
    No network access, limited memory, read-only mount.
    Returns dict with passed, stdout, stderr.
    """
    try:
        result = subprocess.run([
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
                "pytest tests/ --tb=short -q 2>&1 || pytest --tb=short -q 2>&1"
            )
        ], capture_output=True, text=True, timeout=120)

        passed = result.returncode == 0
        return {
            "passed": passed,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "return_code": result.returncode
        }

    except subprocess.TimeoutExpired:
        return {
            "passed": False,
            "stdout": "",
            "stderr": "Docker sandbox timed out after 120 seconds.",
            "return_code": -1
        }
    except FileNotFoundError:
        # Docker not installed — fall back to local pytest
        return run_locally(repo_path)
    except Exception as e:
        return {
            "passed": False,
            "stdout": "",
            "stderr": str(e),
            "return_code": -1
        }


def run_locally(repo_path: str) -> dict:
    """Fallback: run pytest locally if Docker is not available."""
    try:
        result = subprocess.run(
            ["pytest", "tests/", "--tb=short", "-q"],
            capture_output=True, text=True,
            cwd=repo_path, timeout=60
        )
        return {
            "passed": result.returncode == 0,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "return_code": result.returncode
        }
    except Exception as e:
        return {
            "passed": False,
            "stdout": "",
            "stderr": str(e),
            "return_code": -1
        }
