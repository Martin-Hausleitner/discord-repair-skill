#!/bin/bash
set -euo pipefail

discord_app="/Applications/Discord.app"
resources="$discord_app/Contents/Resources"
settings="$HOME/Library/Application Support/Vencord/settings/settings.json"

printf 'architecture=%s\n' "$(uname -m)"

if [[ ! -d "$discord_app" ]]; then
  echo "FAIL discord_stable=missing"
  exit 1
fi

bundle_id="$(/usr/libexec/PlistBuddy -c 'Print :CFBundleIdentifier' "$discord_app/Contents/Info.plist")"
printf 'bundle_id=%s\n' "$bundle_id"
[[ "$bundle_id" == "com.hnc.Discord" ]] || { echo "FAIL unsupported_discord_channel"; exit 2; }

for archive in "$resources/app.asar" "$resources/_app.asar"; do
  [[ -f "$archive" ]] || { echo "FAIL missing=$(basename "$archive")"; exit 3; }
done

[[ -r "$settings" ]] || { echo "FAIL vencord_settings=missing"; exit 4; }
command -v node >/dev/null 2>&1 || { echo "FAIL node_required_to_validate_vencord_json"; exit 4; }
node -e 'JSON.parse(require("fs").readFileSync(process.argv[1], "utf8"))' "$settings" \
  || { echo "FAIL vencord_settings=invalid_json"; exit 4; }

for competing in /Applications/vesktop.app /Applications/Discord\ PTB.app /Applications/Discord\ Canary.app; do
  [[ ! -e "$competing" ]] || { echo "FAIL competing_client=$competing"; exit 5; }
done

for term in BetterDiscord Equicord BetterVencordPatch; do
  if pgrep -ifl "$term" >/dev/null 2>&1; then
    echo "FAIL competing_process=$term"
    exit 6
  fi
done

if find "$HOME/Library/LaunchAgents" -maxdepth 1 -type f \( -iname '*betterdiscord*' -o -iname '*equicord*' -o -iname '*bettervencordpatch*' \) -print -quit | grep -q .; then
  echo "FAIL competing_launch_agent=present"
  exit 7
fi

echo "PASS Discord Stable + Vencord archives and settings are present"
