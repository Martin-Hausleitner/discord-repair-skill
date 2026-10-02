---
name: discord-aqua-repair
description: Repair Discord Stable voice capture with one physical button, AquaMuteSync observation, and Vencord-safe recovery on macOS.
metadata:
  version: 1.1.0
  triggers:
    - repair AquaMuteSync
    - Discord recording button broken
    - measure Discord voice latency
    - fix AutoStream FPS
---

# Discord Aqua Repair

Use this skill for a macOS Discord Stable setup that routes one physical control through AquaMuteSync and Vencord. Keep the control path single-owner and observable.

## Non-negotiable boundaries

- Use Codex Computer Use only for Discord, AquaMuteSync, Vencord, or other GUI interaction. Do not use Orca, AppleScript, synthetic keyboard tools, or a second GUI driver.
- The physical button must produce exactly one `set_recording` action. AquaMuteSync watches that state and Vencord remains the Discord-side integration. Never add a second producer, duplicate shortcut, macro, or fallback hotkey.
- Remove a shortcut collision only after observing the collision in the current UI or configuration. Do not guess which binding is stale.
- Never open the graphical Vencord Installer. Follow the sibling `discord-repair/SKILL.md` quiet recovery path, including the pinned custom-bundle-safe CLI and live-call deferral. The old GUI installer and CyberKird wrapper are prohibited by the operator as of 2026-09-07.
- A VCVM demo account must already be provisioned and usable. Do not bypass CAPTCHA, email verification, login controls, or rate limits.
- Keep account names, channel names, device identifiers, local paths, tokens, screenshots, and logs out of public reports. Replace them with placeholders such as `$HOME`, `<demo-account>`, and `<voice-channel>`.
- Do not call `app_state`, `set_recording`, or any input/process-writing API from an observer or benchmark.

## Repair sequence

1. Inspect the latest Discord and AquaMuteSync state with Computer Use. Record whether the button, helper, Vencord integration, and current shortcut are visible.
2. Trace one press: physical button → one `set_recording` transition → AquaMuteSync watch event → Vencord/Discord state. If two transitions appear for one press, stop and report the duplicate producer.
3. If a collision is confirmed, remove only the conflicting shortcut and re-test one press. Do not change unrelated bindings.
4. If Vencord is missing or broken, follow the sibling Discord Repair skill: back up, defer while Discord runs, and use its verified quiet guard. Validate the Stable branch, custom plugins and both archive roles before continuing.
5. Confirm the demo-account preconditions in VCVM. Use a non-sensitive test call; never run a synthetic recording trial while a real user is dictating or in a sensitive call.

## Read-only latency benchmark

Use the bundled observer for measurements. It samples timestamps from an existing local event stream; it does not publish state or press controls.

```sh
python3 .codex/skills/discord-aqua-repair/scripts/observe_latency.py --input "$HOME/aqua-events.jsonl" --output "$HOME/aqua-benchmark.json"
```

The input must contain sanitized JSON Lines with `{"phase":"start|stop","t_ms":123.4}` records. The output reports start and stop p50, p95, and p99 plus sample counts. A valid run must preserve the recording state before and after the observation; if the stream is unavailable or the state changes, report `inconclusive` rather than inventing a latency result.

Compare start and stop distributions separately. Do not collapse them into one average, and do not claim an improvement without the sample counts and restoration result.

## AutoStream FPS

Report AutoStream FPS as two values:

- **Desired FPS**: the configured target in the UI or configuration.
- **Effective FPS**: the observed delivered rate during the test window.

Changing Desired FPS does not prove Effective FPS changed. Record resolution, network conditions, and the observation window using placeholders only. Never restart a live call or stream solely to make the values match.

## Publish checklist

Before sharing a README excerpt, issue, benchmark, or screenshot:

- Replace personal paths with `$HOME` and redact usernames, account IDs, channel names, device IDs, ports, tokens, and message text.
- Remove raw logs and screenshots unless they have been reviewed for secrets and metadata.
- State that the benchmark is read-only and that the recording state was restored.
- Include start/stop p50, p95, p99 and sample counts, or mark the result inconclusive.
- Include Desired vs Effective FPS separately.
- Confirm no CAPTCHA, email, login, or rate-limit bypass was used.
