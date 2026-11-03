# AGENTS.md

## Agent skills

### Issue tracker

GitHub Issues on a Projects board — milestones as epics, stories as issues, tech tasks as sub-issues. See `docs/agents/issue-tracker.md`.

### Domain docs

Single-context: `GLOSSARY.md` + `docs/adr/` at the repo root. See `docs/agents/domain.md`.

### Spec-driven development (OpenSpec)

Docs have distinct jobs — don't mix them: `docs/PRD.md` = scope contract (what/why, human-validated) · `openspec/specs/` = living behavior specs (how the system behaves) · `docs/adr/` = decision record (why we chose X over Y) · GitHub issues = execution tracking.

- Initialize in US2 if absent: `npx openspec init` (generates `openspec/` + its own `openspec/AGENTS.md`, which is authoritative for CLI details).
- Any behavior change starts as an OpenSpec **change proposal** (`openspec/changes/<id>/`: spec deltas + tasks) BEFORE code. No proposal, no PR.
- Implement proposal tasks with TDD. Never edit `openspec/specs/` directly — specs only change via archived proposals.
- `openspec validate` must pass before merge; `openspec archive` after merge folds deltas into specs.
- A GitHub issue closes only when its change proposal is archived (spec updated = feature truly done).


## MAIN RULES
- main branch protected, 1 review needed
- use conventional commits and conventional branches
- use TDD

## PR POLICY
- the agent never merges PRs (no `gh pr merge`, not even `--admin`): it opens the PR with a review checklist as comment and stops
- the user reviews and merges every PR personally; `--admin` bypass is the user's conscious decision, never the agent's

## NOT TO DO STUFF
- no credencials in code.
- update AGENTS.md, README.md, or docs affected by changes.
- keep away from bloat, max 200 lines this file, keep track if progressive disclosure is used in order to be able to store more information.
- for simple glue/setup scripts do NOT use python: use bash + jq (json parsing included). Python only when there is real logic worth testing.

