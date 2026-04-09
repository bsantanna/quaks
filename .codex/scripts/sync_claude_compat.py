#!/usr/bin/env python3

from __future__ import annotations

import json
import re
import shutil
from pathlib import Path
from textwrap import dedent


ROOT = Path(__file__).resolve().parents[2]
CLAUDE_DIR = ROOT / ".claude"
CODEX_DIR = ROOT / ".codex"
SKILLS_DIR = CODEX_DIR / "skills"
AGENTS_DIR = CODEX_DIR / "agents"
SAFE_SKILL_NAME = re.compile(r"^[a-z0-9][a-z0-9_-]*$")


def split_frontmatter(text: str) -> tuple[list[str], str]:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return [], text.strip() + "\n"

    frontmatter: list[str] = []
    for index, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            body = "\n".join(lines[index + 1 :]).strip() + "\n"
            return frontmatter, body
        frontmatter.append(line)

    return [], text.strip() + "\n"


def parse_frontmatter(lines: list[str]) -> dict[str, str]:
    data: dict[str, str] = {}
    current_key: str | None = None
    current_value: list[str] = []

    def flush() -> None:
        nonlocal current_key, current_value
        if current_key is None:
            return
        data[current_key] = "\n".join(current_value).strip()
        current_key = None
        current_value = []

    for line in lines:
        key_match = re.match(r"^([A-Za-z0-9_-]+):\s*(.*)$", line)
        if key_match and not line.startswith("  "):
            flush()
            current_key = key_match.group(1)
            current_value = [key_match.group(2).strip()]
            continue

        if current_key is not None:
            current_value.append(line.rstrip())

    flush()
    return data


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def ensure_within(base: Path, candidate: Path) -> Path:
    resolved_base = base.resolve()
    resolved_candidate = candidate.resolve()
    resolved_candidate.relative_to(resolved_base)
    return resolved_candidate


def validate_skill_name(name: str, source: str) -> str:
    if not SAFE_SKILL_NAME.fullmatch(name):
        raise ValueError(
            f"Invalid skill name {name!r} in {source}. "
            "Skill names must match ^[a-z0-9][a-z0-9_-]*$."
        )
    return name


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.rstrip() + "\n", encoding="utf-8")


def load_skills() -> list[dict[str, str]]:
    skills: list[dict[str, str]] = []

    for skill_file in sorted(CLAUDE_DIR.glob("skills/*/SKILL.md")):
        raw_text = read_text(skill_file)
        frontmatter_lines, body = split_frontmatter(raw_text)
        meta = parse_frontmatter(frontmatter_lines)
        name = validate_skill_name(
            meta.get("name", skill_file.parent.name).strip(),
            str(skill_file.relative_to(ROOT)),
        )
        description = meta.get("description", "").strip()

        skills.append(
            {
                "name": name,
                "description": description,
                "source": str(skill_file.relative_to(ROOT)),
                "body": body,
            }
        )

    return skills


def extract_section(text: str, heading: str, next_headings: list[str] | None = None) -> str:
    pattern = re.compile(rf"(?ms)^## {re.escape(heading)}\n(.*?)(?=^## |\Z)")
    match = pattern.search(text)
    if not match:
        return ""

    content = match.group(1).rstrip()
    if not next_headings:
        return content

    for next_heading in next_headings:
        marker = f"\n## {next_heading}\n"
        if marker in content:
            content = content.split(marker, 1)[0].rstrip()
    return content


def render_claude_shared_context() -> list[str]:
    claude_text = read_text(CLAUDE_DIR / "CLAUDE.md")
    general_guidelines = extract_section(claude_text, "General Guidelines")
    behavioral_guidelines = extract_section(claude_text, "Behavioral Guidelines")
    project_overview = extract_section(claude_text, "Project Overview")
    skills = extract_section(claude_text, "Skills")

    lines = [
        "## Upstream Shared Guidance",
        "",
        "The following material is loaded from `.claude/CLAUDE.md` and should be treated as shared project guidance.",
        "When an item is specific to Claude's UX or approval model, preserve the intent but apply it through the active tool's native mechanisms.",
    ]

    if general_guidelines:
        adapted_guidelines = [
            "Before broad or risky implementation work, explain the intended approach and use the active tool's planning or approval mechanisms when available.",
            "If the request is ambiguous, clarify requirements before making changes.",
            "After finishing code changes, call out relevant edge cases and suggest or run the most appropriate tests.",
            "When a task expands across many files, break it into smaller verifiable steps instead of changing everything at once.",
            "For bugs, prefer starting with a reproducer or regression test before applying the fix.",
            "When corrected by the user, incorporate the correction and avoid repeating the same mistake.",
        ]
        lines.extend(
            [
                "",
                "### General Guidelines",
                "",
                "Adapted from `.claude/CLAUDE.md` for tool-neutral use:",
                "",
            ]
        )
        for guideline in adapted_guidelines:
            lines.append(f"- {guideline}")

    if behavioral_guidelines:
        lines.extend(
            [
                "",
                "### Behavioral Guidelines",
                "",
                behavioral_guidelines,
            ]
        )

    if project_overview:
        lines.extend(
            [
                "",
                "### Project Overview",
                "",
                project_overview,
            ]
        )

    if skills:
        lines.extend(
            [
                "",
                "### Skill Inventory",
                "",
                skills,
            ]
        )

    return lines


def render_codex_agents(skills: list[dict[str, str]]) -> str:
    lines = [
        "# Codex Compatibility Layer",
        "",
        "> Auto-generated from `.claude/CLAUDE.md` and `.claude/skills/*/SKILL.md`.",
        "> Do not edit this file by hand. Regenerate with `python .codex/scripts/sync_claude_compat.py`.",
        "",
        "## Purpose",
        "",
        "This directory makes Codex reuse the existing Claude-oriented project specs without preloading all skill context on every session.",
        "The vendor-neutral source of truth remains in `.claude/` and `.mcp.json`.",
        "",
        "## Base Behavior",
        "",
        "- Think before coding. State assumptions, surface ambiguity, and clarify when needed.",
        "- Prefer the simplest change that solves the task.",
        "- Keep edits surgical and directly traceable to the request.",
        "- Define success criteria and verify the result.",
        "",
        "## Progressive Context Loading",
        "",
        "- Treat `.claude/CLAUDE.md` as upstream project memory.",
        "- Do not preload all generated skill documents by default.",
        "- If the user explicitly asks for a skill, load only the matching `.codex/skills/<name>/AGENTS.md`.",
        "- If the user invokes a slash-like token such as `/quant`, interpret it as a request to load the matching skill context even though Codex CLI reserves native slash commands for built-ins.",
        "- If the user asks to use a specialist agent, prefer the matching custom agent in `.codex/agents/<name>.toml`.",
        "- Keep vendor-neutral guidance in `.claude/` and only put Codex glue in `.codex/`.",
        "",
    ]

    lines.extend(render_claude_shared_context())
    lines.extend(
        [
            "",
        "## Available Skill Contexts",
        "",
        ]
    )

    for skill in skills:
        lines.append(f"- `{skill['name']}` -> `.codex/skills/{skill['name']}/AGENTS.md`")
        if skill["description"]:
            lines.append(f"  {skill['description']}")

    lines.extend(
        [
            "",
            "## Entry Points",
            "",
            "- Start a skill-scoped Codex session with `./codex-skill <name>`.",
            "- Use `./codex-skill <name> \"task...\"` to launch a one-shot prompt with only that skill context loaded on top of the base repo instructions.",
            "- Inside an existing session, ask Codex to load `.codex/skills/<name>/AGENTS.md` when you want that context.",
            "",
            "## Compatibility Notes",
            "",
            "- Tool-local files such as `.claude/settings.local.json` are not part of the shared cross-tool contract and are intentionally not mirrored here.",
            "- `.mcp.json` is the shared MCP server declaration for this repository.",
            "- Run `python .codex/scripts/sync_claude_compat.py` after changing `.claude/CLAUDE.md` or any Claude skill.",
        ]
    )

    return "\n".join(lines) + "\n"


def render_skill_agents(skill: dict[str, str]) -> str:
    description = skill["description"] or "No description provided."
    return (
        f"# Skill: {skill['name']}\n\n"
        f"> Auto-generated from `{skill['source']}`.\n"
        "> Load this file only when the user explicitly requests this skill or when a skill-scoped session is launched.\n"
        "> Do not edit this file by hand. Regenerate with `python .codex/scripts/sync_claude_compat.py`.\n\n"
        "## Purpose\n\n"
        f"{description}\n\n"
        "## Activation\n\n"
        f"- This context is for the `{skill['name']}` skill only.\n"
        f"- It should augment the base repo `AGENTS.md`, not replace it.\n"
        f"- Prefer loading this file through `./codex-skill {skill['name']}` or by explicitly asking Codex to read `.codex/skills/{skill['name']}/AGENTS.md`.\n\n"
        "## Source Skill\n\n"
        f"{skill['body'].rstrip()}\n"
    )


def render_custom_agent(skill: dict[str, str]) -> str:
    description = skill["description"] or "Specialist agent."
    body = skill["body"].rstrip()
    instructions = (
        "You are a specialist agent generated from the repository's reusable skill definitions.\n"
        "Stay within the scope of this skill unless the parent agent explicitly broadens the task.\n\n"
        f"{body}\n"
    )
    if "'''" not in instructions:
        rendered_instructions = "developer_instructions = '''\n" + instructions + "'''\n"
    else:
        escaped = instructions.replace("\\", "\\\\").replace('"""', '\\"\\"\\"')
        rendered_instructions = 'developer_instructions = """\n' + escaped + '"""\n'
    return (
        f'name = "{skill["name"]}"\n'
        f'description = "{description.replace(chr(34), chr(39))}"\n'
        f"{rendered_instructions}"
    )


def render_codex_readme(skills: list[dict[str, str]]) -> str:
    lines = [
        "# Codex Compatibility",
        "",
        "This directory mirrors the reusable Claude project specs into Codex-friendly files.",
        "",
        "## Source of truth",
        "",
        "- `.claude/CLAUDE.md` for shared project memory",
        "- `.claude/skills/*/SKILL.md` for reusable task specializations",
        "- `.mcp.json` for shared MCP server metadata",
        "",
        "## Generated artifacts",
        "",
        "- `.codex/AGENTS.md` defines the base compatibility and progressive loading rules.",
        "- `.codex/skills/*/AGENTS.md` hold the heavy skill context and are meant to be loaded only on demand.",
        "- `.codex/agents/*.toml` provide optional skill-scoped custom agents.",
        "- `.codex/source-map.json` records the source-to-generated mapping.",
        "",
        "## Progressive-loading entrypoints",
        "",
    ]

    for skill in skills:
        lines.append(f"- `./codex-skill {skill['name']}`")

    lines.extend(
        [
            "",
            "Inside an existing Codex session, you can also say `load .codex/skills/<name>/AGENTS.md for this task`.",
            "",
            "## Regeneration",
            "",
            "Run:",
            "",
            "```bash",
            "python .codex/scripts/sync_claude_compat.py",
            "```",
        ]
    )

    return "\n".join(lines) + "\n"


def render_config() -> str:
    return dedent(
        """\
        # Repo-local Codex compatibility settings.
        # Keep this file intentionally small and portable.

        project_doc_fallback_filenames = ["CLAUDE.md"]
        """
    )


def build_source_map(skills: list[dict[str, str]]) -> dict[str, object]:
    return {
        "project_memory": {
            "source": ".claude/CLAUDE.md",
            "generated": ".codex/AGENTS.md",
            "entrypoint": "AGENTS.md",
        },
        "mcp": {
            "source": ".mcp.json",
            "note": "Shared vendor-neutral MCP metadata.",
        },
        "skills": [
            {
                "name": skill["name"],
                "source": skill["source"],
                "generated_skill_context": f".codex/skills/{skill['name']}/AGENTS.md",
                "generated_custom_agent": f".codex/agents/{skill['name']}.toml",
            }
            for skill in skills
        ],
    }


def remove_stale_generated(skills: list[dict[str, str]]) -> None:
    active_skill_names = {skill["name"] for skill in skills}

    if SKILLS_DIR.exists():
        for path in SKILLS_DIR.iterdir():
            if path.name == "README.md":
                continue
            if path.is_dir() and path.name not in active_skill_names:
                shutil.rmtree(path)

    if AGENTS_DIR.exists():
        for path in AGENTS_DIR.glob("*.toml"):
            if path.stem not in active_skill_names:
                path.unlink()


def main() -> None:
    skills = load_skills()

    remove_stale_generated(skills)

    write_text(CODEX_DIR / "AGENTS.md", render_codex_agents(skills))
    write_text(CODEX_DIR / "README.md", render_codex_readme(skills))
    write_text(CODEX_DIR / "config.toml", render_config())
    write_text(SKILLS_DIR / "README.md", "# Skills\n\nGenerated progressive-loading skill contexts.\n")
    write_text(AGENTS_DIR / "README.md", "# Agents\n\nGenerated custom agents derived from Claude skills.\n")

    for skill in skills:
        skill_context_path = ensure_within(
            SKILLS_DIR,
            SKILLS_DIR / skill["name"] / "AGENTS.md",
        )
        custom_agent_path = ensure_within(
            AGENTS_DIR,
            AGENTS_DIR / f"{skill['name']}.toml",
        )
        write_text(skill_context_path, render_skill_agents(skill))
        write_text(custom_agent_path, render_custom_agent(skill))

    source_map = build_source_map(skills)
    write_text(CODEX_DIR / "source-map.json", json.dumps(source_map, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
