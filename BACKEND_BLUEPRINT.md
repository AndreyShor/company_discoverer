# Backend Project Blueprint
This document specifies the architectural layout, core stack, and setup patterns of the LegalMate backend. Provide this blueprint to AI agents when bootstrapping a new backend service or transferring the architecture to another application.

## Core Technology Stack
- **Framework**: FastAPI with Uvicorn ASGI server.
- **Languages**: Python > 3.10
  - Vector Database / Semantic Retrieval: **Qdrant**
  - Cache / Dist. Locks / Realtime: **Redis**
- **AI & NLP**: 
  - LangChain / LangGraph (with custom agent state machines)
  - OpenAI / XAI
- **Security & APIs**:
  - Sentinels: Custom XSS Guard Middleware, Security Headers Middleware, Auth routes with CSRF and JWT.
  - Rate Limiting: SlowAPI
- **Observability**: Sentry (Traces, Profiles, Exceptions), Structlog for structured JSON logging.

---

## Directory & Architectural Structure

The system enforces a strict bounded context, separating routing (HTTP transport) from core business logic (Services) and validations (Models).

### 1. `main.py`
The FastAPI entry point. 
- **Roles**: Aggregates routers (`prefix="/api/v1"`), initializes connections inside `@asynccontextmanager async def lifespan`, mounts middlewares, and sets global exception handlers (HTTPException, RequestValidationError, unhandled exceptions).
- **Setup Pattern**: Always establish robust `retries` for databases (Qdrant, Redis, Supabase) in the lifespan.

### 2. `api/` (Transport Layer)
Handles external HTTP interactions, request parsing, and response formatting.
- `routes/`: Modular endpoints categorized by domain (`auth.py`, `company.py`, `billing.py`, etc.).
- `LLM/`: Domain-specific AI endpoints (`routes/`), specialized internal logic (`controllers/`), and orchestrators for connecting models via LangChain/LangGraph.

### 3. `core/` (Configuration & Cross-Cutting Concerns)
Application-wide utilities.
- `config.py` & `stripe_config.py`: Environment variable loading (with `pydantic` Settings) and external config initialization.
- `security_middleware.py`: Defines classes `RequestXSSGuardMiddleware` and `SecurityHeadersMiddleware`.
- `logging.py` & `observability.py`: Logging factories defining structured outputs and Sentry interceptors.
- `cache.py`: Redis client setup singletons.

### 4. `database/` (Data Infrastructure)
Wrappers and singleton managers for persistent storage engines.
- `Qdrant.py`: Qdrant connection properties, collections setup, and global state management.
- `rpc/`: Stored procedures/queries for the Supabase databases.

### 5. `models/` (Data Validations & Serialization)
Pydantic v2 classes handling strong typing. Grouped by domain:
- `auth_models.py`, `billing_models.py`, `company_models.py`.
- **Constraint**: Models must solely define shapes natively, without embedded backend logic.

### 6. `services/` (Business Logic Layer)
Domain logic isolated from HTTP scope.
- `billing_service.py`: Encapsulates Stripe webhooks, race condition handling, and Supabase ledger updates.
- `task_manager.py`: Distributed, Redis-based task queuing logic with cancellation handling.
- `attachments_service.py`: Logic managing S3/Supabase bucket file storing, extracting metadata, and converting.

### 7. `scripts/` (Utilities & Compilations)
Standalone execution files for CI/CD or initialization.
- `generate_graph.py`: Renders the LangGraph state machine to a PNG.
- `warmup_model.py`: Pre-warms the OpenAI embedding model.

---

## Important Implementation Patterns

### 1. Global State
Avoid holding global variables blindly. Connections (Supabase, Qdrant, Redis) use singleton patterns, instantiated exclusively in `main.py`'s `lifespan`.

### 2. Authentication Flow
- **Access Tokens**: Short-lived (15 min), returned directly via JSON payload in response body.
- **Refresh Tokens**: Long-lived (30 days), stored exclusively within `httpOnly` secure cookies.
- **Cross-Site Protection**: Active CSRF tokens are issued and expected via header on mutating HTTP calls.

### 3. Rate Limiting & Abuse Prevention
`SlowAPI` handles per-IP request limitations locally, caching rates.

### 4. Background Tasks & Concurrency
Use a horizontal-scaling friendly system. The `TaskManager` stores task states in Redis, allowing cancellation flows properly handled even when running multiple Uvicorn worker nodes.

### 5. Exception Handling
Exceptions should be raised centrally (`fastapi.HTTPException`). The global exception handler logs `4xx` requests safely (omitting PII), while `5xx` errors automatically trigger detailed `Sentry` events.
