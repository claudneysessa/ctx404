# Changelog

All notable CTX404 changes are documented here. The project follows Semantic Versioning where practical during beta development.

## [Unreleased]

### Added

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
