import os
import time
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
import httpx

from .models import ToolCall, EvaluationResult, ActionDecision
from ..rules.security import SecurityRuleChecker
from ..rules.budget import BudgetRuleChecker
from ..rules.rate_limiter import SlidingWindowRateLimiter
from .circuit_breaker import AgentCircuitBreaker

class ClientPolicyEngine:
    """
    Lightweight execution engine for BreakPoint AI client SDK.
    Supports local offline evaluation and remote cloud evaluation via API key.
    """

    def __init__(self, config_path: Optional[str] = None, api_key: Optional[str] = None, cloud_url: str = "https://api.breakpoint.sh/v1"):
        self.api_key = api_key or os.environ.get("BREAKPOINT_API_KEY")
        self.cloud_url = cloud_url.rstrip("/")
        self.config: Dict[str, Any] = {}
        self.budget_checker = BudgetRuleChecker()
        self.rate_limiter = SlidingWindowRateLimiter()
        self.circuit_breaker = AgentCircuitBreaker()
        
        if config_path and Path(config_path).exists():
            with open(config_path, "r", encoding="utf-8") as f:
                self.config = yaml.safe_load(f) or {}

    def _get_tool_policy(self, tool_name: str) -> Optional[Dict[str, Any]]:
        policies = self.config.get("policies", [])
        for p in policies:
            if p.get("tool_name") == tool_name:
                return p
        return None

    def evaluate(self, tool_call: ToolCall) -> EvaluationResult:
        # MODE 2: CLOUD MODE (If api_key is present)
        if self.api_key:
            return self._evaluate_cloud(tool_call)

        # MODE 1: LOCAL DETERMINISTIC MODE
        return self._evaluate_local(tool_call)

    def _evaluate_cloud(self, tool_call: ToolCall) -> EvaluationResult:
        start_time = time.perf_counter()
        try:
            resp = httpx.post(
                f"{self.cloud_url}/evaluate",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json=tool_call.model_dump(),
                timeout=2.0
            )
            data = resp.json()
            latency = (time.perf_counter() - start_time) * 1000.0
            return EvaluationResult(**data)
        except Exception as e:
            # Fallback to local evaluation if cloud network fails
            return self._evaluate_local(tool_call)

    def _evaluate_local(self, tool_call: ToolCall) -> EvaluationResult:
        start_time = time.perf_counter()
        tool_name = tool_call.tool_name
        arguments = tool_call.arguments
        agent_id = tool_call.agent_id

        try:
            can_run, cb_reason = self.circuit_breaker.can_execute(tool_name)
            if not can_run:
                latency = (time.perf_counter() - start_time) * 1000.0
                return EvaluationResult(
                    call_id=tool_call.call_id,
                    tool_name=tool_name,
                    decision=ActionDecision.BLOCK,
                    allowed=False,
                    reason=cb_reason,
                    latency_ms=round(latency, 2),
                    synthetic_error=f"GuardBlock: {cb_reason}"
                )

            policy = self._get_tool_policy(tool_name)
            rules = policy.get("rules", {}) if policy else {}

            if rules.get("hard_block", {}).get("enabled", False):
                reason = rules["hard_block"].get("reason", "This tool is hard-blocked for autonomous agents.")
                self.circuit_breaker.record_failure(tool_name)
                latency = (time.perf_counter() - start_time) * 1000.0
                return EvaluationResult(
                    call_id=tool_call.call_id,
                    tool_name=tool_name,
                    decision=ActionDecision.BLOCK,
                    allowed=False,
                    reason=reason,
                    latency_ms=round(latency, 2),
                    synthetic_error=f"GuardBlock: {reason}"
                )

            is_safe, sec_reason = SecurityRuleChecker.check_arguments(arguments)
            if not is_safe:
                self.circuit_breaker.record_failure(tool_name)
                latency = (time.perf_counter() - start_time) * 1000.0
                return EvaluationResult(
                    call_id=tool_call.call_id,
                    tool_name=tool_name,
                    decision=ActionDecision.BLOCK,
                    allowed=False,
                    reason=sec_reason,
                    latency_ms=round(latency, 2),
                    synthetic_error=f"SecurityPolicyViolation: {sec_reason}"
                )

            budget_config = rules.get("budget_limits", {})
            if budget_config:
                p_name = budget_config.get("param_name", "amount")
                max_p = budget_config.get("max_per_call", 50.0)
                is_b_ok, b_reason = self.budget_checker.check_budget(
                    arguments, param_name=p_name, max_per_call=max_p, session_id=tool_call.session_id
                )
                if not is_b_ok:
                    latency = (time.perf_counter() - start_time) * 1000.0
                    return EvaluationResult(
                        call_id=tool_call.call_id,
                        tool_name=tool_name,
                        decision=ActionDecision.BLOCK,
                        allowed=False,
                        reason=b_reason,
                        latency_ms=round(latency, 2),
                        synthetic_error=f"BudgetViolation: {b_reason}"
                    )

            self.circuit_breaker.record_success(tool_name)
            latency = (time.perf_counter() - start_time) * 1000.0
            return EvaluationResult(
                call_id=tool_call.call_id,
                tool_name=tool_name,
                decision=ActionDecision.ALLOW,
                allowed=True,
                reason="Policy check passed. Execution permitted.",
                latency_ms=round(latency, 2)
            )

        except Exception as e:
            latency = (time.perf_counter() - start_time) * 1000.0
            return EvaluationResult(
                call_id=tool_call.call_id,
                tool_name=tool_name,
                decision=ActionDecision.BLOCK,
                allowed=False,
                reason=f"Security engine fail-closed on internal exception: {str(e)}",
                latency_ms=round(latency, 2),
                synthetic_error="GuardInternalError: Execution halted safely."
            )
