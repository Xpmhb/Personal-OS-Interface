"""
Nightly loop - can be called from API or Worker
"""
import logging
import os
import requests
from datetime import datetime
from database import SessionLocal

logger = logging.getLogger(__name__)


async def send_morning_brief(content: str):
    """Send Morning Brief to Telegram"""
    import asyncio
    
    telegram_token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    
    if not telegram_token or not chat_id:
        logger.warning("Telegram not configured, skipping Morning Brief delivery")
        return
    
    url = f"https://api.telegram.org/bot{telegram_token}/sendMessage"
    message = f"🌅 *Morning Brief* - {datetime.utcnow().strftime('%Y-%m-%d')}\n\n{content}"
    
    # Truncate if too long
    if len(message) > 4000:
        message = message[:3997] + "..."
    
    try:
        # Run sync requests in thread pool
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(None, lambda: requests.post(url, json={
            "chat_id": chat_id,
            "text": message,
            "parse_mode": "Markdown"
        }))
        if response.status_code == 200:
            logger.info("Morning Brief delivered to Telegram")
        else:
            logger.error(f"Failed to send Morning Brief: {response.text}")
    except Exception as e:
        logger.error(f"Error sending Morning Brief: {e}")


async def run_full_nightly_loop():
    """Run the complete nightly pipeline"""
    # Import here to avoid circular imports
    from runtime.engine import execute_agent
    from models import Agent, Artifact, Execution
    from sqlalchemy import desc

    logger.info("Starting nightly loop...")
    db = SessionLocal()

    try:
        # CFO - find any CFO agent
        cfo = db.query(Agent).filter(Agent.name.like("%cfo%")).first()
        cfo_result = None
        if cfo:
            cfo_result = await execute_agent(
                db=db,
                agent_id=str(cfo.id),
                prompt="Analyze available financial data. Flag anomalies, unusual patterns, or concerns. Cite all sources."
            )

        # COO - find any COO agent
        coo = db.query(Agent).filter(Agent.name.like("%coo%")).first()
        coo_result = None
        if coo:
            coo_result = await execute_agent(
                db=db,
                agent_id=str(coo.id),
                prompt="Review operational data. Generate a checklist of active items, identify bottlenecks."
            )
        
        # CTO - find any CTO agent
        cto = db.query(Agent).filter(Agent.name.like("%cto%")).first()
        cto_result = None
        if cto:
            cto_result = await execute_agent(
                db=db,
                agent_id=str(cto.id),
                prompt="Review system activity. Suggest technical improvements and recommend builds."
            )

        # CEO Synthesis - find any CEO agent (prefer nadella)
        ceo = db.query(Agent).filter(Agent.name.like("%ceo%")).first()
        ceo_result = None
        if ceo:
            # Get recent artifacts
            cfo_art = db.query(Artifact).join(Execution).filter(
                Execution.agent_id == cfo.id
            ).order_by(desc(Artifact.created_at)).first() if cfo else None

            coo_art = db.query(Artifact).join(Execution).filter(
                Execution.agent_id == coo.id
            ).order_by(desc(Artifact.created_at)).first() if coo else None

            cto_art = db.query(Artifact).join(Execution).filter(
                Execution.agent_id == cto.id
            ).order_by(desc(Artifact.created_at)).first() if cto else None

            synthesis_context = {
                "cfo": cfo_art.content if cfo_art else "No CFO report.",
                "coo": coo_art.content if coo_art else "No COO report.",
                "cto": cto_art.content if cto_art else "No CTO report."
            }

            ceo_result = await execute_agent(
                db=db,
                agent_id=str(ceo.id),
                prompt=f"""Synthesize into a Morning Brief for {datetime.utcnow().strftime('%Y-%m-%d')}.

Format required:
# Morning Brief

## Executive Summary
## Key Decisions Needed
## Today's Priorities
## Risk Flags""",
                context=synthesis_context
            )

        # Get CEO artifact (Morning Brief)
        if ceo_result and ceo_result.get("artifact_id"):
            brief_artifact = db.query(Artifact).filter(
                Artifact.id == ceo_result["artifact_id"]
            ).first()
            if brief_artifact:
                # Send Morning Brief to Telegram
                await send_morning_brief(brief_artifact.content)

        logger.info("Nightly loop completed successfully")
        return {
            "status": "completed",
            "cfo_status": cfo_result.get("status") if cfo_result else "skipped",
            "coo_status": coo_result.get("status") if coo_result else "skipped",
            "cto_status": cto_result.get("status") if cto_result else "skipped",
            "ceo_status": ceo_result.get("status") if ceo_result else "skipped",
            "ceo_artifact": ceo_result.get("artifact_id") if ceo_result else None
        }

    except Exception as e:
        logger.error(f"Nightly loop failed: {e}")
        return {"status": "failed", "error": str(e)}
    finally:
        db.close()
