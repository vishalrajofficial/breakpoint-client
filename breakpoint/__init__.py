"""
BreakPoint AI: Zero-Trust Runtime Firewall & Circuit Breaker for Autonomous AI Agents
"""

__version__ = "0.1.0"

from .sdk import BreakpointGuard, BreakpointBlockedException
from .core.engine import ClientPolicyEngine
from .core.models import ToolCall, EvaluationResult, ActionDecision

__all__ = [
    "BreakpointGuard",
    "BreakpointBlockedException",
    "ClientPolicyEngine",
    "ToolCall",
    "EvaluationResult",
    "ActionDecision"
]
