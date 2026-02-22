"""
Worker entry point — starts scheduler and runs background jobs
"""
import asyncio
import logging
from database import SessionLocal, engine, Base
from nightly import start_scheduler, trigger_nightly_loop

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    # Initialize DB
    Base.metadata.create_all(bind=engine)

    logger.info("Starting Personal AI OS Worker...")

    # Start scheduler (blocking)
    scheduler = start_scheduler()

    try:
        scheduler.start()
    except KeyboardInterrupt:
        logger.info("Scheduler stopped.")
        scheduler.shutdown()


if __name__ == "__main__":
    main()