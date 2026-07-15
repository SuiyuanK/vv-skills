# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project purpose

This repository is a **multi-platform skill/plugin** for research-paper writing workflows (not a conventional app/service). It provides a routed skill system for brainstorming, chapter writing, literature review, figures, and LaTeX output.

The main execution model is:
1. Entry/routing via `skills/using-research-writing/SKILL.md`
2. Medium/full-paper orchestration via `skills/paper-orchestration/SKILL.md`
3. Mandatory brainstorming via `skills/brainstorming-research/SKILL.md`
4. Evidence-driven sections via `skills/evidence-driven-writing/SKILL.md`
5. Chapter-by-chapter writing via `skills/writing-chapters/SKILL.md`
6. Optional specialized skills (literature, experiments, figures, review, LaTeX, environment setup)

## Key architecture (big picture)

- `skills/` — Primary modular skill system (authoritative behavior).
  - `using-research-writing/` is the workflow router and rule gate.
  - `paper-orchestration/` handles medium/full-paper task packets, subagent routing, review gates, and capability-use audits.
  - `brainstorming-research/` enforces conversational requirement collection before writing.
  - `evidence-driven-writing/` forces evidence maps and paragraph blueprints before Introduction/Related Work drafting.
  - `writing-chapters/` enforces one-chapter-at-a-time writing with two-stage review.
  - `experiment-results-planning/` separates real results from mock planning data and defines experiment/table/figure handoff.
- `hooks/` — Session-start injection for platforms (especially Claude/Cursor), including loading entry skill context.
  - `hooks/session-start` injects `using-research-writing` content at session start.
  - `hooks/hooks.json` wires SessionStart for Claude plugin.
- `.claude-plugin/plugin.json`, `.cursor-plugin/plugin.json` — Plugin metadata + hook wiring per platform.
- `plan-template/` — Canonical template files copied into user project `plan/`.
- `modules/` — Legacy compatibility docs; keep in sync conceptually with `skills/` behavior.
- `scripts/` — Operational tooling:
  - `init_plan.sh` / `init_plan.ps1`: bootstrap `plan/` from `plan-template/`
  - `style_check.sh` / `style_check.ps1`: writing-style checks for markdown
  - `scholar_search.py`: multi-source literature retrieval + citation formatting
  - `pdf_parser.py`: PDF text/section/metadata extraction

## Workflow invariants to preserve

When editing skills or workflow logic, maintain these repository-level invariants:

- Do not bypass brainstorming for writing tasks.
- Do not bypass `paper-orchestration` for medium/full-paper work.
- Do not draft Introduction or Related Work without an evidence map.
- Keep `plan/` as persistent project memory (`project-overview.md`, `progress.md`, `notes.md`, `outline.md`, `stage-gates.md`).
- Keep chapter flow sequential and confirmation-driven (one chapter at a time, user confirmation before moving on).
- Do not fabricate citations or research facts.
- Do not present mock/synthetic planning data as real results.
- Keep user instructions and process notes out of manuscript body.
- Preserve compatibility across platform entry points (`SKILL.md`, `AGENTS.md`, `GEMINI.md`, plugin manifests, hooks).

## Common commands

> Run from repository root (`research-writing-skill-main`).

### Plan bootstrap

```bash
bash scripts/init_plan.sh
```

Initialize plan for a specific project directory:

```bash
bash scripts/init_plan.sh /path/to/project
```

PowerShell:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/init_plan.ps1
```

### Style/lint-like checks for markdown output

```bash
bash scripts/style_check.sh chapters/01-introduction.md
```

PowerShell:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/style_check.ps1 -FilePath chapters/01-introduction.md
```

### Literature search utility

```bash
python scripts/scholar_search.py "deep learning" --sources crossref --year 2020-2024 --limit 20
```

Export BibTeX:

```bash
python scripts/scholar_search.py "transformer attention" --format bibtex --output refs.bib
```

### PDF parsing utility

```bash
python scripts/pdf_parser.py paper.pdf --sections --json output.json
```

### Test/verification status

There is no dedicated unit-test framework in this repository. Validation is script-level:
- run `style_check` on modified markdown outputs
- run `scripts/check_skill_integrity.ps1` after skill workflow edits
- run `scripts/research_quality_gate.ps1 -ProjectPath <paper-project>` on manuscript workspaces
- run target Python scripts with representative inputs to verify behavior

## Important references

- `README.md` / `README_EN.md` — user-facing positioning, workflow, and platform support.
- `SKILL.md` — legacy/main entry for compatible runtimes.
- `AGENTS.md` and `GEMINI.md` — platform-specific skill-loading entry points.

## Notes on instruction files

No `.cursorrules`, `.cursor/rules/`, or `.github/copilot-instructions.md` were found in this repository at the time of writing this file.
