---
name: ctx404
description: Bootstrap a new Claude Code repository or adopt an existing one with Git, a compact self-maintaining context protocol, deterministic Python helpers, and tiered Haiku/Sonnet subagents. Use when the user explicitly invokes /ctx404 to start durable project-local context without overwriting existing project files.
disable-model-invocation: true
---

# CTX404

Detect whether the target is new or already contains a project. Bootstrap new repositories and adopt existing repositories without retrospectively analyzing or reorganizing them.

## Workflow

1. Resolve the requested project root. Default to the current working directory. If the user invoked `/ctx404 upgrade`, follow **Reviewed upgrade** below instead of bootstrap.
2. Run the bootstrap preflight:

   ```powershell
   python "<skill-directory>/scripts/bootstrap.py" prepare --target "<project-root>"
   ```

3. Read the JSON result. If `authorityDecisionRequired` is true, stop before installation and present the detected paths plus exactly these choices:
   - `index` (recommended): keep existing sources authoritative and use CTX404 as the compact routing and continuity layer;
   - `exclusive`: make CTX404 the primary durable-context authority, with later migration or retirement of the previous system requiring separate explicit approval;
   - `cancel`: leave the project unchanged.
4. Never choose for the user. If the user selects `index` or `exclusive`, rerun prepare with `--authority-mode <choice>`. If the user selects `cancel`, stop immediately.
5. Read the final JSON result's `mode` field. Do not invoke native `/init` or generate a recap automatically in either mode.
6. If `mode` is `adopt`, do not explore or summarize the existing repository as part of installation.
7. Install the CTX404 structure:

   ```powershell
   python "<skill-directory>/scripts/bootstrap.py" install --target "<project-root>"
   ```

8. Validate the installed context system:

   ```powershell
   python "<project-root>/.claude/scripts/context_tool.py" validate --root "<project-root>"
   ```

9. Report the repository mode, authority mode, detected authorities, created or merged files, and validation result.
   If `alreadyInstalled` is true, report `installedVersion`, `skillVersion`, and `upgradeAvailable`. Never present a global skill update as a project upgrade and never overlay project protocol files.
10. Tell the user that CTX404 has finished and the repository is now self-maintaining.
11. Explain that project agents written to `.claude/agents/` become available after Claude Code restarts because file-defined agents load at session start.
12. State that native `/init` and recap were intentionally not run. Recommend them only as optional manual orientation choices after installation. Require user review before saving either result as durable context.
13. For `new`, take ownership of the repository in the same turn and refine the `Project definition workspace` from explicit user intent and verified evidence. Synchronize `README.md` and `.claude/context/index.json`. If the purpose is unavailable, ask only one minimal question instead of inventing it.
14. For `adopt`, state that no retrospective analysis was performed and durable context starts now. If authority mode is `index`, name the preserved authority paths and explain that CTX404 points to them instead of duplicating their content.
15. Stop using CTX404 after this handoff; subsequent maintenance belongs to the repository protocol.

## Reviewed upgrade

1. Never upgrade during ordinary `/ctx404`. Require explicit `/ctx404 upgrade` intent.
2. Produce a read-only migration plan:

   ```powershell
   python "<skill-directory>/scripts/bootstrap.py" upgrade-plan --target "<project-root>"
   ```

3. Report installed version, target version, exact planned changes and preserved state. If no reviewed migration path exists, stop.
4. If `authorityDecisionRequired` is true, present `index`, `exclusive` and `cancel` exactly as in bootstrap. Never choose for the user.
5. After explicit approval, apply the selected versioned migration:

   ```powershell
   python "<skill-directory>/scripts/bootstrap.py" upgrade-apply --target "<project-root>" --authority-mode "<choice>"
   ```

6. Report the backup-safe result and doctor validation. Never delete or retire an old governance system as part of upgrade.

## Guardrails

- Require explicit user invocation because this workflow creates files and initializes Git.
- Preserve every pre-existing project file. Do not rewrite README.md, reorganize code, infer project history, or scan the repository merely to populate context during adoption.
- Treat existing planning, memory, state and decision systems as possible authorities. Never silently declare CTX404 their replacement.
- Default recommendations to `index`. Require an explicit user choice before `exclusive`, and never delete or retire an existing system during installation.
- Merge the managed governance block into an existing `CLAUDE.md` and merge CTX404 hooks into an existing `.claude/settings.json`; preserve unrelated content and settings.
- Refuse managed-path collisions instead of overwriting custom agents, hooks, scripts, or context files.
- Treat project protocol upgrades as a separate reviewed migration. Reinstalling the global skill or rerunning `/ctx404` must not silently overlay an initialized repository.
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
