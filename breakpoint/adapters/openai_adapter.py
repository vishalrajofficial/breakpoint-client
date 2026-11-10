import json
from typing import Any, Dict, List, Callable, Optional
from ..core.engine import PolicyEngine
from ..core.models import ToolCall, EvaluationResult

class BreakpointOpenAIAdapter:
    """
    Adapter that intercepts OpenAI tool_calls payloads before execution.
    Compatible with OpenAI ChatCompletions and Assistants API.
    """

    def __init__(self, engine: PolicyEngine, agent_id: str = "openai-agent"):
        self.engine = engine
        self.agent_id = agent_id

    def intercept_tool_call(self, tool_call_dict: Dict[str, Any]) -> EvaluationResult:
        """
        Parses an OpenAI tool_call item and evaluates it through the policy engine.
        Expected format:
        {
            "id": "call_xyz",
            "type": "function",
            "function": {"name": "...", "arguments": "{\\"param\\": 123}"}
        }
        """
        fn = tool_call_dict.get("function", {})
        tool_name = fn.get("name", "unknown_tool")
        raw_args = fn.get("arguments", "{}")

        if isinstance(raw_args, str):
            try:
                parsed_args = json.loads(raw_args)
            except Exception:
                parsed_args = {"raw_payload": raw_args}
        else:
            parsed_args = raw_args

        call = ToolCall(
            call_id=tool_call_dict.get("id"),
            agent_id=self.agent_id,
            tool_name=tool_name,
            arguments=parsed_args
        )
        return self.engine.evaluate(call)

    def execute_with_guard(self, tool_call_dict: Dict[str, Any], registry: Dict[str, Callable]) -> Dict[str, Any]:
        """
        Safely executes the tool if allowed, or creates an OpenAI tool message error.
        """
        eval_result = self.intercept_tool_call(tool_call_dict)
        call_id = tool_call_dict.get("id", "call_unknown")
        tool_name = tool_call_dict.get("function", {}).get("name")

        if not eval_result.allowed:
            return {
                "role": "tool",
                "tool_call_id": call_id,
                "name": tool_name,
                "content": json.dumps({
                    "error": eval_result.synthetic_error or eval_result.reason,
                    "status": "GUARD_BLOCKED",
                    "latency_ms": eval_result.latency_ms
                })
            }

        fn = registry.get(tool_name)
        if not fn:
            return {
                "role": "tool",
                "tool_call_id": call_id,
                "name": tool_name,
                "content": json.dumps({"error": f"Tool '{tool_name}' not found in registry."})
            }

        raw_args = tool_call_dict.get("function", {}).get("arguments", "{}")
        args = json.loads(raw_args) if isinstance(raw_args, str) else raw_args
        res = fn(**args)
        return {
            "role": "tool",
            "tool_call_id": call_id,
            "name": tool_name,
            "content": json.dumps({"result": res, "status": "SUCCESS"})
        }
