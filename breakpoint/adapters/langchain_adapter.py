from typing import Any, Dict, Callable
from ..core.engine import PolicyEngine
from ..core.models import ToolCall, EvaluationResult

class BreakpointLangChainGuard:
    """
    Adapter that integrates BreakPoint AI into LangChain and LangGraph tool execution pipelines.
    """

    def __init__(self, engine: PolicyEngine, agent_id: str = "langchain-agent"):
        self.engine = engine
        self.agent_id = agent_id

    def wrap_tool(self, tool_instance):
        """
        Wraps a LangChain BaseTool instance, intercepting its .run() / ._run() method.
        """
        orig_run = tool_instance._run

        def guarded_run(*args, **kwargs):
            tool_name = getattr(tool_instance, "name", "langchain_tool")
            
            # Combine args and kwargs into argument dict
            arguments = kwargs.copy()
            if args:
                arguments["_args"] = list(args)

            call = ToolCall(
                agent_id=self.agent_id,
                tool_name=tool_name,
                arguments=arguments
            )

            eval_result = self.engine.evaluate(call)
            if not eval_result.allowed:
                return f"[BreakPoint AI Block]: {eval_result.synthetic_error or eval_result.reason}"

            return orig_run(*args, **kwargs)

        tool_instance._run = guarded_run
        return tool_instance
