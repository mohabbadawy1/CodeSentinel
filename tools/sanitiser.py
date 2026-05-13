import re

# Patterns that could be used for prompt injection inside repo files
INJECTION_PATTERNS = [
    r"ignore\s+(all\s+)?(previous|above|prior)\s+instructions",
    r"you are now",
    r"forget\s+(your|all)",
    r"system\s*prompt",
    r"jailbreak",
    r"disregard\s+(all\s+)?instructions",
    r"act\s+as\s+",
    r"new\s+instructions\s*:",
    r"override\s+(previous\s+)?instructions",
]

MAX_CONTENT_LENGTH = 8000


def sanitise(content: str) -> str:
    """
    Sanitise repository content before it enters any LLM context window.
    Removes potential prompt injection patterns and truncates long content.
    """
    for pattern in INJECTION_PATTERNS:
        content = re.sub(pattern, "[REDACTED]", content, flags=re.IGNORECASE)

    if len(content) > MAX_CONTENT_LENGTH:
        content = content[:MAX_CONTENT_LENGTH] + "\n... [truncated by CodeSentinel sanitiser]"

    return content


def sanitise_findings(findings: str) -> str:
    """Sanitise a findings report string."""
    return sanitise(findings)
