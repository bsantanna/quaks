---
name: quaks-generator
description: Creates and registers new autonomous agents in quaks inheriting from SupervisedWorkflowAgent, and optionally exposes their workflow over the tenant-scoped MCP server so external clients (Claude Code, Claude.ai, ChatGPT) can replay the pipeline as a published Claude skill. Supports two graph patterns — direct graph (deterministic edges) and command multi-agentic (LLM-based supervisor routing). Use when the user wants to "prototype a new agent", "scaffold a multi-agent workflow", "generate a supervised graph", "expose an agent over MCP", or "publish an agent as a Claude skill" by specifying a directory, intent, sub-agent roles, and preferred graph pattern.
metadata:
  category: development
  tool: quaks
  framework: LangGraph
---

# Quaks Generator

You are an expert at scaffolding cloud-native autonomous agents for the **quaks** toolkit. Your goal is to create a new agent prototype that inherits from the `SupervisedWorkflowAgentBase` class, register it within the backend, and — when the user asks for it — expose the same workflow over the tenant-scoped **MCP server** so the agent can be replayed by external Claude clients as a published skill in the `quaks-agents` plugin.

The two halves of the system mirror each other:

| Layer | Used by | Storage | Entry point |
|-------|---------|---------|-------------|
| **In-process LangGraph agent** | Quaks UI, Airflow ETL DAGs | PostgreSQL checkpointer + per-tenant agent settings | `POST /messages/post` |
| **MCP-exposed workflow** | External Claude / GPT clients via the `quaks-agents` plugin | Same tenant agent settings, served as `prompts/get` + `tools/call` | `https://quaks.ai/mcp/` |

A new agent typically needs **both** — the LangGraph implementation for batch/ETL use, and an MCP registrar so users can run the same workflow inside their own Claude Code session against their own tenant's customised prompts.

## Workflow

### 1. Information Gathering
Ensure you have the target **directory**, **general intent**, the **roles** for the LangGraph sub-agents, and the preferred **graph pattern**:

- **Direct Graph** — Deterministic sequential pipeline using `add_edge()`. Nodes execute in a fixed order (A → B → C → END). Best when the workflow is a predictable pipeline. Saves LLM calls, lower message count, easier to debug. Abstract methods (`get_planner`, `get_supervisor`, `get_reporter`) become no-op stubs.
- **Command Multi-Agentic** — LLM-based supervisor routing using `Command` interface. The supervisor decides which node to invoke next based on content. Best when the next step is genuinely dynamic (e.g., optional workers, conditional branching, iterative refinement loops). Uses all four abstract methods (`get_coordinator`, `get_planner`, `get_supervisor`, `get_reporter`) with real logic.

### 2. Implementation Requirements
- **Base Class**: Inherit from `SupervisedWorkflowAgentBase` (`app/services/agent_types/base.py`).
- **Connectivity**: Depends on the chosen graph pattern:
  - **Direct Graph**: Use `add_edge()` for fixed sequential transitions. Nodes return `Command` objects with explicit `goto` targets. The `get_workflow_builder` wires the full pipeline with deterministic edges.
  - **Command Multi-Agentic**: Use the **Command interface** (`langgraph.types.Command`) with LLM-based routing. The supervisor node inspects state and decides which worker to invoke next. Supports conditional branching and iterative loops.
- **Dynamic Prompts**: Implement system prompts in `prompts.py` using **Jinja2 templates** with `{{ CURRENT_TIME }}` and other runtime variables.

### 3. File Structure Generation
Generate the following files in `app/services/agent_types/[directory]/`:
- `__init__.py`: Agent constants — `AGENT_CONFIGURATION` dict (name, desc, desc_for_llm, is_optional per role) and `AGENTS` list.
- `agent.py`: Main class logic using the Command interface for node routing.
- `state.py`: Typed state definitions extending `MessagesState` with `Annotated[List, join_messages]`.
- `schema.py`: TypedDict routers for structured LLM output (e.g., `CoordinatorRouter`).
- `prompts.py`: Jinja2 template strings for system prompts.

### 4. Registration
Register the new agent in these files:
- `app/services/agent_types/registry.py` — Add the agent to `AgentRegistry.__init__` and `self.registry` dict.
- `app/core/container.py` — Add a `providers.Factory` for the agent and wire it into the `agent_registry` singleton.

### 5. API Endpoint Documentation
Add the new agent type to `valid_agent_types` in `app/interface/api/agents/schema.py`. This list gates the `POST /agents/create` endpoint validation. Without this step, the API will reject creation requests for the new agent type with a "not supported" error.

## Best Practices

### Choosing the Graph Pattern

Ask the user which pattern they prefer. Use this decision matrix to guide the conversation:

| Criteria | Direct Graph | Command Multi-Agentic |
|----------|-------------|----------------------|
| Workflow shape | Fixed sequential pipeline (A → B → C) | Dynamic routing, conditional branches, loops |
| LLM calls | Minimal (one per node) | Extra calls for supervisor routing decisions |
| Message budget | Low (~1 per chain node) | Higher (supervisor + routing overhead) |
| Debuggability | High — predictable execution path | Moderate — path depends on LLM decisions |
| Flexibility | Low — pipeline is hardcoded | High — supervisor can skip/repeat/branch |
| Abstract methods | Stubs (no-op) for planner/supervisor/reporter | Real implementations with routing logic |
| Best for | Data pipelines, report generation, sequential analysis | Research assistants, adaptive workflows, multi-tool orchestration |

#### Direct Graph Pattern (deterministic edges)

```python
# get_workflow_builder — fixed sequential pipeline
workflow_builder.add_edge(START, "coordinator")
workflow_builder.add_edge("aggregator", "headlines_creator")
workflow_builder.add_edge("headlines_creator", "news_writer")
workflow_builder.add_edge("news_writer", "editor")
workflow_builder.add_edge("editor", END)

# Abstract method stubs — not used
def get_planner(self, state): return Command(goto="supervisor")
def get_supervisor(self, state): return Command(goto=END)
def get_reporter(self, state): return Command(goto="supervisor")
```

#### Command Multi-Agentic Pattern (LLM-based supervisor routing)

```python
# get_workflow_builder — supervisor routes dynamically
workflow_builder.add_edge(START, "coordinator")
workflow_builder.add_node("coordinator", self.get_coordinator)
workflow_builder.add_node("planner", self.get_planner)
workflow_builder.add_node("supervisor", self.get_supervisor)
workflow_builder.add_node("worker_a", self.get_worker_a)
workflow_builder.add_node("worker_b", self.get_worker_b)
workflow_builder.add_node("reporter", self.get_reporter)
# No add_edge between workers — supervisor decides routing via Command

# Supervisor node — LLM picks the next worker
def get_supervisor(self, state):
    chat_model = self.get_chat_model(state["agent_id"], state["schema"])
    router = chat_model.with_structured_output(SupervisorRouter)
    response = self.get_supervisor_chain(router, state["supervisor_system_prompt"]).invoke(...)
    return Command(goto=response["next"], update={"messages": [...]})
```

### Use Simple Chains for Tool-less Nodes

Nodes that don't need tools should use a **simple chain** (`ChatPromptTemplate | ChatModel`) instead of `create_react_agent`. React agents add overhead messages (tool-call scaffolding) even with an empty tool list.

```python
def _invoke_chain(self, agent_id, schema, system_prompt, state):
    chat_model = self.get_chat_model(agent_id, schema)
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("placeholder", "{messages}"),
    ])
    chain = prompt | chat_model
    return chain.invoke({"messages": state["messages"]})
```

Only use `create_react_agent` for nodes that actually call tools.

### Message Budget: Stay Under the Recursion Limit

The default `recursion_limit` is **30**. Each graph node invocation (including react agent internal steps like tool calls) counts toward this. Budget carefully:

| Node type | Estimated messages |
|-----------|--------------------|
| Simple chain (system + messages → LLM) | 1 |
| React agent with 1 tool call | ~3 (call + response + summary) |
| React agent with N tool calls | ~2N + 1 |
| LLM-based supervisor routing | 1 per routing decision |

Design your graph so the total stays well under 30. For a 4-role sequential pipeline with 1 tool-using node: ~1 (coordinator) + ~4 (react aggregator) + 1 + 1 + 1 = ~8 messages.

### Tool Design: Sync vs Async

LangGraph's `create_react_agent` invokes tools **synchronously** via `.invoke()`. If wrapping an async service:
- Define the tool as a **sync function** (`def`, not `async def`)
- Bridge the async call with `asyncio.get_event_loop().run_until_complete()`
- Using `async def` on a tool will raise `NotImplementedError: StructuredTool does not support sync invocation`

```python
@tool("fetch_data")
def fetch_data(query: str) -> str:
    """Fetch data from the service."""
    import asyncio
    results = asyncio.get_event_loop().run_until_complete(
        service.async_method(query)
    )
    return json.dumps(results)
```

### Dependency Injection for External Services

When your agent needs services beyond `AgentUtils` (e.g., `MarketsNewsService`, `Elasticsearch`):
- Accept them as **additional constructor parameters** alongside `agent_utils`
- Wire them in `container.py` via the existing providers
- Expose them to graph nodes via `self.service_name` and build tools with closures

```python
# container.py
quaks_news_analyst_agent = providers.Factory(
    QuaksNewsAnalystAgent,
    agent_utils=agent_utils,
    markets_news_service=markets_news_service,  # additional dependency
)
```

### Abstract Method Stubs

`SupervisedWorkflowAgentBase` requires `get_coordinator`, `get_planner`, `get_supervisor`, and `get_reporter` as abstract methods. If your graph uses deterministic edges and doesn't need some of these, provide **no-op stubs**:

```python
def get_planner(self, state) -> Command[Literal["supervisor"]]:
    return Command(goto="supervisor")

def get_supervisor(self, state) -> Command:
    return Command(goto=END)

def get_reporter(self, state) -> Command[Literal["supervisor"]]:
    return Command(goto="supervisor")
```

### Prompt Settings Persistence

Default prompts are stored in `prompts.py` as constants and persisted to PostgreSQL via `create_default_settings`. This allows runtime modification through the API without code changes. Use a dict loop for clean registration:

```python
def create_default_settings(self, agent_id: str, schema: str):
    prompts = {
        "coordinator_system_prompt": COORDINATOR_SYSTEM_PROMPT,
        "writer_system_prompt": WRITER_SYSTEM_PROMPT,
    }
    for key, value in prompts.items():
        self.agent_setting_service.create_agent_setting(
            agent_id=agent_id, setting_key=key,
            setting_value=value, schema=schema,
        )
```

## Reference Implementations

### Direct Graph Pattern
See `app/services/agent_types/quaks/insights/news/` for a complete example:
- **QuaksNewsAnalystAgent**: 4-role sequential pipeline (aggregator → headlines_creator → news_writer → editor)
- Deterministic edges via `add_edge()`, simple chains for tool-less nodes, `create_react_agent` only for the aggregator (which uses `fetch_latest_news` tool)
- External service injection (`MarketsNewsService`)
- Abstract methods (`get_planner`, `get_supervisor`, `get_reporter`) are no-op stubs

### Command Multi-Agentic Pattern
See agent-lab upstream `app/services/agent_types/coordinator_planner_supervisor/` for the dynamic supervisor routing example:
- Uses all four abstract methods with real LLM-based routing logic
- Supervisor node decides which worker to invoke next via structured output
- Supports conditional branching and iterative refinement loops

## ETL Testing Notebooks

When an agent is designed for batch/ETL use cases (e.g., triggered by Airflow DAGs), **always create a companion Jupyter notebook** in `notebooks/` that exercises the full ETL flow via HTTP calls. This allows fast local testing without deploying to Airflow.

### Why

- Airflow DAGs run as Kubernetes tasks — testing requires a full release cycle
- Notebooks reproduce the exact same HTTP flow the DAG performs
- Each step is in its own cell for incremental execution and debugging
- The report can be previewed inline before committing to Elasticsearch

### Notebook Structure

Follow this cell layout (each step is a separate code cell with a markdown header):

1. **Setup** — Load env vars from `.env`, configure endpoints and constants
2. **Authenticate** — `POST /auth/login` with service account credentials
3. **Create Resources** — Create integration → language model → agent via API
4. **Send Message** — `POST /messages/post` with the ETL trigger message (e.g., `BATCH_ETL`)
5. **Preview** — Render the result inline (`display(HTML(...))` or `display(Markdown(...))`)
6. **Index to Elasticsearch** — Bulk index the result into the target ES index

### Naming Convention

`notebooks/{sequence}_{agent_description}_etl.ipynb`

Example: `notebooks/14_insights_quaks_news_analyst_etl.ipynb`

### Required Environment Variables

Document these in the notebook's opening markdown cell:

| Variable | Purpose |
|----------|---------|
| `QUAKS_API_URL` | Backend endpoint (e.g., `http://localhost:18000`) |
| `QUAKS_SERVICE_ACCOUNT_USERNAME` | Service account username |
| `QUAKS_SERVICE_ACCOUNT_SECRET` | Service account password |
| `QUAKS_INTEGRATION_TYPE` | LLM provider type (default: `xai_api_v1`) |
| `QUAKS_INTEGRATION_API_KEY` | LLM provider API key |
| `QUAKS_LANGUAGE_MODEL_TAG` | Model tag (default: agent-specific) |
| `ELASTICSEARCH_URL` | Elasticsearch endpoint |
| `ELASTICSEARCH_API_KEY` | Elasticsearch API key |

### Integration Endpoint Mapping

Use a constant dict to derive the API endpoint from the integration type:

```python
INTEGRATION_ENDPOINTS = {
    "xai_api_v1": "https://api.x.ai/v1/",
    "openai_api_v1": "https://api.openai.com/v1/",
    "anthropic_api_v1": "https://api.anthropic.com",
}
```

### API Flow Pattern

The notebook must replicate the exact HTTP calls the DAG makes:

```python
# 1. Login
login_response = requests.post(f"{API_URL}/auth/login", json={"username": ..., "password": ...})
access_token = login_response.json()["access_token"]
headers = {"Authorization": f"Bearer {access_token}"}

# 2. Create integration
requests.post(f"{API_URL}/integrations/create", json={...}, headers=headers)

# 3. Create language model
requests.post(f"{API_URL}/llms/create", json={"integration_id": ..., "language_model_tag": ...}, headers=headers)

# 4. Create agent
requests.post(f"{API_URL}/agents/create", json={"agent_name": ..., "agent_type": ..., "language_model_id": ...}, headers=headers)

# 5. Send ETL message
requests.post(f"{API_URL}/messages/post", json={"agent_id": ..., "message_role": "human", "message_content": "BATCH_ETL"}, headers=headers, timeout=600)

# 6. Index result into ES
requests.post(f"{ES_URL}/_bulk", headers={"Authorization": f"ApiKey {ES_API_KEY}", ...}, data=bulk_body)
```

### Reference Implementation

See `notebooks/14_insights_quaks_news_analyst_etl.ipynb` for a complete example that tests the `quaks_insights_news` Airflow DAG.

---

## Exposing the Agent Over MCP (Tenant-Scoped)

When the user asks to "expose the agent over MCP", "make it usable from Claude Code", "publish it as a quaks skill", or wants the workflow to be replayable from outside the platform, the agent's prompts and helper tools have to be registered on the FastMCP server. The MCP layer lives in `app/interface/mcp/` and is **per-tenant by construction** — every prompt resolution and tool call is scoped by the JWT `sub` claim of the calling user.

### Why MCP and the Backend Agent Coexist

The LangGraph agent and the MCP registrar are **two views of the same workflow**:

- The LangGraph agent runs server-side, owns checkpointing, and is invoked synchronously by the Quaks UI or asynchronously by an Airflow DAG (BATCH_ETL message).
- The MCP registrar exports each role's **system prompt** as an MCP prompt, each pure-data lookup as an **MCP tool**, and the publish step as a shared `publish_content_mcp` tool. The orchestration of those primitives lives in a **client-side Claude skill** under `plugins/quaks-agents/skills/<agent>/SKILL.md`.

This split is deliberate: the heavy LLM cost (and the tenant's choice of frontier model) stays on the user's side, while the platform supplies its tenant-tuned prompts and proprietary data tools. Only generate the MCP side when the user actually wants external replayability — the LangGraph agent is sufficient for ETL-only use cases.

### Registrar Architecture

`McpRegistrar` (`app/interface/mcp/registrar.py`) is a tiny base class with three optional hooks: `register_tools`, `register_prompts`, `register_resources`. `build_mcp_server` (`app/interface/mcp/server.py`) iterates a list of registrars and calls all three hooks on each. The list is assembled in `Container` as `mcp_registrars = providers.List(...)` and consumed once in `app/main.py`.

Registrars come in two flavours:

- **`DefaultToolRegistrar`** — platform-wide tools (`get_agent_list`, `publish_content_mcp`). Always present. Do not modify when adding a new agent.
- **Per-agent registrar** (e.g. `NewsToolRegistrar`, `FinancialAnalystV1ToolRegistrar`) — owns the tools, prompts, and resources for one agent's workflow. **You add one of these per new agent.**

### Tenant Scoping: The Two Paths

Tenant scope flows through two helpers that you should reuse rather than reimplement:

- **`_get_mcp_schema()`** (`app/interface/mcp/schema.py`) — Reads `get_access_token()` from FastMCP, extracts `sub`, prefixes it (`f"id_{sub}"`), and delegates to `app.infrastructure.auth.user.get_schema()`. Returns `"public"` when auth is disabled. Use this in **tools** that need tenant-scoped DB or Elasticsearch reads.
- **`UserPromptResolver`** (`app/interface/mcp/user_prompt_resolver.py`) — For each `(agent_type, setting_key)` pair, looks up whether the authenticated tenant has saved a custom system prompt under their schema. If yes, renders the user's template; if it raises during render, logs the error and falls back to the bundled default. If the schema is `"public"` or the agent isn't installed in the tenant's schema, returns the default. Use this in **prompts and resources** so per-tenant customisation works transparently.

The tenant override mechanism is what lets a user open the Quaks UI, edit the `coordinator_system_prompt` for their copy of an agent, and immediately see their edits reflected when they next call the MCP `prompts/get` endpoint from Claude Code — without code changes or redeploys.

### Per-Agent Registrar File Skeleton

Place the new file at `app/interface/mcp/<agent_name>_tool_registrar.py`. The skeleton below captures every conventional element observed in `news_tool_registrar.py` and `financial_analyst_v1_tool_registrar.py`:

```python
from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Annotated, Optional

from fastmcp import FastMCP
from jinja2.sandbox import SandboxedEnvironment
from pydantic import Field

from app.interface.mcp.registrar import McpRegistrar
from app.interface.mcp.user_prompt_resolver import UserPromptResolver
from app.services.agent_types.<path>.<agent>.prompts import (
    COORDINATOR_SYSTEM_PROMPT,
    EXECUTION_PLAN,
    REPORTER_SYSTEM_PROMPT,
    # ... one default per role
)

if TYPE_CHECKING:
    from app.core.container import Container

_AGENT_TYPE = "<agent_type_key>"  # MUST match the key registered in AgentRegistry

_ROLE_SETTING_KEYS = {
    "coordinator": "coordinator_system_prompt",
    "reporter": "reporter_system_prompt",
}

_DEFAULT_TEMPLATES = {
    "coordinator": COORDINATOR_SYSTEM_PROMPT,
    "reporter": REPORTER_SYSTEM_PROMPT,
}

_JINJA_ENV = SandboxedEnvironment()  # sandboxed — never use a plain Environment


def _render_prompt(template_str: str, current_time: str | None = None) -> str:
    if current_time is not None and not current_time.strip():
        raise ValueError("current_time must be a non-empty string when provided")
    template = _JINJA_ENV.from_string(template_str)
    resolved_time = current_time or datetime.now().strftime("%a %b %d %Y %H:%M:%S %z")
    return template.render(CURRENT_TIME=resolved_time, EXECUTION_PLAN=EXECUTION_PLAN)


class <Agent>ToolRegistrar(McpRegistrar):
    def __init__(self, user_prompt_resolver: UserPromptResolver) -> None:
        self._user_prompt_resolver = user_prompt_resolver

    def _resolve_prompt(self, role: str, current_time: str | None = None) -> str:
        return self._user_prompt_resolver.resolve(
            agent_type=_AGENT_TYPE,
            setting_key=_ROLE_SETTING_KEYS[role],
            default_template=_DEFAULT_TEMPLATES[role],
            render=lambda t: _render_prompt(t, current_time=current_time),
        )

    def register_tools(self, mcp: FastMCP, container: Container) -> None:
        @mcp.tool(
            name="<verb>_<noun>_mcp",
            description="<one-paragraph LLM-facing description, including source>",
            annotations={"readOnlyHint": True, "openWorldHint": False},
        )
        async def my_tool(
            arg: Annotated[str, Field(description="...")],
        ) -> dict:
            svc = container.<service>()  # already tenant-scoped where applicable
            return svc.fetch(arg.upper())

    def register_prompts(self, mcp: FastMCP) -> None:
        @mcp.prompt(
            name=f"{_AGENT_TYPE}_coordinator",
            description="System prompt for the coordinator step. ...",
        )
        def coordinator(
            current_time: Annotated[Optional[str], Field(description="...")] = None,
        ) -> str:
            return self._resolve_prompt("coordinator", current_time=current_time)

    def register_resources(self, mcp: FastMCP) -> None:
        @mcp.resource(
            uri=f"prompt://{_AGENT_TYPE}_coordinator",
            name=f"{_AGENT_TYPE}_coordinator",
            description="System prompt for the coordinator step.",
        )
        def resource_coordinator() -> str:
            return self._resolve_prompt("coordinator")
```

A few non-obvious rules baked into the skeleton:

- The `_AGENT_TYPE` constant **must** match the key registered in `AgentRegistry`, otherwise `UserPromptResolver` will never find the user's saved settings (it filters `agents` by `agent_type`).
- The role-to-setting-key map **must** match the keys persisted in `create_default_settings` on the agent class — that's how the UI overrides flow through to MCP.
- Every `@mcp.prompt` should have a mirrored `@mcp.resource` at `prompt://<name>`. Some MCP clients only consume resources; others only consume prompts — registering both costs nothing and keeps both clients happy.
- Pure data tools must be `async def` and use `Annotated[..., Field(...)]` for every argument. The `Field(description=...)` text is what shows up in the LLM's tool listing — write it for an LLM, not for a developer.
- Set `annotations={"readOnlyHint": True, "openWorldHint": False}` on read-only data tools. Set `readOnlyHint: False` for tools that mutate state (publishes, writes).
- Use `jinja2.sandbox.SandboxedEnvironment`, never `jinja2.Environment` — user-supplied prompt templates run through this and a sandbox prevents template injection.

### Tools That Need Tenant-Scoped Data

If your tool reads from PostgreSQL or per-tenant Elasticsearch indices, derive the schema from the access token:

```python
from app.interface.mcp.schema import _get_mcp_schema

@mcp.tool(name="get_agent_list", ...)
async def get_agent_list() -> list[AgentItem]:
    schema = _get_mcp_schema()
    return container.agent_service().get_agents(schema)
```

If your tool reads from a global index (e.g. `quaks_markets-news_latest`, `quaks_stocks-eod_latest`), no schema is needed — the data is shared across tenants. The current pattern in `news_tool_registrar` and `financial_analyst_v1_tool_registrar` uses global indices and only the prompts are tenant-scoped; that is intentional and the right default unless the user explicitly asks for tenant-scoped tool data.

### Returning Structured Data: Add Pydantic Models to `schema.py`

When a tool returns more than a primitive, declare a `BaseModel` in `app/interface/mcp/schema.py` and use it as the return annotation. FastMCP serialises the model into JSON schema for the tool descriptor automatically. Keep field descriptions LLM-friendly (the same text appears in the tool listing). For paginated lists, include a `cursor: Optional[str]` field that the tool can echo back — see `NewsList` / `InsightsNewsList` for the canonical shape.

### Wire the Registrar in the Container

Edit `app/core/container.py`:

```python
<agent>_tool_registrar = providers.Singleton(
    <Agent>ToolRegistrar,
    user_prompt_resolver=user_prompt_resolver,  # already a singleton in the container
)

mcp_registrars = providers.List(
    default_tool_registrar,
    news_tool_registrar,
    financial_analyst_v1_tool_registrar,
    <agent>_tool_registrar,  # add here
)
```

The registrar is a `Singleton` and stateless — do **not** make it a `Factory`, otherwise FastMCP will register the same prompts twice if the container is queried twice during startup.

### Update the Server Instructions

`_SERVER_INSTRUCTIONS` in `app/interface/mcp/server.py` is a free-form Markdown blob that ships as the MCP server's `instructions` field. Add three things for a new agent:

1. One bullet per new tool under **Available tools**.
2. One bullet per new prompt under **Available prompts (`<agent>` workflow)**.
3. A numbered "**To replicate the full `<agent>` workflow**" section that mirrors the steps the client-side skill performs.

These instructions show up in the MCP client's discovery response and are the LLM's first-pass understanding of the server — keep them tight and behaviour-focused.

### Publishing the Agent's Output

`publish_content_mcp` (already in `DefaultToolRegistrar`) is the **shared output sink** for every agent that produces a publishable artefact. Do not register a per-agent publish tool. The flow:

1. The skill instructs the client LLM to convert its final output to HTML and call `publish_content_mcp` with `key_skill_name` set to the slash-prefixed skill name (e.g. `/news_analyst`, `/financial_analyst_v1`).
2. `PublishedContentService` checks `key_skill_name` against `ALLOWED_SKILLS` (a `frozenset` in `app/services/published_content.py`) — **add the new skill name there, otherwise calls are rejected with `UnauthorizedSkillError`**.
3. The author identity is the `preferred_username` claim from the access token (Keycloak), not user-supplied.
4. Document IDs are `sha256(executive_summary + author_username + skill_name)` — re-publishing the same summary returns `"duplicate"`, not an error.

### Testing the Registrar

Add a `tests/unit/test_<agent>_tool_registrar.py` modelled on `test_news_tool_registrar.py` and `test_financial_analyst_v1_tool_registrar.py`. The pattern is:

- Mock `UserPromptResolver` to return a known template string and assert the rendered output contains expected substrings.
- Mock `container.<service>()` and assert the tool calls hit the right service method with the right arguments.
- Cover both the "user has overridden the prompt" path (resolver returns the override) and the "default template" path (resolver returns the bundled default).

Run with `uv run pytest tests/unit/test_<agent>_tool_registrar.py -v`.

---

## Publishing as a Claude Skill (`quaks-agents` plugin)

Once the MCP layer is up, package the workflow as an external skill so end users can invoke it from Claude Code with `/quaks-agents:<agent>`.

### Skill File Layout

The plugin lives at the repo root under `plugins/quaks-agents/`:

```
plugins/quaks-agents/
├── .mcp.json                       # MCP server URL — shared by every skill in the plugin
├── .claude-plugin/
│   └── plugin.json                 # plugin metadata (name, version, keywords)
└── skills/
    ├── news-analyst/SKILL.md
    ├── financial-analyst-v1/SKILL.md
    └── <new-agent>/SKILL.md        # add yours here
```

`.mcp.json` already points at `https://quaks.ai/mcp/` — do not duplicate it per skill. `plugin.json`'s `version` field is bumped automatically by `python-semantic-release`.

### SKILL.md Anatomy

Each `SKILL.md` is a self-contained playbook the Claude client reads on `/quaks-agents:<agent>`. The structure used by both existing skills:

1. **Frontmatter** — `name`, then a `description` that combines the explicit slash-invocation hint with **trigger phrases** ("Also use this skill when the user asks to ..."). The triggers are what get the skill picked up automatically when the user doesn't type the slash command.
2. **Title + role line** — "You are the Quaks &lt;Agent&gt; — ..." establishes voice and one-sentence purpose.
3. **MCP Server Resources** — explicit list of every prompt and tool the skill will use, copied verbatim from the registrar's names. This is what Claude consults to know what's available.
4. **Mode Selection** — deterministic rules for picking between QA mode (answer directly using the coordinator prompt) and the full multi-step pipeline. Use keyword matching, not LLM judgement, so behaviour is predictable. Reference: news-analyst keys off briefing keywords; financial-analyst-v1 keys off ticker-shaped tokens.
5. **One section per pipeline step** — each step is a short numbered list: load prompt → adopt prompt → call tools / produce output. Be explicit about what feeds into the next step ("the reporter step needs the full article content; do not summarise in the aggregator").
6. **Writing guidelines** — voice, formatting rules, ticker formatting (`(SYMBOL)`), currency formatting (`USD ` prefix, never `$`), allowed HTML tags. These live in the skill, not the prompt, because they're client-side post-processing rules.
7. **Publish step** — extract executive summary, convert to HTML if needed, call `publish_content_mcp`, handle each of the four return statuses (`published`, `duplicate`, `rejected`, auth error). Always show the user the full report when publish fails so the work isn't lost.

### Skill Description Rules

The frontmatter description is the **only** mechanism that drives auto-triggering. Make it pushy:

- Lead with what the skill produces.
- Add `Invoke explicitly with /quaks-agents:<name>.`
- Add `Also use this skill when the user asks to ...` followed by 6-10 paraphrases of trigger intents — domain keywords, ratio names, indicator names, action verbs.
- End with `even if they don't mention 'quaks' or '<agent>' by name.`

### When to Add a New Skill vs Extend an Existing One

Add a new skill when the workflow has a distinct deliverable and audience (e.g. financial analysis vs market briefing). Extend an existing skill when the new behaviour is a different mode of the same workflow (e.g. add a "compact" briefing mode to news-analyst). Each skill costs the user one `/quaks-agents:<name>` slot in their plugin menu, so prefer extension when in doubt.

---

## End-to-End Build Order for a New MCP-Exposed Agent

When the user wants both halves, follow this order — each step is verifiable on its own and unblocks the next:

1. **Backend agent** (LangGraph) → verify: `uv run pytest tests/unit/test_<agent>.py` passes and `make run` boots without import errors.
2. **AgentRegistry + Container + `valid_agent_types`** → verify: `POST /agents/create` accepts the new `agent_type`.
3. **Default settings + prompts** → verify: `GET /agents/{id}/settings` returns the seeded role prompts.
4. **MCP registrar** (`app/interface/mcp/<agent>_tool_registrar.py`) → verify: `tests/unit/test_<agent>_tool_registrar.py` passes both the user-override and default-template paths.
5. **Container wiring** (`mcp_registrars`) + **`_SERVER_INSTRUCTIONS`** update → verify: `make run` and curl `https://localhost/mcp/` returns the new tool/prompt names.
6. **Allowlist** in `PublishedContentService.ALLOWED_SKILLS` (only if the skill will publish) → verify: a manual `publish_content_mcp` call from Claude Code returns `"published"` instead of `"rejected"`.
7. **`plugins/quaks-agents/skills/<agent>/SKILL.md`** → verify: `/quaks-agents:<agent>` in a fresh Claude Code session loads the skill, fetches the prompts from the live MCP server, and produces a final artefact identical in shape to the in-process LangGraph agent's output.
8. **Companion ETL notebook** (only if the agent has a BATCH_ETL trigger) — see the prior section.

Stop and confirm with the user before moving past step 5; the cost of a wrong tool name or a mismatched `_AGENT_TYPE` is silent fallback to defaults rather than a loud failure, so it pays to verify discovery against the running server before writing the client-side skill.
