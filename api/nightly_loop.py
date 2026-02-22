"""
Nightly loop - can be called from API or Worker
"""
import logging
from datetime import datetime
from database import SessionLocal

logger = logging.getLogger(__name__)


async def run_full_nightly_loop():
    """Run the complete nightly pipeline"""
    # Import here to avoid circular imports
    from runtime.engine import execute_agent
    from models import Agent, Artifact, Execution
    from sqlalchemy import desc

    logger.info("Starting nightly loop...")
    db = SessionLocal()

    try:
        # CFO
        cfo = db.query(Agent).filter(Agent.name == "cfo-agent").first()
        cfo_result = None
        if cfo:
            cfo_result = await execute_agent(
                db=db,
                agent_id=str(cfo.id),
                prompt="Analyze available financial data. Flag anomalies, unusual patterns, or concerns. Cite all sources."
            )

        # COO
        coo = db.query(Agent).filter(Agent.name == "coo-agent").first()
        coo_result = None
        if coo:
            coo_result = await execute_agent(
                db=db,
                agent_id=str(coo.id),
                prompt="Review operational data. Generate a checklist of active items, identify bottlenecks."
            )

        # CTO
        cto = db.query(Agent).filter(Agent.name == "cto-agent").first()
        cto_result = None
        if cto:
            cto_result = await execute_agent(
                db=db,
                agent_id=str(cto.id),
                prompt="Review system activity. Suggest technical improvements and recommend builds."
            )

        # CEO Synthesis
        ceo = db.query(Agent).filter(Agent.name == "ceo-agent").first()
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
