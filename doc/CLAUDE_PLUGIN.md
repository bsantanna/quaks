<div align="center">
  <img src="logo.svg" alt="Quaks Logo" width="200" />
</div>

<h2 align="center"><a href="https://github.com/bsantanna/quaks">Quaks</a></h2>
<h3 align="center">Claude Code Plugin</h3>

---

## Prerequisites

- [Claude Code](https://claude.ai/code) v1.0.33 or later

## Install

### Step 1: Add the marketplace

```bash
/plugin marketplace add bsantanna/quaks
```

### Step 2: Install the plugin

```bash
/plugin install quaks-agents@quaks
```

## Usage

### Investor Briefing

Generate a full investor briefing with the latest market news:

```bash
/quaks-agents:news-analyst
```

### Financial Q&A

Ask a specific financial question:

```bash
/quaks-agents:news-analyst What's happening with NVDA?
```

## What's Included

### MCP Server

The plugin automatically registers the Quaks MCP server (`https://quaks.ai/mcp`), providing access to the following tools:

| Tool | Description |
|------|-------------|
| `get_markets_news_mcp` | Retrieve latest market news articles with optional filters (search term, ticker, days, size) |
| `get_insights_news_mcp` | Retrieve pre-generated investor briefings |
| `get_agent_list` | List available Quaks agents |

### Skills

| Skill | Description |
|-------|-------------|
| `/quaks-agents:news-analyst` | Financial news analyst that produces investor briefings and answers market questions |

## Updating

Refresh the marketplace to get the latest version:

```bash
/plugin marketplace update
```

## Uninstall

```bash
/plugin uninstall quaks-agents@quaks
```
