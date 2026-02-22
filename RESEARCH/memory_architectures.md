# Memory Architectures for AI Agents
## Research Summary

Based on academic research (Generative Agents, MemGPT, ReAct) and industry best practices:

---

## Memory Types

### 1. Sensory Memory (Immediate)
- Current conversation context
- Last N messages (configurable)
- Token budget: ~4k tokens

### 2. Working Memory (Short-term)
- Current task context
- Recent tool call results
- Retrieved documents

### 3. Long-term Memory (Persistent)
- Agent's accumulated knowledge
- Past interactions
- Key decisions and facts
- Stored in database (Postgres)

---

## Memory Operations

### Retrieval
```
Query: "What did we decide about pricing?"
Process:
1. Search memory for "pricing", "decisions"
2. Retrieve top K most relevant memories
3. Inject into context as context
```

### Storage (Append-only)
```
New Information: "Decided to price at $99/month"
Process:
1. Generate embedding
2. Store in memories table with:
   - content: "Decided to price at $99/month"
   - memory_type: "fact" | "decision" | "insight"
   - created_at: timestamp
   - embedding_id: vector reference
```

### Summarization (Compaction)
```
Trigger: When memory exceeds max_tokens
Process:
1. Retrieve oldest N memories
2. Summarize into condensed form
3. Delete old entries
4. Store summary as new entry
```

---

## Implementation Patterns

### Pattern 1: Simple Append
```python
# Every interaction appends to memory
memory.append(f"User asked: {prompt}")
memory.append(f"Agent responded: {response}")
```
**Pros:** Simple, complete history
**Cons:** Token limit hit quickly

### Pattern 2: Summarize + Retrieve
```python
# On each run:
1. Retrieve relevant memories (vector search)
2. Summarize old memories periodically
3. Keep only recent + high-signal
```
**Pros:** Scales, maintains relevance
**Cons:** Some information loss

### Pattern 3: Hierarchical (MemGPT-style)
```
Level 1: Recent conversation (in-context)
Level 2: Recent summaries (retrieved)
Level 3: Full history (archived)
```
**Pros:** Best of both worlds
**Cons:** Complex implementation

---

## For MVP-0.1

Current implementation uses **Pattern 2** (summarize + retrieve):

```python
# Get memory
memories = query(limit=max_tokens)
summary = summarize(memories)
context = f"MEMORY:\n{summary}"

# After run
append_memory(f"Ran: {prompt[:100]}. Result: {artifact_id}")

# Periodic compaction
if len(memories) > max_entries:
    summarize_old_memories()
```

---

## Research Sources

1. **Generative Agents** (Stanford, 2023)
   - Simulated believable human behavior with memory architecture
   - Key: reflection mechanism to summarize and generalize

2. **MemGPT** (2024)
   - Hierarchical memory management for LLMs
   - Key: paging mechanism between context and storage

3. **ReAct** (2023)
   - Combines reasoning + acting
   - Key: tool use updates working memory

---

## Recommended Improvements for v0.2

1. **Add embeddings to memory table**
   - Enable semantic search over memories

2. **Memory types**
   - Distinguish facts, decisions, insights
   - Different retention for each

3. **Reflection mechanism**
   - Periodically summarize and generalize
   - Extract patterns from interactions

4. **Importance scoring**
   - Weight memories by importance
   - Always keep high-signal memories
