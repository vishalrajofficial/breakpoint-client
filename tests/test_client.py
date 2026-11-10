import pytest
from breakpoint.sdk import BreakpointGuard, BreakpointBlockedException

def test_guard_intercepts_sql_drop():
    guard = BreakpointGuard(config_path="config/breakpoint.yaml")

    @guard.protect(tool_name="database.execute_sql")
    def execute_sql(query: str):
        return "Executed"

    with pytest.raises(BreakpointBlockedException) as exc:
        execute_sql("DROP TABLE users;")
    
    assert "DROP" in str(exc.value)

def test_guard_allows_safe_sql():
    guard = BreakpointGuard(config_path="config/breakpoint.yaml")

    @guard.protect(tool_name="database.execute_sql")
    def execute_sql(query: str):
        return "SUCCESS"

    res = execute_sql("SELECT count(*) FROM orders WHERE active = true")
    assert res == "SUCCESS"

def test_guard_intercepts_over_budget():
    guard = BreakpointGuard(config_path="config/breakpoint.yaml")

    @guard.protect(tool_name="payment.refund")
    def process_refund(amount: float):
        return "Refunded"

    with pytest.raises(BreakpointBlockedException) as exc:
        process_refund(amount=5000.0)

    assert "limit" in str(exc.value) or "Budget" in str(exc.value)
