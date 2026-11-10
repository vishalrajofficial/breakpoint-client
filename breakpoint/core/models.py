from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
import time
import uuid

class ActionDecision(str, Enum):
    ALLOW = "ALLOW"
    BLOCK = "BLOCK"
    REQUIRE_APPROVAL = "REQUIRE_APPROVAL"

class RiskLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

class CircuitState(str, Enum):
    CLOSED = "CLOSED"     # Normal operation, calls allowed
    OPEN = "OPEN"         # Tripped, all calls blocked
    HALF_OPEN = "HALF_OPEN" # Testing if service recovered

class ToolCall(BaseModel):
    call_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    agent_id: str = "default_agent"
    tool_name: str
    arguments: Dict[str, Any] = Field(default_factory=dict)
    timestamp: float = Field(default_factory=time.time)
    session_id: Optional[str] = None

class EvaluationResult(BaseModel):
    call_id: str
    tool_name: str
    decision: ActionDecision
    allowed: bool
    reason: str
    latency_ms: float = 0.0
    synthetic_error: Optional[str] = None
    requires_approval: bool = False
    approval_token: Optional[str] = None

class AuditEvent(BaseModel):
    timestamp: str
    call_id: str
    agent_id: str
    tool_name: str
    arguments: Dict[str, Any]
    decision: ActionDecision
    reason: str
    latency_ms: float
