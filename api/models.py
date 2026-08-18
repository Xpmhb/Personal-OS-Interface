"""
Database models — SQLite compatible for testing
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, Integer, BigInteger, Float, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from database import Base


def generate_uuid():
    return str(uuid.uuid4())


class Agent(Base):
    __tablename__ = "agents"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(100), unique=True, nullable=False)
    display_name = Column(String(200))
    spec = Column(JSON, nullable=False)
    status = Column(String(20), default="active")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    executions = relationship("Execution", back_populates="agent")
    memories = relationship("Memory", back_populates="agent")
    permissions = relationship("AgentPermission", back_populates="agent")


class File(Base):
    __tablename__ = "files"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    filename = Column(String(500), nullable=False)
    content_type = Column(String(100))
    size_bytes = Column(BigInteger)
    hash = Column(String(64))
    storage_path = Column(String(1000))
    namespace = Column(String(100), default="default")
    status = Column(String(20), default="pending")
    uploaded_at = Column(DateTime, default=datetime.utcnow)

    chunks = relationship("FileChunk", back_populates="file")


class FileChunk(Base):
    __tablename__ = "file_chunks"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    file_id = Column(String(36), ForeignKey("files.id", ondelete="CASCADE"))
    chunk_index = Column(Integer, nullable=False)
    chunk_text = Column(Text, nullable=False)
    token_count = Column(Integer)
    embedding_id = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)

    file = relationship("File", back_populates="chunks")


class AgentPermission(Base):
    __tablename__ = "agent_permissions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    agent_id = Column(String(36), ForeignKey("agents.id", ondelete="CASCADE"))
    resource_type = Column(String(50), nullable=False)
    resource_id = Column(String(200), nullable=False)
    permission = Column(String(20), default="read")
    granted_at = Column(DateTime, default=datetime.utcnow)

    agent = relationship("Agent", back_populates="permissions")


class Execution(Base):
    __tablename__ = "executions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    agent_id = Column(String(36), ForeignKey("agents.id"))
    status = Column(String(20), default="running")
    prompt = Column(Text)
    started_at = Column(DateTime, default=datetime.utcnow)
    ended_at = Column(DateTime)
    duration_ms = Column(Integer)
    tokens_in = Column(Integer)
    tokens_out = Column(Integer)
    cost_estimate_usd = Column(Float)
    error = Column(Text)

    agent = relationship("Agent", back_populates="executions")
    tool_calls = relationship("ToolCall", back_populates="execution")
    artifacts = relationship("Artifact", back_populates="execution")


class ToolCall(Base):
    __tablename__ = "tool_calls"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    execution_id = Column(String(36), ForeignKey("executions.id", ondelete="CASCADE"))
    tool_id = Column(String(50), nullable=False)
    input = Column(JSON)
    output = Column(JSON)
    duration_ms = Column(Integer)
    called_at = Column(DateTime, default=datetime.utcnow)

    execution = relationship("Execution", back_populates="tool_calls")


class Artifact(Base):
    __tablename__ = "artifacts"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    execution_id = Column(String(36), ForeignKey("executions.id", ondelete="CASCADE"))
    title = Column(String(500))
    content = Column(Text, nullable=False)
    artifact_type = Column(String(50), default="markdown")
    created_at = Column(DateTime, default=datetime.utcnow)

    execution = relationship("Execution", back_populates="artifacts")


class Memory(Base):
    __tablename__ = "memories"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    agent_id = Column(String(36), ForeignKey("agents.id", ondelete="CASCADE"))
    content = Column(Text, nullable=False)
    memory_type = Column(String(20), default="fact")
    token_count = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)

    agent = relationship("Agent", back_populates="memories")


class AccessLog(Base):
    __tablename__ = "access_log"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    agent_id = Column(String(36))
    resource_type = Column(String(50))
    resource_id = Column(String(200))
    action = Column(String(20))
    decision = Column(String(10))
    logged_at = Column(DateTime, default=datetime.utcnow)


class WorkObject(Base):
    """A durable, source-grounded delegation that can span research, planning, approval, and execution."""
    __tablename__ = "work_objects"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    title = Column(String(300), nullable=False)
    objective = Column(Text, nullable=False)
    completion_test = Column(Text)
    status = Column(String(40), default="queued", nullable=False)
    authority_lane = Column(String(40), default="draft_only", nullable=False)
    source_scope = Column(JSON, default=list)
    source_task_url = Column(String(1000))
    owner_name = Column(String(200), default="You")
    priority = Column(String(20), default="medium")
    due_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class EvidenceItem(Base):
    """A cited fact, meeting signal, or source excerpt associated with a work object."""
    __tablename__ = "evidence_items"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    work_object_id = Column(String(36), ForeignKey("work_objects.id", ondelete="CASCADE"), nullable=False, index=True)
    source_type = Column(String(50), nullable=False)
    source_title = Column(String(500), nullable=False)
    source_url = Column(String(1000))
    excerpt = Column(Text, nullable=False)
    confidence = Column(Float, default=0.8)
    is_inference = Column(Integer, default=0)
    captured_at = Column(DateTime, default=datetime.utcnow)


class DecisionRecord(Base):
    """Separates a recommendation and its assumptions from the cited evidence behind it."""
    __tablename__ = "decision_records"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    work_object_id = Column(String(36), ForeignKey("work_objects.id", ondelete="CASCADE"), nullable=False, index=True)
    recommendation = Column(Text, nullable=False)
    rationale = Column(Text)
    confidence = Column(Float, default=0.7)
    status = Column(String(30), default="proposed")
    created_at = Column(DateTime, default=datetime.utcnow)
    accepted_at = Column(DateTime)


class PlanStep(Base):
    """An editable execution step in a work object's plan."""
    __tablename__ = "plan_steps"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    work_object_id = Column(String(36), ForeignKey("work_objects.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(500), nullable=False)
    description = Column(Text)
    owner_name = Column(String(200), default="XPM Jarvis")
    due_at = Column(DateTime)
    status = Column(String(30), default="proposed")
    risk_class = Column(String(30), default="read")
    position = Column(Integer, default=0)
    depends_on = Column(JSON, default=list)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ApprovalRequest(Base):
    """An action-specific approval with an expiry and idempotency key."""
    __tablename__ = "approval_requests"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    work_object_id = Column(String(36), ForeignKey("work_objects.id", ondelete="CASCADE"), nullable=False, index=True)
    action_type = Column(String(100), nullable=False)
    target_system = Column(String(100), nullable=False)
    action_summary = Column(Text, nullable=False)
    impact_summary = Column(Text)
    risk_class = Column(String(30), default="reversible_write")
    status = Column(String(30), default="pending", nullable=False)
    idempotency_key = Column(String(100), unique=True, default=generate_uuid)
    requested_by = Column(String(200), default="XPM Jarvis")
    resolved_by = Column(String(200))
    requested_at = Column(DateTime, default=datetime.utcnow)
    resolved_at = Column(DateTime)
    expires_at = Column(DateTime)


class ActionReceipt(Base):
    """An immutable result for a policy-checked external action."""
    __tablename__ = "action_receipts"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    work_object_id = Column(String(36), ForeignKey("work_objects.id", ondelete="CASCADE"), nullable=False, index=True)
    approval_id = Column(String(36), ForeignKey("approval_requests.id"))
    target_system = Column(String(100), nullable=False)
    operation = Column(String(200), nullable=False)
    external_id = Column(String(300))
    external_url = Column(String(1000))
    summary = Column(Text, nullable=False)
    compensation_hint = Column(Text)
    status = Column(String(30), default="completed")
    created_at = Column(DateTime, default=datetime.utcnow)


class WorkEvent(Base):
    """Append-only run timeline event for the command-center activity stream."""
    __tablename__ = "work_events"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    work_object_id = Column(String(36), ForeignKey("work_objects.id", ondelete="CASCADE"), nullable=False, index=True)
    event_type = Column(String(80), nullable=False)
    message = Column(Text, nullable=False)
    payload = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)


class WebhookDelivery(Base):
    """Idempotency ledger for inbound connector events such as ClickUp webhooks."""
    __tablename__ = "webhook_deliveries"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    provider = Column(String(80), nullable=False)
    delivery_key = Column(String(500), nullable=False, unique=True, index=True)
    event_type = Column(String(120), nullable=False)
    external_task_id = Column(String(300))
    external_comment_id = Column(String(300))
    work_object_id = Column(String(36), ForeignKey("work_objects.id"))
    received_at = Column(DateTime, default=datetime.utcnow)
    payload = Column(JSON, default=dict)
