# Contributing to CTX404

Thank you for helping CTX404 become reliable across real projects and machines. Issues, discussions and pull requests are welcome in English or Portuguese.

## Before contributing

- Search existing issues and pull requests.
- Never publish secrets, credentials, private repository context or unredacted logs.
- Keep the installed skill compact. Community documentation, CI and examples belong at repository level and are not copied by `scripts/install.py`.
- Preserve the central contract: Opus owns consequential judgment; Python handles deterministic bookkeeping; lower-cost agents handle only suitable auxiliary work.

## Report a bug

Use the bug template and provide:

- operating system and shell;
- Claude Code, Python and Git versions;
- CTX404 version or commit;
- whether the repository was new or already contained project files;
- exact steps and sanitized output;
- expected and actual behavior.

## Propose a feature

Explain the problem first, then the proposed behavior, context/token impact, compatibility risks and alternatives. CTX404 avoids features that increase startup context without a measurable continuity benefit.

## Pull request workflow

1. Fork the repository and create a focused branch.
2. Make the smallest coherent change.
3. Update English and Portuguese documentation when user-facing behavior changes.
4. Run `python -m unittest discover -s tests -v`.
5. Run `python scripts/bootstrap.py --help` and compile changed Python files.
6. Describe what changed, why, how it was tested and any remaining limitation.
7. Open a pull request. Maintainers may request a fresh-project forward test for changes to `SKILL.md`, hooks, agents or governance.

By contributing, you agree that your contribution is licensed under the MIT License.
