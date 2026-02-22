"""
Pydantic schemas for Agent spec validation
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class MemoryScope(str, Enum):
    private = "private"
    shared = "shared"
    ephemeral = "ephemeral"


class ToolPermission(BaseModel):
    tool_id: str
    ops: List[str] = ["read"]


class MemoryConfig(BaseModel):
    scope: MemoryScope = MemoryScope.private
    max_tokens: int = 8000
    retention_days: int = 30


class DataPermissions(BaseModel):
    datasets: List[str] = []
    tables: List[str] = []
    vector_namespaces: List[str] = []
    files: List[str] = []


class Triggers(BaseModel):
    manual: bool = True
    schedules: List[str] = []
    events: List[str] = []


class Guardrails(BaseModel):
    budget_usd_per_day: float = 10.0
    max_tool_calls_per_run: int = 50
    approval_required_ops: List[str] = []


class LLMConfig(BaseModel):
    model: str = "anthropic/claude-3.5-sonnet"
    temperature: float = 0.3
    max_tokens: int = 4096


class AgentSpec(BaseModel):
    """Full agent specification - the core contract"""
    version: str = "1.0"
    name: str = Field(..., min_length=1, max_length=100)
    display_name: Optional[str] = None
    role_definition: str = Field(..., min_length=10)
    capabilities: List[str] = []
    tools_allowed: List[ToolPermission] = []
    memory: MemoryConfig = MemoryConfig()
    data_permissions: DataPermissions = DataPermissions()
    triggers: Triggers = Triggers()
    guardrails: Guardrails = Guardrails()
    llm: LLMConfig = LLMConfig()


class AgentCreate(BaseModel):
    """Create agent from spec"""
    spec: AgentSpec


class AgentUpdate(BaseModel):
    """Update agent - all fields optional"""
    display_name: Optional[str] = None
    spec: Optional[AgentSpec] = None
    status: Optional[str] = None


class AgentRunRequest(BaseModel):
    """Run an agent with a prompt"""
    prompt: str = Field(..., min_length=1)
    context: Optional[Dict[str, Any]] = None


class AgentResponse(BaseModel):
    """Agent response from API"""
    id: str
    name: str
    display_name: Optional[str]
    spec: dict
    status: str
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    class Config:
        from_attributes = True


class ExecutionResponse(BaseModel):
    """Execution response"""
    execution_id: str
    agent_id: str
    agent_name: str
    status: str
    prompt: Optional[str] = None
    artifact_id: Optional[str] = None
    duration_ms: Optional[int] = None
    tokens_in: Optional[int] = None
    tokens_out: Optional[int] = None
    cost_estimate_usd: Optional[float] = None


class FactoryStartRequest(BaseModel):
    """Start agent creation from natural language"""
    description: str = Field(..., min_length=5)


class FactoryClarifyResponse(BaseModel):
    """Clarifying questions from factory"""
    session_id: str
    questions: List[str]
    partial_spec: Optional[dict] = None


class FactoryClarifyRequest(BaseModel):
    """Answer clarifying questions"""
    session_id: str
    answers: Dict[str, str]
