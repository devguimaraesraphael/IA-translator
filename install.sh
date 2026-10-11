#!/usr/bin/env bash
# Links every skill in ./skills into ~/.claude/skills. Existing real folders are moved to a dated backup.
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEST="${CLAUDE_SKILLS_DIR:-$HOME/.claude/skills}"
BACKUP="$DEST/.backup-ia-translator-$(date +%Y%m%d-%H%M%S)"
DRY_RUN=0

[[ "${1:-}" == "--dry-run" ]] && DRY_RUN=1

run() { if (( DRY_RUN )); then echo "[dry-run] $*"; else "$@"; fi; }

run mkdir -p "$DEST"

for skill in "$REPO"/skills/*/; do
  name="$(basename "$skill")"
  target="$DEST/$name"

  if [[ -L "$target" ]]; then
    [[ "$(readlink -f "$target")" == "${skill%/}" ]] && { echo "ok      $name (already linked)"; continue; }
    run rm "$target"
  elif [[ -e "$target" ]]; then
    run mkdir -p "$BACKUP"
    run mv "$target" "$BACKUP/$name"
    echo "backup  $name -> $BACKUP/$name"
  fi

  run ln -s "${skill%/}" "$target"
  echo "linked  $name"
done
