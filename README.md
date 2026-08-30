# Discord Repair Skill

A public Codex skill for maintaining a fast, repairable Discord Stable + Vencord setup on macOS.

It deliberately avoids the tempting but fragile route: no Discord channel switching, no competing client mods, no `sudo`, and no mystery patchers. The skill uses Discord Stable at `/Applications/Discord.app`, backs up only the Vencord runtime state required for recovery, and uses the official Vencord installer path.

## What it does

- Verifies Discord Stable, the Vencord archive pair, and persisted Vencord settings.
- Creates a local, SHA-256-manifested snapshot before repair. The backup excludes account tokens, messages, browser profiles, and media caches.
- Repairs Vencord through the official installer or the already-installed CyberKird wrapper for the Stable branch.
- Applies a conservative performance profile: NoTrack, NoTypingAnimation, CrashHandler, ConsoleJanitor, and Hardware Acceleration when appropriate.
- Preserves live calls and streams: a restart is never forced merely to make a setting look green.
- Documents AquaMuteSync readiness and the rules for safe latency measurement.

The repository is public. Local backups, their manifests, Discord logs, and screenshots may contain private path or account-adjacent metadata; keep all of them out of Git and issue comments.

## Use

Copy or symlink `.codex/skills/discord-repair` into your Codex skills directory, then invoke the skill when Discord or Vencord needs recovery. The included scripts can also be run directly:

```sh
bash .codex/skills/discord-repair/scripts/verify.sh
bash .codex/skills/discord-repair/scripts/backup-vencord.sh
```

The skill is intentionally macOS-specific. It is designed for a setup that values predictable recovery and low background overhead more than accumulating plugins.
