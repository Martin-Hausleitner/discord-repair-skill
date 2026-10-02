---
name: discord-repair
description: Keep macOS Discord Stable with custom AutoStream and AquaMuteSync working, diagnose live failures, and repair update damage quietly without opening the graphical Vencord Installer.
metadata:
  version: 2.0.0
---

# Discord, AutoStream and Aqua recovery

## Operator contract, 2026-09-07

Never open, download for auto-launch, or invoke the graphical Vencord Installer. The old CyberKird macOS wrapper downloads a GUI binary and passes CLI flags which that binary ignores. Its `at.vencord.cyberkird` LaunchAgent is disabled. Do not reenable it, `org.aaron.autovencordpatch`, or competing patchers. Never run `pnpm inject` / `scripts/runInstaller.mjs` on this Mac: its Darwin path opens the same GUI.

Maintain `/Applications/Discord.app` only. Preserve the custom distribution and existing plugin settings. Do not substitute Discord PTB/Canary, Vesktop, stock Vencord, or another mod. Do not quit/reload Discord, stop a stream, disconnect a call, synthesize recording events, or send messages to test. An active call/stream requires deferring disruptive work. A maintenance request alone is not permission to interrupt it.

GUI interaction must use Codex Computer Use exclusively. If actions do not take effect, inspect once, correct once, then report the concrete limitation after three stalled attempts. Do not substitute AppleScript, browser evaluation, or Orca.

## Known installation

- Custom source and deployed bundle: `/Users/mh/code/hoerbert/Vencord/dist`.
- `/Users/mh/Library/Application Support/Vencord/dist` must remain a symlink to that directory.
- Settings: `/Users/mh/Library/Application Support/Vencord/settings/settings.json`.
- Required plugins: `AutoStream.enabled=true`, `AquaMuteSync.enabled=true`.
- Aqua watch: `org.n281.aqua-watch`, WebSocket `127.0.0.1:8688`.
- Mouse bridge: `org.aqua.mouse-bridge`, HTTP `127.0.0.1:8690/status`.
- Quiet guard: `/Users/mh/Library/Application Support/discord-repair/discord_guard.py`.
- Guard LaunchAgent: `local.mh.vencord-auto-repair`.
- Local status: `/Users/mh/Library/Application Support/discord-repair/status.json`.
- Local backups: `/Users/mh/Library/Application Support/discord-repair/backups/`.

## Diagnose first

Run the guard in its read-only mode (check its `--help` for exact interface), inspect its status and `launchctl print gui/$(id -u)/local.mh.vencord-auto-repair`. Confirm both custom plugin names occur in renderer.js and selected enabled flags remain true. Do not dump all settings, tokens, environment, private channel data, or message history.

Read `http://127.0.0.1:8690/status` with a three-second timeout. `watchLinked` proves the bridge connection, not Discord behavior. For the helper, use `/opt/homebrew/bin/node` and the built-in WebSocket to receive the initial state from `ws://127.0.0.1:8688`. Send at most `{"type":"get_state"}`. Never send `app_state`, `set_recording`, mute controls or simulated events: that would fabricate the state being measured.

Check `apps.discord.online`, `apps.discord.muted`, sequence and timestamps, `recording`, and `degraded`. Fresh changing Discord reports are stronger evidence than a listening port. If a shell probe reports offline while the listener exists, rerun the direct absolute-path probe and expose its real error before restarting anything. Do not assume module resolution is the cause without the actual exception.

Inspect live Discord with Codex Computer Use. A visible active stream and injected AutoStream button prove live presence; they do not prove a new automatic start. Full AutoStream start/stop and physical Aqua parity testing require an idle, authorized test window. State that gap explicitly rather than claiming E2E from unit tests or configuration.

## Quiet update recovery

The guard checks periodically without windows or notifications. Healthy installations are no-ops. Repair is allowed only when Discord is fully closed, update files are stable, required custom files exist, and archive state is unambiguous. Never overwrite `_app.asar` from an old Discord release onto a new `app.asar`. Mixed archives require explicit diagnosis. No kill, relaunch, automatic dependency update, stock download, or speculative rebuild.

The pinned local CLI is `/Users/mh/Library/Application Support/discord-repair/bin/VencordInstallerCli-darwin`. It derives from official `Vencord/Installer` revision `089cab0720743c5afab41f9b6f166f3b723e8de0`, with one local correction: the CLI `InstallLatestBuilds` uses the GUI's `if IsDevInstall { return nil }` guard. Unmodified upstream CLI can falsely report success in developer mode. Source archive and patch are under `discord-repair/source/`.

Required environment is `VENCORD_DEV_INSTALL=1` and `VENCORD_USER_DATA_DIR=/Users/mh/Library/Application Support/Vencord`. Required arguments are `--install --location=/Applications/Discord.app`. Never use `--repair`: that path downloads a stock distribution. Never omit developer mode. Never pass the dist directory itself as the base. Never combine location and branch.

Use the guard rather than manually launching this command. It must back up before changes, verify the new archive marker and original archive, and rate-limit failures. Exit status alone does not prove success. Never replace the CLI without repeating the fixture patch/repatch test and updating its verified digest.

## Plugin failure recovery

If a plugin is missing from the bundle, inspect the actual custom source and current dirty tree before building. Preserve all existing changes. Run the focused tests:

`node --test src/userplugins/autoStream/index.test.mjs src/userplugins/aquaMuteSync/index.test.mjs`

from `/Users/mh/code/hoerbert/Vencord`. Build only after diagnosing a concrete source/deployment mismatch, back up dist before replacement, and verify plugin inclusion afterward. A source build alone does not update an already loaded Discord renderer. Do not force reload during a call.

If an Aqua helper is absent, inspect its existing LaunchAgent and exact error first; restore the same service, preserving its configuration. Do not restart healthy audio services or toggle microphones. Runtime checks must remain observational during dictation.

## Evidence and memory

Keep a local report with: cause, exact changed files, backup path, CLI source/digest, guard test result, plugin test result, live helper evidence, observed Discord state, and pending runtime tests. Keep confidential backups local. If the user asks to remember the repair, add a small update note to `/Users/mh/.codex/memories/extensions/ad_hoc/notes/`; do not edit MEMORY.md directly. Store an additional Hans summary only when its destination is clear and authorized. Never treat an old report as fresh runtime proof.
