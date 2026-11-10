from typing import Any, Dict, Callable, Optional
from ..core.engine import PolicyEngine
from ..core.models import ToolCall, EvaluationResult

class BreakpointGeminiAdapter:
    """
    Adapter that intercepts Google Gemini function calls before execution.
    Compatible with google.generativeai and Google GenAI SDKs.
    """

    def __init__(self, engine: PolicyEngine, agent_id: str = "gemini-agent"):
        self.engine = engine
        self.agent_id = agent_id

    def intercept_call(self, function_name: str, function_args: Dict[str, Any]) -> EvaluationResult:
        """
        Evaluates a tool call proposed by the Gemini model.
        """
        call = ToolCall(
            agent_id=self.agent_id,
            tool_name=function_name,
            arguments=function_args
        )
        return self.engine.evaluate(call)

    def wrap_tool_execution(self, function_name: str, function_args: Dict[str, Any], tool_fn: Callable) -> Dict[str, Any]:
        """
        Executes the tool function if allowed. If blocked, returns a synthetic error payload
        formatted specifically for Gemini's function response channel.
        """
        eval_result = self.intercept_call(function_name, function_args)

        if not eval_result.allowed:
            # Return synthetic feedback for Gemini to self-correct
            return {
                "status": "BLOCKED",
                "decision": eval_result.decision.value,
                "error": eval_result.synthetic_error or eval_result.reason,
                "detail": "BreakPoint AI Zero-Trust Guard blocked this tool execution."
            }

        # Safe execution
        try:
            result = tool_fn(**function_args)
            return {"status": "SUCCESS", "result": result}
        except Exception as e:
            return {"status": "EXECUTION_ERROR", "error": str(e)}
