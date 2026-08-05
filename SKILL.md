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

9. Report in **one short paragraph and nothing else**. Say it worked, say the one or two things the user must still do — restart Claude Code, accept the workspace trust dialog once — and close by pointing at the documentation instead of reproducing it: `README.md` in the project and https://github.com/claudneysessa/ctx404. Nothing else earns a line — no file lists, no tables, no headings, no architecture, no narration of the commands you ran, no explanation of what CTX404 is. Installing a tool is a chore, not an event; whoever wants the detail follows the link.

   For `adopt`, one extra clause in the same paragraph: durable context starts now, nothing about the repository's past was analyzed. In `index` mode, name the preserved authority paths there. If `alreadyInstalled` is true, the paragraph is one sentence with the installed and skill versions and whether an upgrade exists; never present a global skill update as a project upgrade, and never overlay project protocol files.

10. For `new` only, after that paragraph, refine `.claude/context/project-definition.md` from explicit user intent and verified evidence. Define only personas that materially help the project, mark uncertain statements as assumptions, and never invent missing facts. Synchronize `README.md` and `.claude/context/index.json`. If the purpose is unavailable, ask one minimal question instead of inventing it.
11. Stop using CTX404 after this handoff; subsequent maintenance belongs to the repository protocol.

## Reviewed upgrade

1. Never upgrade during ordinary `/ctx404`. Require explicit `/ctx404 upgrade` intent.
2. Produce a read-only migration plan:

   ```powershell
   python "<skill-directory>/scripts/bootstrap.py" upgrade-plan --target "<project-root>"
   ```

3. Ask **one question and nothing else**: whether to upgrade from the installed version to the target version. Two lines at most — the versions, and the question. No table, no per-file list, no description of what changes, no benefit pitch; the user invoked `upgrade`, they already want it. If they want the detail before deciding, point at https://github.com/claudneysessa/ctx404 and the `CHANGELOG.md`. If no reviewed migration path exists, say so in one line and stop.
4. If `authorityDecisionRequired` is true, present `index`, `exclusive` and `cancel` exactly as in bootstrap. Never choose for the user.
5. After explicit approval, apply the selected versioned migration:

   ```powershell
   python "<skill-directory>/scripts/bootstrap.py" upgrade-apply --target "<project-root>" --authority-mode "<choice>"
   ```

6. Report the result in **one short paragraph and nothing else**: the new version, that doctor passed, anything in `warnings`, and the restart and trust reminders if they apply. Close by pointing at `CHANGELOG.md` and https://github.com/claudneysessa/ctx404 for what changed. Do not restate the plan, do not list created files, do not explain the new architecture — the user approved an upgrade, not a briefing. Never delete or retire an old governance system as part of upgrade.
7. Upgrade the protocol and nothing else. If you notice project content the new version made inconsistent, state it in one line as a suggestion and stop; do not rewrite the user's files in the same turn unless asked.

## Guardrails

- Require explicit user invocation because this workflow creates files and initializes Git.
- Preserve every pre-existing project file. Do not rewrite README.md, reorganize code, infer project history, or scan the repository merely to populate context during adoption.
- Treat existing planning, memory, state and decision systems as possible authorities. Never silently declare CTX404 their replacement.
- Default recommendations to `index`. Require an explicit user choice before `exclusive`, and never delete or retire an existing system during installation.
- Keep the CTX404 footprint in `CLAUDE.md` to the marked import stub. The protocol lives in `.claude/ctx404-instructions.md` and `.claude/rules/ctx404-context.md`; project identity and scope live in `.claude/context/project-definition.md`. Merge CTX404 hooks into an existing `.claude/settings.json`; preserve unrelated content and settings.
- Treat `.claude/ctx404-instructions.md` and `.claude/rules/ctx404-context.md` as managed: a reviewed upgrade replaces them. Never rewrite `.claude/context/project-definition.md`, which belongs to the project.
- Refuse managed-path collisions instead of overwriting custom agents, hooks, scripts, or context files.
- Treat project protocol upgrades as a separate reviewed migration. Reinstalling the global skill or rerunning `/ctx404` must not silently overlay an initialized repository.
- Never delete, overwrite, publish, commit, add a remote, or push.
- Preserve any existing `CLAUDE.md`; install the import stub above it and leave everything else untouched.
- On `upgrade-apply` from a pre-0.4.0 project, the inline governance block is removed from `CLAUDE.md` and replaced by the stub. Surface `warnings` if any are returned; the rest of the payload is for you, not for the user.
- Installing and upgrading are chores. One short paragraph each, and a link for whoever wants the detail. A long report is a defect: it buries the two or three things the user must actually do, and it reads as a tool talking about itself.
- Never invoke native `/init` or generate a recap during CTX404 installation. Both are optional and user-controlled after the deterministic installation is complete.
- Never treat optional `/init` or recap output as project evidence until the user reviews it; refine project context from explicit intent and verified files.
- Do not enumerate or read the installed CTX404 directory. The workflow paths are defined here; invoke the bundled scripts directly.
- Preserve Opus quality and responsibility. Delegate only mechanical work that does not require its judgment, and only when delegation costs less than direct execution.
- Use the bundled Python scripts and templates. Do not regenerate equivalent files manually.
- Treat the folder-derived project name as an initial assumption. Refine it with the other project definitions after bootstrap.
- Define project-specific personas only when they materially support the verified project scope.
- Treat Python and Git as required. Node.js may be present but is not required by CTX404 v1.
