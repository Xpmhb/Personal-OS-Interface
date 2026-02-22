"""
APScheduler-based nightly loop
Runs: CFO → COO → CTO → CEO (Morning Brief)
"""
import logging
from datetime import datetime
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger

from database import SessionLocal
from runtime.engine import execute_agent

logger = logging.getLogger(__name__)

# Agent name to role mapping
NIGHTLY_SEQUENCE = [
    ("cfo-agent", "Analyze financial data, flag anomalies and concerns."),
    ("coo-agent", "Review operations data, generate checklist and bottlenecks."),
    ("cto-agent", "Review system logs, suggest technical improvements."),
    ("ceo-agent", None)  # CEO runs last with context from others
]


async def run_nightly_cfo(db):
    """Run CFO agent for nightly anomaly scan"""
    from models import Agent
    agent = db.query(Agent).filter(Agent.name == "cfo-agent").first()
    if not agent:
        logger.error("CFO agent not found")
        return None

    result = await execute_agent(
        db=db,
        agent_id=str(agent.id),
        prompt="Analyze available financial data. Flag anomalies, unusual patterns, or concerns. Cite all sources. Be specific."
    )
    logger.info(f"CFO run completed: {result.get('status')}")
    return result


async def run_nightly_coo(db):
    """Run COO agent for nightly ops check"""
    from models import Agent
    agent = db.query(Agent).filter(Agent.name == "coo-agent").first()
    if not agent:
        logger.error("COO agent not found")
        return None

    result = await execute_agent(
        db=db,
        agent_id=str(agent.id),
        prompt="Review operational data. Generate a checklist of active items, identify bottlenecks, and suggest process improvements. Be specific."
    )
    logger.info(f"COO run completed: {result.get('status')}")
    return result


async def run_nightly_cto(db):
    """Run CTO agent for nightly build suggestions"""
    from models import Agent
    agent = db.query(Agent).filter(Agent.name == "cto-agent").first()
    if not agent:
        logger.error("CTO agent not found")
        return None

    result = await execute_agent(
        db=db,
        agent_id=str(agent.id),
        prompt="Review system activity and logs. Suggest technical improvements, flag any issues, and recommend builds for the next day. Be specific."
    )
    logger.info(f"CTO run completed: {result.get('status')}")
    return result


async def run_nightly_ceo(db, context: dict):
    """Run CEO agent to synthesize Morning Brief"""
    from models import Agent, Artifact, Execution
    from sqlalchemy import desc

    agent = db.query(Agent).filter(Agent.name == "ceo-agent").first()
    if not agent:
        logger.error("CEO agent not found")
        return None

    # Get recent artifacts from other executives
    cfo_art = db.query(Artifact).join(Execution).filter(
        Execution.agent_id == db.query(Agent).filter(Agent.name == "cfo-agent").first().id
    ).order_by(desc(Artifact.created_at)).first()

    coo_art = db.query(Artifact).join(Execution).filter(
        Execution.agent_id == db.query(Agent).filter(Agent.name == "coo-agent").first().id
    ).order_by(desc(Artifact.created_at)).first()

    cto_art = db.query(Artifact).join(Execution).filter(
        Execution.agent_id == db.query(Agent).filter(Agent.name == "cto-agent").first().id
    ).order_by(desc(Artifact.created_at)).first()

    synthesis_context = {
        "cfo": cfo_art.content if cfo_art else "No CFO report available.",
        "coo": coo_art.content if coo_art else "No COO report available.",
        "cto": cto_art.content if cto_art else "No CTO report available."
    }

    result = await execute_agent(
        db=db,
        agent_id=str(agent.id),
        prompt=f"""Synthesize the following department reports into a Morning Brief for {datetime.utcnow().strftime('%Y-%m-%d')}.

Format:
# Morning Brief

## Executive Summary (3-5 sentences)
## Key Decisions Needed
## Today's Priorities
## Risk Flags
## Department Summaries""",
        context=synthesis_context
    )
    logger.info(f"CEO run completed: {result.get('status')}")
    return result


async def run_full_nightly_loop():
    """Run the complete nightly pipeline"""
    logger.info("Starting nightly loop...")
    db = SessionLocal()

    try:
        # Run each executive in sequence
        cfo_result = await run_nightly_cfo(db)
        coo_result = await run_nightly_coo(db)
        cto_result = await run_nightly_cto(db)

        # CEO synthesis with context from others
        ceo_result = await run_nightly_ceo(db, {
            "cfo": cfo_result.get("artifact_content", "") if cfo_result else "",
            "coo": coo_result.get("artifact_content", "") if coo_result else "",
            "cto": cto_result.get("artifact_content", "") if cto_result else ""
        })

        logger.info("Nightly loop completed successfully")
        return {"status": "completed", "ceo_artifact": ceo_result.get("artifact_id")}

    except Exception as e:
        logger.error(f"Nightly loop failed: {e}")
        return {"status": "failed", "error": str(e)}
    finally:
        db.close()


def start_scheduler():
    """Start the APScheduler for nightly runs"""
    scheduler = BlockingScheduler()

    # Run at 2 AM daily
    scheduler.add_job(
        run_full_nightly_loop,
        CronTrigger(hour=2, minute=0),
        id="nightly_loop",
        name="Nightly Executive Loop",
        replace_existing=True
    )

    logger.info("Scheduler started. Nightly loop will run at 2:00 AM UTC.")
    return scheduler


# For manual triggering via API
async def trigger_nightly_loop():
    """Manually trigger the nightly loop"""
    return await run_full_nightly_loop()
