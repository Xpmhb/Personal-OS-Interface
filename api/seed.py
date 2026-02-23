"""
Database seed script - loads default executive agents on startup
"""
import json
import os
import uuid
from pathlib import Path
from database import SessionLocal, engine, Base
from models import Agent


def load_default_agents():
    """Load default executive agent specs into database"""

    # Create tables
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()

    try:
        # Check if agents already exist
        existing = db.query(Agent).count()
        if existing > 0:
            print(f"Database already has {existing} agents. Skipping seed.")
            return

        # Load spec files - look in api/agents/specs only
        specs_dir = Path(__file__).parent / "agents" / "specs"

        loaded_count = 0

        if not specs_dir.exists():
            print(f"Specs directory not found: {specs_dir}")
            return

        for spec_file in specs_dir.glob("*.spec.json"):
                try:
                    with open(spec_file) as f:
                        spec = json.load(f)

                    # Always generate a fresh UUID (don't use spec id)
                    agent_id = str(uuid.uuid4())

                    agent = Agent(
                        id=agent_id,
                        name=spec["name"],
                        display_name=spec.get("display_name", spec["name"]),
                        spec=spec,
                        status="active"
                    )
                    db.add(agent)
                    print(f"Added agent: {agent.name} ({spec.get('archetype', 'standard')})")
                    loaded_count += 1

                except Exception as e:
                    print(f"Error loading {spec_file}: {e}")

        db.commit()
        print(f"Loaded {loaded_count} default agents!")

    except Exception as e:
        db.rollback()
        print(f"Error seeding database: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    load_default_agents()
