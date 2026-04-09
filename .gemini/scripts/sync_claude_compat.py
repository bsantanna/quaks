#!/usr/bin/env python3

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CLAUDE_DIR = ROOT / ".claude"
GEMINI_DIR = ROOT / ".gemini"
SKILLS_DIR = GEMINI_DIR / "skills"

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
    for line in lines:
        match = re.match(r"^([A-Za-z0-9_-]+):\s*(.*)$", line)
        if match:
            data[match.group(1)] = match.group(2).strip()
    return data

def extract_section(text: str, heading: str) -> str:
    pattern = re.compile(rf"(?ms)^## {re.escape(heading)}\n(.*?)(?=^## |\Z)")
    match = pattern.search(text)
    return match.group(1).rstrip() if match else ""

def sync():
    # 1. Update GEMINI.md from CLAUDE.md
    claude_md = (CLAUDE_DIR / "CLAUDE.md").read_text()
    behavioral = extract_section(claude_md, "Behavioral Guidelines")
    project_overview = extract_section(claude_md, "Project Overview")
    
    # Simple templates for GEMINI.md
    gemini_md_content = f"""# GEMINI.md

This file provides foundational mandates to Gemini CLI when working with code in this repository. These instructions take absolute precedence over general workflows.

## Source of Truth

The vendor-neutral source of truth for project guidelines and specialized knowledge resides in:
- `.claude/CLAUDE.md`
- `.claude/skills/*/SKILL.md`
- `.mcp.json`

## Behavioral Mandates

{behavioral}

## Project Overview

{project_overview}

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
"""
    (ROOT / "GEMINI.md").write_text(gemini_md_content)

    # 2. Update skills
    for skill_file in CLAUDE_DIR.glob("skills/*/SKILL.md"):
        raw_text = skill_file.read_text()
        frontmatter_lines, body = split_frontmatter(raw_text)
        meta = parse_frontmatter(frontmatter_lines)
        name = meta.get("name", skill_file.parent.name)
        
        skill_dir = SKILLS_DIR / name
        skill_dir.mkdir(parents=True, exist_ok=True)
        
        description = meta.get("description", "")
        
        gemini_skill_content = f"""# {name.replace('-', ' ').title()} Skill

{description}

## Source of Truth
This skill is an adapter for `.claude/skills/{name}/SKILL.md`.

{body}
"""
        (skill_dir / "SKILL.md").write_text(gemini_skill_content)

    print("Gemini compatibility layer synchronized.")

if __name__ == "__main__":
    sync()
