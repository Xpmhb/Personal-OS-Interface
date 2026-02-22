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
