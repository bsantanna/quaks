# GEMINI.md

This file provides foundational mandates to Gemini CLI when working with code in this repository. These instructions take absolute precedence over general workflows.

## Source of Truth

The vendor-neutral source of truth for project guidelines and specialized knowledge resides in:
- `.claude/CLAUDE.md`
- `.claude/skills/*/SKILL.md`
- `.mcp.json`

## Behavioral Mandates


**Tradeoff:** These guidelines bias toward caution over speed. For trivial tasks, use judgment.

### 1. Think Before Coding

**Don't assume. Don't hide confusion. Surface tradeoffs.**

Before implementing:
- State your assumptions explicitly. If uncertain, ask.
- If multiple interpretations exist, present them - don't pick silently.
- If a simpler approach exists, say so. Push back when warranted.
- If something is unclear, stop. Name what's confusing. Ask.

### 2. Simplicity First

**Minimum code that solves the problem. Nothing speculative.**

- No features beyond what was asked.
- No abstractions for single-use code.
- No "flexibility" or "configurability" that wasn't requested.
- No error handling for impossible scenarios.
- If you write 200 lines and it could be 50, rewrite it.

Ask yourself: "Would a senior engineer say this is overcomplicated?" If yes, simplify.

### 3. Surgical Changes

**Touch only what you must. Clean up only your own mess.**

When editing existing code:
- Don't "improve" adjacent code, comments, or formatting.
- Don't refactor things that aren't broken.
- Match existing style, even if you'd do it differently.
- If you notice unrelated dead code, mention it - don't delete it.

When your changes create orphans:
- Remove imports/variables/functions that YOUR changes made unused.
- Don't remove pre-existing dead code unless asked.

The test: Every changed line should trace directly to the user's request.

### 4. Goal-Driven Execution

**Define success criteria. Loop until verified.**

Transform tasks into verifiable goals:
- "Add validation" → "Write tests for invalid inputs, then make them pass"
- "Fix the bug" → "Write a test that reproduces it, then make it pass"
- "Refactor X" → "Ensure tests pass before and after"

For multi-step tasks, state a brief plan:
```
1. [Step] → verify: [check]
2. [Step] → verify: [check]
3. [Step] → verify: [check]
```

Strong success criteria let you loop independently. Weak criteria ("make it work") require constant clarification.

---

## Project Overview


Quaks is a multi-agent financial agents platform built on [Agent-Lab](https://github.com/bsantanna/agent-lab). It uses LLM-powered agents (LangChain/LangGraph) to perform asset management, market data analysis, and alpha-seeking tasks. The backend is Python/FastAPI, the frontend is Angular 20, and market data flows through Airflow DAGs into Elasticsearch.

## Skill Activation

When the user requests a specialty or uses a slash command (e.g., `/quant`), activate the corresponding Gemini skill located in `.gemini/skills/<name>/SKILL.md`.

- `/software-engineering` — Architecture, common commands, and code conventions.
- `/seo` — SEO audit and optimization.
- `/quant` — Quantitative finance analysis.
- `/quaks-generator` — Agent scaffolding.

## Common Commands

### Backend (Python)
- `make run` — Run app locally.
- `make test` — Run all tests.
- `make lint` — Run linting.
- `ruff format .` — Format code.
- `ruff check --fix .` — Fix linting issues.

### Frontend (Angular)
- `npm start` — Run dev server.
- `npm run build` — Production build.
- `npx jest` — Run tests.

## Regeneration

Run the synchronization script after changing `.claude/CLAUDE.md` or any Claude skill:

```bash
python .gemini/scripts/sync_claude_compat.py
```
