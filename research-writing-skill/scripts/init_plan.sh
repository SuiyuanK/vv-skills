#!/usr/bin/env bash
set -euo pipefail

# Usage:
#   bash scripts/init_plan.sh [project_root]
# Default project_root is current directory.

PROJECT_ROOT="${1:-$(pwd)}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
TEMPLATE_DIR="$SKILL_DIR/plan-template"
PLAN_DIR="$PROJECT_ROOT/plan"

mkdir -p "$PLAN_DIR"

copied=0
for name in project-overview.md progress.md notes.md outline.md stage-gates.md; do
  src="$TEMPLATE_DIR/$name"
  dst="$PLAN_DIR/$name"

  if [[ ! -f "$src" ]]; then
    echo "[WARN] template missing: $src"
    continue
  fi

  if [[ -f "$dst" ]]; then
    echo "[SKIP] exists: $dst"
  else
    cp "$src" "$dst"
    echo "[ADD]  $dst"
    copied=$((copied + 1))
  fi
done

echo "[DONE] plan bootstrap finished. files_copied=$copied plan_dir=$PLAN_DIR"
