# CTX404

<p align="center">
  <img src="docs/assets/ctx404-social-card.png" alt="CTX404 — Your AI forgot. Your repository won't." width="100%">
</p>

<p align="center"><strong>Your AI forgot. Your repository won't.</strong></p>

[Leia em Português (Brasil)](README.pt-BR.md)

[![Public beta](https://img.shields.io/badge/status-public_beta-f59e0b)](https://github.com/claudneysessa/ctx404/releases)
[![Tests](https://github.com/claudneysessa/ctx404/actions/workflows/test.yml/badge.svg)](https://github.com/claudneysessa/ctx404/actions/workflows/test.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-41e681.svg)](LICENSE)

> **Public beta:** CTX404 is ready for real-project testing, but interfaces may change before v1.0. Please report unexpected behavior through [Issues](https://github.com/claudneysessa/ctx404/issues).

CTX404 is an open-source Claude Code skill that bootstraps durable, indexed and token-aware context inside new or existing repositories.

For a new repository it initializes Git and delegates Claude Code's native `/init`. For an existing repository it skips `/init`, preserves current files and starts durable context from the installation point forward. Both modes install project-local governance, narrowly scoped Haiku and Sonnet helpers, and deterministic Python validation. The global skill is no longer a runtime dependency after installation.

**Run once. The skill leaves. The context system stays.** Clone the initialized repository on another machine and its rules, current state, index, history, hooks and maintenance helpers travel with the code.

## Quick start

### Install

```bash
# macOS · Linux · WSL · Git Bash
curl -fsSL https://raw.githubusercontent.com/claudneysessa/ctx404/main/install.sh | sh
```

```powershell
# Windows · PowerShell 5.1+
irm https://raw.githubusercontent.com/claudneysessa/ctx404/main/install.ps1 | iex
```

Then:

1. Restart Claude Code if the command is not immediately discovered.
2. Open Claude Code in the target project directory.
3. Run `/ctx404`.
4. Describe what the project should become.

CTX404 detects the repository automatically. Empty projects use the original bootstrap flow. Existing projects use non-destructive adoption: project files and README stay untouched, existing Claude guidance is preserved, settings are merged, and no retrospective repository analysis runs during installation.

## Existing repositories

Adoption means **install now and keep working**. CTX404 does not try to reconstruct the project's past, generate speculative documentation or spend a large-model session cataloguing everything. Context grows organically as future work touches each area.

After installation, CTX404 recommends an optional manual baseline. Ask Claude for a concise, evidence-based repository summary or run native `/init` yourself, review the result, and approve it before saving anything as durable context.

Installation stops instead of overwriting when a CTX404-managed agent, hook, script or context path already exists with unknown ownership.

## What it creates

```text
new-project/
├── .git/
├── .claude/
│   ├── agents/
│   │   ├── context-scout.md
│   │   └── context-curator.md
│   ├── hooks/
│   │   ├── session_context.py
│   │   └── guard_agent_bash.py
│   ├── scripts/context_tool.py
│   ├── settings.json
│   └── context/
│       ├── index.json
│       ├── current.json
│       ├── schema.json
│       ├── history.jsonl
│       ├── templates/topic.md
│       └── topics/
├── CLAUDE.md
└── README.md
```

New sessions receive a compact status summary. They can query the index and load only the topic needed for the current task instead of treating the entire repository as startup context.

## Delegation is guidance, not magic

CTX404 gives Claude explicit routes and guardrails for delegating low-judgment work to cheaper models:

- **Haiku:** bounded discovery, file location and factual extraction;
- **Sonnet:** multi-file reading, synthesis and context curation;
- **Opus:** architecture, trade-offs, risky changes and final judgment;
- **Python:** deterministic installation, validation and context maintenance.

Claude still decides whether delegation is worthwhile. Model routing, savings and output quality are not guaranteed. CTX404 does not replace review, judgment or accurate project definitions.

## Requirements

- Claude Code with skill support;
- Python 3 available as `python`;
- Git available as `git`;
- Windows, macOS or Linux.

Runtime helpers use only the Python standard library. CTX404 installs no Python or Node.js packages in initialized projects.

## Verify locally

```bash
python -m unittest discover -s tests -v
python -m compileall -q scripts assets/templates/.claude
```

See the reproducible [calculator continuity laboratory](examples/calculator-lab/README.md) and [tested environments](TESTED_ENVIRONMENTS.md).

## Security and privacy

CTX404 keeps project context inside the repository. That makes it portable, but it also means the repository's own visibility and ignore rules matter. Never store passwords, API keys, private keys or other secrets in context files. See [SECURITY.md](SECURITY.md).

## Contributing

Issues, compatibility reports and focused pull requests are welcome in English or Portuguese. Read [CONTRIBUTING.md](CONTRIBUTING.md) and the [Code of Conduct](CODE_OF_CONDUCT.md).

## Creator

CTX404 was created and is maintained by [Claudney Sarti Sessa](https://github.com/claudneysessa) — [@claudneysessa](https://github.com/claudneysessa).

## License

[MIT](LICENSE)
