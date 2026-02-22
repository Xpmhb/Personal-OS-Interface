"""
UI routes — server-rendered Jinja2 templates
"""
from fastapi import APIRouter, Request, Depends, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from datetime import datetime, timedelta
from database import get_db
from config import get_settings

router = APIRouter()
templates = Jinja2Templates(directory="templates")


def check_auth(request: Request) -> bool:
    """Check if user is authenticated"""
    return request.cookies.get("session") == "authenticated"


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@router.post("/login")
async def login_submit(request: Request, password: str = Form(...)):
    settings = get_settings()
    if password == settings.admin_password:
        response = RedirectResponse(url="/", status_code=303)
        response.set_cookie("session", "authenticated", httponly=True, max_age=86400)
        return response
    return templates.TemplateResponse("login.html", {"request": request, "error": "Invalid password"})


@router.get("/logout")
async def logout():
    response = RedirectResponse(url="/login", status_code=303)
    response.delete_cookie("session")
    return response


@router.get("/", response_class=HTMLResponse)
async def dashboard(request: Request, db: Session = Depends(get_db)):
    if not check_auth(request):
        return RedirectResponse(url="/login", status_code=303)

    from models import Agent, Execution, Artifact, File as FileModel

    # Get agents
    agents = db.query(Agent).filter(Agent.status != "inactive").all()
    executives = [a for a in agents if a.name in ["ceo-agent", "cto-agent", "cfo-agent", "coo-agent"]]

    # Format executives for template
    exec_data = []
    for a in executives:
        last_exec = db.query(Execution).filter(
            Execution.agent_id == a.id
        ).order_by(desc(Execution.started_at)).first()

        exec_data.append({
            "id": str(a.id),
            "name": a.name,
            "display_name": a.display_name,
            "status": a.status,
            "spec": a.spec,
            "last_run": last_exec.started_at.strftime("%Y-%m-%d %H:%M") if last_exec else None
        })

    # Stats
    today = datetime.utcnow().replace(hour=0, minute=0, second=0)
    runs_today = db.query(Execution).filter(Execution.started_at >= today).count()
    cost_today = db.query(func.coalesce(func.sum(Execution.cost_estimate_usd), 0)).filter(
        Execution.started_at >= today
    ).scalar() or 0
    files_indexed = db.query(FileModel).filter(FileModel.status == "indexed").count()

    stats = {
        "total_agents": len(agents),
        "runs_today": runs_today,
        "cost_today": float(cost_today),
        "files_indexed": files_indexed
    }

    # Morning brief (latest CEO artifact)
    morning_brief = db.query(Artifact).join(Execution).join(Agent).filter(
        Agent.name == "ceo-agent",
        Artifact.title.like("%Morning Brief%")
    ).order_by(desc(Artifact.created_at)).first()

    brief_data = None
    if morning_brief:
        brief_data = {
            "content": morning_brief.content,
            "created_at": morning_brief.created_at.strftime("%Y-%m-%d %H:%M")
        }

    # Recent executions
    recent = db.query(Execution).order_by(desc(Execution.started_at)).limit(10).all()
    recent_data = []
    for e in recent:
        agent = db.query(Agent).filter(Agent.id == e.agent_id).first()
        recent_data.append({
            "agent_name": agent.name if agent else "Unknown",
            "status": e.status,
            "duration_ms": e.duration_ms,
            "cost_estimate_usd": float(e.cost_estimate_usd) if e.cost_estimate_usd else 0,
            "started_at": e.started_at.strftime("%H:%M:%S") if e.started_at else ""
        })

    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "active": "dashboard",
        "executives": exec_data,
        "stats": stats,
        "morning_brief": brief_data,
        "recent_executions": recent_data
    })


@router.get("/executive", response_class=HTMLResponse)
async def executive_page(request: Request, db: Session = Depends(get_db)):
    if not check_auth(request):
        return RedirectResponse(url="/login", status_code=303)

    from models import Agent, Execution, Artifact

    agents = db.query(Agent).filter(
        Agent.name.in_(["ceo-agent", "cto-agent", "cfo-agent", "coo-agent"])
    ).all()

    agent_data = []
    for a in agents:
        last_artifact = db.query(Artifact).join(Execution).filter(
            Execution.agent_id == a.id
        ).order_by(desc(Artifact.created_at)).first()

        artifact_data = None
        if last_artifact:
            artifact_data = {
                "content": last_artifact.content[:500],
                "created_at": last_artifact.created_at.strftime("%Y-%m-%d %H:%M")
            }

        agent_data.append({
            "id": str(a.id),
            "name": a.name,
            "display_name": a.display_name,
            "status": a.status,
            "spec": a.spec,
            "last_artifact": artifact_data
        })

    return templates.TemplateResponse("executive.html", {
        "request": request,
        "active": "executive",
        "agents": agent_data
    })


@router.get("/registry", response_class=HTMLResponse)
async def registry_page(request: Request, db: Session = Depends(get_db)):
    if not check_auth(request):
        return RedirectResponse(url="/login", status_code=303)

    from models import Agent

    agents = db.query(Agent).order_by(desc(Agent.created_at)).all()
    agent_data = [
        {
            "id": str(a.id),
            "name": a.name,
            "display_name": a.display_name,
            "status": a.status,
            "spec": a.spec
        }
        for a in agents
    ]

    return templates.TemplateResponse("registry.html", {
        "request": request,
        "active": "registry",
        "agents": agent_data
    })


@router.get("/activity", response_class=HTMLResponse)
async def activity_page(request: Request, db: Session = Depends(get_db)):
    if not check_auth(request):
        return RedirectResponse(url="/login", status_code=303)

    from models import Agent, Execution

    agents = db.query(Agent).all()
    executions = db.query(Execution).order_by(desc(Execution.started_at)).limit(50).all()

    exec_data = []
    for e in executions:
        agent = db.query(Agent).filter(Agent.id == e.agent_id).first()
        exec_data.append({
            "id": str(e.id),
            "agent_name": agent.display_name if agent else "Unknown",
            "status": e.status,
            "prompt": e.prompt or "",
            "duration_ms": e.duration_ms,
            "cost_estimate_usd": float(e.cost_estimate_usd) if e.cost_estimate_usd else 0,
            "started_at": e.started_at.strftime("%Y-%m-%d %H:%M:%S") if e.started_at else ""
        })

    return templates.TemplateResponse("activity.html", {
        "request": request,
        "active": "activity",
        "agents": [{"id": str(a.id), "display_name": a.display_name} for a in agents],
        "executions": exec_data
    })


@router.get("/execution/{execution_id}", response_class=HTMLResponse)
async def execution_detail(request: Request, execution_id: str, db: Session = Depends(get_db)):
    if not check_auth(request):
        return RedirectResponse(url="/login", status_code=303)

    from models import Execution, ToolCall, Artifact, Agent

    execution = db.query(Execution).filter(Execution.id == execution_id).first()
    if not execution:
        return HTMLResponse("<h1>Execution not found</h1>", status_code=404)

    agent = db.query(Agent).filter(Agent.id == execution.agent_id).first()
    tool_calls = db.query(ToolCall).filter(ToolCall.execution_id == execution_id).order_by(ToolCall.called_at).all()
    artifacts = db.query(Artifact).filter(Artifact.execution_id == execution_id).all()

    exec_data = {
        "id": str(execution.id),
        "agent_name": agent.display_name if agent else "Unknown",
        "status": execution.status,
        "prompt": execution.prompt,
        "started_at": execution.started_at.strftime("%Y-%m-%d %H:%M:%S") if execution.started_at else "",
        "ended_at": execution.ended_at.strftime("%Y-%m-%d %H:%M:%S") if execution.ended_at else "",
        "duration_ms": execution.duration_ms,
        "tokens_in": execution.tokens_in,
        "tokens_out": execution.tokens_out,
        "cost_estimate_usd": float(execution.cost_estimate_usd) if execution.cost_estimate_usd else 0,
        "error": execution.error,
        "tool_calls": [
            {
                "tool_id": tc.tool_id,
                "input": tc.input,
                "output": tc.output,
                "duration_ms": tc.duration_ms,
                "called_at": tc.called_at.strftime("%H:%M:%S") if tc.called_at else ""
            }
            for tc in tool_calls
        ],
        "artifacts": [
            {
                "title": a.title,
                "content": a.content,
                "artifact_type": a.artifact_type,
                "created_at": a.created_at.strftime("%Y-%m-%d %H:%M") if a.created_at else ""
            }
            for a in artifacts
        ]
    }

    return templates.TemplateResponse("execution.html", {
        "request": request,
        "active": "activity",
        "execution": exec_data
    })
