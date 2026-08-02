# Changelog

All notable CTX404 changes are documented here. The project follows Semantic Versioning where practical during beta development.

## [Unreleased]

### Added

- `Why context lives in the repository` section in the governance template: durable context is versioned in the repository because the same work continues on more than one machine, and Git is what synchronizes them. Includes the portability test — does the mechanism reach the other machines through `git pull`? — and an explicit instruction not to fork the rule per repository.

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
