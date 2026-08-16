# Changelog

All notable CTX404 changes are documented here. The project follows Semantic Versioning where practical during beta development.

## [Unreleased]

### Added

- A `Stop` hook, `.claude/hooks/context_gate.py`, blocks the end of a session that deliberated without recording anything. Reading context was always a hook and therefore certain; writing it was a paragraph of prose asking the model to remember, and a request loses to whatever else holds the turn. The asymmetry had a predictable shape: sessions that produced files got recorded, and sessions that produced only decisions — the ones whose reasoning exists nowhere else — did not. The gate reads the transcript, counts the exchanges since the last `complete`, and blocks once at three. Never twice: Claude Code sets `stop_hook_active` on the retry and the hook stands down, so the cost of a false positive is one turn. It fails open on an unreadable transcript, a missing context directory, or an auxiliary agent.
- `context_tool.py review` reads deliberation back out. Recording a rejected option is only half of the promise — `find` searches summaries and keywords, never topic bodies, so a rejected idea written into a topic was stored and unreachable, which from the user's chair is the same as never written. `review --section rejected`, `--query`, and `--topic` make it retrievable, so an option turned down in June can be reconsidered on purpose in August instead of being re-proposed as if it were new.
- The context rule documents a deliberation record — `Decided`, `Rejected`, `Revoked`, `Constraints`, `Open` — and instructs the model to run `review` before proposing anything resembling earlier work, and to cite the recorded reason instead of re-suggesting a rejected option.

- `prepare` refuses to install when Git ignores `.claude/context/`, naming the exact rule from `git check-ignore -v` and printing the replacement recipe. A `.claude/` ignore is common — people reach for it to keep `settings.local.json` out of the repository — and it silently voids the only thing CTX404 promises, since the context never reaches another machine. There is deliberately no "install anyway": `.git/info/exclude` cannot override `.gitignore`, and forcing every future topic with `git add -f` is not a maintainable state. CTX404 reports and stops; it never edits the ignore file, which may belong to the team or to the machine.
- `doctor` warns when the context becomes ignored after installation, since the rule can be added months later by someone else.
- `prepare` stops before touching an existing `CLAUDE.md`, reporting its real filename and the local Markdown files it links to. A project that governs its own context names those files from its instructions, which detects setups a fixed filename list misses. Those files become detected authorities and flow into the existing index/exclusive/cancel gate.
- `prepare --claude-md rename` fixes a `claude.md` whose casing only works on case-insensitive filesystems, using a two-step `git mv` because a direct rename is a no-op on Windows. Left alone, the project's own rules silently stop loading on Linux and in CI.

- A `revert` phase undoes an installation: it removes exactly the recorded files, restores a merged `CLAUDE.md` or `.claude/settings.json` from backup, and reverses a filename rename. It refuses when a created file changed afterwards, naming those files, since that usually means real context was written there; `--force` discards them. Files already committed are removed from the working tree but never rewritten out of history.
- An installation receipt is written inside the Git directory before each step, so a process killed mid-install still leaves an exact record. `prepare` and `install` now detect that partial state and refuse to run over it, pointing at `revert` instead of failing with a confusing managed-path collision.

### Fixed

- Installation and upgrade work inside a Git worktree or submodule, where `.git` is a file rather than a directory. The Git directory is now resolved with `git rev-parse` instead of assumed.
- A `CLAUDE.md` that is not valid UTF-8 fails with a clear message instead of a raw `UnicodeDecodeError` traceback, and the process exit code now reflects the `ok` field.

### Changed

- The install and upgrade reports now end with an unmissable restart warning instead of a middle line reading `Restart session to apply updates`. A session reads `CLAUDE.md`, the protocol file and the `SessionStart` and `PreToolUse` hooks once, at startup, so the session that installs CTX404 keeps running with none of them: no status injection, no context gate, nothing recorded. The old line stated the fact but read as housekeeping, and the failure it was meant to prevent is expensive and silent — installation succeeds, the session behaves normally, and hours of decisions leave no trace on disk. The warning is now the last thing on screen, separated from the rest of the block, and the skill refines the project definition before reporting rather than after. `install` and `upgrade-apply` also return `restartRequired`, and the skill states the missing protocol once if the user keeps working instead of restarting. The READMEs and the landing page carry the same step.
- The protocol no longer defines durable context in terms of file changes. A decision, an option the user rejected and why, a reversal, a structure discussed but not implemented, and a constraint the user revealed are all recordable on their own; the previous wording listed "durable change" and "completed step" and then excluded "read-only questions that produce no durable discovery", which an hour of pure design conversation matches word for word. The test is now whether a future session would have to ask again, not whether a file moved.

- `/ctx404` and `/ctx404 upgrade` now report in one short paragraph and point at the README and the repository instead of reproducing them. Upgrade asks a single yes-or-no question instead of presenting a change table. The install flow had seven separate "tell the user" steps and the upgrade added two more, which together produced a wall of text on what is a chore; a long report buries the two things the user must actually do.
- `/ctx404 upgrade` migrates the protocol and stops. Project content the new version made inconsistent is reported as a one-line suggestion instead of being rewritten in the same turn.

- `Why context lives in the repository` section in the governance template: durable context is versioned in the repository because the same work continues on more than one machine, and Git is what synchronizes them. Includes the portability test — does the mechanism reach the other machines through `git pull`? — and an explicit instruction not to fork the rule per repository.

## [0.4.0-beta.1] - 2026-08-04

### Changed

- CTX404 no longer writes its protocol into `CLAUDE.md`. The file now receives a marked stub of two `@` imports; a measured install drops the CTX404 footprint there from about 7,900 characters to under 600.
- The protocol moved to `.claude/ctx404-instructions.md`, a fully managed file that a reviewed upgrade replaces outright. Upgrades no longer depend on the user having left the inline text untouched.
- Project identity and the definition workspace moved to `.claude/context/project-definition.md`, which is project-owned and never rewritten by CTX404.
- Governance marker schema is now `2`.

### Added

- `.claude/rules/ctx404-context.md`, a path-scoped rule holding the `complete` procedure, topic format and context boundaries. Claude Code loads it only when `.claude/context/` is touched, so the always-loaded protocol drops from roughly 1,900 to about 990 tokens per session.
- Chained reviewed migrations. `upgrade-plan` and `upgrade-apply` report `hops` and walk `0.2.0-beta.1 → 0.3.0-beta.1 → 0.4.0-beta.1` in one reviewed run, so projects on the oldest beta are no longer stranded.
- `upgrade-apply` removes the pre-0.4.0 inline block from `CLAUDE.md`, carries the edited project definition into the new file, and reports `created` and `warnings`.
- Doctor verifies both imports in `CLAUDE.md`, the managed instructions file and its version, the project definition and the path-scoped rule. A silently broken import is now an error instead of an invisible loss of protocol.
- Installation refuses to overwrite an existing `.claude/rules/ctx404-context.md`.
- `.claude/settings.json` now ships an allow rule scoped to the context helper, merged into an existing file without touching the user's own rules, and added to pre-0.4.0 projects by `upgrade-apply`. Claude Code ignores `permissions.allow` from project settings until the workspace trust dialog is accepted once, so `SKILL.md` now tells the user to do that after installation; hooks are unaffected.
- `upgrade-apply` refreshes managed implementation files — the context helper, hooks, agents, topic template and schema — and reports them as `refreshed`. Without this, a migrated project kept the old helper while the newly installed rule told Claude to call a subcommand it did not have, and the old doctor silently skipped the new checks. Files differing only in line endings are left alone.
- `context_tool.py topic-write` writes topic bodies deterministically: Claude supplies the body on stdin, the helper builds the frontmatter, preserves provenance on update and syncs the index. Topic writing no longer depends on a file-editing tool, which Claude Code blocks inside `.claude/` as a sensitive path — previously a non-interactive session lost topic files silently while `complete` still reported success.

### Removed

- Installation-time handoff guidance left the always-loaded protocol; it lives in `SKILL.md`, which is already loaded while `/ctx404` runs.

## [0.3.0-beta.1] - 2026-08-02

### Added

- Existing-authority preflight for state, planning, memory, context and architecture-decision systems.
- Explicit `index`, `exclusive` or `cancel` decision before modifying a repository with overlapping governance.
- `governance.authorities` routing map in the compact context index.

### Changed

- `index` is the recommended safe adoption mode; CTX404 points to existing authorities instead of duplicating them.
- Preflight now stops before Git initialization when an authority decision is required.
- Repeated installation reports project and skill versions without silently upgrading planted repositories.
- Explicit `/ctx404 upgrade` workflow with read-only planning, versioned migration, local backup, doctor validation and rollback.
- First reviewed project migration path: `v0.2.0-beta.1` to `v0.3.0-beta.1`.

- Requirements now appear before installation in both README languages and on the landing page.
- Inspection-first installation is recommended, with the remote one-command path explicitly labeled as a convenience that executes remote code.
- Installer scope and transactional replacement behavior are documented before execution.

## [0.2.0-beta.1] - 2026-08-02

### Added

- Automatic detection of new and existing repositories.
- Non-destructive adoption mode that starts durable context at installation time without reconstructing project history.
- Optional, user-reviewed guidance for a concise project recap or a manual native `/init` after installation.
- Direct deterministic installation without automatically invoking native `/init` or generating a recap.
- Deterministic coverage for adoption, managed-path conflicts and repeated installation.

### Changed

- Existing `README.md`, project files, `CLAUDE.md` guidance and unrelated Claude settings are preserved.
- CTX404 governance is merged into existing Claude configuration instead of replacing it.
- Installation now refuses unknown collisions only at paths managed by CTX404.

## [0.1.0-beta.1] - 2026-08-02

### Added

- First public beta of the `/ctx404` Claude Code skill.
- One-command installers for PowerShell and POSIX shells.
- Git initialization and isolated delegation to Claude Code's native `/init`.
- Project-local governance, indexed JSON state, append-only history and selective topic loading.
- Scoped Haiku and Sonnet helpers with deterministic Python validation.
- English-first documentation with a complete Portuguese version.
- Responsive bilingual GitHub Pages landing page.
- MIT license, contribution guide, security policy, issue forms and pull request template.
- Cross-platform automated tests and a documented calculator continuity laboratory.

[0.1.0-beta.1]: https://github.com/claudneysessa/ctx404/releases/tag/v0.1.0-beta.1
[0.2.0-beta.1]: https://github.com/claudneysessa/ctx404/releases/tag/v0.2.0-beta.1
[0.3.0-beta.1]: https://github.com/claudneysessa/ctx404/releases/tag/v0.3.0-beta.1
[0.4.0-beta.1]: https://github.com/claudneysessa/ctx404/releases/tag/v0.4.0-beta.1
