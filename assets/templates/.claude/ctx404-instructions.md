<!-- ctx404:instructions:start version="{{CTX404_VERSION}}" schema="2" -->

# CTX404 Context Protocol

<!--
Managed by CTX404. A reviewed upgrade replaces this file entirely; do not edit it.
Project content belongs in .claude/context/project-definition.md, .claude/context/topics/, or CLAUDE.md.
This is the always-loaded core. Detail that only applies while working with context lives in
.claude/rules/ctx404-context.md, which Claude Code loads on its own when .claude/context/ is touched.
-->

This repository owns its durable context. Chat history and global model memory are not project records. Anything stored outside the repository does not reach other machines through `git pull`, so it is not a project record however convenient it looks.

Claude Code auto memory is disabled for this project. `.claude/context/` is the portable, Git-versioned continuity system.

{{AUTHORITY_POLICY}}

## Start every session

1. Use the compact CTX404 status injected by the `SessionStart` hook as initial context.
2. If the hook reports that status is unavailable, run `python .claude/scripts/context_tool.py status` once as a fallback.
3. Do not re-read `.claude/context/index.json` or `.claude/context/current.json` unless raw fields are required for the task or an update.
4. Match the user's request to the returned topics and load only the relevant files.
5. Do not read the full operational history or scan the entire repository unless the task requires it.
6. Do not ask for information already recorded and valid. Ask only when context is absent, contradictory, or insufficient for a material decision.

## Maintain context after relevant work

Deliberation is durable context: the repo shows state, never why. Record decisions, the options the user rejected and why, reversals, the structure discussed, constraints revealed, and any durable change, blocker, next step, or discovery. An unrecorded rejection returns next session as a fresh suggestion, never reconsidered on purpose.

Read `.claude/rules/ctx404-context.md` for the procedure. Do not improvise it, hand-write timestamps, or edit `current.json` directly.

Skip greetings, repetition, and lookups that revealed nothing. No file changed is not an exemption: would a future session ask this again? The `Stop` hook blocks a session that deliberated without recording.

## Route work by cost

Judgment or responsibility → Opus. Deterministic bookkeeping → the Python helper. Finding unknown facts → `context-scout` (Haiku). Synthesizing several sources → `context-curator` (Sonnet). One known file that is cheaper to read directly → read it directly.

Opus keeps user intent, ambiguity, architecture, consequential planning, risk analysis, critical validation, and final communication. Never delegate those merely because an auxiliary agent can attempt them. Treat auxiliary output as evidence and recheck it before consequential decisions.

## Communicate compactly

- Lead with the result. Remove filler, repeated facts, decorative formatting, and unnecessary narration.
- Preserve exact technical terms, commands, code, API names, and decisive error text.
- Do not invent abbreviations or dump full files and logs unless requested.
- Prefer professional clarity over compression for security warnings, irreversible actions, and ordered procedures.

## Where things live

- `.claude/ctx404-instructions.md` — this managed core protocol.
- `.claude/rules/ctx404-context.md` — context-writing procedure, loaded automatically when `.claude/context/` is touched.
- `.claude/context/project-definition.md` — project identity and scope. Project-owned; CTX404 never rewrites it.
- `.claude/context/` — index, current state, append-only history, topics.
- `CLAUDE.md` — the user's own instruction file. CTX404 owns only the marked import block at its top.

<!-- ctx404:instructions:end -->
