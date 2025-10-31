#!/bin/bash
# --- DealCraft Repo Branch Cleanup (safe by default) ---
# What this does:
# 1) Prunes local refs, lists remote branches
# 2) Finds branches merged into DEFAULT_BRANCH, excludes "keep" list
# 3) Skips branches that still have OPEN PRs
# 4) Deletes safe remote branches (dry-run by default), then local merged branches
# 5) Enables GitHub setting: "Automatically delete head branches"
#
# Requirements:
# - gh CLI authenticated: `gh auth login`
# - git CLI and push rights to origin
#
# Customize these:
REPO_SLUG="routerjoe/DealCraft"         # <owner>/<repo>
DEFAULT_BRANCH="main"                    # default branch
DRY_RUN="true"                           # set to "false" to actually delete

# Keep list (regex): protected & long-lived branches you NEVER want auto-deleted
KEEP_REGEX='^(origin/(main|develop|dev|release/.*|hotfix/.*|gh-pages|wiki|docs|pages|changelog|v[0-9]+\.[0-9]+\.[0-9]+))$'

set -euo pipefail

echo "Repo: $REPO_SLUG | Default: $DEFAULT_BRANCH | DRY_RUN=$DRY_RUN"
echo "Fetching/pruning remote refs…"
git fetch --all --prune

# Ensure we're on default branch and up to date (optional but recommended)
current_branch="$(git rev-parse --abbrev-ref HEAD)"
if [[ "$current_branch" != "$DEFAULT_BRANCH" ]]; then
  echo "Switching to $DEFAULT_BRANCH…"
  git checkout "$DEFAULT_BRANCH"
fi
git pull --ff-only origin "$DEFAULT_BRANCH"

echo
echo "Remote branches merged into origin/$DEFAULT_BRANCH (candidates):"
git branch -r --merged "origin/$DEFAULT_BRANCH" | sed 's|^\s*||' | grep -vE "$KEEP_REGEX" || true

# Build deletion list excluding:
# - protected/keep branches (KEEP_REGEX)
# - branches with OPEN PRs
echo
echo "Computing safe-to-delete remote branches (no open PRs, merged into $DEFAULT_BRANCH)…"
SAFE_DELETE=()
while IFS= read -r rb; do
  rb="$(echo "$rb" | sed 's|^\s*||')"
  [[ -z "$rb" ]] && continue
  [[ "$rb" =~ ^origin/ ]] || continue
  if echo "$rb" | grep -Eq "$KEEP_REGEX"; then
    continue
  fi
  head_branch="${rb#origin/}"
  # Skip default branch explicitly
  [[ "$head_branch" == "$DEFAULT_BRANCH" ]] && continue
  # Skip if has open PR
  open_pr_count="$(gh pr list --repo "$REPO_SLUG" --state open --head "$head_branch" --json number -q 'length' || echo "0")"
  if [[ "${open_pr_count:-0}" -gt 0 ]]; then
    echo "Skip (open PR exists): $head_branch"
    continue
  fi
  SAFE_DELETE+=("$head_branch")
done < <(git branch -r --merged "origin/$DEFAULT_BRANCH")

echo
echo "Safe remote branches:"
if [[ "${#SAFE_DELETE[@]}" -gt 0 ]]; then
  printf '  - %s\n' "${SAFE_DELETE[@]}"
else
  echo "  (none)"
fi

# Delete or dry-run
if [[ "${#SAFE_DELETE[@]}" -gt 0 ]]; then
  echo
  if [[ "$DRY_RUN" == "true" ]]; then
    echo "DRY RUN: would delete these remote branches:"
    printf '  git push origin --delete %s\n' "${SAFE_DELETE[@]}"
  else
    echo "Deleting remote branches…"
    for b in "${SAFE_DELETE[@]}"; do
      git push origin --delete "$b" || echo "WARN: failed to delete $b"
    done
  fi
else
  echo "No remote branches to delete."
fi

# Clean local merged branches (excluding default & develop)
echo
echo "Local merged branches (candidates):"
LOCAL_CANDIDATES=()
while IFS= read -r b; do
  # Remove asterisk, trim all leading/trailing whitespace
  b="$(echo "$b" | sed 's|^\*||' | xargs)"
  [[ -z "$b" ]] && continue
  # Skip protected branches
  [[ "$b" =~ ^($DEFAULT_BRANCH|develop|dev)$ ]] && continue
  LOCAL_CANDIDATES+=("$b")
done < <(git branch --merged "origin/$DEFAULT_BRANCH")

if [[ "${#LOCAL_CANDIDATES[@]}" -gt 0 ]]; then
  printf '  - %s\n' "${LOCAL_CANDIDATES[@]}"
else
  echo "  (none)"
fi

if [[ "${#LOCAL_CANDIDATES[@]}" -gt 0 ]]; then
  if [[ "$DRY_RUN" == "true" ]]; then
    echo "DRY RUN: would delete local merged branches:"
    for b in "${LOCAL_CANDIDATES[@]}"; do
      echo "  git branch -d $b"
    done
  else
    echo "Deleting local merged branches…"
    for b in "${LOCAL_CANDIDATES[@]}"; do
      git branch -d "$b" || echo "WARN: failed to delete local $b"
    done
  fi
fi

# Enable "Automatically delete head branches" on GitHub (one-time repo setting)
# Requires: gh auth scope 'repo' / admin on the repo
echo
echo "Enabling 'Automatically delete head branches' on GitHub…"
gh api -X PATCH "repos/$REPO_SLUG" -f delete_branch_on_merge=true >/dev/null \
  && echo "GitHub setting enabled." \
  || echo "NOTE: Could not enable setting (permissions or scope). Enable in Settings > General > Pull Requests."

echo
echo "Done. Review above output."
echo "TIP: Rerun with DRY_RUN=\"false\" to perform deletions."
# --- end ---
