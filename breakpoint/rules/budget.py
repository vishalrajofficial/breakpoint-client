from typing import Dict, Any, Tuple

class BudgetRuleChecker:
    """Enforces financial transaction limits and parameter bounds."""

    def __init__(self):
        # session_id -> accumulated spend
        self._session_spend: Dict[str, float] = {}

    def check_budget(
        self,
        arguments: Dict[str, Any],
        param_name: str = "amount",
        max_per_call: float = 50.0,
        session_id: str = None,
        max_session_budget: float = 500.0
    ) -> Tuple[bool, str]:
        """
        Validates that a financial parameter does not exceed the allowed threshold.
        """
        if param_name not in arguments:
            return True, "Budget parameter not present in arguments"

        try:
            raw_val = arguments[param_name]
            val = float(raw_val)
        except (ValueError, TypeError):
            return False, f"Invalid numeric value for budget parameter '{param_name}': {arguments.get(param_name)}"

        if val < 0:
            return False, f"Negative value not allowed for '{param_name}': {val}"

        if val > max_per_call:
            return False, (
                f"Financial limit exceeded: '{param_name}' is ${val:.2f}, "
                f"which exceeds the maximum allowed limit of ${max_per_call:.2f} per call."
            )

        if session_id:
            current_total = self._session_spend.get(session_id, 0.0)
            if current_total + val > max_session_budget:
                return False, (
                    f"Session budget exhausted: current spend ${current_total:.2f} + new ${val:.2f} "
                    f"exceeds session cap of ${max_session_budget:.2f}."
                )
            self._session_spend[session_id] = current_total + val

        return True, f"Budget check passed for {param_name} (${val:.2f})"
