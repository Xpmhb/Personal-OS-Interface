"""
System prompt builder for agent execution
"""


def build_system_prompt(spec: dict, memory_summary: str = "", available_tools: list = None) -> str:
    """Build the system prompt from agent spec"""

    role = spec.get("role_definition", "You are an AI assistant.")
    capabilities = spec.get("capabilities", [])
    tools = available_tools or []

    prompt = f"""{role}

## RULES
- When citing internal data, use format: [file_id:chunk_id]
- If you cannot find relevant internal data, say: "Insufficient internal data for this query."
- Stay within your defined capabilities: {', '.join(capabilities)}
- Be concise, actionable, and cite your sources

## CAPABILITIES
{chr(10).join(f'- {cap}' for cap in capabilities)}

## AVAILABLE TOOLS
{chr(10).join(f'- {tool}' for tool in tools) if tools else '- No tools available'}

## MEMORY (Previous Context)
{memory_summary if memory_summary else 'No prior memory.'}

## OUTPUT FORMAT
Provide your analysis as a structured markdown document with:
1. Executive Summary (2-3 sentences)
2. Key Findings
3. Recommendations
4. Sources (cite file_id:chunk_id where applicable)
"""
    return prompt.strip()


def build_morning_brief_prompt(sub_artifacts: dict) -> str:
    """Build the CEO synthesis prompt for Morning Brief"""

    return f"""Synthesize the following department reports into a unified Morning Brief.

## CFO Report
{sub_artifacts.get('cfo', 'No CFO report available.')}

## COO Report
{sub_artifacts.get('coo', 'No COO report available.')}

## CTO Report
{sub_artifacts.get('cto', 'No CTO report available.')}

## OUTPUT FORMAT
# Morning Brief — {{date}}

## Executive Summary
(3-5 sentences synthesizing all reports)

## Key Decisions Needed
(Bulleted list of items requiring human decision)

## Today's Priorities
(Ordered list, highest impact first)

## Risk Flags
(Any concerns or anomalies flagged by department heads)

## Department Summaries
(Brief 2-3 sentence summary per department)
"""
