# XPM Jarvis

**XPM Jarvis** is the governed operational intelligence and execution layer for XP Marketing and its client tenants. It turns a delegated objective into a durable work object with a defined outcome, source-grounded evidence, an editable plan, narrowly scoped approvals, and verified action receipts.

Jarvis is the **product and control plane**. The Hermes agent remains a private reasoning/runtime adapter, and Cognee remains a private memory adapter; neither replaces the authoritative work, policy, and audit state maintained by XPM Jarvis.

> **`@Jarvis` in ClickUp → scoped research → evidence-backed plan → explicit approval → verified receipt.**

## Product role in the XPM platform

| Platform component | Responsibility | Jarvis relationship |
|---|---|---|
| **XPM Jarvis** | Internal operations, plans, approvals, agent actions, and action receipts | The governed execution control plane |
| **XPM Client Portal** | Client requests, content approvals, calendars, and client-safe outcomes | Will expose the approved tenant-facing subset of Jarvis state |
| **XPM Integrator** | Ingestion and normalization from Clockify, GoHighLevel, QuickBooks, ClickUp, and other sources | Produces governed, tenant-scoped context packages for Jarvis |
| **XPM Agentic OS** | Engineering rules, evaluation gates, templates, and incident learning | Governs how all platform repositories are built and changed |
| **Hermes runtime** | Private tool-enabled reasoning and execution orchestration | Internal adapter; never the system of record |
| **Cognee** | Source-aware durable memory | Internal adapter; never the source of tenant permissions |

## What is implemented

| Capability | Status | Description |
|---|---|---|
| **Command center** | Ready | An operator workspace for delegations, plans, evidence, approval decisions, activity, and integration health. |
| **Durable work objects** | Ready | The FastAPI control plane persists objectives, completion tests, authority lanes, source scope, evidence, decisions, plans, approvals, and receipts. |
| **Action approval flow** | Ready | Each consequential operation receives a typed, expiring, action-specific approval record. |
| **Receipt ledger** | Ready | Completed actions can be linked to an approval and recorded with an external identifier, URL, and compensation hint. |
| **ClickUp inbound delegation** | Ready for activation | A signed webhook handler verifies `X-Signature`, deduplicates retries, accepts explicit `@Jarvis` task-comment requests, and creates draft-only work objects. |
| **Hermes and Cognee runtime configuration** | Scaffolded | Private-service configuration is documented and surfaced in the workspace; live credentials and containers are the next activation step. |
| **Otter evidence** | Connected at platform level | Planned as a read-only source for meeting commitments and decision evidence. |

## Architecture

| Layer | Responsibility |
|---|---|
| **React command center** | Displays the delegation ledger, plan, evidence, approvals, activity stream, integration health, and proactive planning queue. |
| **FastAPI control plane** | Owns authoritative work-object, policy-visible approval, event, and action-receipt data. |
| **Jarvis runtime adapter** | Will provide private, tool-enabled reasoning and streamed run progress through the Hermes runtime. It does not become the system of record. |
| **Cognee** | Will provide source-aware durable memory through a private backend integration. |
| **ClickUp webhook** | Converts a signed, explicit `@Jarvis` task comment into a reviewable draft-only delegation. |
| **PostgreSQL** | Production store for the control plane. SQLite is used automatically for a local smoke test when no database URL is supplied. |

## Local development

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

## ClickUp delegation activation

The confirmed first pilot is **Hunter’s Dojo → Live MVP Test Sprint** (`901415896119`). The webhook receiver is available at:

```text
POST /api/integrations/clickup/webhook
```

ClickUp signs each payload with HMAC-SHA256 and sends the hexadecimal digest in `X-Signature`. The receiver rejects unsigned or forged traffic, records a delivery key before processing, and ignores retried deliveries. A `taskCommentPosted` event containing `@Jarvis` creates a **draft-only** work object; it does not create or update a ClickUp task.

| Activation step | Owner | Why it is required |
|---|---|---|
| Re-authorize ClickUp | User | The existing ClickUp connection needs renewal before live delegation can access real workspace content. |
| Create a ClickUp webhook for Hunter’s Dojo → Live MVP Test Sprint | User with Jarvis guidance | ClickUp returns a unique webhook secret when it creates the webhook. |
| Store `CLICKUP_WEBHOOK_SECRET` in the production secret store | User or deployment administrator | Enables server-side signature verification without exposing the secret to the browser. |
| Expose the endpoint over authenticated HTTPS | Deployment | ClickUp needs a reachable callback URL; Jarvis, Cognee, and the database remain private. |
| Run one explicitly approved pilot | User and XPM Jarvis | Validates evidence, planning, approval, idempotency, and the resulting action receipt before standing authority is considered. |

## Environment configuration

Use `.env.example` as the template. Never place a production token in source control.

| Variable | Purpose |
|---|---|
| `HERMES_API_BASE_URL` and `HERMES_API_KEY` | Private Hermes runtime adapter access. |
| `COGNEE_BASE_URL` and `COGNEE_API_KEY` | Private Cognee memory adapter access. |
| `CLICKUP_WEBHOOK_SECRET` | Verifies signed inbound ClickUp webhook deliveries. |
| `JARVIS_CLICKUP_MENTION` | The explicit delegation trigger; defaults to `@Jarvis`. |
| `POSTGRES_URL` | Production control-plane database. |

## Authority model

XPM Jarvis may operate autonomously on research, synthesis, plan drafts, source capture, monitoring, and proactive issue detection **within the source scope and tenant boundary of a work object**. Its initial ClickUp authority is **draft-only**. Any external write needs an action-specific approval that states the exact operation, target system, effect, risk class, and expiry.

The system should not receive standing authority for credentials, access management, destructive changes, communications with material consequences, time-entry approval, accounting entries, payments, banking operations, tax-related actions, or cross-tenant data access.

## Production container topology

The repository includes `Dockerfile.web`, `deploy/nginx.conf`, and `docker-compose.prod.yml`. The production overlay places the React interface behind a same-origin Nginx edge. The browser calls `/api`; Nginx forwards those requests to the private FastAPI service. PostgreSQL, Qdrant, the API, and worker have no public host ports in the overlay.

Start the production-shaped local stack with:

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml up --build -d
```

For the preferred Google Cloud deployment, run this stack on a private Compute Engine VM behind HTTPS, store environment variables in Secret Manager or an equivalent server-side secret service, and expose only the authenticated web edge. The public ClickUp callback should terminate at the same HTTPS edge and proxy only `/api/integrations/clickup/webhook` to the private API.

## Platform direction

XPM Jarvis is not a standalone personal assistant. It is the XPM operating brain: the **control plane** for internal agency operations and tenant-scoped client work. The platform uses shared tenant and event contracts to connect the XPM Client Portal, XPM Integrator, and XPM Agentic OS without forcing an immediate codebase merge. See the companion unified platform architecture plan for the migration sequence.
