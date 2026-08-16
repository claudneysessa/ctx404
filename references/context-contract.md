# CTX404 context contract

The installed repository separates five responsibilities:

- `CLAUDE.md`: the project's own instruction file. CTX404 owns only a marked stub of two imports at its top.
- `.claude/ctx404-instructions.md`: always-loaded core protocol. Managed; a reviewed upgrade replaces it.
- `.claude/rules/ctx404-context.md`: context-writing detail, loaded by Claude Code only when `.claude/context/` is touched. Managed.
- `.claude/context/project-definition.md`: project identity and scope. Project-owned; never rewritten by CTX404.
- `.claude/context/index.json`: compact map of available context.
- `.claude/context/current.json`: current state and next step.
- `.claude/context/topics/`: details loaded only when relevant.
- `.claude/context/history.jsonl`: append-only history, queried only when history is needed.
- `.claude/context/index.json` → `governance`: authority mode and pointers to pre-existing owner sources.
- `.claude/hooks/`: `session_context.py` injects the compact status at session start, `guard_agent_bash.py` narrows what auxiliary agents may run, and `context_gate.py` blocks the end of a session that deliberated without recording.

Maintain these invariants:

- JSON files remain valid UTF-8.
- Topic identifiers are unique and stable.
- Indexed paths are relative to the repository root and exist.
- Current state contains no historical narrative.
- The index contains summaries and pointers, not full documents.
- Important durable information does not exist only in chat history. Durable is not defined by files changed: the test is whether a future session would have to ask again, which makes a decision, a rejected option and its reason, a reversal, and a revealed constraint each recordable on their own.
- A rejected option is recorded so it can be found again. `find` searches summaries and keywords only, so deliberation is read back with `context_tool.py review --section rejected | --query | --topic` before re-proposing anything resembling earlier work.
- In `index` mode, update facts in their owning authority and keep CTX404 as a compact pointer; do not duplicate full living documents.
- In `exclusive` mode, migration or retirement of a previous system remains separate explicit work.
- Secrets may be referenced by path but their values never enter context summaries.

Global skill updates never overlay planted project files. Use the explicit reviewed upgrade workflow for supported version-to-version migrations. Installing or upgrading takes effect only in the next session: `CLAUDE.md`, the protocol file and the hooks are read once, at session start.

Topic Markdown files use the flat frontmatter contract stored at `.claude/context/templates/topic.md`. Run `context_tool.py sync` after topic changes and `context_tool.py doctor` before considering relevant context maintenance complete.
