# Codex Compatibility

This directory mirrors the reusable Claude project specs into Codex-friendly files.

## Source of truth

- `.claude/CLAUDE.md` for shared project memory
- `.claude/skills/*/SKILL.md` for reusable task specializations
- `.mcp.json` for shared MCP server metadata

## Generated artifacts

- `.codex/AGENTS.md` defines the base compatibility and progressive loading rules.
- `.codex/skills/*/AGENTS.md` hold the heavy skill context and are meant to be loaded only on demand.
- `.codex/agents/*.toml` provide optional skill-scoped custom agents.
- `.codex/source-map.json` records the source-to-generated mapping.

## Progressive-loading entrypoints

- `./codex-skill quaks-generator`
- `./codex-skill quant`
- `./codex-skill seo`
- `./codex-skill software-engineering`

Inside an existing Codex session, you can also say `load .codex/skills/<name>/AGENTS.md for this task`.

## Regeneration

Run:

```bash
python .codex/scripts/sync_claude_compat.py
```
