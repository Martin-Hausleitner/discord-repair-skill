#!/bin/bash
set -euo pipefail
umask 077

backup_root="$HOME/Library/Application Support/discord-repair/backups"
stamp="$(date +%Y%m%d-%H%M%S)"
destination="$backup_root/$stamp"
discord_resources="/Applications/Discord.app/Contents/Resources"
vencord_settings="$HOME/Library/Application Support/Vencord/settings/settings.json"

if [[ ! -d /Applications/Discord.app ]]; then
  echo "Discord Stable is missing at /Applications/Discord.app" >&2
  exit 1
fi

for required in "$discord_resources/app.asar" "$discord_resources/_app.asar" "$vencord_settings"; do
  if [[ ! -f "$required" ]]; then
    echo "Required recovery input is missing: $required" >&2
    exit 2
  fi
done

mkdir -p "$destination"

for file in "$discord_resources/app.asar" "$discord_resources/_app.asar" "$vencord_settings"; do
  ditto "$file" "$destination/$(basename "$file")"
done

if [[ ! -f "$destination/app.asar" || ! -f "$destination/_app.asar" ]]; then
  echo "Vencord archive pair is incomplete; backup kept at $destination" >&2
  exit 3
fi

(cd "$destination" && shasum -a 256 app.asar _app.asar settings.json > SHA256SUMS)
echo "$destination"
