<!-- ctx404:governance:start version="{{CTX404_VERSION}}" schema="1" -->

# CTX404 Context Protocol

This repository owns its durable context. Chat history and global model memory are not project records.

Claude Code auto memory is disabled for this project. `.claude/context/` is the portable, Git-versioned continuity system.

{{AUTHORITY_POLICY}}

## Initial project identity

- Project name: `{{PROJECT_NAME}}`
- Source: repository folder name at bootstrap.
- Installation mode: `{{INSTALL_MODE}}`.
- Treat this as an initial assumption. If the user defines another name, update this section, `.claude/context/index.json`, and `README.md` together.

## Project definition workspace

<!-- ctx404:project-definition:start -->

- Purpose: pending definition
- In scope: pending definition
- Out of scope: pending definition
- Primary users or stakeholders: pending definition
- Project-specific constraints: pending definition
- Sources of truth: pending definition
- Working personas: pending definition

<!-- ctx404:project-definition:end -->

After CTX404 finishes, take ownership of this workspace. Refine it from explicit user intent and verified repository evidence. Define only personas that materially help the project. Mark uncertain statements as assumptions and never invent missing facts. If no reliable purpose is available, ask one minimal question to establish it before refining the remaining fields.

Durable context starts at installation time. For an existing repository, do not scan or summarize solely to reconstruct its past or fill this workspace; let context grow as future work touches each area. Native `/init` and recap are never part of automatic CTX404 installation. After installation, recommend an optional concise project recap or manual `/init`; run either only when the user chooses it, show the result for approval, and save only verified facts.

## Start every session

1. Use the compact CTX404 status injected by the `SessionStart` hook as initial context.
2. If the hook reports that status is unavailable, run `python .claude/scripts/context_tool.py status` once as a fallback.
3. Do not re-read `.claude/context/index.json` or `.claude/context/current.json` unless raw fields are required for the task or an update.
4. Match the user's request to the returned topics and load only the relevant files.
5. Do not read the full operational history or scan the entire repository unless the task requires it.
6. Do not ask for information already recorded and valid. Ask only when context is absent, contradictory, or insufficient for a material decision.

## Route work by cost

- Opus retains judgment and responsibility: user intent, ambiguity, architecture, consequential planning, meaningful implementation, risk analysis, critical validation, and final communication.
- Python performs decisions already made: timestamps, revisions, history append, index synchronization, validation, status, and path checks. Python never chooses project meaning or content.
- Delegate exact search, unknown file discovery, and factual extraction to `context-scout` (Haiku) when exploration is required.
- Delegate multi-file comparison, long-document synthesis, contradiction detection, and context consistency review to `context-curator` (Sonnet) when several sources must be understood together.
- Read one known relevant file directly when starting an agent would cost more. Do not delegate information already active in context.
- Never delegate architecture, ambiguous interpretation, consequential changes, or final acceptance merely because an auxiliary agent can attempt them.
- Treat auxiliary output as evidence. Opus evaluates it and rechecks critical evidence before consequential decisions.
- Project hooks restrict auxiliary-agent Bash use to the deterministic context helper. They do not select which agent to invoke; route by the descriptions and rules above.

Decision rule: judgment or responsibility → Opus; deterministic bookkeeping → Python; finding facts → Haiku; synthesizing several sources → Sonnet; cheaper direct known read → Opus reads directly.

## Communicate compactly

- Lead with the result. Remove filler, repeated facts, decorative formatting, and unnecessary narration.
- Preserve exact technical terms, commands, code, API names, and decisive error text.
- Do not invent abbreviations or dump full files and logs unless requested.
- Prefer professional clarity over compression for security warnings, irreversible actions, and ordered procedures.

## Maintain context after relevant work

Update context only after a durable change, decision, completed step, new blocker, changed next step, or new reusable discovery.

1. Opus decides the durable summary, next step, status, affected topics, and references.
2. Update or create only affected topic bodies using `.claude/context/templates/topic.md`; do not manually manage their revision or timestamps.
3. Run the deterministic completion command once. It synchronizes topics, assigns the real timestamp, appends history, increments current revision, updates current last, and runs doctor:

   ```text
   python .claude/scripts/context_tool.py complete --summary "<completed result>" --next-step "<next action or no pending work>" --status active --topic "<topic-id>" --ref "<relative-path>"
   ```

4. Include repeated `--topic` and `--ref` arguments only when relevant. Use `--event-type` for a more specific history type when useful.
5. Do not manually write timestamps, increment revisions, append history, or edit `current.json` for ordinary completion.
6. Do not consider relevant work complete unless `complete` returns `ok: true` and doctor has no issues.

Do not update context for greetings, repeated information, or read-only questions that produce no durable discovery.

## Context boundaries

- `.claude/context/index.json` is a compact map, not an encyclopedia.
- `.claude/context/current.json` represents the present, not history.
- `.claude/context/history.jsonl` is append-only operational history and is not loaded by default.
- `.claude/context/topics/` contains details loaded on demand.
- `README.md` contains consolidated project documentation.
- Use relative paths, stable topic IDs, short summaries, and explicit keywords.
- Topic frontmatter is parsed as JSON-compatible scalars, not full YAML. Write `keywords` as an inline JSON array with every string quoted, for example `keywords: ["cli", "architecture"]`. Copy `.claude/context/templates/topic.md`, replace its fields, and validate before completion.
- Never copy secret values into context, summaries, history entries, or chat. Reference only their safe relative location when needed.
- Never invent missing context. If repair is needed, preserve evidence and correct only what can be verified.

<!-- ctx404:governance:end -->
