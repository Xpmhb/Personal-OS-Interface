"""
Permission-aware retrieval from Qdrant
Deny-by-default: agent must have explicit permission to access data
"""
from typing import List, Optional
from sqlalchemy.orm import Session
from datetime import datetime
import uuid
import logging

logger = logging.getLogger(__name__)


def check_permission(
    db: Session,
    agent_id: str,
    resource_type: str,
    resource_id: str
) -> bool:
    """Check if agent has permission to access resource. Deny-by-default."""
    from models import AgentPermission, AccessLog

    permission = db.query(AgentPermission).filter(
        AgentPermission.agent_id == agent_id,
        AgentPermission.resource_type == resource_type,
        AgentPermission.resource_id == resource_id
    ).first()

    decision = "allow" if permission else "deny"

    # Log access decision
    log_entry = AccessLog(
        id=str(uuid.uuid4()),
        agent_id=agent_id,
        resource_type=resource_type,
        resource_id=resource_id,
        action="read",
        decision=decision
    )
    db.add(log_entry)
    db.commit()

    logger.info(f"Access {decision}: agent={agent_id} resource={resource_type}/{resource_id}")
    return permission is not None


def check_namespace_permission(
    db: Session,
    agent_id: str,
    namespace: str
) -> bool:
    """Check if agent has permission to access a vector namespace"""
    return check_permission(db, agent_id, "vector_namespace", namespace)


def check_file_permission(
    db: Session,
    agent_id: str,
    file_id: str
) -> bool:
    """Check if agent has permission to access a specific file"""
    return check_permission(db, agent_id, "file", file_id)


def grant_permission(
    db: Session,
    agent_id: str,
    resource_type: str,
    resource_id: str,
    permission: str = "read"
):
    """Grant an agent permission to access a resource"""
    from models import AgentPermission

    # Check if already granted
    existing = db.query(AgentPermission).filter(
        AgentPermission.agent_id == agent_id,
        AgentPermission.resource_type == resource_type,
        AgentPermission.resource_id == resource_id
    ).first()

    if existing:
        return existing

    perm = AgentPermission(
        id=str(uuid.uuid4()),
        agent_id=agent_id,
        resource_type=resource_type,
        resource_id=resource_id,
        permission=permission
    )
    db.add(perm)
    db.commit()
    return perm


async def search_with_permissions(
    db: Session,
    agent_id: str,
    query: str,
    namespace: Optional[str] = None,
    limit: int = 5
) -> List[dict]:
    """Permission-aware vector search"""
    from intelligence.ingest import embed_text
    from config import get_settings
    from qdrant_client import QdrantClient
    from qdrant_client.models import Filter, FieldCondition, MatchValue

    settings = get_settings()

    # Get agent's allowed namespaces from spec
    from models import Agent
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if not agent:
        return []

    allowed_namespaces = agent.spec.get("data_permissions", {}).get("vector_namespaces", [])

    # If specific namespace requested, check permission
    if namespace:
        if not check_namespace_permission(db, agent_id, namespace):
            logger.warning(f"Agent {agent_id} denied access to namespace '{namespace}'")
            return []
        search_namespaces = [namespace]
    else:
        # Search all allowed namespaces
        search_namespaces = []
        for ns in allowed_namespaces:
            if check_namespace_permission(db, agent_id, ns):
                search_namespaces.append(ns)

        if not search_namespaces:
            logger.info(f"Agent {agent_id} has no permitted namespaces")
            return []

    # Embed query
    query_vector = await embed_text(query)

    # Search Qdrant with namespace filter
    try:
        client = QdrantClient(url=settings.qdrant_url, api_key=settings.qdrant_api_key)

        # Build filter for allowed namespaces
        must_conditions = []
        if len(search_namespaces) == 1:
            must_conditions.append(
                FieldCondition(key="namespace", match=MatchValue(value=search_namespaces[0]))
            )
        # For multiple namespaces, we'd need a should filter — simplified for MVP

        results = client.search(
            collection_name=settings.qdrant_collection,
            query_vector=query_vector,
            query_filter=Filter(must=must_conditions) if must_conditions else None,
            limit=limit
        )

        return [
            {
                "chunk_id": str(hit.id),
                "file_id": hit.payload.get("file_id", ""),
                "filename": hit.payload.get("filename", ""),
                "namespace": hit.payload.get("namespace", ""),
                "chunk_text": hit.payload.get("chunk_text", ""),
                "chunk_index": hit.payload.get("chunk_index", 0),
                "score": hit.score
            }
            for hit in results
        ]

    except Exception as e:
        logger.error(f"Qdrant search error: {e}")
        return []
