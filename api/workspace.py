"""XPM Jarvis operational intelligence control-plane API.

The product control plane lives here: a durable work object records the user's
objective, supporting evidence, plan, approvals, and action receipts. XPM Jarvis
and external connectors can propose work, but this layer remains authoritative
for policy-visible state and operator-facing history.
"""
from __future__ import annotations

import os
from datetime import datetime, timedelta
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from database import SessionLocal, get_db
from models import (
    ActionReceipt,
    ApprovalRequest,
    DecisionRecord,
    EvidenceItem,
    PlanStep,
    WorkEvent,
    WorkObject,
)

router = APIRouter()


class WorkObjectCreate(BaseModel):
    title: str = Field(min_length=3, max_length=300)
    objective: str = Field(min_length=3)
    completion_test: Optional[str] = None
    authority_lane: str = "draft_only"
    source_scope: list[str] = Field(default_factory=lambda: ["clickup", "otter", "cognee"])
    source_task_url: Optional[str] = None
    owner_name: str = "You"
    priority: str = "medium"


class PlanStepCreate(BaseModel):
    title: str
    description: Optional[str] = None
    owner_name: str = "XPM Jarvis"
    risk_class: str = "read"
    position: int = 0
    depends_on: list[str] = Field(default_factory=list)


class EvidenceCreate(BaseModel):
    source_type: str
    source_title: str
    excerpt: str
    source_url: Optional[str] = None
    confidence: float = Field(default=0.8, ge=0, le=1)
    is_inference: bool = False


class ApprovalCreate(BaseModel):
    action_type: str
    target_system: str
    action_summary: str
    impact_summary: Optional[str] = None
    risk_class: str = "reversible_write"
    expires_in_minutes: int = Field(default=15, ge=1, le=1440)


class ApprovalResolution(BaseModel):
    approved: bool
    resolved_by: str = "You"
    note: Optional[str] = None


class EventCreate(BaseModel):
    event_type: str
    message: str
    payload: dict[str, Any] = Field(default_factory=dict)


class ReceiptCreate(BaseModel):
    target_system: str
    operation: str
    summary: str
    approval_id: Optional[str] = None
    external_id: Optional[str] = None
    external_url: Optional[str] = None
    compensation_hint: Optional[str] = None
    status: str = "completed"


def iso(value: Optional[datetime]) -> Optional[str]:
    return value.isoformat() if value else None


def serialize_evidence(item: EvidenceItem) -> dict[str, Any]:
    return {
        "id": item.id,
        "source_type": item.source_type,
        "source_title": item.source_title,
        "source_url": item.source_url,
        "excerpt": item.excerpt,
        "confidence": item.confidence,
        "is_inference": bool(item.is_inference),
        "captured_at": iso(item.captured_at),
    }


def serialize_plan_step(step: PlanStep) -> dict[str, Any]:
    return {
        "id": step.id,
        "title": step.title,
        "description": step.description,
        "owner_name": step.owner_name,
        "status": step.status,
        "risk_class": step.risk_class,
        "position": step.position,
        "depends_on": step.depends_on or [],
        "due_at": iso(step.due_at),
    }


def serialize_approval(approval: ApprovalRequest) -> dict[str, Any]:
    return {
        "id": approval.id,
        "action_type": approval.action_type,
        "target_system": approval.target_system,
        "action_summary": approval.action_summary,
        "impact_summary": approval.impact_summary,
        "risk_class": approval.risk_class,
        "status": approval.status,
        "requested_by": approval.requested_by,
        "resolved_by": approval.resolved_by,
        "requested_at": iso(approval.requested_at),
        "resolved_at": iso(approval.resolved_at),
        "expires_at": iso(approval.expires_at),
    }


def serialize_receipt(receipt: ActionReceipt) -> dict[str, Any]:
    return {
        "id": receipt.id,
        "target_system": receipt.target_system,
        "operation": receipt.operation,
        "external_id": receipt.external_id,
        "external_url": receipt.external_url,
        "summary": receipt.summary,
        "compensation_hint": receipt.compensation_hint,
        "status": receipt.status,
        "created_at": iso(receipt.created_at),
    }


def serialize_event(event: WorkEvent) -> dict[str, Any]:
    return {
        "id": event.id,
        "event_type": event.event_type,
        "message": event.message,
        "payload": event.payload or {},
        "created_at": iso(event.created_at),
    }


def serialize_work_object(db: Session, work: WorkObject, detail: bool = False) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "id": work.id,
        "title": work.title,
        "objective": work.objective,
        "completion_test": work.completion_test,
        "status": work.status,
        "authority_lane": work.authority_lane,
        "source_scope": work.source_scope or [],
        "source_task_url": work.source_task_url,
        "owner_name": work.owner_name,
        "priority": work.priority,
        "due_at": iso(work.due_at),
        "created_at": iso(work.created_at),
        "updated_at": iso(work.updated_at),
    }
    if detail:
        evidence = (
            db.query(EvidenceItem)
            .filter(EvidenceItem.work_object_id == work.id)
            .order_by(EvidenceItem.captured_at.desc())
            .all()
        )
        decisions = (
            db.query(DecisionRecord)
            .filter(DecisionRecord.work_object_id == work.id)
            .order_by(DecisionRecord.created_at.desc())
            .all()
        )
        steps = (
            db.query(PlanStep)
            .filter(PlanStep.work_object_id == work.id)
            .order_by(PlanStep.position.asc(), PlanStep.created_at.asc())
            .all()
        )
        approvals = (
            db.query(ApprovalRequest)
            .filter(ApprovalRequest.work_object_id == work.id)
            .order_by(ApprovalRequest.requested_at.desc())
            .all()
        )
        receipts = (
            db.query(ActionReceipt)
            .filter(ActionReceipt.work_object_id == work.id)
            .order_by(ActionReceipt.created_at.desc())
            .all()
        )
        events = (
            db.query(WorkEvent)
            .filter(WorkEvent.work_object_id == work.id)
            .order_by(WorkEvent.created_at.desc())
            .limit(30)
            .all()
        )
        payload.update(
            {
                "evidence": [serialize_evidence(item) for item in evidence],
                "decisions": [
                    {
                        "id": item.id,
                        "recommendation": item.recommendation,
                        "rationale": item.rationale,
                        "confidence": item.confidence,
                        "status": item.status,
                        "created_at": iso(item.created_at),
                    }
                    for item in decisions
                ],
                "plan_steps": [serialize_plan_step(step) for step in steps],
                "approvals": [serialize_approval(item) for item in approvals],
                "receipts": [serialize_receipt(item) for item in receipts],
                "events": [serialize_event(item) for item in events],
            }
        )
    return payload


def add_event(db: Session, work_id: str, event_type: str, message: str, payload: Optional[dict[str, Any]] = None) -> WorkEvent:
    event = WorkEvent(
        work_object_id=work_id,
        event_type=event_type,
        message=message,
        payload=payload or {},
    )
    db.add(event)
    return event


def get_work_or_404(db: Session, work_id: str) -> WorkObject:
    work = db.query(WorkObject).filter(WorkObject.id == work_id).first()
    if not work:
        raise HTTPException(status_code=404, detail="Work object not found")
    return work


def seed_workspace_demo() -> None:
    """Create a local demonstration run so the command center is useful before connectors are live."""
    db = SessionLocal()
    try:
        if db.query(WorkObject).count() > 0:
            return
        work = WorkObject(
            title="Launch the XPM Jarvis operating pilot",
            objective="Validate the @Jarvis delegation workflow for XPM operations with a real ClickUp project and meeting evidence.",
            completion_test="A delegated ClickUp task produces a cited plan, an approved task update, and a receipt without duplicate writes.",
            status="awaiting_approval",
            authority_lane="draft_only",
            source_scope=["clickup", "otter", "cognee", "approved_web"],
            priority="high",
            due_at=datetime.utcnow() + timedelta(days=7),
        )
        db.add(work)
        db.flush()

        evidence = [
            EvidenceItem(
                work_object_id=work.id,
                source_type="ClickUp",
                source_title="XPM Jarvis control-plane build task",
                excerpt="The task requires a first working command center, durable delegation state, approvals, and ClickUp foundations.",
                confidence=0.96,
            ),
            EvidenceItem(
                work_object_id=work.id,
                source_type="Otter",
                source_title="Pilot planning meeting — placeholder evidence",
                excerpt="A source-linked meeting decision should become a proposed ClickUp task rather than an untracked note.",
                confidence=0.78,
            ),
        ]
        db.add_all(evidence)
        db.add(
            DecisionRecord(
                work_object_id=work.id,
                recommendation="Start with a tightly scoped research-to-ClickUp flow and keep all writes behind action-specific approval.",
                rationale="This validates the product thesis while limiting the authority and blast radius of the first pilot.",
                confidence=0.9,
            )
        )
        db.add_all(
            [
                PlanStep(
                    work_object_id=work.id,
                    title="Complete the command-center foundation",
                    description="Create work objects, plan board, evidence view, approval cards, and timeline.",
                    owner_name="XPM Jarvis",
                    risk_class="read",
                    position=1,
                ),
                PlanStep(
                    work_object_id=work.id,
                    title="Re-authorize ClickUp and configure the pilot list",
                    description="Connect the delegated-work flow to a real ClickUp location with least privilege.",
                    owner_name="You",
                    risk_class="credential",
                    position=2,
                ),
                PlanStep(
                    work_object_id=work.id,
                    title="Run the first @Jarvis delegation",
                    description="Research the context, review the plan, approve an exact ClickUp write, and verify the receipt.",
                    owner_name="XPM Jarvis",
                    risk_class="reversible_write",
                    position=3,
                    depends_on=["Complete the command-center foundation", "Re-authorize ClickUp and configure the pilot list"],
                ),
            ]
        )
        db.add(
            ApprovalRequest(
                work_object_id=work.id,
                action_type="create_clickup_tasks",
                target_system="ClickUp",
                action_summary="Create the approved pilot task structure after the plan has been reviewed.",
                impact_summary="This will create project work items and may notify the assignees configured in ClickUp.",
                risk_class="reversible_write",
                expires_at=datetime.utcnow() + timedelta(days=2),
            )
        )
        add_event(db, work.id, "work_created", "XPM Jarvis created a durable delegation contract for the pilot.")
        add_event(db, work.id, "evidence_ready", "Evidence pack assembled from scoped work context.")
        add_event(db, work.id, "approval_requested", "A ClickUp write is ready for action-specific approval.")
        db.commit()
    finally:
        db.close()


@router.get("/workspace/dashboard")
def get_dashboard(db: Session = Depends(get_db)) -> dict[str, Any]:
    works = db.query(WorkObject).order_by(WorkObject.updated_at.desc()).limit(8).all()
    pending = (
        db.query(ApprovalRequest)
        .filter(ApprovalRequest.status == "pending")
        .order_by(ApprovalRequest.requested_at.desc())
        .limit(8)
        .all()
    )
    events = db.query(WorkEvent).order_by(WorkEvent.created_at.desc()).limit(12).all()
    return {
        "summary": {
            "active_work": db.query(WorkObject).filter(WorkObject.status.notin_(["completed", "canceled", "failed"])).count(),
            "pending_approvals": len(pending),
            "evidence_items": db.query(EvidenceItem).count(),
            "receipts": db.query(ActionReceipt).count(),
        },
        "work_objects": [serialize_work_object(db, item) for item in works],
        "pending_approvals": [serialize_approval(item) for item in pending],
        "activity": [serialize_event(item) for item in events],
        "integrations": integration_status(),
    }


@router.get("/workspace/integrations")
def integration_status() -> list[dict[str, Any]]:
    return [
        {
            "id": "jarvis",
            "name": "XPM Jarvis",
            "status": "ready" if os.getenv("HERMES_API_BASE_URL") else "scaffolded",
            "detail": "The XPM Jarvis control plane connects to its private agent runtime when HERMES_API_BASE_URL and HERMES_API_KEY are present.",
        },
        {
            "id": "cognee",
            "name": "Cognee Memory",
            "status": "ready" if os.getenv("COGNEE_BASE_URL") else "scaffolded",
            "detail": "Memory service is configured when COGNEE_BASE_URL and COGNEE_API_KEY are present.",
        },
        {
            "id": "clickup",
            "name": "ClickUp",
            "status": "reauthorization_required",
            "detail": "The current ClickUp connection needs re-authorization before live delegation can run.",
        },
        {
            "id": "otter",
            "name": "Otter",
            "status": "connected",
            "detail": "Meeting search and transcript retrieval are available as a read-only evidence source.",
        },
        {
            "id": "clockify",
            "name": "Clockify",
            "status": "not_connected",
            "detail": "Capacity intelligence is planned as a read-first integration.",
        },
        {
            "id": "quickbooks",
            "name": "QuickBooks Online",
            "status": "not_connected",
            "detail": "Read-first reporting requires an Intuit OAuth application and company authorization.",
        },
    ]


@router.get("/work-objects")
def list_work_objects(db: Session = Depends(get_db)) -> list[dict[str, Any]]:
    works = db.query(WorkObject).order_by(WorkObject.updated_at.desc()).all()
    return [serialize_work_object(db, work) for work in works]


@router.post("/work-objects", status_code=201)
def create_work_object(payload: WorkObjectCreate, db: Session = Depends(get_db)) -> dict[str, Any]:
    work = WorkObject(**payload.model_dump())
    db.add(work)
    db.flush()
    add_event(db, work.id, "work_created", "A new delegation contract was created.")
    db.commit()
    db.refresh(work)
    return serialize_work_object(db, work, detail=True)


@router.get("/work-objects/{work_id}")
def get_work_object(work_id: str, db: Session = Depends(get_db)) -> dict[str, Any]:
    return serialize_work_object(db, get_work_or_404(db, work_id), detail=True)


@router.post("/work-objects/{work_id}/plan-steps", status_code=201)
def create_plan_step(work_id: str, payload: PlanStepCreate, db: Session = Depends(get_db)) -> dict[str, Any]:
    get_work_or_404(db, work_id)
    step = PlanStep(work_object_id=work_id, **payload.model_dump())
    db.add(step)
    add_event(db, work_id, "plan_updated", f"Plan step proposed: {payload.title}")
    db.commit()
    db.refresh(step)
    return serialize_plan_step(step)


@router.post("/work-objects/{work_id}/evidence", status_code=201)
def create_evidence(work_id: str, payload: EvidenceCreate, db: Session = Depends(get_db)) -> dict[str, Any]:
    get_work_or_404(db, work_id)
    item = EvidenceItem(work_object_id=work_id, is_inference=int(payload.is_inference), **payload.model_dump(exclude={"is_inference"}))
    db.add(item)
    add_event(db, work_id, "evidence_added", f"Evidence added from {payload.source_type}: {payload.source_title}")
    db.commit()
    db.refresh(item)
    return serialize_evidence(item)


@router.post("/work-objects/{work_id}/approvals", status_code=201)
def create_approval(work_id: str, payload: ApprovalCreate, db: Session = Depends(get_db)) -> dict[str, Any]:
    work = get_work_or_404(db, work_id)
    approval = ApprovalRequest(
        work_object_id=work_id,
        action_type=payload.action_type,
        target_system=payload.target_system,
        action_summary=payload.action_summary,
        impact_summary=payload.impact_summary,
        risk_class=payload.risk_class,
        expires_at=datetime.utcnow() + timedelta(minutes=payload.expires_in_minutes),
    )
    work.status = "awaiting_approval"
    db.add(approval)
    add_event(db, work_id, "approval_requested", f"Approval requested for {payload.action_type} in {payload.target_system}.")
    db.commit()
    db.refresh(approval)
    return serialize_approval(approval)


@router.post("/approvals/{approval_id}/resolve")
def resolve_approval(approval_id: str, payload: ApprovalResolution, db: Session = Depends(get_db)) -> dict[str, Any]:
    approval = db.query(ApprovalRequest).filter(ApprovalRequest.id == approval_id).first()
    if not approval:
        raise HTTPException(status_code=404, detail="Approval request not found")
    if approval.status != "pending":
        raise HTTPException(status_code=409, detail="Approval request is already resolved")
    if approval.expires_at and approval.expires_at < datetime.utcnow():
        approval.status = "expired"
        db.commit()
        raise HTTPException(status_code=409, detail="Approval request has expired")

    approval.status = "approved" if payload.approved else "rejected"
    approval.resolved_by = payload.resolved_by
    approval.resolved_at = datetime.utcnow()
    work = get_work_or_404(db, approval.work_object_id)
    work.status = "executing" if payload.approved else "planning"
    outcome = "approved" if payload.approved else "rejected"
    message = f"{payload.resolved_by} {outcome} {approval.action_type} for {approval.target_system}."
    if payload.note:
        message = f"{message} Note: {payload.note}"
    add_event(db, work.id, "approval_resolved", message)
    db.commit()
    return serialize_approval(approval)


@router.post("/work-objects/{work_id}/receipts", status_code=201)
def create_receipt(work_id: str, payload: ReceiptCreate, db: Session = Depends(get_db)) -> dict[str, Any]:
    work = get_work_or_404(db, work_id)
    if payload.approval_id:
        approval = db.query(ApprovalRequest).filter(ApprovalRequest.id == payload.approval_id).first()
        if not approval or approval.work_object_id != work_id or approval.status != "approved":
            raise HTTPException(status_code=409, detail="A completed receipt must reference an approved action for this work object")
    receipt = ActionReceipt(work_object_id=work_id, **payload.model_dump())
    db.add(receipt)
    work.status = "completed" if payload.status == "completed" else work.status
    add_event(db, work_id, "action_receipt_recorded", f"{payload.target_system}: {payload.summary}")
    db.commit()
    db.refresh(receipt)
    return serialize_receipt(receipt)


@router.post("/work-objects/{work_id}/events", status_code=201)
def create_event(work_id: str, payload: EventCreate, db: Session = Depends(get_db)) -> dict[str, Any]:
    get_work_or_404(db, work_id)
    event = add_event(db, work_id, payload.event_type, payload.message, payload.payload)
    db.commit()
    db.refresh(event)
    return serialize_event(event)


@router.post("/work-objects/{work_id}/research-draft")
def generate_research_draft(work_id: str, db: Session = Depends(get_db)) -> dict[str, Any]:
    """Create a transparent placeholder research result until the live Jarvis runtime is connected."""
    work = get_work_or_404(db, work_id)
    work.status = "planning"
    decision = DecisionRecord(
        work_object_id=work_id,
        recommendation="Validate the requested outcome with scoped sources, then convert confirmed commitments into ClickUp-ready tasks.",
        rationale="The live XPM Jarvis runtime and ClickUp credentials are not connected yet, so this is a transparent scaffold rather than a model-generated claim.",
        confidence=0.55,
        status="proposed",
    )
    db.add(decision)
    add_event(db, work_id, "research_draft_ready", "A draft research-to-decision handoff is ready for review. Live agent execution is scaffolded but not connected.")
    db.commit()
    return serialize_work_object(db, work, detail=True)


@router.get("/workspace/health")
def workspace_health() -> dict[str, Any]:
    return {
        "status": "ok",
        "control_plane": "ready",
        "jarvis_runtime_configured": bool(os.getenv("HERMES_API_BASE_URL") and os.getenv("HERMES_API_KEY")),
        "hermes_runtime_configured": bool(os.getenv("HERMES_API_BASE_URL") and os.getenv("HERMES_API_KEY")),
        "cognee_configured": bool(os.getenv("COGNEE_BASE_URL")),
        "timestamp": datetime.utcnow().isoformat(),
    }
