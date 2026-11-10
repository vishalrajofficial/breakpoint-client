import time
from typing import Dict, List, Tuple
from collections import defaultdict

class SlidingWindowRateLimiter:
    """Sliding-window rate limiter per (agent_id, tool_name)."""

    def __init__(self):
        # Key: (agent_id, tool_name) -> list of timestamp floats
        self._history: Dict[Tuple[str, str], List[float]] = defaultdict(list)

    def is_allowed(
        self,
        agent_id: str,
        tool_name: str,
        max_calls: int = 10,
        window_seconds: int = 60
    ) -> Tuple[bool, str]:
        """
        Checks whether the rate limit is exceeded for the current window.
        """
        now = time.time()
        key = (agent_id, tool_name)
        window_start = now - window_seconds

        # Clean up timestamps older than window_start
        self._history[key] = [ts for ts in self._history[key] if ts > window_start]

        if len(self._history[key]) >= max_calls:
            earliest_in_window = self._history[key][0]
            retry_after = int(window_seconds - (now - earliest_in_window)) + 1
            return False, (
                f"Rate limit exceeded for tool '{tool_name}': {len(self._history[key])}/{max_calls} "
                f"calls made in the last {window_seconds}s. Retry after {retry_after}s."
            )

        self._history[key].append(now)
        return True, "Rate limit within bounds"

    def reset(self, agent_id: str = None, tool_name: str = None):
        """Resets rate limit counter."""
        if agent_id and tool_name:
            self._history.pop((agent_id, tool_name), None)
        else:
            self._history.clear()
