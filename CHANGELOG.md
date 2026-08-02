# Changelog

All notable CTX404 changes are documented here. The project follows Semantic Versioning where practical during beta development.

## [0.2.0-beta.1] - 2026-08-02

### Added

- Automatic detection of new and existing repositories.
- Non-destructive adoption mode that starts durable context at installation time without reconstructing project history.
- Optional, user-reviewed guidance for a concise project baseline or a manual native `/init` after adoption.
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
