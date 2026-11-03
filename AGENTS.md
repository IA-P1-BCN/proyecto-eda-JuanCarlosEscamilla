# AGENTS.md

## Agent skills

### Issue tracker

GitHub Issues on a Projects board — milestones as epics, stories as issues, tech tasks as sub-issues. See `docs/agents/issue-tracker.md`.

### Domain docs

Single-context: `GLOSSARY.md` + `docs/adr/` at the repo root. See `docs/agents/domain.md`.

### Spec-driven development (OpenSpec)

Docs have distinct jobs — don't mix them: `docs/PRD.md` = scope contract (what/why, human-validated) · `openspec/specs/` = living behavior specs (how the system behaves) · `docs/adr/` = decision record (why we chose X over Y) · GitHub issues = execution tracking.

- Initialized in US2. Re-run if absent: `npx @fission-ai/openspec@latest init . --tools zcode --language es` (generates `openspec/` + `.zcode/` skills; its `openspec/AGENTS.md` is authoritative for CLI details). The npm package `openspec` alone is a 0.0.0 placeholder — always use `@fission-ai/openspec`.
- Any behavior change starts as an OpenSpec **change proposal** (`openspec/changes/<id>/`: spec deltas + tasks) BEFORE code. No proposal, no PR.
- Implement proposal tasks with TDD. Never edit `openspec/specs/` directly — specs only change via archived proposals.
- `openspec validate` must pass before merge; `openspec archive` after merge folds deltas into specs.
- A GitHub issue closes only when its change proposal is archived (spec updated = feature truly done).


## MAIN RULES
- main branch protected, 1 review needed
- use conventional commits and conventional branches
- use TDD

### Repo layout

Monorepo uv workspaces (ADR-0002): `packages/eda_ingesta` (scraper/profiling) · `packages/eda_core` (business logic) · `packages/eda_pipeline` (CLI) · `packages/eda_app` (streamlit). Tests live inside each package (`packages/*/tests`). Notebook at root imports `eda_core` — no logic in notebooks.

### Acceptance criteria

Every user story issue carries its DoD as **Acceptance Criteria: numbered, sequential, verifiable steps** (runnable via `task …`, concrete paths/URLs, expected result after `→`). The AC lives in the issue body and doubles as the review checklist. Template and anti-patterns: `docs/agents/acceptance-criteria.md`.

### Taskfile (requirement)

`Taskfile.yml` at root is the single task runner AND the living documentation of project commands. Every new command (scraper, quarto render, airflow, deploy…) gets a task in the same PR that introduces it. Docs and README point to `task --list`, never to raw commands. Requires go-task (`brew install go-task`).

### README progressive rule

`README.md` reflects the current state: the "Estado del proyecto" checklist and run instructions are updated in the SAME PR as the user story they complete — never leave a placeholder past its story.
### PR workflow

The agent never merges PRs (user merges personally). Small changes extend an OPEN PR instead of opening a new one; unrelated features keep their own PR. Full policy: `docs/agents/pr-workflow.md`.

## NOT TO DO STUFF

## NOT TO DO STUFF
- no credencials in code.
- update AGENTS.md, README.md, or docs affected by changes.
- keep away from bloat, max 200 lines this file, keep track if progressive disclosure is used in order to be able to store more information.
- for simple glue/setup scripts do NOT use python: use bash + jq (json parsing included). Python only when there is real logic worth testing.

