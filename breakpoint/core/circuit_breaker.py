import time
from typing import Dict, Tuple
from ..core.models import CircuitState

class AgentCircuitBreaker:
    """Protects against runaway agent loops by tripping the circuit after consecutive failures."""

    def __init__(self, failure_threshold: int = 3, cooldown_seconds: int = 60):
        self.failure_threshold = failure_threshold
        self.cooldown_seconds = cooldown_seconds
        
        # tool_name -> consecutive failure count
        self._consecutive_failures: Dict[str, int] = {}
        # tool_name -> timestamp when circuit was opened
        self._opened_at: Dict[str, float] = {}

    def get_state(self, tool_name: str) -> CircuitState:
        now = time.time()
        if tool_name in self._opened_at:
            if now - self._opened_at[tool_name] > self.cooldown_seconds:
                return CircuitState.HALF_OPEN
            return CircuitState.OPEN
        return CircuitState.CLOSED

    def can_execute(self, tool_name: str) -> Tuple[bool, str]:
        state = self.get_state(tool_name)
        if state == CircuitState.OPEN:
            remaining = int(self.cooldown_seconds - (time.time() - self._opened_at[tool_name]))
            return False, (
                f"Circuit breaker is OPEN for tool '{tool_name}'. Execution blocked to prevent "
                f"system degradation. Cooldown active for {max(remaining, 1)}s."
            )
        return True, "Circuit closed or half-open"

    def record_failure(self, tool_name: str):
        count = self._consecutive_failures.get(tool_name, 0) + 1
        self._consecutive_failures[tool_name] = count
        if count >= self.failure_threshold:
            self._opened_at[tool_name] = time.time()

    def record_success(self, tool_name: str):
        self._consecutive_failures[tool_name] = 0
        self._opened_at.pop(tool_name, None)
