<h2 align="center"><a href="https://github.com/bsantanna/quaks">Quaks</a></h2>
<h4 align="center">Quantitative Agents for Asset Management, Pricing & Alpha Seeking</h4>

<div align="center">

[![Continuous Integration](https://github.com/bsantanna/quaks/actions/workflows/build.yml/badge.svg)](https://github.com/bsantanna/quaks/actions/workflows/build.yml)
[![Quality Gate](https://sonarcloud.io/api/project_badges/measure?project=bsantanna_quant-agents&metric=alert_status)](https://sonarcloud.io/dashboard?id=bsantanna_quant-agents)
[![Coverage](https://sonarcloud.io/api/project_badges/measure?project=bsantanna_quant-agents&metric=coverage)](https://sonarcloud.io/component_measures?metric=coverage&selected=bsantanna_quant-agents%3Aapp&id=bsantanna_quant-agents)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-009485.svg?logo=fastapi&logoColor=white)](#architecture)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](doc/LICENSE.md)

</div>

---

## Overview

**Quaks** (formerly *quant-agents*) is a multi-agent platform for quantitative finance built on top of [Agent-Lab](https://github.com/bsantanna/agent-lab). It extends Agent-Lab's cloud-native agent framework with a specialized financial data pipeline, market-aware agents, and infrastructure tailored for asset management workflows.

The platform ingests end-of-day market data, financial statements, insider trades, news feeds, and technical indicators into Elasticsearch, then exposes that data to LLM-powered agents capable of research, analysis, and reporting.

## Key Capabilities

- **Market Data Ingestion** -- Airflow DAGs fetch stocks EOD (OHLCV), financial statements, insider trades, earnings estimates, and news headlines via the Alpaca Markets API on a scheduled cadence.
- **Technical Indicator Queries** -- Elasticsearch search templates for RSI, MACD, EMA, ADX, OBV, Stochastic Oscillator, CCI, and Accumulation/Distribution.
- **Multi-Agent Orchestration** -- Coordinator-Planner-Supervisor pattern delegates tasks across specialized roles (Researcher, Coder, Browser Reporter) using LangGraph state graphs.
- **Adaptive RAG** -- Retrieval-Augmented Generation with query rewriting and answer/retrieval grading for high-quality responses grounded in indexed data.
- **Multi-LLM Support** -- Dynamically switch between Claude, GPT, Ollama, Grok/XAI per agent.
- **Full Observability** -- OpenTelemetry instrumentation with Prometheus, Grafana, Loki, and Tempo.

## Architecture

```
                      Angular 20 Frontend
                             |
                        FastAPI (REST / MCP)
                             |
              +--------------+--------------+
              |              |              |
        Agent Registry   LangGraph     LLM Service
              |           Workflows    (Claude, GPT,
         Agent Types         |         Ollama, Grok)
              |              |
   +----------+----------+  |
   |          |           |  |
Adaptive  Coordinator  React |
  RAG     Planner-     RAG   |
          Supervisor         |
              |              |
     +--------+--------+----+----+
     |        |         |        |
  Postgres  Redis  Elasticsearch  Vault
  (pgvector)       (market data)  (secrets)
                        |
                   Airflow DAGs
                   (data ingestion)
```

### Upstream: Agent-Lab

Quaks inherits its core architecture from [Agent-Lab](https://github.com/bsantanna/agent-lab), an MIT-licensed cloud-native toolkit for building LLM-powered autonomous agents. Agent-Lab provides:

- Clean Architecture with dependency injection (`dependency-injector`)
- Agent base classes and LangGraph workflow abstractions
- PostgreSQL persistence (relational + pgvector + LangGraph checkpoints)
- Keycloak authentication, Vault secrets management
- MCP server for agent-to-agent communication
- Kubernetes Helm charts and Terraform modules

Quaks adds the financial domain layer: market data pipelines, Elasticsearch index templates with technical indicator search scripts, and quantitative-focused agent configurations.

## Agent Types

| Agent | Description |
|-------|-------------|
| **Coordinator-Planner-Supervisor** | Multi-agent orchestration with plan-execute pattern. Delegates across Researcher, Coder, and Browser Reporter roles. |
| **Adaptive RAG** | Retrieval-Augmented Generation with adaptive query rewriting and graded retrieval/answer quality. |
| **ReAct RAG** | Lightweight ReAct (Reasoning + Acting) agent with tool use and RAG capabilities. |
| **Vision Document** | Analyzes images and documents, extracting structured information from visual inputs. |
| **Voice Memos** | Audio transcription and analysis with content analyst and reporter roles. |
| **Azure Entra ID Voice Memos** | Enterprise variant with Azure Entra ID organization integration. |

## Market Data Pipeline

Airflow DAGs run on a scheduled cadence and ingest the following into Elasticsearch:

| Index | Content |
|-------|---------|
| `stocks-eod` | Daily OHLCV price data |
| `stocks-metadata` | Fundamentals, ratios, company info |
| `stocks-financial-statements` | Income statements, balance sheets, cash flow |
| `stocks-insider-trades` | Insider transaction records |
| `stocks-estimated-earnings` | Analyst earnings estimates |
| `markets-news` | Financial news headlines and summaries |

Terraform manages index lifecycle policies (365-day retention), index templates, and Mustache-based search templates for technical indicators.

## Tech Stack

| Layer | Technologies |
|-------|-------------|
| **Backend** | Python 3.12, FastAPI, SQLAlchemy, Pydantic |
| **AI/ML** | LangChain, LangGraph, langchain-anthropic, langchain-openai, langchain-ollama, langchain-xai |
| **Frontend** | Angular 20, Tailwind CSS, TypeScript |
| **Data Stores** | PostgreSQL (pgvector), Elasticsearch, Redis |
| **Infrastructure** | Docker Compose, Terraform, Apache Airflow |
| **Auth & Secrets** | Keycloak, HashiCorp Vault |
| **Observability** | OpenTelemetry, Prometheus, Grafana, Loki, Tempo |
| **Browser Automation** | browser-use, chromedp |

## Getting Started

### Prerequisites

- Python 3.12+
- Docker & Docker Compose
- Node.js 20+ (for frontend development)

### Local Development

```bash
# Start infrastructure services
docker compose up -d postgres redis vault

# Install Python dependencies
pip install -r requirements.txt

# Run the application
uvicorn app.main:app --host 0.0.0.0 --port 18000 --reload
```

### Full Stack (Docker)

```bash
docker compose up -d
```

This starts the FastAPI app, PostgreSQL (with pgvector), Redis, Vault, headless Chrome, and the full observability stack (OTel Collector, Prometheus, Grafana, Loki, Tempo).

### Terraform Setup

```bash
# Elasticsearch index templates and search scripts
cd terraform/elasticsearch
terraform init && terraform apply

# Kibana dashboards
cd terraform/kibana
terraform init && terraform apply
```

## Project Structure

```
app/
  core/              # Dependency injection container
  domain/            # Models and repository interfaces
  infrastructure/    # Database, auth, metrics
  interface/api/     # REST API routers
  services/          # Business logic and agent implementations
    agent_types/     # Agent type registry and implementations
  static/            # Pre-built frontend assets
dags/                # Airflow DAGs for market data ingestion
docker/              # Dockerfiles (app, dags)
frontend/            # Angular 20 web application
terraform/           # Elasticsearch and Kibana IaC
otel/                # OpenTelemetry collector configuration
notebooks/           # Jupyter notebooks
tests/               # Unit and integration tests
```

## License

This project is licensed under the GPLv3 License. See the [LICENSE](doc/LICENSE.md) file for details.
