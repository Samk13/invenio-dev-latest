#!/usr/bin/env bash
set -euo pipefail

usage() {
    cat <<EOF
Usage: $(basename "$0") [OPTIONS] [BASE_BRANCH]

Generate a .diff file for the current branch against a base branch.

By default:
  - Uses 'master' as the base branch if it exists.
  - Falls back to 'main' if 'master' does not exist.
  - Includes committed changes only.
  - Writes the diff to <current-branch>.diff.

Options:
  --staged    Include committed branch changes plus all currently
              staged changes. Unstaged and untracked files are excluded.

  -h, --help  Show this help message.

Arguments:
  BASE_BRANCH Override the base branch
              (e.g. main, develop, release/1.0).

Examples:
  $(basename "$0")
      Committed branch changes against master/main.

  $(basename "$0") main
      Committed branch changes against main.

  $(basename "$0") --staged
      Committed branch changes + staged changes.

  $(basename "$0") --staged develop
      Same, using develop as the base.

Note:
  Unstaged and untracked files are not included with --staged.
EOF
}

INCLUDE_STAGED=false
BASE_BRANCH=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --staged)
            INCLUDE_STAGED=true
            shift
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        -*)
            echo "Error: unknown option '$1'" >&2
            usage >&2
            exit 1
            ;;
        *)
            if [[ -n "$BASE_BRANCH" ]]; then
                echo "Error: multiple base branches specified" >&2
                exit 1
            fi
            BASE_BRANCH="$1"
            shift
            ;;
    esac
done

CURRENT_BRANCH=$(git branch --show-current)

if [[ -z "$CURRENT_BRANCH" ]]; then
    echo "Error: not currently on a branch" >&2
    exit 1
fi

# Determine base branch
if [[ -z "$BASE_BRANCH" ]]; then
    if git rev-parse --verify master >/dev/null 2>&1; then
        BASE_BRANCH="master"
    elif git rev-parse --verify main >/dev/null 2>&1; then
        BASE_BRANCH="main"
    else
        echo "Error: neither master nor main exists." >&2
        echo "Specify a base branch: $(basename "$0") <branch>" >&2
        exit 1
    fi
fi

if ! git rev-parse --verify "$BASE_BRANCH" >/dev/null 2>&1; then
    echo "Error: branch '$BASE_BRANCH' does not exist" >&2
    exit 1
fi

OUTPUT="${CURRENT_BRANCH//\//-}.diff"

if [[ "$INCLUDE_STAGED" == true ]]; then
    #
    # Compare the merge-base directly against the INDEX.
    #
    # This gives us:
    #   - committed changes on the current branch
    #   - staged changes
    #   - NOT unstaged changes
    #
    MERGE_BASE=$(git merge-base "$BASE_BRANCH" HEAD)

    git diff --cached "$MERGE_BASE" -- > "$OUTPUT"
else
    #
    # Committed branch changes only.
    #
    git diff "$BASE_BRANCH"...HEAD -- > "$OUTPUT"
fi

echo "Current branch: $CURRENT_BRANCH"
echo "Base branch:    $BASE_BRANCH"
echo "Staged:         $INCLUDE_STAGED"
echo "Created:        $OUTPUT"