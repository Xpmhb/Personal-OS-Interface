from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from agents.schemas import (
    AgentCreate, AgentUpdate, AgentRunRequest, AgentResponse,
    FactoryStartRequest, FactoryClarifyRequest, FactoryClarifyResponse
)
from typing import List
import uuid
from datetime import datetime

router = APIRouter()


@router.get("", response_model=List[AgentResponse])
def list_agents(status: str = None, db: Session = Depends(get_db)):
    """List all agents, optionally filter by status"""
    from models import Agent
    query = db.query(Agent)
    if status:
        query = query.filter(Agent.status == status)
    agents = query.order_by(Agent.created_at.desc()).all()
    return [
        AgentResponse(
            id=str(a.id),
            name=a.name,
            display_name=a.display_name,
            spec=a.spec,
            status=a.status,
            created_at=a.created_at.isoformat() if a.created_at else None,
            updated_at=a.updated_at.isoformat() if a.updated_at else None,
        )
        for a in agents
    ]


@router.post("", response_model=AgentResponse, status_code=201)
def create_agent(request: AgentCreate, db: Session = Depends(get_db)):
    """Register a new agent from validated spec"""
    from models import Agent

    # Check for duplicate name
    existing = db.query(Agent).filter(Agent.name == request.spec.name).first()
    if existing:
        raise HTTPException(status_code=409, detail=f"Agent '{request.spec.name}' already exists")

    agent_id = uuid.uuid4()
    spec_dict = request.spec.model_dump()

    db_agent = Agent(
        id=agent_id,
        name=request.spec.name,
        display_name=request.spec.display_name or request.spec.name,
        spec=spec_dict,
        status="active"
    )
    db.add(db_agent)
    db.commit()
    db.refresh(db_agent)

    return AgentResponse(
        id=str(db_agent.id),
        name=db_agent.name,
        display_name=db_agent.display_name,
        spec=db_agent.spec,
        status=db_agent.status,
        created_at=db_agent.created_at.isoformat() if db_agent.created_at else None,
        updated_at=db_agent.updated_at.isoformat() if db_agent.updated_at else None,
    )


@router.get("/{agent_id}", response_model=AgentResponse)
def get_agent(agent_id: str, db: Session = Depends(get_db)):
    """Get agent by ID"""
    from models import Agent
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    return AgentResponse(
        id=str(agent.id),
        name=agent.name,
        display_name=agent.display_name,
        spec=agent.spec,
        status=agent.status,
        created_at=agent.created_at.isoformat() if agent.created_at else None,
        updated_at=agent.updated_at.isoformat() if agent.updated_at else None,
    )


@router.patch("/{agent_id}", response_model=AgentResponse)
def update_agent(agent_id: str, update: AgentUpdate, db: Session = Depends(get_db)):
    """Update agent spec or metadata"""
    from models import Agent
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    if update.display_name is not None:
        agent.display_name = update.display_name
    if update.spec is not None:
        agent.spec = update.spec.model_dump()
    if update.status is not None:
        if update.status not in ["active", "inactive", "deployed"]:
            raise HTTPException(status_code=400, detail="Invalid status")
        agent.status = update.status

    agent.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(agent)

    return AgentResponse(
        id=str(agent.id),
        name=agent.name,
        display_name=agent.display_name,
        spec=agent.spec,
        status=agent.status,
        created_at=agent.created_at.isoformat() if agent.created_at else None,
        updated_at=agent.updated_at.isoformat() if agent.updated_at else None,
    )


@router.delete("/{agent_id}")
def deactivate_agent(agent_id: str, db: Session = Depends(get_db)):
    """Deactivate an agent (soft delete)"""
    from models import Agent
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    agent.status = "inactive"
    agent.updated_at = datetime.utcnow()
    db.commit()
    return {"status": "deactivated", "agent_id": str(agent_id)}


@router.post("/{agent_id}/run")
async def run_agent(agent_id: str, request: AgentRunRequest, db: Session = Depends(get_db)):
    """Execute an agent with a prompt — dispatches to runtime engine"""
    from models import Agent
    from runtime.engine import execute_agent

    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    if agent.status == "inactive":
        raise HTTPException(status_code=400, detail="Agent is inactive")

    # Execute via runtime engine
    result = await execute_agent(
        db=db,
        agent_id=agent_id,
        prompt=request.prompt,
        context=request.context
    )

    return result


@router.post("/{agent_id}/deploy")
def deploy_agent(agent_id: str, db: Session = Depends(get_db)):
    """Enable scheduled triggers for agent"""
    from models import Agent

    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    agent.status = "deployed"
    agent.updated_at = datetime.utcnow()
    db.commit()

    return {
        "status": "deployed",
        "agent_id": str(agent_id),
        "triggers": agent.spec.get("triggers", {})
    }
