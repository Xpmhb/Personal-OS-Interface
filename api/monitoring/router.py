from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
from pydantic import BaseModel
from typing import Optional

router = APIRouter()


@router.get("/executions")
def list_executions(
    limit: int = 20,
    agent_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """List recent executions"""
    from models import Execution, Agent
    from sqlalchemy import desc
    
    query = db.query(Execution).order_by(desc(Execution.started_at))
    
    if agent_id:
        query = query.filter(Execution.agent_id == agent_id)
    
    executions = query.limit(limit).all()
    
    result = []
    for e in executions:
        agent = db.query(Agent).filter(Agent.id == e.agent_id).first()
        result.append({
            "id": str(e.id),
            "agent_id": str(e.agent_id),
            "agent_name": agent.name if agent else "Unknown",
            "status": e.status,
            "prompt": e.prompt[:100] + "..." if e.prompt and len(e.prompt) > 100 else e.prompt,
            "started_at": e.started_at.isoformat() if e.started_at else None,
            "duration_ms": e.duration_ms,
            "cost_estimate_usd": float(e.cost_estimate_usd) if e.cost_estimate_usd else 0
        })
    
    return result


@router.get("/executions/{execution_id}")
def get_execution(execution_id: str, db: Session = Depends(get_db)):
    """Get execution detail with tool calls"""
    from models import Execution, ToolCall, Artifact, Agent
    
    execution = db.query(Execution).filter(Execution.id == execution_id).first()
    if not execution:
        return {"error": "Execution not found"}
    
    agent = db.query(Agent).filter(Agent.id == execution.agent_id).first()
    tool_calls = db.query(ToolCall).filter(ToolCall.execution_id == execution_id).all()
    artifacts = db.query(Artifact).filter(Artifact.execution_id == execution_id).all()
    
    return {
        "id": str(execution.id),
        "agent_id": str(execution.agent_id),
        "agent_name": agent.name if agent else "Unknown",
        "status": execution.status,
        "prompt": execution.prompt,
        "started_at": execution.started_at.isoformat() if execution.started_at else None,
        "ended_at": execution.ended_at.isoformat() if execution.ended_at else None,
        "duration_ms": execution.duration_ms,
        "tokens_in": execution.tokens_in,
        "tokens_out": execution.tokens_out,
        "cost_estimate_usd": float(execution.cost_estimate_usd) if execution.cost_estimate_usd else 0,
        "error": execution.error,
        "tool_calls": [
            {
                "id": str(tc.id),
                "tool_id": tc.tool_id,
                "input": tc.input,
                "output": tc.output,
                "duration_ms": tc.duration_ms,
                "called_at": tc.called_at.isoformat() if tc.called_at else None
            }
            for tc in tool_calls
        ],
        "artifacts": [
            {
                "id": str(a.id),
                "title": a.title,
                "artifact_type": a.artifact_type,
                "created_at": a.created_at.isoformat() if a.created_at else None
            }
            for a in artifacts
        ]
    }


@router.get("/artifacts/{artifact_id}")
def get_artifact(artifact_id: str, db: Session = Depends(get_db)):
    """Get artifact content"""
    from models import Artifact

    artifact = db.query(Artifact).filter(Artifact.id == artifact_id).first()
    if not artifact:
        return {"error": "Artifact not found"}

    return {
        "id": str(artifact.id),
        "title": artifact.title,
        "content": artifact.content,
        "artifact_type": artifact.artifact_type,
        "created_at": artifact.created_at.isoformat() if artifact.created_at else None
    }


@router.post("/nightly/trigger")
async def trigger_nightly():
    """Manually trigger the nightly loop"""
    from nightly_loop import run_full_nightly_loop
    result = await run_full_nightly_loop()
    return result
