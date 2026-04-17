# SonarCloud API Reference

Base URL: `https://sonarcloud.io/api/`

**The `organization=bsantanna` parameter is required on all API calls.** Without it, the API returns a 400 error.

## Fetch all open issues (recommended one-liner)

```bash
curl -s "https://sonarcloud.io/api/issues/search?organization=bsantanna&projectKey=bsantanna_quant-agents&ps=100&statuses=OPEN,CONFIRMED" | python3 -c "
import json, sys
data = json.load(sys.stdin)
print(f'Total issues: {data.get(\"total\", 0)}')
for i, issue in enumerate(data.get('issues', []), 1):
    comp = issue.get('component', '').replace('bsantanna_quant-agents:', '')
    print(f'{i}. [{issue.get(\"severity\")}] [{issue.get(\"type\")}] {comp}:{issue.get(\"line\",\"?\")} — {issue.get(\"message\")} (rule: {issue.get(\"rule\")})')
"
```

## Fetch Security Hotspots

```
GET https://sonarcloud.io/api/hotspots/search?organization=bsantanna&projectKey=bsantanna_quant-agents&ps=500&status=TO_REVIEW
```

- `ps` — page size (max 500)
- `status` — `TO_REVIEW` (open), `REVIEWED` (resolved)
- Response includes `hotspots[]` with: `key`, `component`, `securityCategory`, `vulnerabilityProbability` (HIGH/MEDIUM/LOW), `line`, `message`, `ruleKey`

## Fetch Issues (Bugs, Code Smells, Vulnerabilities)

```
GET https://sonarcloud.io/api/issues/search?organization=bsantanna&projectKey=bsantanna_quant-agents&ps=100&statuses=OPEN,CONFIRMED
```

Useful query parameters:
- `types` — `BUG`, `VULNERABILITY`, `CODE_SMELL` (comma-separated)
- `severities` — `BLOCKER`, `CRITICAL`, `MAJOR`, `MINOR`, `INFO`
- `statuses` — `OPEN`, `CONFIRMED`, `REOPENED`, `RESOLVED`, `CLOSED`
- `resolved` — `false` to get only unresolved issues
- `facets` — `severities,types` to get aggregated counts
- Response includes `issues[]` with: `key`, `component`, `line`, `message`, `severity`, `type`, `rule`, `status`

## PR-specific: Quality Gate Debugging

When a PR fails the Sonar quality gate, follow this workflow:

### Step 1 — Check which quality gate conditions failed

```bash
curl -s "https://sonarcloud.io/api/qualitygates/project_status?organization=bsantanna&projectKey=bsantanna_quant-agents&pullRequest=<PR_NUMBER>" | python3 -m json.tool
```

Key conditions: `new_reliability_rating` (bugs), `new_security_rating`, `new_maintainability_rating`, `new_coverage` (≥80%), `new_duplicated_lines_density` (≤3%).

### Step 2 — Find bugs specifically (reliability failures)

```bash
curl -s "https://sonarcloud.io/api/issues/search?organization=bsantanna&projectKey=bsantanna_quant-agents&ps=100&pullRequest=<PR_NUMBER>&inNewCodePeriod=true&types=BUG" | python3 -c "
import json, sys
data = json.load(sys.stdin)
for i, issue in enumerate(data.get('issues', []), 1):
    comp = issue.get('component', '').replace('bsantanna_quant-agents:', '')
    print(f'{i}. [{issue.get(\"severity\")}] {comp}:{issue.get(\"line\",\"?\")} — {issue.get(\"message\")} (rule: {issue.get(\"rule\")})')
"
```

### Step 3 — Find uncovered lines (coverage failures)

```bash
curl -s "https://sonarcloud.io/api/measures/component_tree?organization=bsantanna&component=bsantanna_quant-agents&pullRequest=<PR_NUMBER>&metricKeys=new_coverage,new_uncovered_lines,new_lines_to_cover&ps=100&strategy=leaves&qualifiers=FIL" | python3 -c "
import json, sys
data = json.load(sys.stdin)
for c in data.get('components', []):
    measures = {}
    for m in c.get('measures', []):
        period = m.get('period')
        periods = m.get('periods', [])
        if period: measures[m['metric']] = period.get('value', '')
        elif periods: measures[m['metric']] = periods[0].get('value', '')
    uncovered = measures.get('new_uncovered_lines', '')
    if uncovered and uncovered != '0':
        name = c['key'].replace('bsantanna_quant-agents:', '')
        cov = measures.get('new_coverage', 'N/A')
        lines = measures.get('new_lines_to_cover', '?')
        print(f'cov={cov}% uncovered={uncovered}/{lines} — {name}')
"
```

### Step 4 — Find exact uncovered lines in a file

```bash
curl -s "https://sonarcloud.io/api/sources/lines?key=bsantanna_quant-agents%3A<FILE_PATH_WITH_%2F>&pullRequest=<PR_NUMBER>&from=1&to=1100" | python3 -c "
import json, sys
data = json.load(sys.stdin)
for line in data.get('sources', []):
    cov = line.get('lineHits')
    is_new = line.get('isNew', False)
    if is_new and cov is not None and cov == 0:
        print(f'L{line[\"line\"]}: UNCOVERED')
"
```

Note: File path uses `%2F` for `/` in the URL (e.g., `app%2Fservices%2Fauth.py`).

## Gotchas

- **`inNewCodePeriod=true`** returns ALL issues in the new code period (can be 200+), not just issues introduced by the PR. Use `types=BUG` to narrow down.
- **`app/static/`** is the Angular build output committed to the repo. It's excluded from Sonar analysis via `sonar.exclusions` in `sonar-project.properties`. If Sonar flags issues in build output, verify the exclusion pattern is correct.
- **Agent implementation files** (`app/services/agent_types/**/agent.py`) are excluded from coverage requirements because they require full integration infrastructure (Postgres, Redis, LLM, Elasticsearch) and cannot be unit-tested.
- **`frontend/src/index.html`** is excluded from Sonar because it contains inline bootstrap scripts that trigger false positives (e.g., missing SRI on Google Fonts `<link>` tags).

## Common Rule Keys

| Rule | Category | Description |
|------|----------|-------------|
| `typescript:S6268` | XSS | `bypassSecurityTrustResourceUrl` usage |
| `typescript:S5852` / `python:S5852` | DoS | Regex vulnerable to backtracking |
| `python:S4790` | Crypto | Weak hash function (e.g. MD5) |
| `python:S1192` | Maintainability | Duplicated string literal — extract to constant |
| `python:S1186` | Maintainability | Empty method body — add `pass` with comment |
| `typescript:S7761` | Maintainability | Prefer `.dataset` over `setAttribute('data-*')` |
| `Web:S5725` | Integrity | Missing SRI `integrity` attribute on external `<link>`/`<script>` |
| `Web:MouseEventWithoutKeyboardEquivalentCheck` | Accessibility | Mouse event without keyboard equivalent — add `role`, `tabindex`, `(keydown.enter)`, `(focus)`/`(blur)` |
| `Web:FrameWithoutTitleCheck` | Accessibility | `<iframe>` missing `title` attribute |
