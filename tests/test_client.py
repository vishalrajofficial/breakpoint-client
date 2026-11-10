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

def test_cloud_resilience_fallback_on_unreachable():
    # When cloud endpoint is unreachable, gracefully fall back to deterministic local policy
    guard = BreakpointGuard(
        api_key="bp_test_developer_key",
        config_path="config/breakpoint.yaml"
    )
    # Point to a dummy dead port
    guard.engine.cloud_url = "http://127.0.0.1:59999/v1"

    @guard.protect(tool_name="database.execute_sql")
    def execute_sql(query: str):
        return "SUCCESS"

    # Should still catch and block malicious SQL drop via local engine fallback
    with pytest.raises(BreakpointBlockedException) as exc:
        execute_sql("DROP TABLE logs;")

    assert "DROP" in str(exc.value)

    # Safe SQL continues to work seamlessly
    res = execute_sql("SELECT count(*) FROM users;")
    assert res == "SUCCESS"
