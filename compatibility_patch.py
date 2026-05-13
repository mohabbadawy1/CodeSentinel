# compatibility_patch.py

from pydantic import ConfigDict
from crewai import Agent

# Monkey-patch CrewAI Agent model config
try:
    Agent.model_config = ConfigDict(
        arbitrary_types_allowed=True,
        extra="allow"
    )
except Exception as e:
    print("Patch warning:", e)
