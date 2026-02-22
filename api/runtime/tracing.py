"""
LangWatch integration for agent observability
"""
import os
import logging

logger = logging.getLogger(__name__)

_langwatch_client = None


def get_langwatch_client():
    """Get or initialize LangWatch client"""
    global _langwatch_client
    
    if _langwatch_client is not None:
        return _langwatch_client
    
    try:
        import langwatch
        settings = get_settings()
        
        if settings.langwatch_api_key:
            langwatch.api_key = settings.langwatch_api_key
            _langwatch_client = langwatch
            logger.info("LangWatch initialized")
        else:
            logger.info("LangWatch API key not set, skipping")
            
    except ImportError:
        logger.warning("langwatch not installed, skipping")
    except Exception as e:
        logger.warning(f"Failed to initialize LangWatch: {e}")
    
    return _langwatch_client


def trace_agent_run(agent_name: str, prompt: str, result: dict):
    """Trace an agent execution"""
    client = get_langwatch_client()
    
    if not client:
        return
    
    try:
        # Simple trace - just log the key events
        client.trace(
            name=f"agent_run_{agent_name}",
            metadata={
                "agent": agent_name,
                "prompt": prompt[:200],  # Truncate for logging
                "status": result.get("status"),
                "duration_ms": result.get("duration_ms"),
                "cost_usd": result.get("cost_estimate_usd"),
                "tool_calls": result.get("tool_calls", 0)
            }
        )
    except Exception as e:
        logger.warning(f"Failed to trace: {e}")


def trace_tool_call(agent_name: str, tool_name: str, input_data: dict, output_data: dict):
    """Trace a tool call"""
    client = get_langwatch_client()
    
    if not client:
        return
    
    try:
        client.trace(
            name=f"tool_call_{tool_name}",
            metadata={
                "agent": agent_name,
                "tool": tool_name,
                "input": str(input_data)[:100],
                "output": str(output_data)[:100]
            }
        )
    except Exception as e:
        logger.warning(f"Failed to trace tool: {e}")
