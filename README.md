# BreakPoint AI 🛡️
> **Zero-Trust Runtime Execution Firewall & Circuit Breaker for Autonomous AI Agents**

[![PyPI version](https://img.shields.io/badge/pypi-v0.1.0-blue.svg)](https://pypi.org)
[![License](https://img.shields.io/badge/License-Apache_2.0-green.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.10+-cyan.svg)](https://python.org)

`BreakPoint AI` is a sub-millisecond runtime execution guard for AI agents. It intercepts function calls, tool invocations, and database queries **before** they reach external APIs—preventing catastrophic SQL injections, runaway financial loops, and unauthorized cloud mutations.

---

## ⚡ Quickstart (2 Lines of Code)

```bash
pip install breakpoint-ai
```

### Protect any Python function from untrusted agent execution:
```python
from breakpoint import BreakpointGuard

guard = BreakpointGuard(config_path="config/breakpoint.yaml")

@guard.protect(tool_name="database.execute_sql")
def execute_sql(query: str):
    return db.execute(query)

# If an agent attempts: execute_sql("DROP TABLE users; --")
# --> BreakpointBlockedException: SecurityPolicyViolation: Destructive SQL DROP statement detected (0.12ms)
```

---

## 🔌 Framework Support

### 1. Google Gemini Function Calling
```python
from breakpoint.adapters.gemini_adapter import BreakpointGeminiAdapter

adapter = BreakpointGeminiAdapter(engine=guard.engine)
# Intercepts Gemini function calls and returns synthetic self-correction feedback
result = adapter.wrap_tool_execution(fn_name, fn_args, real_tool_fn)
```

### 2. OpenAI Function Calling & Assistants
```python
from breakpoint.adapters.openai_adapter import BreakpointOpenAIAdapter

adapter = BreakpointOpenAIAdapter(engine=guard.engine)
tool_message = adapter.execute_with_guard(openai_tool_call, tool_registry)
```

### 3. LangChain & LangGraph
```python
from breakpoint.adapters.langchain_adapter import BreakpointLangChainGuard

guard = BreakpointLangChainGuard(engine=guard.engine)
guarded_tool = guard.wrap_tool(my_langchain_tool)
```

---

## 🔒 Two Modes: Free Local or Cloud Managed

```python
# Mode 1: 100% Free Local Mode (No account required, offline YAML policies)
guard = BreakpointGuard(config_path="config/breakpoint.yaml")

# Mode 2: Cloud Managed Mode (Enterprise audit logs, team dashboard, Slack approval bot)
guard = BreakpointGuard(api_key="bp_live_...")
```

---

## 📄 License
Apache 2.0 &bull; Built by [Vishal Raj](https://github.com/vishalrajofficial)
