#!/usr/bin/env bash
set -e

# Parse command-line arguments for version bump type and remote
bump_type="patch"  # default to patch
remote="upstream"  # default to upstream
while [[ $# -gt 0 ]]; do
  case $1 in
    --major)
      bump_type="major"
      shift
      ;;
    --minor)
      bump_type="minor"
      shift
      ;;
    --patch)
      bump_type="patch"
      shift
      ;;
    --remote)
      remote="$2"
      shift 2
      ;;
    *)
      echo "Unknown option: $1"
      echo "Usage: $0 [--major|--minor|--patch] [--remote <remote-name>]"
      exit 1
      ;;
  esac
done

# Detect default branch (main or master)
branch=$(git remote show "$remote" 2>/dev/null | grep 'HEAD branch' | awk '{print $NF}' || echo "master")

# Fetch latest tags quietly
git fetch "$remote" --tags >/dev/null

# Find the latest tag and bump version based on type
latest_tag=$(git describe --tags --abbrev=0 "$remote/$branch" 2>/dev/null || echo "")

if [[ -z "$latest_tag" ]]; then
  # No tags found, use v0.0.0 as base and show all commits
  echo "No tags found, starting from v0.0.0"
  case $bump_type in
    major)
      new_tag="v1.0.0"
      ;;
    minor)
      new_tag="v0.1.0"
      ;;
    patch)
      new_tag="v0.0.1"
      ;;
  esac
  
  # Print changelog header
  echo
  echo "Version ${new_tag} (released $(date +%Y-%m-%d))"
  echo
  
  # Get all commit messages
  git --no-pager log HEAD --pretty=format:"%s" --no-merges \
    | grep -viE '(^release:|chore\(release\)|bump version|prepare release)' \
    | sed 's/^/- /'
else
  # Tags exist, bump version normally
  ver=${latest_tag#v}
  IFS='.' read -r major minor patch <<< "$ver"

  case $bump_type in
    major)
      new_tag="v$((major + 1)).0.0"
      ;;
    minor)
      new_tag="v${major}.$((minor + 1)).0"
      ;;
    patch)
      new_tag="v${major}.${minor}.$((patch + 1))"
      ;;
  esac

  # Print changelog header
  echo
  echo "Version ${new_tag} (released $(date +%Y-%m-%d))"
  echo

  # Get commit messages and exclude release-related ones
  git --no-pager log "${latest_tag}..HEAD" --pretty=format:"%s" --no-merges \
    | grep -viE '(^release:|chore\(release\)|bump version|prepare release)' \
    | sed 's/^/- /'
fi

echo
