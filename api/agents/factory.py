"""
Agent Factory — Create agents from natural language descriptions
Uses LLM to generate clarifying questions and build spec
"""
import uuid
import json
import httpx
from typing import Dict, Optional
from config import get_settings

# In-memory session store for factory conversations
_factory_sessions: Dict[str, dict] = {}


async def start_creation(description: str) -> dict:
    """Start agent creation from natural language — returns clarifying questions"""
    settings = get_settings()
    session_id = str(uuid.uuid4())

    # Use LLM to generate clarifying questions
    system_prompt = """You are an Agent Factory. A user wants to create an AI agent.
Based on their description, generate 3-5 clarifying questions to build a complete agent spec.

Your questions should cover:
1. What specific role/responsibility does this agent have?
2. What data should this agent have access to?
3. What tools does it need? (file_search, sql_query)
4. Should it run on a schedule? If so, how often?
5. Any budget or usage limits?

Return JSON only:
{
  "questions": ["question1", "question2", ...],
  "initial_analysis": {
    "suggested_name": "agent-name",
    "suggested_role": "brief role",
    "suggested_capabilities": ["cap1", "cap2"]
  }
}"""

    try:
        response = await _call_llm(
            system_prompt=system_prompt,
            user_message=f"I want to create an agent: {description}",
            settings=settings
        )

        result = json.loads(response)
        _factory_sessions[session_id] = {
            "description": description,
            "questions": result.get("questions", []),
            "initial_analysis": result.get("initial_analysis", {}),
            "answers": {}
        }

        return {
            "session_id": session_id,
            "questions": result.get("questions", []),
            "initial_analysis": result.get("initial_analysis", {})
        }

    except Exception as e:
        # Fallback: generate default questions
        _factory_sessions[session_id] = {
            "description": description,
            "questions": [
                "What specific tasks should this agent perform?",
                "What data sources should it have access to?",
                "Should it run automatically on a schedule?",
                "Are there any budget limits per day?",
                "What tools does it need (file search, SQL queries, etc.)?"
            ],
            "initial_analysis": {"suggested_name": "custom-agent"},
            "answers": {}
        }

        return {
            "session_id": session_id,
            "questions": _factory_sessions[session_id]["questions"],
            "initial_analysis": _factory_sessions[session_id]["initial_analysis"],
            "note": f"Used fallback questions due to: {str(e)}"
        }


async def process_answers(session_id: str, answers: Dict[str, str]) -> dict:
    """Process answers and generate full agent spec"""
    settings = get_settings()

    if session_id not in _factory_sessions:
        raise ValueError(f"Session {session_id} not found")

    session = _factory_sessions[session_id]
    session["answers"] = answers

    system_prompt = """You are an Agent Factory. Generate a complete agent spec based on the user's description and answers.

Return valid JSON matching this schema:
{
  "version": "1.0",
  "name": "agent-name-lowercase",
  "display_name": "Agent Display Name",
  "role_definition": "Detailed role definition...",
  "capabilities": ["cap1", "cap2"],
  "tools_allowed": [{"tool_id": "file_search", "ops": ["read"]}],
  "memory": {"scope": "private", "max_tokens": 8000, "retention_days": 30},
  "data_permissions": {"datasets": [], "tables": [], "vector_namespaces": [], "files": []},
  "triggers": {"manual": true, "schedules": [], "events": []},
  "guardrails": {"budget_usd_per_day": 10.0, "max_tool_calls_per_run": 50, "approval_required_ops": []},
  "llm": {"model": "anthropic/claude-3.5-sonnet", "temperature": 0.3, "max_tokens": 4096}
}"""

    user_message = f"""Original description: {session['description']}

Questions and answers:
{json.dumps(dict(zip(session['questions'], answers.values())), indent=2)}

Initial analysis: {json.dumps(session['initial_analysis'])}

Generate the complete agent spec."""

    try:
        response = await _call_llm(
            system_prompt=system_prompt,
            user_message=user_message,
            settings=settings
        )

        spec = json.loads(response)

        # Cleanup session
        del _factory_sessions[session_id]

        return {"spec": spec, "status": "ready"}

    except Exception as e:
        return {"error": str(e), "status": "failed"}


async def _call_llm(system_prompt: str, user_message: str, settings) -> str:
    """Call OpenRouter LLM"""
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {settings.openrouter_api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": settings.llm_model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                "temperature": 0.3,
                "max_tokens": 2000,
                "response_format": {"type": "json_object"}
            }
        )
        response.raise_for_status()
        data = response.json()
        content = data["choices"][0]["message"]["content"]
        # Strip markdown fences if present
        content = content.strip()
        if content.startswith("```json"):
            content = content[7:]
        if content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]
        return content.strip()
