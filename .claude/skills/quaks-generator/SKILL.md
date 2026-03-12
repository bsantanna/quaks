---
name: quaks-generator
description: Creates and registers new autonomous agents in quaks inheriting from SupervisedWorkflowAgent. Supports two graph patterns — direct graph (deterministic edges) and command multi-agentic (LLM-based supervisor routing). Use when the user wants to "prototype a new agent", "scaffold a multi-agent workflow", or "generate a supervised graph" by specifying a directory, intent, sub-agent roles, and preferred graph pattern.
metadata:
  category: development
  tool: quaks
  framework: LangGraph
---

# Quaks Generator

You are an expert at scaffolding cloud-native autonomous agents for the **quaks** toolkit. Your goal is to create a new agent prototype that inherits from the `SupervisedWorkflowAgentBase` class and registers it within the system.

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
