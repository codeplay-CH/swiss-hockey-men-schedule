#!/usr/bin/env bash
# Reject commits that touch generated calendar files (except github-actions bot).
set -euo pipefail

FORBIDDEN=(data/games.json public/calendar.ics)
BOT_EMAIL_MARKER="github-actions"

usage() {
  echo "Usage: $0 --staged | --range <git-rev-range>" >&2
  exit 2
}

is_forbidden_file() {
  local file="$1"
  local forbidden
  for forbidden in "${FORBIDDEN[@]}"; do
    if [[ "$file" == "$forbidden" ]]; then
      return 0
    fi
  done
  return 1
}

list_forbidden_in_files() {
  local files="$1"
  local file
  local found=()
  while IFS= read -r file; do
    [[ -z "$file" ]] && continue
    if is_forbidden_file "$file"; then
      found+=("$file")
    fi
  done <<<"$files"
  if ((${#found[@]} > 0)); then
    printf '%s\n' "${found[@]}"
    return 0
  fi
  return 1
}

is_bot_commit() {
  local sha="$1"
  local email name
  email=$(git log -1 --format='%ae' "$sha")
  name=$(git log -1 --format='%an' "$sha")
  [[ "$email" == *"$BOT_EMAIL_MARKER"* ]] || [[ "$name" == "github-actions[bot]" ]]
}

fail_with_help() {
  local context="$1"
  shift
  echo "ERROR: $context touches generated calendar data:" >&2
  printf '  - %s\n' "$@" >&2
  echo >&2
  echo "Only the GitHub Action should commit these files." >&2
  echo "Restore them: git restore --staged --worktree data/games.json public/calendar.ics" >&2
  exit 1
}

check_staged() {
  local files forbidden
  files=$(git diff --cached --name-only || true)
  if forbidden=$(list_forbidden_in_files "$files"); then
    fail_with_help "Staged changes" $forbidden
  fi
}

check_range() {
  local range="$1"
  local sha files forbidden author
  if ! git rev-parse --verify "${range}^{commit}" >/dev/null 2>&1; then
    # Empty range (e.g. force-push edge case) — nothing to check.
    return 0
  fi
  while IFS= read -r sha; do
    [[ -z "$sha" ]] && continue
    if is_bot_commit "$sha"; then
      continue
    fi
    files=$(git diff-tree --no-commit-id --name-only -r "$sha" || true)
    if forbidden=$(list_forbidden_in_files "$files"); then
      author=$(git log -1 --format='%an <%ae>' "$sha")
      fail_with_help "Commit ${sha:0:7} by ${author}" $forbidden
    fi
  done < <(git rev-list "$range" 2>/dev/null || true)
}

case "${1:-}" in
  --staged)
    check_staged
    ;;
  --range)
    [[ $# -eq 2 ]] || usage
    check_range "$2"
    ;;
  *)
    usage
    ;;
esac
