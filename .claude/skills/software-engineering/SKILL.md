---
name: software-engineering
description: Use when the user asks about architecture, running, testing, linting, or building the project, or about code conventions.
---

# Software Engineering

## Architecture

### Dependency Injection

All wiring is in `app/core/container.py` using `dependency-injector`. The `Container` class declares every service, repository, and agent as a provider. FastAPI endpoints receive dependencies via container wiring (configured in `wiring_config`). To add a new service, register it as a provider in the Container and add the endpoint module to wiring.

### Agent System

Agents are the core abstraction. The class hierarchy:

```
AgentBase (ABC)
├── WorkflowAgentBase          # LangGraph state graph + checkpointer
│   ├── ContactSupportAgentBase
│   └── WebAgentBase           # Adds browser automation + web search tools
│       └── SupervisedWorkflowAgentBase  # Coordinator → Planner → Supervisor pattern
└── TestEchoAgent              # Simple echo agent for testing
```

Key patterns:
- **AgentBase** (`app/services/agent_types/base.py`): Defines `create_default_settings`, `get_input_params`, `process_message` abstract methods. Also houses `AgentUtils` which bundles all shared dependencies (services, repos, config).
- **AgentRegistry** (`app/services/agent_types/registry.py`): Maps string type keys (e.g. `"test_echo"`) to agent instances. To register a new agent: add it to the registry dict, create a factory in `Container`, and wire it into `AgentRegistry.__init__`.
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

Angular 21 app in `frontend/`. Production build output goes to `app/static/frontend/browser/` and is served by FastAPI as a static mount at `/`. The frontend communicates with the backend REST API. Stock charts and performance comparison views embed Kibana dashboards via iframe (the `#/view/` URLs in `stock-eod-charts.ts` and `stock-comparison-charts.ts` are Kibana dashboard embed URLs, not internal routes).

**Navigation header ↔ Hamburger menu sync:** The hamburger menu (`navigation-header/hamburger-menu/`) is the mobile counterpart of the desktop navigation header. It mirrors navigation links, search autocompletes, theme switcher, and settings. When adding, removing, or modifying navigation items, theme options, or settings in the desktop header, always apply the same changes to the hamburger menu (and vice versa).

### Frontend Theming System

The frontend supports multiple themes via CSS custom properties scoped to `[data-theme="<name>"]` on the `<html>` element. Theme preference is persisted in `localStorage` and managed by `ThemeService`.

#### Architecture

- **Theme tokens** are defined in `frontend/src/styles.scss` under `[data-theme="<name>"]` selectors
- **ThemeService** (`frontend/src/app/shared/services/theme.service.ts`) reads/writes localStorage, applies `data-theme` attribute
- **ThemeName type** is defined in `frontend/src/app/shared/models/navigation.models.ts`
- **Settings dropdown** (`frontend/src/app/navigation-header/settings-dropdown/`) provides the UI to switch themes

#### Design Tokens (CSS Custom Properties)

Every theme MUST define all of these tokens:

```css
[data-theme="<name>"] {
  /* Surfaces — background layers from darkest to lightest */
  --surface-base: <color>;       /* HTML/body background */
  --surface-panel: <color>;      /* Main content panel */
  --surface-elevated: <color>;   /* Cards, dropdowns, header/footer */
  --surface-hover: <color>;      /* Hover state backgrounds */

  /* Borders */
  --border-primary: <color>;     /* Default borders */
  --border-accent: <color>;      /* Accent-colored borders (matches accent) */

  /* Text */
  --text-primary: <color>;       /* Main text */
  --text-secondary: <color>;     /* Labels, descriptions */
  --text-muted: <color>;         /* Timestamps, metadata, disabled */

  /* Accent — brand/highlight color */
  --accent-primary: <color>;     /* Active tabs, links, badges, focus rings */
  --accent-hover: <color>;       /* Accent hover state */

  /* Status */
  --status-positive: <color>;    /* Gains, success (green family) */
  --status-negative: <color>;    /* Losses, errors (red family) */

  /* Typography */
  --font-heading: <stack>;       /* Page titles, nav titles */
  --font-body: <stack>;          /* Body text, paragraphs */
  --font-data: <stack>;          /* Financial data, monospace content */

  /* Shape */
  --radius: <px>;                /* Border radius: 0px=sharp, 8px=rounded */
}
```

#### How to Add a New Theme

1. **Define tokens** — Add a new `[data-theme="<name>"]` block in `styles.scss` with all required tokens
2. **Register the type** — Add the name to `ThemeName` union in `navigation.models.ts`
3. **Add UI option** — Add a button in `settings-dropdown.html` with a `.theme-swatch-<name>` color swatch
4. **Add swatch style** — Add `.theme-swatch-<name>` in `settings-dropdown.scss` with a representative gradient
5. **Import fonts** — If using custom fonts, add the `@import url(...)` to `styles.scss`
6. **Run tests** — `npx jest` (all 159+ tests should pass unchanged)

#### Styling Conventions

- **NEVER use hardcoded Tailwind color classes** (e.g., `bg-gray-800`, `text-white`, `border-blue-500`) for themed elements. Use SCSS classes that reference CSS vars instead.
- **DO use Tailwind** for layout/spacing (`flex`, `grid`, `px-4`, `gap-2`, etc.) — these are theme-independent.
- **Component SCSS files** define theme-aware classes using `var(--token)`. Examples: `.nav-btn`, `.tools-list`, `.autocomplete-input`, `.interval-btn`.
- **Reusable class patterns** used across components:
  - `.actions-tab` / `.actions-tab-bar` — Tab navigation (used in stock-eod-actions, heatmaps)
  - `.tools-list` / `.tools-item` / `.tools-title` / `.tools-subtitle` — List items (tools, insights)
  - `.autocomplete-input` / `.autocomplete-dropdown` / `.autocomplete-item` — Search inputs (stock, news, comparison)
  - `.interval-btn` / `.interval-active` — Time range button groups
  - `.dashboard-panel` / `.dashboard-panel-blur` — Container panels
  - `.variance-positive` / `.variance-negative` — Gain/loss coloring
  - `.news-card` / `.news-title` / `.news-summary` / `.news-meta` / `.news-ticker-badge` — News components
  - `.info-header` / `.info-label` / `.info-divider` — Stock info header
- **SVG icons** use explicit fill/stroke colors (not `currentColor`) since they're loaded via `<img>` tags. Store in `frontend/public/svg/`.
- **SSR safety** — Guard browser APIs (`localStorage`, `ResizeObserver`) with `isPlatformBrowser` from `@angular/common`.

#### Theme Design Guidelines

- **Contrast**: Ensure sufficient contrast between `--text-primary` and `--surface-panel` (WCAG AA: 4.5:1 minimum)
- **Accent**: Pick ONE strong accent color. It will be used for active tabs, links, badges, focus rings, and active buttons.
- **Surfaces**: Use 4 tiers of darkness. `--surface-base` < `--surface-panel` < `--surface-elevated` < `--surface-hover` (from darkest to lightest for dark themes).
- **Radius**: `0px` for sharp/terminal themes, `8px` for soft/rounded themes. This single value controls ALL borders site-wide.
- **Fonts**: Import via Google Fonts `@import url(...)` in `styles.scss`. Use monospace for `--font-data` in data-heavy themes.

### Insights Agent Profiles

The Insights section displays AI agent profiles. Each agent has a listing card on the agents page and a dedicated profile page loaded from a static JSON file.

#### Architecture

- **Agents page** (`page-insights-agents/`) — Grid of agent cards linking to `/insights/profile/:agentName`
- **Profile page** (`page-insights-profile/`) — Reads `:agentName` from the route, fetches `/json/insight_agent_{agentName}.json`, renders a two-column layout (bio + avatar sidebar)
- **Profile data** — Static JSON files in `frontend/public/json/` prefixed `insight_agent_<agent_name>.json`

#### JSON Schema

```json
{
  "name": "Agent Display Name",
  "role": "Agent Role/Title",
  "avatar": "/svg/agent-avatar.svg",
  "ctaLabel": "Button Label",
  "ctaLink": "/path/to/page",
  "ctaIcon": "/svg/icon-name.svg",
  "bio": [
    "First paragraph of the agent description.",
    "Second paragraph with more details."
  ]
}
```

Required fields: `name`, `role`, `avatar`, `bio`.
Optional fields: `ctaLabel`, `ctaLink`, `ctaIcon` — when `ctaLink` is set, a call-to-action button renders below the bio.

#### How to Add a New Agent Profile

1. **Create JSON** — Add `frontend/public/json/insight_agent_<agent-name>.json` with all required fields
2. **Add avatar** — Place the agent's SVG avatar in `frontend/public/svg/`
3. **Add card** — Add an `<a class="agent-card">` entry in `insights-agents.html` linking to `/insights/profile/<agent-name>`
4. **Run tests** — `npx jest` (all tests should pass unchanged)

### Observability

OpenTelemetry is configured in `app/infrastructure/metrics/tracer.py`. Instrumented: FastAPI, HTTPx, LangChain, SQLAlchemy, Psycopg. Exports via OTLP to a collector that feeds Prometheus (metrics), Loki (logs), Tempo (traces), and Grafana (dashboards). Config in `otel/`.

---

## Dependency Management

Dependencies are managed with [uv](https://docs.astral.sh/uv/) and declared in `pyproject.toml`.

### Structure

- `[project.dependencies]` — Runtime dependencies (fastapi, langchain, etc.)
- `[dependency-groups.dev]` — Dev tools (ruff, flake8, isort, pre-commit)
- `[dependency-groups.test]` — Test tools (pytest, testcontainers)
- `[dependency-groups.notebooks]` — Jupyter notebook dependencies

### Lock File

`uv.lock` is committed to the repo and provides deterministic, reproducible installs across CI and Docker. Always run `uv lock` after modifying dependencies in `pyproject.toml`.

### Adding/Removing Dependencies

```bash
# Add a runtime dependency
uv add <package>

# Add a dev dependency
uv add --group dev <package>

# Add a test dependency
uv add --group test <package>

# Remove a dependency
uv remove <package>
```

### Local Development

The project uses conda for Python version management. Install dependencies with uv:

```bash
conda activate agent-lab
uv sync --group dev --group test
```

### Docker

The Docker image uses `uv sync --frozen --no-dev` for production-only, deterministic installs from `uv.lock`.

### CI

CI uses `uv sync --frozen --group dev --group test` to install all dependency groups from the lock file.

---

## Common Commands

### Backend

**Important:** All Python commands must use the `agent-lab` conda environment: `conda run -n agent-lab <command>`

```bash
# Run the app locally (requires Postgres, Redis, Vault running)
make run

# Run all tests (spins up testcontainers: Postgres, Redis, Vault, Keycloak, Ollama, chromedp)
make test

# Run a single test file
pytest tests/integration/test_status_endpoint.py

# Run a single test by name
pytest tests/integration/test_status_endpoint.py -k "test_name"

# Lint
make lint

# Format (via ruff)
ruff format .
ruff check --fix .
```

### Backend Debugging

```bash
# View live app container logs (useful for debugging API errors)
docker compose logs -f app

# Rebuild and restart the app container after backend code changes
docker compose build app && docker compose up -d app
```

**Note:** The backend runs inside a Docker container (`compose.yml`). Local changes to Python files in `app/` are NOT reflected until the container is rebuilt. Always rebuild after modifying backend code.

### Frontend (from `frontend/` directory)

```bash
npm install
npm start                   # Dev server on port 4200
npm run build               # Production build → copies output to app/static/frontend/
npx jest                    # Run all Jest tests
npx jest -- <pattern>       # Run tests matching a pattern (e.g. npx jest -- markets-performance)
```

## REST API Design

Follow the **Richardson Maturity Model** (Level 3) when designing or modifying API endpoints.

### HTTP Method Selection

Choose the method based on the operation's semantics, not implementation convenience:

| Method | Use When | Safe | Idempotent | Cacheable |
|--------|----------|------|------------|-----------|
| `GET` | Retrieving data (reads, queries, searches, bulk lookups) | Yes | Yes | Yes |
| `POST` | Creating resources or triggering non-idempotent operations | No | No | No |
| `PUT` | Full replacement of a resource | No | Yes | No |
| `PATCH` | Partial update of a resource | No | No | No |
| `DELETE` | Removing a resource | No | Yes | No |

**Key rule:** If a request is **safe** (no side effects) and **idempotent** (same result on repeated calls), it MUST be a GET. This enables browser/CDN caching via `Cache-Control` headers. POST requests are never cached by browsers regardless of cache headers.

### Query Parameters vs Request Body

- **GET endpoints**: Pass filters via query parameters. For lists, use comma-separated values (e.g., `?key_tickers=AAPL,MSFT,NVDA`).
- **POST/PUT/PATCH endpoints**: Use JSON request body for resource creation/mutation.
- **URL path parameters**: Use for resource identifiers (e.g., `/stats_close/{index_name}/{key_ticker}`).

### Caching

- Use the `cache_control(max_age)` dependency from `app/interface/api/cache_control.py`.
- Read-heavy, infrequently-changing data (e.g., market caps, EOD stats): `cache_control(86400)` (24h).
- Frequently-changing data (e.g., news, real-time prices): `cache_control(3600)` (1h) or less.
- Caching only works with GET — never rely on cache headers for POST endpoints.

### Resource Naming

- Use **nouns** for resources, not verbs: `/markets/stats_close`, not `/markets/get_stats`.
- Use **snake_case** for path segments and query params (matching Python conventions).
- Use plural when returning collections: `/markets/news`, `/markets/indicators`.

### Validation

- Path/query params are validated via `_validate_index_name()` regex in `endpoints.py`.
- Never expose internal patterns (e.g., ES wildcards `*`) through the API — resolve them server-side or use aliases.

---

## Code Conventions

- **Linting**: flake8 (ignores E203, E501, W201, W503) + ruff (auto-fix + format). Both run as pre-commit hooks.
- **Pre-commit hooks**: Also run `make test` as a local hook on every commit — tests must pass before commits succeed.
- **Config files**: YAML-based (`config-*.yml`), loaded conditionally by env var in `Container`.
- **Agent prompts**: Use Jinja2 templates stored in agent settings, rendered via `AgentBase.parse_prompt_template()`.
- **Dependency management**: uv with `pyproject.toml` + `uv.lock`. Runtime, dev, test, and notebook dependencies are split into groups.
- **Versioning**: Managed by `python-semantic-release`. Version is declared in `pyproject.toml`, `docker/app/Dockerfile` (`SERVICE_VERSION`), and `frontend/package.json`.
- **Testing**: pytest with testcontainers — tests spin up real Postgres, Redis, Vault, Keycloak, Ollama, and chromedp containers. The `conftest.py` session fixture manages container lifecycle.
