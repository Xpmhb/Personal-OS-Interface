"""
Agent execution engine — the core runtime
Load spec → build context → call LLM → execute tools → save artifact → log
"""
import uuid
import json
import time
import logging
from datetime import datetime
from typing import Optional, Dict, Any

import httpx
from sqlalchemy.orm import Session

from config import get_settings
from runtime.prompts import build_system_prompt
from runtime.tools import get_tool_definitions_for_llm, TOOLS
from runtime.memory import get_memory, append_memory
from runtime.tracing import trace_agent_run

logger = logging.getLogger(__name__)


async def execute_agent(
    db: Session,
    agent_id: str,
    prompt: str,
    context: Optional[Dict[str, Any]] = None
) -> dict:
    """Execute an agent: load spec → build prompt → call LLM → tools → artifact"""
    from models import Agent, Execution, ToolCall, Artifact

    settings = get_settings()
    start_time = time.time()

    # Load agent
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if not agent:
        raise ValueError(f"Agent {agent_id} not found")

    spec = agent.spec

    # Create execution record
    execution_id = str(uuid.uuid4())
    execution = Execution(
        id=execution_id,
        agent_id=agent_id,
        prompt=prompt,
        status="running"
    )
    db.add(execution)
    db.commit()

    try:
        # Load memory
        max_memory_tokens = spec.get("memory", {}).get("max_tokens", 4000)
        memory_summary = get_memory(db, agent_id, max_memory_tokens)

        # Get allowed tools
        tools_allowed = spec.get("tools_allowed", [])
        tool_definitions = get_tool_definitions_for_llm(tools_allowed)
        tool_names = [t.get("tool_id", "") if isinstance(t, dict) else t for t in tools_allowed]

        # Build system prompt
        system_prompt = build_system_prompt(
            spec=spec,
            memory_summary=memory_summary,
            available_tools=tool_names
        )

        # Get LLM config
        llm_config = spec.get("llm", {})
        model = llm_config.get("model", settings.llm_model)
        temperature = llm_config.get("temperature", settings.llm_temperature)
        max_tokens = llm_config.get("max_tokens", settings.llm_max_tokens)

        # Call LLM
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ]

        # Add context if provided (e.g., from nightly loop)
        if context:
            context_str = json.dumps(context, indent=2)
            messages.append({"role": "user", "content": f"Additional context:\n{context_str}"})

        total_tokens_in = 0
        total_tokens_out = 0
        tool_call_records = []
        max_iterations = 5  # Prevent infinite tool call loops

        for iteration in range(max_iterations):
            async with httpx.AsyncClient(timeout=120.0) as client:
                payload = {
                    "model": model,
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                }

                if tool_definitions and iteration < max_iterations - 1:
                    payload["tools"] = tool_definitions

                response = await client.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {settings.openrouter_api_key}",
                        "Content-Type": "application/json"
                    },
                    json=payload
                )
                response.raise_for_status()
                data = response.json()

            # Track tokens
            usage = data.get("usage", {})
            total_tokens_in += usage.get("prompt_tokens", 0)
            total_tokens_out += usage.get("completion_tokens", 0)

            choice = data["choices"][0]
            message = choice["message"]

            # Check for tool calls
            if message.get("tool_calls"):
                messages.append(message)

                for tool_call in message["tool_calls"]:
                    # Guardrail: check tool call limit
                    max_calls = spec.get("guardrails", {}).get("max_tool_calls_per_run", 50)
                    if len(tool_call_records) >= max_calls:
                        logger.warning(f"Agent {agent_id} hit tool call limit ({max_calls})")
                        messages.append({
                            "role": "tool",
                            "tool_call_id": tool_call["id"],
                            "content": json.dumps({"error": "Tool call limit reached"})
                        })
                        continue

                    fn_name = tool_call["function"]["name"]
                    fn_args = json.loads(tool_call["function"]["arguments"])

                    logger.info(f"Tool call: {fn_name}({fn_args})")

                    # Execute tool
                    if fn_name in TOOLS:
                        tool_fn = TOOLS[fn_name]["function"]
                        result = await tool_fn(db=db, agent_id=agent_id, **fn_args)
                    else:
                        result = {"error": f"Unknown tool: {fn_name}"}

                    # Log tool call
                    tc = ToolCall(
                        id=str(uuid.uuid4()),
                        execution_id=execution_id,
                        tool_id=fn_name,
                        input=fn_args,
                        output=result.get("output", result),
                        duration_ms=result.get("duration_ms", 0)
                    )
                    db.add(tc)
                    tool_call_records.append(tc)

                    # Add tool result to messages
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call["id"],
                        "content": json.dumps(result.get("output", result))
                    })

                continue  # Next iteration with tool results

            else:
                # Final response — no more tool calls
                final_content = message.get("content", "")
                break
        else:
            final_content = message.get("content", "No response generated.")

        # Calculate cost estimate
        # Approximate: $3/M input, $15/M output for Claude 3.5 Sonnet
        cost_estimate = (total_tokens_in * 3 / 1_000_000) + (total_tokens_out * 15 / 1_000_000)

        # Save artifact
        artifact_id = str(uuid.uuid4())
        artifact = Artifact(
            id=artifact_id,
            execution_id=execution_id,
            title=f"{agent.display_name} — {datetime.utcnow().strftime('%Y-%m-%d %H:%M')}",
            content=final_content,
            artifact_type="markdown"
        )
        db.add(artifact)

        # Update memory with key facts from this run
        memory_entry = f"Ran with prompt: '{prompt[:100]}'. Generated artifact. Used {len(tool_call_records)} tool calls."
        append_memory(db, agent_id, memory_entry, "execution")

        # Update execution record
        duration_ms = int((time.time() - start_time) * 1000)
        execution.status = "completed"
        execution.ended_at = datetime.utcnow()
        execution.duration_ms = duration_ms
        execution.tokens_in = total_tokens_in
        execution.tokens_out = total_tokens_out
        execution.cost_estimate_usd = cost_estimate

        db.commit()

        return {
            "execution_id": execution_id,
            "agent_id": str(agent_id),
            "agent_name": agent.name,
            "status": "completed",
            "artifact_id": artifact_id,
            "artifact_content": final_content,
            "duration_ms": duration_ms,
            "tokens_in": total_tokens_in,
            "tokens_out": total_tokens_out,
            "cost_estimate_usd": round(cost_estimate, 6),
            "tool_calls": len(tool_call_records)
        }

    except Exception as e:
        logger.error(f"Execution error for agent {agent_id}: {e}")

        execution.status = "failed"
        execution.ended_at = datetime.utcnow()
        execution.duration_ms = int((time.time() - start_time) * 1000)
        execution.error = str(e)
        db.commit()

        return {
            "execution_id": execution_id,
            "agent_id": str(agent_id),
            "agent_name": agent.name,
            "status": "failed",
            "error": str(e)
        }
