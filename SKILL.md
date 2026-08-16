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

3. Read the JSON result. If `ok` is false and `contextIgnored` is present, stop. Git ignores the context directory, so nothing CTX404 writes would ever reach another machine — installing would deliver none of what it promises. Report, in at most ten lines:

   - the offending rule exactly as returned: `<contextIgnored.source>:<contextIgnored.line>` matches `<contextIgnored.pattern>`. Read the source out loud rather than assuming `.gitignore`; it may be `.git/info/exclude` or a global ignore file, and then the fix is somewhere else entirely.
   - the `recipe` lines verbatim, as a code block, as the replacement.
   - one sentence on why the obvious fix fails: `.claude/` cannot be negated, because Git does not descend into an excluded directory, which is why the recipe starts at `.claude/*`. `settings.local.json` stays ignored.
   - that they should fix the rule and run `/ctx404` again.

   Never offer to install anyway, and never edit the ignore file yourself. `.git/info/exclude` cannot override `.gitignore`, and forcing each future topic with `git add -f` is not a state anyone maintains, so there is no working alternative to offer. The ignore file may also belong to the whole team or to the machine.

4. Read the JSON result. If `claudeMdDecisionRequired` is true, stop before installation. The project already has its own `CLAUDE.md` and CTX404 must never edit it unattended. Say what was found and ask, in at most six lines:

   - When `claudeMd.needsRename` is true, say the file is named `<claudeMd.path>` instead of `CLAUDE.md`. Explain the real risk, not a style complaint: it works on Windows and macOS because those filesystems ignore case, but on Linux, in a container or in CI, Claude Code looks for `CLAUDE.md`, does not find it, and the project's own rules silently stop loading. Offer `[S] Renomear  [N] Manter  [C] Cancelar` (`[R] Rename  [K] Keep  [C] Cancel` in English).
   - When `claudeMd.linkedDocs` is not empty, name those files and say plainly that this repository already keeps its own context control. Do not call it redundant outright — it is redundant in `exclusive` mode and useful in `index` mode, and the next gate is where that is decided.
   - Rerun prepare with `--claude-md rename` or `--claude-md keep`. On cancel, stop and change nothing.

   `.claude/CLAUDE.md` and `CLAUDE.local.md` are legitimate locations, not naming mistakes; never offer to rename them.

5. Read the JSON result again. If `authorityDecisionRequired` is true, stop before installation, name the detected paths in one line, and present exactly these choices with bracketed initials, labelled in Portuguese if the user writes Portuguese and in English otherwise. Files carrying `kind: claude-md-reference` came from the project's own instructions, so say so — the user wrote those rules and needs to recognise them. The option tokens themselves stay verbatim, since they are the values passed to `--authority-mode`:
   - `[I] index` (recommended): keep existing sources authoritative and use CTX404 as the compact routing and continuity layer;
   - `[E] exclusive`: make CTX404 the primary durable-context authority, with later migration or retirement of the previous system requiring separate explicit approval;
   - `[C] cancel`: leave the project unchanged.
6. Never choose for the user. Accept the initial or the whole word, in any case; treat any other reply as not an answer and ask once more rather than assuming. If the user selects `index` or `exclusive`, rerun prepare with `--authority-mode <choice>`. If the user selects `cancel`, stop immediately.
7. Read the final JSON result's `mode` field. Do not invoke native `/init` or generate a recap automatically in either mode.
8. If `mode` is `adopt`, do not explore or summarize the existing repository as part of installation.
9. Install the CTX404 structure:

   ```powershell
   python "<skill-directory>/scripts/bootstrap.py" install --target "<project-root>"
   ```

10. Validate the installed context system:

   ```powershell
   python "<project-root>/.claude/scripts/context_tool.py" validate --root "<project-root>"
   ```

11. For `new` only, refine `.claude/context/project-definition.md` from explicit user intent and verified evidence. Define only personas that materially help the project, mark uncertain statements as assumptions, and never invent missing facts. Synchronize `README.md` and `.claude/context/index.json`. If the purpose is unavailable, ask one minimal question instead of inventing it. Do this **before** the report, so the restart warning is the last thing on screen.
12. Report with **this block, copied whole, and nothing around it**. No sentence before, none after, and nothing else in the turn. Always English, whatever language the user writes in:

   ```text
   ====================================
   CTX404 Installed
   CTX404 now at <version>
   https://github.com/claudneysessa/ctx404
   ****************************************
   RESTART THE SESSION TO ACTIVATE CTX404
   Its instructions and hooks load only at
   session start. Until you restart, nothing
   in this session is recorded as context.
   ****************************************
   ```

   Replace `<version>` with the real one. Three lines may be added, above the asterisk banner only, and only when they apply: the preserved authority paths in `index` mode; `Durable context starts after the restart` for `adopt`; `Accept the workspace trust dialog once`. Nothing is ever added inside the banner, and nothing else is ever added anywhere — no file list, no table, no architecture, no narration of the commands you ran. The banner is never shortened, softened, moved, or dropped, and never translated.

   If `alreadyInstalled` is true, replace the top half with the installed version, the skill version, and whether an upgrade exists, and keep the restart half only if this run actually changed the project. Never present a global skill update as a project upgrade, and never overlay project protocol files.

13. Stop using CTX404 after this handoff; subsequent maintenance belongs to the repository protocol.
14. If the user keeps working in the same session instead of restarting, say once, in one line, that CTX404 is not loaded yet and nothing from this session will be recorded — then do what they asked. Repeat it once more only if durable work is being produced. This is the failure the block exists to prevent: the protocol looks installed, the session behaves as if it were not, and hours of work leave no trace.

## Reviewed upgrade

1. Never upgrade during ordinary `/ctx404`. Require explicit `/ctx404 upgrade` intent.
2. Produce a read-only migration plan:

   ```powershell
   python "<skill-directory>/scripts/bootstrap.py" upgrade-plan --target "<project-root>"
   ```

3. Ask **one question and nothing else**: whether to upgrade from the installed version to the target version. Two lines at most — the versions, then the question with its options spelled out as bracketed initials. Pick the wording from how the user has been writing: Portuguese gets `Aplicar? [S] Sim  [N] Não`, every other language gets `Apply? [Y] Yes  [N] No`.

   ```text
   CTX404 0.4.0-beta.2 → 0.4.0-beta.3.
   Aplicar? [S] Sim  [N] Não
   ```

   Never ask a bare "apply?" — the user must be able to see what a valid answer looks like without guessing. Accept the initial or the whole word, in either language, in any case; treat any other reply as not an answer and ask once more rather than assuming. No table, no per-file list, no description of what changes, no benefit pitch; the user invoked `upgrade`, they already want it. If they ask what changes before deciding, point at https://github.com/claudneysessa/ctx404 and the `CHANGELOG.md`. If no reviewed migration path exists, say so in one line and stop.
4. If `authorityDecisionRequired` is true, present `index`, `exclusive` and `cancel` exactly as in bootstrap. Never choose for the user.
5. After explicit approval, apply the selected versioned migration:

   ```powershell
   python "<skill-directory>/scripts/bootstrap.py" upgrade-apply --target "<project-root>" --authority-mode "<choice>"
   ```

6. Report with **this block, copied whole, and nothing around it**. No sentence before, none after. Always English, whatever language the user writes in:

   ```text
   ====================================
   CTX404 Updated
   CTX404 now at <version>
   https://github.com/claudneysessa/ctx404
   ****************************************
   RESTART THE SESSION TO ACTIVATE CTX404
   This session still runs the old protocol.
   Instructions and hooks load only at
   session start.
   ****************************************
   ```

   Replace `<version>` with the real one. Add a line only when `warnings` is non-empty, one per warning, above the asterisk banner; nothing else is ever added. The banner is never shortened, softened, moved, or dropped. Never delete or retire an old governance system as part of upgrade.

7. Upgrade the protocol and nothing else. If you notice project content the new version made inconsistent, state it in one line as a suggestion and stop; do not rewrite the user's files in the same turn unless asked.

## Revert

1. CTX404 records what it did in a receipt inside the Git directory, written before each step so an interrupted run still leaves an exact trail.
2. If `prepare` or `install` reports `interruptedInstall`, a previous run died partway. Do not install over it. Say so in one line and run:

   ```powershell
   python "<skill-directory>/scripts/bootstrap.py" revert --target "<project-root>"
   ```

3. Use the same command when the user asks to undo a CTX404 installation. It removes exactly what was created, restores a merged `CLAUDE.md` or `.claude/settings.json` from backup, and undoes a filename rename.
4. Revert refuses when a file CTX404 created has changed since installation, naming those files. That usually means real work was recorded there. Show the list and confirm before rerunning with `--force`, which discards it.
5. Relay any `warnings`. Files already committed are removed from the working tree but stay in Git history; CTX404 never rewrites history.

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
- A CTX404 installation does not take effect in the session that performed it. `CLAUDE.md`, `.claude/ctx404-instructions.md` and the `SessionStart` and `PreToolUse` hooks are read when a session starts, so the session that just installed them still has no status injection, no context gate and no protocol. Restarting is the one step the user cannot skip, so it is the last thing they read and the only thing in the report that is allowed to be loud.
- Never invoke native `/init` or generate a recap during CTX404 installation. Both are optional and user-controlled after the deterministic installation is complete.
- Never treat optional `/init` or recap output as project evidence until the user reviews it; refine project context from explicit intent and verified files.
- Do not enumerate or read the installed CTX404 directory. The workflow paths are defined here; invoke the bundled scripts directly.
- Preserve Opus quality and responsibility. Delegate only mechanical work that does not require its judgment, and only when delegation costs less than direct execution.
- Use the bundled Python scripts and templates. Do not regenerate equivalent files manually.
- Treat the folder-derived project name as an initial assumption. Refine it with the other project definitions after bootstrap.
- Define project-specific personas only when they materially support the verified project scope.
- Treat Python and Git as required. Node.js may be present but is not required by CTX404 v1.
