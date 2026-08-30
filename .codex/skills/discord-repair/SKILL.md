---
name: discord-repair
description: Repair and harden Discord Stable plus Vencord on macOS using a verified local backup, the official Vencord installer, and safe performance defaults.
metadata:
  version: 1.0.0
  triggers:
    - repair Discord Vencord
    - Discord will not start
    - restore Vencord backup
    - fix Discord performance on macOS
---

# Discord Repair

Restore a working Discord Stable + Vencord installation on macOS without silently changing channels, installing competing clients, or overwriting the user's settings.

## Safety boundaries

- Use only `/Applications/Discord.app`; never substitute Beta, PTB, Canary, Vesktop, BetterDiscord, or Equicord.
- Use the official Vencord macOS installer only: `https://github.com/Vencord/Installer/releases/latest/download/VencordInstaller.MacOS.zip`.
- Do not use `sudo`, foreign `curl | bash` installers, or destructive deletes.
- Create a local backup before repair. Backups stay on the Mac and are never committed, uploaded, or attached to a report.
- Do not quit Discord, interrupt a call, or restart a stream unless the user explicitly asks. If a repair requires a restart, explain that impact and wait for it.
- For Discord UI interaction, use Codex Computer Use; inspect the latest state before every click and verify the resulting state.

## 1. Inspect before acting

Run the verification script:

```sh
bash .codex/skills/discord-repair/scripts/verify.sh
```

Confirm all of the following:

- Apple Silicon or Intel architecture, plus Rosetta only when an x86 installer actually fails.
- Discord Stable exists at `/Applications/Discord.app` and has bundle ID `com.hnc.Discord`.
- Vencord's patched `app.asar` and original `_app.asar` are both present.
- The Vencord settings file is readable and the configured helper/LaunchAgent paths exist when used.
- No competing Discord client or patcher is active.

Treat a failed check as a concrete repair target; do not broadly reinstall unrelated software.

## 2. Snapshot the current working state

Before patching, run:

```sh
bash .codex/skills/discord-repair/scripts/backup-vencord.sh
```

The script snapshots the Vencord settings and the two Discord resource archives into `~/Library/Application Support/discord-repair/backups/`, creates SHA-256 hashes, and prints the exact backup directory. It does not copy Discord tokens, browser profiles, messages, or cached media.

## 3. Repair Vencord conservatively

If Discord Stable exists but Vencord is absent or broken, use the local CyberKird wrapper only when it is already installed and points to the official installer:

```sh
"$HOME/Library/Application Support/vencord-autopatcher/vencord-autopatcher.sh" -b stable -u
```

If that wrapper is missing, download the official Vencord installer from the official GitHub release, inspect the download source, and run it interactively. Do not replace it with BetterVencordPatch or another patcher.

The only permitted download is the official Vencord release asset. Download it as an archive, then test the archive before opening it; never pipe a download into a shell:

```sh
installer_zip="$HOME/Downloads/VencordInstaller.MacOS.zip"
curl -fL --proto '=https' --retry 3 -o "$installer_zip" \
  "https://github.com/Vencord/Installer/releases/latest/download/VencordInstaller.MacOS.zip"
unzip -t "$installer_zip"
open "$installer_zip"
```

This is intentionally an interactive installer path. If Gatekeeper blocks it, use the macOS Privacy & Security approval flow; do not bypass it, disable Gatekeeper, or substitute an unofficial binary. On Apple Silicon, try Rosetta only when the official installer itself fails to start, then record the failure and retry the same official asset.

Validate the patch by checking both `app.asar` and `_app.asar`, then use Computer Use to confirm the Vencord section appears in Discord settings. A Gatekeeper prompt needs an explicit user action in macOS Privacy & Security; do not work around it.

## 4. Apply the efficient profile

Keep the profile small and observable:

- Required `NoTrack`: keep `disableAnalytics` enabled. It disables analytics, metrics, and Sentry reporting.
- Enable `NoTypingAnimation`.
- Keep `CrashHandler` enabled.
- Enable `ConsoleJanitor`, but preserve error-level logs; it can hide useful diagnostics.
- In Discord Settings → Advanced, keep Hardware Acceleration enabled. Changing it can require a Discord restart, so do not restart a live call or stream without explicit permission.
- Prefer fewer enabled plugins over speculative performance plugins. Confirm OpenAsar/Vencord state rather than installing another client mod.

Use the live Vencord Plugins UI to toggle these values and re-inspect every resulting switch. Some settings take effect only after a renderer reload; document that as pending rather than forcing an interruption. Treat Hardware Acceleration as **unknown** until the live Advanced settings page visibly confirms it; its usual default is not proof.

## 5. Restore after an update or failure

1. In the selected backup directory, run `shasum -a 256 -c SHA256SUMS` to verify the archived snapshot before relying on it.
2. Compare the current archives and Vencord settings to that verified snapshot.
3. Run the official Stable patch path above.
4. Restore only the Vencord settings file from the selected backup if the user asks to recover their preferences.
5. Validate Discord's Vencord navigation, required plugin states, and the configured LaunchAgent.
6. If Discord cannot start, stop and report the exact failure plus the backup path; do not try alternative clients or broad cache deletion.

## 6. AquaMuteSync note

When AquaMuteSync is installed, confirm `enabled: true`, its configured helper port (commonly `8688`), and a live helper on localhost. A 50-ms drift poll is a current configuration choice, not a universal requirement. Measure the helper-to-Discord state transition with a read-only WebSocket observer before claiming a latency improvement. The observer must only request state: it must never publish an `app_state` payload, because that would become a second Discord state producer. Never run a synthetic recording trial while the user is actively dictating or in a sensitive call.

## Completion evidence

Report the Discord channel, Vencord patch evidence, backup path and hash manifest, enabled profile switches, Hardware Acceleration state, and any restart still required. Keep remaining risks explicit.
