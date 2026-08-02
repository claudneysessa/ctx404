---
name: ctx404
description: Bootstrap a new Claude Code repository or adopt an existing one with Git, a compact self-maintaining context protocol, deterministic Python helpers, and tiered Haiku/Sonnet subagents. Use when the user explicitly invokes /ctx404 to start durable project-local context without overwriting existing project files.
disable-model-invocation: true
---

# CTX404

Detect whether the target is new or already contains a project. Bootstrap new repositories and adopt existing repositories without retrospectively analyzing or reorganizing them.

## Workflow

1. Resolve the requested project root. Default to the current working directory.
2. Run the bootstrap preflight and Git initialization:

   ```powershell
   python "<skill-directory>/scripts/bootstrap.py" prepare --target "<project-root>"
   ```

3. Read the JSON result's `mode` field. Do not invoke native `/init` or generate a recap automatically in either mode.
4. If `mode` is `adopt`, do not explore or summarize the existing repository as part of installation.
5. Install the CTX404 structure:

   ```powershell
   python "<skill-directory>/scripts/bootstrap.py" install --target "<project-root>"
   ```

6. Validate the installed context system:

   ```powershell
   python "<project-root>/.claude/scripts/context_tool.py" validate --root "<project-root>"
   ```

7. Report the mode, created or merged files, and validation result.
8. Tell the user that CTX404 has finished and the repository is now self-maintaining.
9. Explain that project agents written to `.claude/agents/` become available after Claude Code restarts because file-defined agents load at session start.
10. State that native `/init` and recap were intentionally not run. Recommend them only as optional manual orientation choices after installation. Require user review before saving either result as durable context.
11. For `new`, take ownership of the repository in the same turn and refine the `Project definition workspace` from explicit user intent and verified evidence. Synchronize `README.md` and `.claude/context/index.json`. If the purpose is unavailable, ask only one minimal question instead of inventing it.
12. For `adopt`, state that no retrospective analysis was performed and durable context starts now.
13. Stop using CTX404 after this handoff; subsequent maintenance belongs to the repository protocol.

## Guardrails

- Require explicit user invocation because this workflow creates files and initializes Git.
- Preserve every pre-existing project file. Do not rewrite README.md, reorganize code, infer project history, or scan the repository merely to populate context during adoption.
- Merge the managed governance block into an existing `CLAUDE.md` and merge CTX404 hooks into an existing `.claude/settings.json`; preserve unrelated content and settings.
- Refuse managed-path collisions instead of overwriting custom agents, hooks, scripts, or context files.
- Never delete, overwrite, publish, commit, add a remote, or push.
- Preserve any existing `CLAUDE.md`; install the managed governance block above it.
- Never invoke native `/init` or generate a recap during CTX404 installation. Both are optional and user-controlled after the deterministic installation is complete.
- Never treat optional `/init` or recap output as project evidence until the user reviews it; refine project context from explicit intent and verified files.
- Do not enumerate or read the installed CTX404 directory. The workflow paths are defined here; invoke the bundled scripts directly.
- Preserve Opus quality and responsibility. Delegate only mechanical work that does not require its judgment, and only when delegation costs less than direct execution.
- Use the bundled Python scripts and templates. Do not regenerate equivalent files manually.
- Treat the folder-derived project name as an initial assumption. Refine it with the other project definitions after bootstrap.
- Define project-specific personas only when they materially support the verified project scope.
- Treat Python and Git as required. Node.js may be present but is not required by CTX404 v1.
