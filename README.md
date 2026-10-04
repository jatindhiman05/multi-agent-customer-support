# VoltNest

**Production-oriented multi-agent customer support platform with safe AI-driven workflows, authenticated commerce operations, RAG, real-time streaming, and deterministic action execution.**

VoltNest explores a practical question:

> How do you let an LLM reason about real customer-support workflows without giving it uncontrolled access to application state?

The system combines **LangGraph**, **FastAPI**, **PostgreSQL/pgvector**, and a **Next.js** customer application to support conversational assistance, order tracking, payments, returns, cancellations, product/policy questions, and human escalation.

The core engineering principle is:

> **LLMs interpret and reason. Application code authorizes and executes.**

---

## Live Demo

**Frontend**

https://multi-agent-customer-support-nine.vercel.app/

The frontend is deployed on Vercel and communicates with the FastAPI backend through a server-side BFF layer.

---

## What VoltNest Supports

VoltNest currently provides:

- multi-turn customer-support conversations
- authenticated customer sessions
- customer-specific order history
- order details and shipment tracking
- payment and refund status
- return eligibility and return creation
- order cancellation with automatic eligible refunds
- product, warranty, shipping, and policy questions through RAG
- human-support escalation and support-ticket creation
- structured confirmation flows for state-changing actions
- persistent conversation history
- conversation deletion
- real-time response streaming
- safe retry and request replay handling
- structured customer-facing UI cards
- request tracing and structured application logs
- automated backend/frontend CI
- automated agent-routing evaluation

---

# Architecture

```text
                              Customer
                                 │
                                 ▼
                     ┌───────────────────────┐
                     │   Next.js Frontend    │
                     │   React / TypeScript  │
                     └───────────┬───────────┘
                                 │
                         Server-side BFF
                                 │
                                 ▼
                     ┌───────────────────────┐
                     │        FastAPI        │
                     │ Auth / Rate Limiting  │
                     │ Request Context       │
                     └───────────┬───────────┘
                                 │
                                 ▼
                     ┌───────────────────────┐
                     │   Chat Service Layer  │
                     │ Idempotency / Retry   │
                     │ Conversation Storage  │
                     └───────────┬───────────┘
                                 │
                                 ▼
                     ┌───────────────────────┐
                     │      LangGraph        │
                     │      Supervisor       │
                     └───────────┬───────────┘
                                 │
        ┌────────────┬───────────┼───────────┬────────────┐
        │            │           │           │            │
        ▼            ▼           ▼           ▼            ▼
     Orders       Payments     Returns   Cancellation   Knowledge
        │            │           │           │            │
        │            │           │           │            ▼
        │            │           │           │       RAG Pipeline
        │            │           │           │            │
        └────────────┴─────┬─────┴───────────┘            ▼
                           │                            pgvector
                           ▼                               │
                         Tools                             ▼
                           │                         Cross-Encoder
                           ▼                               │
                       Services                            ▼
                           │                         Grounded LLM
                           ▼
                     Repositories
                           │
                           ▼
                      PostgreSQL
```

The LLM orchestration layer never receives unrestricted database access.

---

# Agent System

A structured-output supervisor routes each customer message to the appropriate capability:

```text
Customer Message
       │
       ▼
   Supervisor
       │
       ├── conversation
       ├── order
       ├── payment
       ├── returns
       ├── cancellation
       ├── knowledge
       └── escalation
```

Conversation history is included when routing, allowing contextual follow-ups such as:

```text
Customer: Where is ORD-1003?
Assistant: ORD-1003 is currently in transit.
Customer: When will it arrive?
```

The final message still routes to the order workflow even though the order number was omitted.

The supervisor uses structured output rather than parsing free-form model text.

---

# AI / Application Boundary

VoltNest intentionally separates reasoning from business logic.

Operational capabilities follow:

```text
Agent
  │
  ▼
Bounded Tool
  │
  ▼
Service
  │
  ▼
Repository
  │
  ▼
PostgreSQL
```

Responsibilities are separated:

| Layer | Responsibility |
|---|---|
| Agent | Understand language and choose capabilities |
| Tool | Expose a narrow application operation |
| Service | Enforce business rules |
| Repository | Perform persistence operations |
| PostgreSQL | Remain the operational source of truth |

Customer identity is supplied from trusted authentication context rather than model-generated arguments.

---

# Safe State-Changing Actions

Returns and cancellations are not executed directly from an LLM tool call.

They use a confirmation boundary:

```text
Customer requests destructive action
              │
              ▼
      Validate resource ownership
              │
              ▼
       Check business rules
              │
              ▼
        PendingAction
              │
              ▼
      Confirmation required
         │            │
      Reject        Confirm
         │            │
         ▼            ▼
     No mutation   Action Executor
                       │
                       ▼
                Re-check eligibility
                       │
                       ▼
               Database transaction
```

For cancellation, the LLM can identify the request and invoke the **read-only eligibility capability**, but application code deterministically creates the pending action once eligibility has been established.

The actual cancellation path re-checks eligibility during execution while holding the relevant database lock.

This means an LLM cannot directly convert:

```text
"Cancel my order"
```

into a database mutation.

---

# Retrieval-Augmented Generation

Static support knowledge and live operational data are intentionally separated.

For example:

```text
"What is the warranty on the wireless earbuds?"
```

uses RAG.

```text
"Where is ORD-1003?"
```

uses authenticated operational data.

The knowledge pipeline is:

```text
Support Documents
       │
       ▼
    Chunking
       │
       ▼
BGE Embeddings
       │
       ▼
PostgreSQL + pgvector
       │
       ▼
Candidate Retrieval
       │
       ▼
Cross-Encoder Reranking
       │
       ▼
Relevant Context
       │
       ▼
Grounded Generation
```

This prevents static documents from being treated as the source of truth for live customer state.

---

# Real-Time Response Streaming

VoltNest exposes both regular and streaming chat endpoints.

```text
POST /chat
POST /chat/stream
```

The streaming path emits incremental response events while preserving the same backend orchestration and persistence boundaries.

Request context is propagated into the streaming worker so logs generated during asynchronous response processing retain the original request and conversation identifiers.

---

# Reliable Chat Execution

Chat requests carry a unique request ID.

The backend maintains request state so retries do not blindly duplicate work:

```text
processing
    │
    ├── success ──► completed
    │
    └── failure ──► failed
                       │
                       ▼
                     retry
```

The system includes:

- request hashing
- idempotent replay of completed requests
- conflicting request-ID detection
- in-progress request detection
- failed-request retry
- stale-processing request recovery
- atomic request initialization
- conversation reuse during retries

The frontend retry flow reuses the original request ID so a transient failure does not create duplicate customer messages or duplicate operations.

---

# Structured UI

Agents do not generate arbitrary frontend components.

The backend exposes trusted structured UI metadata such as:

```text
order_list
order_status
order_details
payment_status
confirmation
return_result
cancellation_result
support_ticket
```

The frontend renders these payloads into customer-facing components.

This keeps presentation deterministic and avoids parsing LLM prose to decide application UI behavior.

---

# Authentication and Authorization

Customer-specific endpoints derive identity from authenticated application context.

```text
JWT
 │
 ▼
Authenticated Customer ID
 │
 ▼
Service
 │
 ▼
Ownership-aware query
 │
 ▼
Customer resource
```

The browser cannot choose another customer's internal ID when requesting operational data.

Authorization regression testing verifies that one customer cannot retrieve another customer's orders or conversations.

Additional protections include:

- password hashing
- JWT expiry
- role validation
- login rate limiting
- chat rate limiting
- HttpOnly frontend session cookies
- production `Secure` cookies
- `SameSite=Lax`
- explicit CORS configuration

---

# Observability

VoltNest emits structured application logs for important execution boundaries.

Examples include:

```text
request.started
request.completed
chat.started
chat.completed
route.selected
agent.started
agent.completed
chat.retry_started
chat.stale_request_reclaimed
```

Request IDs and conversation IDs are propagated through the execution path to make individual customer requests traceable.

The backend also exposes:

```text
GET /health
GET /ready
```

`/ready` verifies database connectivity before reporting the application ready.

---

# Evaluation

Agent behavior is evaluated separately from deterministic business logic.

The supervisor currently achieves:

> **100% accuracy on a 27-scenario routing evaluation suite**

The suite covers:

- conversation
- order/delivery
- payments
- returns
- cancellations
- knowledge/RAG
- escalation
- contextual follow-ups
- escalation precedence
- conversational/meta follow-ups

This metric refers specifically to the repository's current 27-scenario evaluation suite and is not intended as a claim of universal routing accuracy.

Run it with:

```bash
python -m scripts.evaluate_supervisor
```

---

# Safety Tests

Destructive-action behavior is tested independently from routing quality.

The confirmation safety suite verifies:

```text
Reject
   └── no mutation

Unclear response
   └── no mutation

Pending but unconfirmed action
   └── no mutation

Explicit confirmation
   └── execution permitted
```

Run:

```bash
python -m scripts.test_confirmation_safety
```

Cancellation proposal generation also has a focused regression test verifying that an eligible cancellation creates a pending confirmation action **without mutating the order**:

```bash
python -m scripts.test_cancellation_proposal
```

---

# Tech Stack

### AI / Agentic Systems

- LangGraph
- LangChain
- Groq-hosted LLMs
- Hugging Face embeddings
- BGE embeddings
- Cross-encoder reranking
- Retrieval-Augmented Generation

### Backend

- Python 3.11
- FastAPI
- SQLAlchemy
- PostgreSQL
- pgvector
- Alembic
- JWT authentication

### Frontend

- Next.js 16
- React 19
- TypeScript
- Tailwind CSS
- TanStack Query
- shadcn
- Zod

### Infrastructure

- Docker / Docker Compose
- AWS EC2
- Vercel
- GitHub Actions

---

# Repository Structure

```text
.
├── .github/
│   └── workflows/
│       └── ci.yml
│
├── alembic/                 # Database migrations
│
├── frontend/                # Next.js customer application
│
├── scripts/                 # Seed, evaluation and regression scripts
│
├── src/
│   ├── actions/             # Controlled state-changing execution
│   ├── agents/              # Specialized support agents
│   ├── api/                 # FastAPI endpoints and schemas
│   ├── core/                # Configuration, auth, logging, context
│   ├── db/                  # SQLAlchemy models and database setup
│   ├── graph/               # LangGraph state and orchestration
│   ├── repositories/        # Persistence layer
│   ├── services/            # Business logic
│   └── tools/               # Bounded capabilities exposed to agents
│
├── Dockerfile
├── compose.yaml
├── requirements.txt
└── README.md
```

---

# CI

GitHub Actions validates both backend and frontend changes.

### Backend

The CI environment:

1. starts PostgreSQL with pgvector
2. installs Python dependencies
3. verifies Python imports
4. applies Alembic migrations
5. seeds deterministic test data
6. runs repository/service/business-rule tests

### Frontend

CI:

1. installs dependencies with `npm ci`
2. runs ESLint
3. creates a production Next.js build

LLM-dependent evaluations are intentionally kept separate from deterministic CI checks.

---

# Deployment

The deployed architecture is:

```text
                       Internet
                          │
                          ▼
                  Vercel / Next.js
                          │
                    Server-side BFF
                          │
                          ▼
                       AWS EC2
                          │
                          ▼
                 Dockerized FastAPI
                          │
                          ▼
                 PostgreSQL + pgvector
```

The frontend never needs direct access to backend credentials.

The production backend runs in Docker and exposes independent health and readiness endpoints.

---

# Running Locally

## 1. Clone

```bash
git clone https://github.com/jatindhiman05/multi-agent-customer-support.git
cd multi-agent-customer-support
```

## 2. Create a Python environment

```bash
python -m venv .venv
```

Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

macOS/Linux:

```bash
source .venv/bin/activate
```

## 3. Install backend dependencies

```bash
pip install -r requirements.txt
```

## 4. Configure environment variables

Create the local environment configuration required by the backend.

Typical configuration includes:

```text
DATABASE_URL
JWT_SECRET
JWT_ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES
GROQ_API_KEY
ALLOWED_ORIGINS
CHAT_PROCESSING_LEASE_SECONDS
```

Never commit production secrets.

## 5. Start PostgreSQL

```bash
docker compose up -d postgres
```

The development Compose configuration exposes PostgreSQL on host port `5434`.

## 6. Run migrations

```bash
alembic upgrade head
```

## 7. Seed development data

```bash
python -m scripts.seed_db
```

## 8. Start FastAPI

```bash
uvicorn src.api.main:app --reload
```

Backend:

```text
http://localhost:8000
```

## 9. Start the frontend

Open another terminal:

```bash
cd frontend
npm install
npm run dev
```

The frontend requires its backend API configuration to point to the local FastAPI application.

---

# Useful Validation Commands

Backend compilation:

```bash
python -m compileall -q src scripts
```

Supervisor evaluation:

```bash
python -m scripts.evaluate_supervisor
```

Confirmation safety:

```bash
python -m scripts.test_confirmation_safety
```

Cancellation proposal safety:

```bash
python -m scripts.test_cancellation_proposal
```

Frontend:

```bash
cd frontend
npm run lint
npm run build
```

---

# Key Design Decisions

### Why PostgreSQL instead of giving agents database access?

Operational commerce data is relational and stateful. Services and repositories provide a controlled boundary around it while PostgreSQL remains the source of truth.

### Why separate RAG from operational tools?

Policy documents answer general questions. They should not determine whether a customer's payment succeeded or where an order currently is.

### Why require confirmation?

Natural-language interpretation is probabilistic. Destructive application state changes should not depend solely on probabilistic model behavior.

### Why use specialized agents?

Different support domains require different tools and constraints. Routing narrows the capabilities available for each request instead of exposing every operation to one unrestricted agent.

### Why keep deterministic tests separate from agent evaluation?

Database correctness, authorization, locking, transactions, and confirmation safety should have deterministic pass/fail tests. LLM routing behavior requires scenario-based evaluation instead.

---

# Engineering Focus

VoltNest is intentionally not designed as a collection of AI demos.

The project focuses on the engineering boundaries required when AI interacts with real application state:

- authentication
- authorization
- deterministic business rules
- transactional writes
- row locking
- explicit confirmation
- idempotency
- failure recovery
- structured outputs
- observability
- evaluation
- CI/CD
- production deployment

The goal is not to maximize the number of agents.

The goal is to build a support system where AI reasoning can be useful **without making the LLM the source of truth or authority over customer data**.

---

# Author

**Jatin Dhiman**  