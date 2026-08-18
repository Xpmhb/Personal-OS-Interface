"""ClickUp webhook foundation for explicit XPM Jarvis delegation.

The endpoint accepts signed inbound events only. It records every delivery before
creating a work object so provider retries cannot duplicate work. A live ClickUp
write is intentionally not performed here: webhook events only create or update
the internal, reviewable delegation state.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import os
import re
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from database import get_db
from models import WebhookDelivery, WorkObject
from workspace import add_event, serialize_work_object

router = APIRouter()


def _webhook_secret() -> str:
    secret = os.getenv("CLICKUP_WEBHOOK_SECRET")
    if not secret:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="ClickUp webhook receiver is not configured. Store CLICKUP_WEBHOOK_SECRET before enabling deliveries.",
        )
    return secret


def _extract_comment_text(payload: dict[str, Any]) -> str:
    comment = payload.get("comment") or {}
    if not isinstance(comment, dict):
        return ""
    return str(
        comment.get("comment_text")
        or comment.get("text")
        or comment.get("comment")
        or ""
    ).strip()


def _delivery_key(payload: dict[str, Any], raw_body: bytes) -> tuple[str, str | None, str | None]:
    task_id = str(payload.get("task_id") or (payload.get("task") or {}).get("id") or "") or None
    comment = payload.get("comment") or {}
    comment_id = str(comment.get("id") or "") if isinstance(comment, dict) else None
    webhook_id = str(payload.get("webhook_id") or "unknown")
    event_type = str(payload.get("event") or "unknown")
    raw_hash = hashlib.sha256(raw_body).hexdigest()[:20]
    return f"{webhook_id}:{event_type}:{task_id or 'none'}:{comment_id or raw_hash}", task_id, comment_id


def _jarvis_mention() -> str:
    """Read the product-facing trigger while supporting the previous pilot variable."""
    return (
        os.getenv("JARVIS_CLICKUP_MENTION")
        or os.getenv("HERMES_CLICKUP_MENTION")
        or "@Jarvis"
    ).strip()


def _is_jarvis_delegation(payload: dict[str, Any]) -> bool:
    mention = _jarvis_mention().lower()
    event_type = str(payload.get("event") or "")
    if event_type != "taskCommentPosted":
        return False
    return mention in _extract_comment_text(payload).lower()


def _pilot_scope() -> dict[str, str]:
    return {
        "space_name": os.getenv("CLICKUP_PILOT_SPACE_NAME", "Hunter's Dojo"),
        "list_id": os.getenv("CLICKUP_PILOT_LIST_ID", "901415896119"),
        "list_name": os.getenv("CLICKUP_PILOT_LIST_NAME", "Live MVP Test Sprint"),
    }


def _delegation_objective(payload: dict[str, Any]) -> str:
    mention = _jarvis_mention()
    text = _extract_comment_text(payload)
    stripped = re.sub(re.escape(mention), "", text, flags=re.IGNORECASE).strip(" :,-\n")
    return stripped or "Review the linked ClickUp task, gather scoped context, and propose an execution plan."


@router.get("/clickup/status")
def clickup_status() -> dict[str, Any]:
    configured = bool(os.getenv("CLICKUP_WEBHOOK_SECRET"))
    return {
        "provider": "ClickUp",
        "receiver_status": "configured" if configured else "awaiting_secret",
        "endpoint": "/api/integrations/clickup/webhook",
        "mention": _jarvis_mention(),
        "action_mode": "draft_only",
        "pilot_scope": _pilot_scope(),
        "next_step": "Create the webhook for the configured pilot location and store its returned secret as CLICKUP_WEBHOOK_SECRET.",
    }


@router.post("/clickup/webhook", status_code=status.HTTP_202_ACCEPTED)
async def receive_clickup_webhook(request: Request, db: Session = Depends(get_db)) -> dict[str, Any]:
    """Verify and record a ClickUp event; create a draft-only work object for @Jarvis comments."""
    raw_body = await request.body()
    provided_signature = request.headers.get("X-Signature", "")
    secret = _webhook_secret()
    expected_signature = hmac.new(secret.encode("utf-8"), raw_body, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(provided_signature, expected_signature):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid ClickUp webhook signature")

    try:
        payload = json.loads(raw_body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Webhook body must be valid JSON") from exc

    if not isinstance(payload, dict):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Webhook payload must be a JSON object")

    delivery_key, task_id, comment_id = _delivery_key(payload, raw_body)
    existing = db.query(WebhookDelivery).filter(WebhookDelivery.delivery_key == delivery_key).first()
    if existing:
        return {
            "status": "duplicate_ignored",
            "delivery_key": delivery_key,
            "work_object_id": existing.work_object_id,
        }

    event_type = str(payload.get("event") or "unknown")
    delivery = WebhookDelivery(
        provider="clickup",
        delivery_key=delivery_key,
        event_type=event_type,
        external_task_id=task_id,
        external_comment_id=comment_id,
        payload=payload,
    )
    db.add(delivery)

    if not _is_jarvis_delegation(payload):
        db.commit()
        return {"status": "recorded_no_delegation", "delivery_key": delivery_key, "event": event_type}

    task_name = str((payload.get("task") or {}).get("name") or f"ClickUp task {task_id or 'unknown'}")
    objective = _delegation_objective(payload)
    pilot = _pilot_scope()
    work = WorkObject(
        title=f"ClickUp · {task_name}",
        objective=objective,
        completion_test="Produce a source-linked plan and request approval before any external ClickUp write.",
        status="queued",
        authority_lane="draft_only",
        source_scope=["clickup", f"clickup:list:{pilot['list_id']}", "otter", "cognee"],
        source_task_url=f"https://app.clickup.com/t/{task_id}" if task_id else None,
        owner_name="You",
        priority="medium",
    )
    db.add(work)
    db.flush()
    delivery.work_object_id = work.id
    add_event(
        db,
        work.id,
        "clickup_delegation_received",
        f"Explicit {_jarvis_mention()} delegation received from ClickUp task {task_id or 'unknown'}.",
        {"clickup_task_id": task_id, "clickup_comment_id": comment_id, "delivery_key": delivery_key, "pilot_scope": pilot},
    )
    add_event(
        db,
        work.id,
        "scope_pending",
        "XPM Jarvis will gather scoped context and propose a plan. No ClickUp write has been authorized.",
    )
    db.commit()
    db.refresh(work)
    return {
        "status": "delegation_created",
        "delivery_key": delivery_key,
        "work_object": serialize_work_object(db, work, detail=True),
        "received_at": datetime.utcnow().isoformat(),
    }
