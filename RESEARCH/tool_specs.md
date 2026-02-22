# Executive Agent Tool Specifications
## Required Tools for Digital Twin Functionality

---

## CEO Agent Tools

### Required
| Tool | Capability | Purpose |
|------|------------|---------|
| `calendar_read` | Read calendar | Schedule visibility |
| `email_summary` | Summarize inbox | Priority emails |
| `file_search` | RAG search | Company docs |
| `slack_read` | Read channels | Team activity |
| `metrics_query` | SQL queries | KPIs |

### Optional
| Tool | Capability | Purpose |
|------|------------|---------|
| `web_search` | Brave/Tavily | Market research |
| `github_read` | Repo activity | Engineering status |
| `notion_read` | Wiki access | Company knowledge |

---

## CFO Agent Tools

### Required
| Tool | Capability | Purpose |
|------|------------|---------|
| `financial_query` | SQL + metrics | Financial data |
| `quickbooks_read` | QB API | Real financials |
| `plaid_read` | Bank connections | Cash flow |
| `file_search` | RAG | Financial docs |
| `anomaly_detect` | Pattern analysis | Flag issues |

### Optional
| Tool | Capability | Purpose |
|------|------------|---------|
| `expense_review` | Receipt scanning | Expense approval |
| `revenue_tracking` | Revenue analytics | MRR tracking |

---

## CTO Agent Tools

### Required
| Tool | Capability | Purpose |
|------|------------|---------|
| `github_read` | PR/issue status | Engineering status |
| `file_search` | Tech docs | Architecture docs |
| `metrics_query` | System metrics | Uptime/performance |
| `aws_read` | Cloud resources | Infrastructure |
| `log_search` | Error logs | Debugging |

### Optional
| Tool | Capability | Purpose |
|------|------------|---------|
| `code_review` | PR analysis | Code quality |
| `security_scan` | Vulnerability scan | Security |

---

## COO Agent Tools

### Required
| Tool | Capability | Purpose |
|------|------------|---------|
| `project_read` | Project status | Task tracking |
| `slack_read` | Team channels | Activity |
| `calendar_read` | Meetings | Schedule |
| `metrics_query` | Ops metrics | Performance |
| `file_search` | SOPs, workflows | Procedures |

### Optional
| Tool | Capability | Purpose |
|------|------------|---------|
| `crm_read` | Pipeline | Sales ops |
| `support_read` | Ticket queue | Support load |

---

## Tool Implementation Specs

### calendar_read
```python
async def calendar_read(
    days_ahead: int = 7,
    calendar_id: str = "primary"
) -> list[dict]:
    """Read upcoming calendar events"""
    # Uses Google Calendar API
    # Returns: [{title, time, attendees, location}]
```

### slack_read
```python
async def slack_read(
    channel: str,
    limit: int = 50
) -> list[dict]:
    """Read recent messages from Slack channel"""
    # Uses Slack API
    # Returns: [{user, text, timestamp, thread}]
```

### email_summary
```python
async def email_summary(
    query: str = "is:unread",
    limit: int = 10
) -> dict:
    """Summarize recent emails"""
    # Uses Gmail API
    # Returns: {count, summaries, priorities}
```

### financial_query
```python
async def financial_query(
    query: str,  # Natural language
    tables: list[str] = ["metrics", "financial_data"]
) -> dict:
    """Query financial data"""
    # Uses SQL + semantic search
    # Returns: {results, sources}
```

### github_read
```python
async def github_read(
    repo: str,
    type: str = "prs",  # prs, issues, commits
    limit: int = 10
) -> list[dict]:
    """Read GitHub activity"""
    # Uses GitHub API
    # Returns: [{title, status, author, time}]
```

---

## Tool Permissions Matrix

| Tool | CEO | CFO | CTO | COO |
|------|-----|-----|-----|-----|
| calendar_read | ✅ | ✅ | ✅ | ✅ |
| email_summary | ✅ | ⚠️ | ⚠️ | ❌ |
| slack_read | ✅ | ⚠️ | ✅ | ✅ |
| file_search | ✅ | ✅ | ✅ | ✅ |
| metrics_query | ✅ | ✅ | ✅ | ✅ |
| financial_query | ⚠️ | ✅ | ❌ | ⚠️ |
| quickbooks_read | ❌ | ✅ | ❌ | ❌ |
| github_read | ⚠️ | ❌ | ✅ | ⚠️ |
| project_read | ⚠️ | ❌ | ⚠️ | ✅ |

Legend: ✅ Full | ⚠️ Limited | ❌ None

---

## Implementation Priority

### Phase 1 (MVP-0.2)
1. `calendar_read` — All agents
2. `file_search` — Already done
3. `metrics_query` — Already done
4. `sql_query` — Already done

### Phase 2
1. `slack_read` — CEO, CTO, COO
2. `github_read` — CTO
3. `email_summary` — CEO

### Phase 3
1. `financial_query` — CFO
2. `quickbooks_read` — CFO
3. `project_read` — COO
