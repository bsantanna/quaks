# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Quaks is a multi-agent quantitative finance platform built on [Agent-Lab](https://github.com/bsantanna/agent-lab). It uses LLM-powered agents (LangChain/LangGraph) to perform asset management, market data analysis, and alpha-seeking tasks. The backend is Python/FastAPI, the frontend is Angular 20, and market data flows through Airflow DAGs into Elasticsearch.

## Common Commands

### Backend

```bash
# Run the app locally (requires Postgres, Redis, Vault running)
make run                    # or: uvicorn app.main:app --host 0.0.0.0 --port 18000 --reload

# Run all tests (spins up testcontainers: Postgres, Redis, Vault, Keycloak, Ollama, chromedp)
make test                   # or: pytest --cov=app --cov-report=xml

# Run a single test file
pytest tests/integration/test_status_endpoint.py

# Run a single test by name
pytest tests/integration/test_status_endpoint.py -k "test_name"

# Lint
make lint                   # or: python -m flake8 .

# Format (via ruff)
ruff format .
ruff check --fix .
```

### Frontend (from `frontend/` directory)

```bash
npm install
npm start                   # Dev server on port 4200
npm run build               # Production build → copies output to app/static/frontend/
npm test                    # Karma/Jasmine tests
```

### Infrastructure

```bash
# Full stack via Docker
docker compose up -d

# Terraform (Elasticsearch index templates, search scripts, Kibana dashboards)
make setup                  # or: cd terraform/elasticsearch && terraform init && terraform apply
```

### Environment Selection

Configuration is selected by environment variable in `app/core/container.py`:
- `DOCKER=1` → `config-docker.yml`
- `TESTING=1` → `config-test.yml` (testcontainers ports: Postgres 15432, Redis 16379, Vault 18200, Keycloak 18080, Ollama 21434, chromedp 19222)
- `DEVELOPING=1` → `config-dev.yml` (standard local ports, auth disabled)
- None set → reads from HashiCorp Vault at runtime

## Architecture

### Dependency Injection

All wiring is in `app/core/container.py` using `dependency-injector`. The `Container` class declares every service, repository, and agent as a provider. FastAPI endpoints receive dependencies via container wiring (configured in `wiring_config`). To add a new service, register it as a provider in the Container and add the endpoint module to wiring.

### Agent System

Agents are the core abstraction. The class hierarchy:

```
AgentBase (ABC)
├── WorkflowAgentBase          # LangGraph state graph + checkpointer
│   ├── ContactSupportAgentBase
│   ├── WebAgentBase           # Adds browser automation + web search tools
│   │   ├── SupervisedWorkflowAgentBase  # Coordinator → Planner → Supervisor pattern
│   │   │   ├── CoordinatorPlannerSupervisorAgent
│   │   │   ├── VoiceMemosAgent
│   │   │   └── AzureEntraIdVoiceMemosAgent
│   │   └── AdaptiveRagAgent
│   └── VisionDocumentAgent
└── ReactRagAgent              # Uses langgraph prebuilt create_react_agent
```

Key patterns:
- **AgentBase** (`app/services/agent_types/base.py`): Defines `create_default_settings`, `get_input_params`, `process_message` abstract methods. Also houses `AgentUtils` which bundles all shared dependencies (services, repos, config).
- **AgentRegistry** (`app/services/agent_types/registry.py`): Maps string type keys (e.g. `"adaptive_rag"`, `"coordinator_planner_supervisor"`) to agent instances. To register a new agent: add it to the registry dict, create a factory in `Container`, and wire it into `AgentRegistry.__init__`.
- **WorkflowAgentBase**: Provides `get_workflow_builder()` → compiles LangGraph `StateGraph` with a PostgreSQL checkpointer. Handles `process_message` by invoking the graph and publishing progress via Redis (`TaskNotificationService`).
- **SupervisedWorkflowAgentBase**: Implements multi-role orchestration with abstract methods for `get_coordinator`, `get_planner`, `get_supervisor`, `get_reporter`.

### LLM Integration

`AgentBase.get_chat_model()` dynamically selects the LangChain chat model class based on `integration.integration_type`:
- `openai_api_v1` → `ChatOpenAI`
- `anthropic_api_v1` → `ChatAnthropic`
- `xai_api_v1` → `ChatXAI`
- `ollama_api_v1` / default → `ChatOllama`

API keys and endpoints are stored in Vault under `integration_{id}` and retrieved via `get_integration_credentials()`.

### Request Flow

1. HTTP request hits a FastAPI router in `app/interface/api/`
2. Router calls a service (e.g., `MessageService.process_message`)
3. Service resolves the agent type via `AgentRegistry.get_agent()`
4. Agent builds a LangGraph workflow, invokes it with PostgreSQL checkpointing
5. Progress updates publish to Redis; final result returns as JSON

### Database Schema

Three PostgreSQL databases:
- **agent_lab**: Relational data (agents, agent_settings, messages, attachments, language_models, language_model_settings, integrations) via SQLAlchemy
- **agent_lab_vectors**: pgvector embeddings via `DocumentRepository`
- **agent_lab_checkpoints**: LangGraph workflow state via `GraphPersistenceFactory`

### Market Data Pipeline

- Airflow DAGs in `dags/` fetch data from Alpaca Markets API on schedule
- Data lands in Elasticsearch indices: `stocks-eod`, `stocks-metadata`, `stocks-financial-statements`, `stocks-insider-trades`, `stocks-estimated-earnings`, `markets-news`
- Terraform in `terraform/elasticsearch/` manages index lifecycle policies (365-day retention), index templates, and Mustache search templates for technical indicators (RSI, MACD, EMA, ADX, OBV, Stochastic, CCI, AD)
- `MarketsNewsService` and `MarketsStatsService` query Elasticsearch and are injected via the Container

### Frontend

Angular 20 app in `frontend/`. Production build output goes to `app/static/frontend/browser/` and is served by FastAPI as a static mount at `/`. The frontend communicates with the backend REST API.

### Observability

OpenTelemetry is configured in `app/infrastructure/metrics/tracer.py`. Instrumented: FastAPI, HTTPx, LangChain, SQLAlchemy, Psycopg. Exports via OTLP to a collector that feeds Prometheus (metrics), Loki (logs), Tempo (traces), and Grafana (dashboards). Config in `otel/`.

## Code Conventions

- **Linting**: flake8 (ignores E203, E501, W201, W503) + ruff (auto-fix + format). Both run as pre-commit hooks.
- **Pre-commit hooks**: Also run `make test` as a local hook on every commit — tests must pass before commits succeed.
- **Config files**: YAML-based (`config-*.yml`), loaded conditionally by env var in `Container`.
- **Agent prompts**: Use Jinja2 templates stored in agent settings, rendered via `AgentBase.parse_prompt_template()`.
- **Versioning**: Managed by `python-semantic-release`. Version is declared in `docker/app/Dockerfile` (`SERVICE_VERSION`) and `frontend/package.json`.
- **Testing**: pytest with testcontainers — tests spin up real Postgres, Redis, Vault, Keycloak, Ollama, and chromedp containers. The `conftest.py` session fixture manages container lifecycle.
