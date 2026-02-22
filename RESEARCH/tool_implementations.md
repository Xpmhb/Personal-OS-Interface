# Executive Agent Tool Implementations
## Production-Grade Tool Code

---

## 1. File Search Tool

```python
class FileSearchTool:
    """Search company documents using vector search"""
    
    def __init__(self, qdrant_client, embedding_service):
        self.qdrant = qdrant_client
        self.embed = embedding_service
    
    async def search(
        self,
        query: str,
        agent_id: str,
        namespace: str = None,
        limit: int = 5
    ) -> list[dict]:
        # 1. Embed query
        query_vector = await self.embed(query)
        
        # 2. Get agent permissions
        namespaces = get_agent_namespaces(agent_id)
        
        # 3. Filter by allowed namespaces
        if namespace and namespace not in namespaces:
            return {"error": "Permission denied", "code": "FORBIDDEN"}
        
        search_namespaces = [namespace] if namespace else namespaces
        
        # 4. Search Qdrant
        results = self.qdrant.search(
            collection_name="agent_documents",
            query_vector=query_vector,
            query_filter=self._build_filter(search_namespaces),
            limit=limit
        )
        
        # 5. Format with citations
        formatted = []
        for r in results:
            formatted.append({
                "content": r.payload["chunk_text"],
                "source": f"[{r.payload['file_id']}:{r.payload['chunk_index']}]",
                "filename": r.payload.get("filename"),
                "score": r.score
            })
        
        return {"results": formatted, "count": len(formatted)}
```

---

## 2. SQL Query Tool

```python
class SQLQueryTool:
    """Execute read-only SQL queries"""
    
    def __init__(self, db_session):
        self.db = db_session
        self.allowed_tables = ["metrics", "financial_data", "operations"]
    
    async def query(
        self,
        agent_id: str,
        query: str,
        max_rows: int = 100
    ) -> dict:
        # 1. Parse table from query
        table = self._extract_table(query)
        
        # 2. Check permissions
        if not self._has_permission(agent_id, table):
            return {"error": f"Permission denied for table {table}"}
        
        # 3. Validate query (whitelist only)
        if not self._is_safe_query(query):
            return {"error": "Query not allowed"}
        
        # 4. Execute (read-only)
        try:
            result = self.db.execute(text(query).limit(max_rows))
            rows = [dict(row._mapping) for row in result]
            return {"results": rows, "count": len(rows)}
        except Exception as e:
            return {"error": str(e)}
```

---

## 3. Calendar Tool

```python
class CalendarReadTool:
    """Read Google Calendar events"""
    
    def __init__(self, google_creds):
        self.creds = google_creds
        self.service = build("calendar", "v3", credentials=creds)
    
    async def read(
        self,
        days_ahead: int = 7,
        calendar_id: str = "primary"
    ) -> list[dict]:
        # Get time range
        now = datetime.utcnow()
        end = now + timedelta(days=days_ahead)
        
        events = self.service.events().list(
            calendarId=calendar_id,
            timeMin=now.isoformat() + "Z",
            timeMax=end.isoformat() + "Z",
            singleEvents=True,
            orderBy="startTime"
        ).execute()
        
        return [
            {
                "title": e["summary"],
                "start": e["start"].get("dateTime", e["start"].get("date")),
                "end": e["end"].get("dateTime", e["end"].get("date")),
                "attendees": [a.get("email") for a in e.get("attendees", [])],
                "location": e.get("location"),
                "description": e.get("description")
            }
            for e in events.get("items", [])
        ]
```

---

## 4. Slack Read Tool

```python
class SlackReadTool:
    """Read Slack channel messages"""
    
    def __init__(self, bot_token):
        self.client = WebClient(token=bot_token)
    
    async def read(
        self,
        channel: str,
        limit: int = 50
    ) -> list[dict]:
        # Get channel ID from name
        channel_id = self._resolve_channel(channel)
        
        # Fetch messages
        result = self.client.conversations_history(
            channel=channel_id,
            limit=limit
        )
        
        return [
            {
                "user": m.get("user"),
                "text": m.get("text"),
                "ts": m.get("ts"),
                "thread_ts": m.get("thread_ts"),
                "reactions": m.get("reactions", [])
            }
            for m in result["messages"]
        ]
```

---

## 5. GitHub Tool

```python
class GitHubReadTool:
    """Read GitHub activity"""
    
    def __init__(self, token, repo: str):
        self.github = Github(token)
        self.repo = repo
    
    async def get_prs(self, state: str = "open", limit: int = 10):
        repo = self.github.get_repo(self.repo)
        prs = repo.get_pulls(state=state)
        
        return [
            {
                "number": pr.number,
                "title": pr.title,
                "state": pr.state,
                "author": pr.user.login,
                "created_at": pr.created_at.isoformat(),
                "labels": [l.name for l in pr.labels]
            }
            for pr in prs[:limit]
        ]
    
    async def get_issues(self, state: str = "open", limit: int = 10):
        repo = self.github.get_repo(self.repo)
        issues = repo.get_issues(state=state)
        
        return [
            {
                "number": issue.number,
                "title": issue.title,
                "state": issue.state,
                "author": issue.user.login,
                "labels": [l.name for l in issue.labels]
            }
            for issue in issues[:limit]
        ]
```

---

## 6. Email Summary Tool

```python
class EmailSummaryTool:
    """Summarize Gmail inbox"""
    
    def __init__(self, google_creds):
        self.creds = google_creds
        self.service = build("gmail", "v1", credentials=creds)
    
    async def summarize(
        self,
        query: str = "is:unread",
        limit: int = 10
    ) -> dict:
        # Get messages
        results = self.service.users().messages().list(
            userId="me",
            q=query,
            maxResults=limit
        ).execute()
        
        messages = []
        for msg_id in results.get("messages", []):
            msg = self.service.users().messages().get(
                userId="me",
                id=msg_id["id"]
            ).execute()
            
            messages.append({
                "id": msg["id"],
                "subject": self._get_header(msg, "Subject"),
                "from": self._get_header(msg, "From"),
                "date": self._get_header(msg, "Date"),
                "snippet": msg["snippet"]
            })
        
        return {
            "count": len(messages),
            "messages": messages
        }
```

---

## Tool Permission Matrix

| Tool | CEO | CFO | CTO | COO |
|------|-----|-----|-----|-----|
| file_search | ✅ | ✅ | ✅ | ✅ |
| sql_query | ✅ | ✅ | ✅ | ✅ |
| calendar_read | ✅ | ✅ | ✅ | ✅ |
| slack_read | ✅ | ⚠️ | ✅ | ✅ |
| email_summary | ✅ | ❌ | ❌ | ❌ |
| github_read | ⚠️ | ❌ | ✅ | ⚠️ |
| financial_query | ⚠️ | ✅ | ❌ | ⚠️ |
| project_read | ⚠️ | ❌ | ⚠️ | ✅ |

Legend: ✅ Full | ⚠️ Limited | ❌ None
