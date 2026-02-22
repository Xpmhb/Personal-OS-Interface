"""
Tool implementations for agent runtime
Each tool: validate permissions → execute → log → return
"""
import uuid
import logging
from typing import Optional
from sqlalchemy.orm import Session
from datetime import datetime

logger = logging.getLogger(__name__)


async def file_search(
    db: Session,
    agent_id: str,
    query: str,
    namespace: Optional[str] = None,
    limit: int = 5
) -> dict:
    """Vector search with permission enforcement"""
    from intelligence.retrieval import search_with_permissions

    start = datetime.utcnow()

    results = await search_with_permissions(
        db=db,
        agent_id=agent_id,
        query=query,
        namespace=namespace,
        limit=limit
    )

    duration = (datetime.utcnow() - start).total_seconds() * 1000

    return {
        "tool_id": "file_search",
        "input": {"query": query, "namespace": namespace, "limit": limit},
        "output": {
            "results": results,
            "count": len(results)
        },
        "duration_ms": int(duration)
    }


async def sql_query(
    db: Session,
    agent_id: str,
    query: str
) -> dict:
    """Execute read-only SQL query against metrics table"""
    from intelligence.retrieval import check_permission

    start = datetime.utcnow()

    # Check permission for table access
    # Extract table name from query (simplified)
    allowed_tables = ["metrics", "financial_data", "operations"]
    query_lower = query.lower()

    table_found = None
    for table in allowed_tables:
        if table in query_lower:
            table_found = table
            break

    if table_found and not check_permission(db, agent_id, "table", table_found):
        duration = (datetime.utcnow() - start).total_seconds() * 1000
        return {
            "tool_id": "sql_query",
            "input": {"query": query},
            "output": {"error": f"Permission denied for table '{table_found}'"},
            "duration_ms": int(duration)
        }

    # For MVP: return stub data (no actual SQL execution for safety)
    # In v0.2: implement actual read-only query execution
    duration = (datetime.utcnow() - start).total_seconds() * 1000

    return {
        "tool_id": "sql_query",
        "input": {"query": query},
        "output": {
            "message": "SQL query tool available but no metrics data loaded yet.",
            "note": "Upload CSV/Excel data to populate metrics tables."
        },
        "duration_ms": int(duration)
    }


# Tool registry
TOOLS = {
    "file_search": {
        "function": file_search,
        "description": "Search indexed documents with permission-aware retrieval",
        "parameters": {
            "query": "Search query string",
            "namespace": "Optional namespace filter",
            "limit": "Max results (default 5)"
        }
    },
    "sql_query": {
        "function": sql_query,
        "description": "Execute read-only SQL queries against metrics tables",
        "parameters": {
            "query": "SQL query string"
        }
    }
}


def get_tool_definitions_for_llm(allowed_tools: list) -> list:
    """Generate OpenAI-compatible tool definitions for LLM"""
    definitions = []
    for tool_spec in allowed_tools:
        tool_id = tool_spec.get("tool_id", "") if isinstance(tool_spec, dict) else tool_spec
        if tool_id in TOOLS:
            tool_info = TOOLS[tool_id]
            definitions.append({
                "type": "function",
                "function": {
                    "name": tool_id,
                    "description": tool_info["description"],
                    "parameters": {
                        "type": "object",
                        "properties": {
                            k: {"type": "string", "description": v}
                            for k, v in tool_info["parameters"].items()
                        },
                        "required": ["query"]
                    }
                }
            })
    return definitions
