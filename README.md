# Hermes Chief-of-Staff Workspace

Hermes is a **source-grounded operating system for delegated work**. It turns a request into a durable work object with a defined outcome, evidence, a decision record, an editable plan, narrowly scoped approvals, and action receipts.

The initial product flow is intentionally controlled:

> **`@Hermes` in ClickUp → scoped research → evidence-backed plan → explicit approval → verified receipt.**

## What Is Implemented

| Capability | Status | Description |
|---|---|---|
| **Command center** | Ready | A polished workspace for active delegations, plans, evidence, approval decisions, activity, and integration health. |
| **Durable work objects** | Ready | The FastAPI control plane persists objectives, completion tests, authority lanes, source scope, evidence, decisions, plans, approvals, and receipts. |
| **Action approval flow** | Ready | Each consequential operation receives a typed, expiring, action-specific approval record. |
| **Receipt ledger** | Ready | Completed actions can be linked to their approval and recorded with an external identifier, URL, and compensation hint. |
| **ClickUp inbound delegation** | Ready for activation | A signed webhook handler verifies `X-Signature`, deduplicates retries, accepts explicit `@Hermes` task-comment requests, and creates draft-only work objects. |
| **Hermes and Cognee configuration** | Scaffolded | Private-service configuration is documented and surfaced in the workspace; live credentials and containers are the next activation step. |
| **Otter evidence** | Connected at platform level | Planned as a read-only source for meeting commitments and decision evidence. |

## Architecture

| Layer | Responsibility |
|---|---|
| **React command center** | Displays the delegation ledger, plan, evidence, approvals, activity stream, integration health, and proactive planning queue. |
| **FastAPI control plane** | Owns the authoritative work-object, policy-visible approval, event, and action-receipt data. |
| **Hermes Agent** | Will provide private, tool-enabled reasoning and streamed run progress. It does not become the system of record. |
| **Cognee** | Will provide source-aware durable memory through a private backend integration. |
| **ClickUp webhook** | Converts a signed, explicit `@Hermes` task comment into a reviewable draft-only delegation. |
| **PostgreSQL** | Production store for the control plane. SQLite is used automatically for a local smoke test when no database URL is supplied. |

## Local Development

### 1. Configure the front end

```bash
npm install
cp .env.example .env
```

For a local backend started on port `8001`, add this to `.env.local`:

```bash
VITE_API_BASE_URL=http://127.0.0.1:8001/api
```

Start the front end:

```bash
npm run dev
```

### 2. Configure and start the API

Install the Python dependencies from the API directory:

```bash
cd api
sudo uv pip install --system -r requirements.txt
```

Then start the API:

```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

The local API creates a demonstration work object at startup. Open the command center at the Vite URL to inspect it.

## ClickUp Delegation Activation

The confirmed first pilot is **Hunter’s Dojo → Live MVP Test Sprint** (`901415896119`). The webhook receiver is present at:

```text
POST /api/integrations/clickup/webhook
```

ClickUp signs each payload with HMAC-SHA256 and sends the hexadecimal digest in `X-Signature`. The receiver rejects unsigned or forged traffic, records a delivery key before processing, and ignores retried deliveries. A `taskCommentPosted` event containing `@Hermes` creates a **draft-only** work object; it does not create or update a ClickUp task.

| Activation step | Owner | Why it is required |
|---|---|---|
| Re-authorize ClickUp | User | The existing ClickUp connection needs renewal before live delegation can access real workspace content. |
| Create a ClickUp webhook for Hunter’s Dojo → Live MVP Test Sprint | User with Hermes guidance | ClickUp returns a unique webhook secret when it creates the webhook. |
| Store `CLICKUP_WEBHOOK_SECRET` in the production secret store | User or deployment administrator | Enables server-side signature verification without exposing the secret to the browser. |
| Expose the endpoint over authenticated HTTPS | Deployment | ClickUp needs a reachable callback URL; Hermes, Cognee, and the database remain private. |
| Run one explicitly approved pilot | User and Hermes | Validates evidence, planning, approval, idempotency, and the resulting action receipt before standing authority is considered. |

## Environment Configuration

Use `.env.example` as the template. Never place a production token in source control.

| Variable | Purpose |
|---|---|
| `HERMES_API_BASE_URL` and `HERMES_API_KEY` | Private Hermes Agent access. |
| `COGNEE_BASE_URL` and `COGNEE_API_KEY` | Private Cognee memory access. |
| `CLICKUP_WEBHOOK_SECRET` | Verifies signed inbound ClickUp webhook deliveries. |
| `HERMES_CLICKUP_MENTION` | The explicit delegation mention; defaults to `@Hermes`. |
| `POSTGRES_URL` | Production control-plane database. |

## Authority Model

Hermes is designed to operate autonomously on research, synthesis, plan drafts, source capture, monitoring, and proactive issue detection **within the source scope of a work object**. Its initial ClickUp authority is **draft-only**. Any external write needs an action-specific approval that states the exact operation, target system, effect, risk class, and expiry.

The system should not receive standing authority for credentials, access management, destructive changes, communications with material consequences, time-entry approval, accounting entries, payments, banking operations, or tax-related actions.

## Validation Completed

The current implementation has been locally verified for front-end production compilation, API startup, durable work-object creation, workspace-dashboard retrieval, signed ClickUp delegation creation, duplicate webhook delivery handling, and the approval-to-action-receipt lifecycle. See [`BUILD_VALIDATION_NOTES.md`](BUILD_VALIDATION_NOTES.md) for the local validation record.

## Production Container Topology

The repository now includes `Dockerfile.web`, `deploy/nginx.conf`, and `docker-compose.prod.yml`. The production overlay places the React interface behind a same-origin Nginx edge. The browser calls `/api`; Nginx forwards those requests to the private FastAPI service. PostgreSQL, Qdrant, the API, and worker have no public host ports in the overlay.

Start the production-shaped local stack with:

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml up --build -d
```

For the preferred Google Cloud deployment, run this stack on a private Compute Engine VM behind HTTPS, store environment variables in Secret Manager or an equivalent server-side secret service, and expose only the authenticated web edge. The future public ClickUp callback should terminate at the same HTTPS edge and proxy only `/api/integrations/clickup/webhook` to the private API.
