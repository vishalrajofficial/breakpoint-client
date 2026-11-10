import functools
import inspect
from typing import Callable, Any, Optional

from .core.engine import ClientPolicyEngine
from .core.models import ToolCall, EvaluationResult, ActionDecision

class BreakpointBlockedException(Exception):
    """Raised when an agent's tool execution is blocked by a BreakPoint AI policy."""
    def __init__(self, result: EvaluationResult):
        self.result = result
        super().__init__(result.synthetic_error or result.reason)

class BreakpointGuard:
    """
    The developer-facing SDK client for BreakPoint AI.
    
    Usage:
        # Local Mode (Free forever, offline YAML policies)
        guard = BreakpointGuard(config_path="config/breakpoint.yaml")

        # Cloud Mode (Enterprise audit logs, team controls, Slack approvals)
        guard = BreakpointGuard(api_key="bp_live_...")

        @guard.protect(tool_name="database.execute_sql")
        def execute_sql(query: str):
            ...
    """

    def __init__(self, config_path: Optional[str] = "config/breakpoint.yaml", api_key: Optional[str] = None, agent_id: str = "agent-01"):
        self.engine = ClientPolicyEngine(config_path=config_path, api_key=api_key)
        self.agent_id = agent_id

    def protect(self, tool_name: Optional[str] = None):
        """
        Decorator to protect any Python tool function from malicious or runaway agent execution.
        """
        def decorator(func: Callable) -> Callable:
            actual_tool_name = tool_name or func.__name__

            @functools.wraps(func)
            def wrapper(*args, **kwargs) -> Any:
                sig = inspect.signature(func)
                bound_args = sig.bind_partial(*args, **kwargs)
                bound_args.apply_defaults()
                arguments = bound_args.arguments

                call = ToolCall(
                    agent_id=self.agent_id,
                    tool_name=actual_tool_name,
                    arguments=arguments
                )

                eval_result = self.engine.evaluate(call)

                if not eval_result.allowed:
                    raise BreakpointBlockedException(eval_result)

                return func(*args, **kwargs)

            return wrapper
        return decorator
