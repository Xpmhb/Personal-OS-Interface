"""
Agent memory — append-only facts with summarization
"""
import uuid
import logging
from typing import List, Optional
from sqlalchemy.orm import Session
from datetime import datetime

import httpx
from config import get_settings

logger = logging.getLogger(__name__)


def get_memory(db: Session, agent_id: str, max_tokens: int = 4000) -> str:
    """Get summarized memory for agent"""
    from models import Memory

    memories = db.query(Memory).filter(
        Memory.agent_id == agent_id
    ).order_by(Memory.created_at.desc()).all()

    if not memories:
        return ""

    # Build memory text, respecting token limit
    memory_text = ""
    total_tokens = 0

    for mem in memories:
        tokens = mem.token_count or len(mem.content.split())
        if total_tokens + tokens > max_tokens:
            break
        memory_text = f"[{mem.created_at.strftime('%Y-%m-%d')}] {mem.content}\n" + memory_text
        total_tokens += tokens

    return memory_text.strip()


def append_memory(db: Session, agent_id: str, content: str, memory_type: str = "fact"):
    """Append a new memory entry"""
    from models import Memory

    token_count = len(content.split())

    memory = Memory(
        id=str(uuid.uuid4()),
        agent_id=agent_id,
        content=content,
        memory_type=memory_type,
        token_count=token_count
    )
    db.add(memory)
    db.commit()

    logger.info(f"Memory appended for agent {agent_id}: {content[:50]}...")
    return memory


async def summarize_and_compact(db: Session, agent_id: str, max_entries: int = 50):
    """Summarize older memories to save space"""
    from models import Memory

    settings = get_settings()
    memories = db.query(Memory).filter(
        Memory.agent_id == agent_id
    ).order_by(Memory.created_at.asc()).all()

    if len(memories) <= max_entries:
        return  # No compaction needed

    # Take oldest half and summarize
    to_summarize = memories[:len(memories) // 2]
    text_to_summarize = "\n".join(
        f"- [{m.created_at.strftime('%Y-%m-%d')}] {m.content}"
        for m in to_summarize
    )

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {settings.openrouter_api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": settings.llm_model,
                    "messages": [
                        {
                            "role": "system",
                            "content": "Summarize these agent memory entries into a concise set of key facts and decisions. Preserve dates and important details."
                        },
                        {
                            "role": "user",
                            "content": text_to_summarize
                        }
                    ],
                    "temperature": 0.1,
                    "max_tokens": 1000
                }
            )
            response.raise_for_status()
            summary = response.json()["choices"][0]["message"]["content"]

        # Delete old entries
        for mem in to_summarize:
            db.delete(mem)

        # Add summary as new entry
        append_memory(db, agent_id, f"[SUMMARY] {summary}", memory_type="summary")

        logger.info(f"Compacted {len(to_summarize)} memories into summary for agent {agent_id}")

    except Exception as e:
        logger.error(f"Memory compaction failed: {e}")
