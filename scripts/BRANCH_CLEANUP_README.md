# Branch Cleanup Script

## Overview

`cleanup_branches.sh` is a safe, automated script for cleaning up merged Git branches in the DealCraft repository. It operates in dry-run mode by default to prevent accidental deletions.

## Features

- ✅ **Safe by default**: Runs in dry-run mode unless explicitly disabled
- ✅ **PR-aware**: Skips branches with open pull requests
- ✅ **Protected branches**: Never deletes main, develop, release, or hotfix branches
- ✅ **Local + Remote**: Cleans both local and remote branches
- ✅ **GitHub integration**: Enables automatic branch deletion on PR merge

## Prerequisites

Before running this script, ensure you have:

1. **Git CLI** installed and configured
2. **GitHub CLI** (`gh`) installed and authenticated
   ```bash
   gh auth login
   ```
3. **Push rights** to the `origin` remote
4. **Admin access** to the repository (for GitHub settings change)

## Usage

### Dry Run (Safe Mode - Default)

To preview what would be deleted without making any changes:

```bash
./scripts/cleanup_branches.sh
```

This will:
- Show all merged branches that are candidates for deletion
- Display which branches have open PRs (and will be skipped)
- List the exact commands that would be executed

### Actual Deletion

To perform the actual cleanup:

```bash
# Option 1: Edit the script and change DRY_RUN="false"
# Option 2: Override via environment variable
DRY_RUN=false ./scripts/cleanup_branches.sh
```

## Configuration

Edit these variables at the top of the script to customize behavior:

```bash
REPO_SLUG="routerjoe/DealCraft"         # GitHub repository
DEFAULT_BRANCH="main"                    # Your default branch
DRY_RUN="true"                           # Set to "false" to actually delete
```

### Protected Branches

The following branches are **never** deleted (configured via `KEEP_REGEX`):

- `main`
- `develop` / `dev`
- `release/*` (any release branch)
- `hotfix/*` (any hotfix branch)
- `gh-pages`
- `wiki`, `docs`, `pages`, `changelog`
- `v*` (version tags like v1.0.0)

To modify this list, edit the `KEEP_REGEX` variable in the script.

## What Gets Deleted

The script will delete branches that meet **ALL** of these criteria:

1. ✅ Branch is merged into `origin/main`
2. ✅ Branch is **not** in the protected list
3. ✅ Branch has **no open pull requests**
4. ✅ Branch is not the current default branch

## Safety Features

1. **Dry-run by default**: Must explicitly disable to delete
2. **PR checking**: Uses GitHub API to verify no open PRs exist
3. **Protected branch list**: Multiple safeguards against deleting important branches
4. **Local safety**: Local branches use `-d` flag (safe delete, only if merged)
5. **Error handling**: Continues on errors with warnings

## Workflow Example

```bash
# Step 1: Run in dry-run mode to see what would be deleted
./scripts/cleanup_branches.sh

# Step 2: Review the output carefully
# - Check that no important branches are listed
# - Verify the "Skip (open PR exists)" messages are correct

# Step 3: If satisfied, run with deletions enabled
DRY_RUN=false ./scripts/cleanup_branches.sh

# Step 4: Verify the cleanup
git branch -a
```

## Troubleshooting

### "Could not enable setting (permissions or scope)"

This error occurs when enabling the GitHub "Automatically delete head branches" setting. You can:
- Ensure you have admin access to the repository
- Ensure `gh` CLI has the `repo` scope: `gh auth refresh -s repo`
- Manually enable in GitHub: Settings → General → Pull Requests → "Automatically delete head branches"

### "WARN: failed to delete branch"

This can happen if:
- The branch has been deleted by someone else
- You don't have push permissions
- The branch is protected on GitHub

These warnings are non-fatal and the script will continue.

### Script switches branches unexpectedly

The script automatically switches to the default branch (`main`) to ensure proper merge detection. This is expected behavior.

## GitHub Auto-Deletion

The script attempts to enable GitHub's native "Automatically delete head branches" feature. Once enabled, GitHub will automatically delete head branches after PRs are merged, reducing the need for manual cleanup.

To verify this setting:
1. Go to your GitHub repository
2. Navigate to Settings → General
3. Scroll to "Pull Requests" section
4. Check if "Automatically delete head branches" is enabled

## Best Practices

1. **Run regularly**: Weekly or monthly to keep your branch list clean
2. **Always dry-run first**: Review the output before actual deletion
3. **Check for active work**: Coordinate with team members before cleanup
4. **Keep PR discipline**: Close or merge PRs promptly to allow branch cleanup
5. **Use GitHub auto-deletion**: Enable it once, let GitHub handle future cleanups

## Related Files

- Main script: `scripts/cleanup_branches.sh`
- This README: `scripts/BRANCH_CLEANUP_README.md`

## Support

For issues or questions:
- Check the script's inline comments
- Review GitHub branch protection rules
- Verify `gh` CLI authentication and permissions
