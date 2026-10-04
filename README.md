# VoltNest

VoltNest is an AI customer support platform built to explore how LLM-based agents can interact with real application data and workflows safely.

Instead of using an LLM only to generate responses, VoltNest connects language-model reasoning with authenticated backend tools, a PostgreSQL database, and a retrieval system for support knowledge.

The core design principle is simple:

> **The LLM can reason about what needs to happen, but application code decides what is allowed to happen.**

The project is actively being developed and expanded toward a complete end-to-end customer support product.

---

## What VoltNest Does

VoltNest handles both informational and operational customer-support requests.

Current workflows include support for:

- customer order queries and tracking
- returns and return eligibility
- order cancellation
- refund information
- support-policy questions
- human-support escalation
- multi-turn conversations
- authenticated customer-specific operations

Additional customer-support workflows are being added as the application evolves.

---

## Architecture

At a high level:

```text
                         Customer
                            │
                            ▼
                     Next.js Frontend
                            │
                            ▼
                       FastAPI API
                            │
                            ▼
                 LangGraph Orchestration
                            │
              ┌─────────────┴─────────────┐
              │                           │
              ▼                           ▼
     Operational Workflows          Knowledge Retrieval
              │                           │
              ▼                           ▼
            Tools                     RAG Pipeline
              │                           │
              ▼                           ▼
           Services                    pgvector
              │                           │
              ▼                           ▼
         Repositories                 Reranking
              │                           │
              ▼                           ▼
         PostgreSQL                  LLM Response
```

VoltNest separates AI reasoning from application logic.

Operational requests use controlled tools backed by service and repository layers. Knowledge questions use a separate retrieval pipeline over the support knowledge base.

This keeps application state and business rules outside the direct control of the LLM.

---

## Agentic Workflow

LangGraph is used to maintain conversation state and coordinate specialized support workflows.

A request generally follows this path:

```text
Customer Message
       │
       ▼
Authentication / Request Context
       │
       ▼
LangGraph
       │
       ▼
Request Routing
       │
       ▼
Relevant Support Workflow
       │
       ├───────────────┐
       ▼               ▼
     Tools          Knowledge Retrieval
       │
       ▼
Business Services
       │
       ▼
Repositories
       │
       ▼
PostgreSQL
```

The orchestration layer determines which capability is appropriate for the request, while actual business operations remain implemented in normal application code.

---

## Tools and Business Logic

Agents do not receive unrestricted database access.

Application operations follow a controlled boundary:

```text
Agent
  │
  ▼
Tool
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

Each layer has a separate responsibility:

- **Agents** understand the customer's request and decide which capability to use.
- **Tools** expose a limited interface to the agent.
- **Services** implement business rules and application logic.
- **Repositories** handle persistence and database queries.
- **PostgreSQL** remains the source of truth for operational data.

This makes it possible to use LLM reasoning without allowing generated model output to directly control the database.

---

## Handling State-Changing Actions

Read operations and write operations are treated differently.

A request that changes application state follows a controlled workflow:

```text
Customer Request
       │
       ▼
Identify Intended Action
       │
       ▼
Validate Customer / Resource
       │
       ▼
Check Business Rules
       │
       ▼
Create Pending Action
       │
       ▼
Request User Confirmation
       │
       ▼
Deterministic Action Execution
       │
       ▼
Database Transaction
       │
       ▼
Result
```

The backend is responsible for validating whether an operation is actually allowed.

The system uses mechanisms such as authentication, ownership validation, confirmation, transactions, locking, and idempotency where appropriate to protect state-changing operations.

---

## Retrieval-Augmented Generation

Customer-specific operational data and company knowledge are intentionally kept separate.

A question such as:

```text
"What is the return policy?"
```

is answered from the support knowledge base.

A question such as:

```text
"Where is my order?"
```

uses authenticated application data instead.

The knowledge retrieval pipeline follows:

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
pgvector
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
LLM
       │
       ▼
Grounded Response
```

This prevents static policy documents from being treated as the source of truth for live customer information.

---

## Authentication and Customer Data

Customer-specific operations are authenticated.

The customer's identity comes from the application authentication layer rather than from values generated by the LLM.

For example:

```text
Authenticated Request
        │
        ▼
Trusted Customer Identity
        │
        ▼
Agent Tool
        │
        ▼
Service
        │
        ▼
Ownership Validation
        │
        ▼
Requested Data / Operation
```

This prevents the model from simply choosing a different customer identity when calling application capabilities.

---

## Tech Stack

### AI / Agent Orchestration

- LangGraph
- LangChain
- LLM APIs
- BGE embeddings
- Cross-encoder reranking

### Backend

- Python
- FastAPI
- PostgreSQL
- pgvector
- SQLAlchemy
- Alembic
- JWT authentication

### Frontend

- Next.js
- React
- TypeScript
- Tailwind CSS
- TanStack Query

### Infrastructure

- Docker
- AWS
- Vercel
- GitHub

---

## Repository Structure

```text
.
├── frontend/              # Customer-facing Next.js application
│
├── src/
│   ├── actions/           # Controlled execution of application actions
│   ├── agents/            # Agent and workflow implementations
│   ├── api/               # FastAPI application and HTTP endpoints
│   ├── db/                # Database configuration and models
│   ├── graph/             # LangGraph orchestration and state
│   ├── repositories/      # Persistence layer
│   ├── services/          # Business logic
│   └── tools/             # Capabilities exposed to agents
│
├── scripts/               # Development/setup utilities
├── alembic/               # Database migrations
├── Dockerfile
├── compose.yaml
└── README.md
```

The structure is intentionally layered so that adding or changing an AI workflow does not require putting business logic inside agent prompts.

---

## Running Locally

### 1. Clone the repository

```bash
git clone https://github.com/jatindhiman05/multi-agent-customer-support.git
cd multi-agent-customer-support
```

### 2. Create a virtual environment

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

### 3. Install backend dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure the environment

Create the required local environment configuration using the project's example environment file.

Secrets such as API keys, JWT secrets, and database credentials should only be supplied through environment configuration and must not be committed to the repository.

### 5. Start the database

```bash
docker compose up -d postgres
```

### 6. Apply database migrations

```bash
alembic upgrade head
```

### 7. Start the backend

```bash
uvicorn src.api.main:app --reload
```

### 8. Start the frontend

In another terminal:

```bash
cd frontend
npm install
npm run dev
```

---

## Why I Built This

I started VoltNest because I wanted to understand what changes when an LLM is connected to an actual application rather than being used only for question answering.

Getting a model to generate a response or call a tool is relatively straightforward. The harder problem is deciding what the model should be trusted to do.

For example, an AI system handling an order cancellation has to deal with questions such as:

- Is the customer authenticated?
- Does the order belong to that customer?
- Is the order still cancellable?
- Did the customer actually confirm the action?
- What happens if the same request is sent twice?
- What happens if execution fails halfway through?

VoltNest keeps those decisions in deterministic application code while using the LLM for language understanding, reasoning, and workflow selection.

That separation between **AI reasoning and application control** is the main engineering idea behind the project.

---

## Current Status

VoltNest is under active development.

The project already includes the core agent orchestration, authenticated operational tools, PostgreSQL persistence, support-policy retrieval, controlled state-changing workflows, a customer-facing frontend, and cloud deployment.

Current development is focused on expanding customer-support coverage, improving multi-turn conversation handling, strengthening reliability and failure handling, and evaluating the system across realistic customer-support scenarios.

---

## Roadmap

The project is being developed incrementally toward a complete customer-facing support application.

Areas currently being improved include:

- broader customer-support workflows
- conversational context and follow-up handling
- payment and refund assistance
- delivery issue handling
- failure recovery
- structured frontend interactions
- automated evaluation
- integration and end-to-end testing
- observability
- deployment automation

Features are added only when the underlying application behavior and safety boundaries are implemented, rather than being simulated through prompts.

---

## Author

**Jatin Dhiman**  
B.E. Computer Science & Engineering  
UIET, Panjab University
