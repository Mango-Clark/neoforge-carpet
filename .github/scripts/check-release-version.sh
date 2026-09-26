#!/usr/bin/env bash
set -euo pipefail

properties_file=${1:-gradle.properties}

property() {
  local key=$1
  sed -nE "s/^[[:space:]]*${key}[[:space:]]*=[[:space:]]*([^[:space:]#]+)[[:space:]]*(#.*)?$/\1/p"
}

current=$(<"$properties_file")
current_tick=$(printf '%s\n' "$current" | property tick_version)
current_carpet=$(printf '%s\n' "$current" | property carpet_version)

if [[ -z "$current_tick" || -z "$current_carpet" ]]; then
  echo '::error::Missing tick_version or carpet_version.'
  exit 1
fi
if [[ "$current_carpet" != '1.4.112' ]]; then
  echo '::error::carpet_version must remain at 1.4.112.'
  exit 1
fi

if [[ "${EVENT_NAME:-push}" == 'workflow_dispatch' ]]; then
  selected_tick=${INPUT_TICK_VERSION:-}
  if [[ ! "$selected_tick" =~ ^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9]*)$ ]]; then
    echo '::error::Manual tick_version must use SemVer MAJOR.MINOR.PATCH.'
    exit 1
  fi
  current_tick=$selected_tick
else
  before=${GITHUB_EVENT_BEFORE:?GITHUB_EVENT_BEFORE is required}
  if [[ "$before" =~ ^0+$ ]]; then
    echo 'No previous commit on this branch; skipping release.'
    exit 0
  fi
  if ! git cat-file -e "${before}:gradle.properties" 2>/dev/null; then
    echo '::error::Previous gradle.properties is unavailable; refusing to release.'
    exit 1
  fi

  previous=$(git show "${before}:gradle.properties")
  previous_tick=$(printf '%s\n' "$previous" | property tick_version)
  previous_carpet=$(printf '%s\n' "$previous" | property carpet_version)
  if [[ -z "$previous_tick" ]]; then
    echo 'No previous tick_version; skipping initial version adoption.'
    exit 0
  fi
  if [[ "$previous_tick" == "$current_tick" ]]; then
    echo "tick_version is unchanged (${current_tick}); skipping release."
    exit 0
  fi
  if [[ "$previous_carpet" != "$current_carpet" ]]; then
    echo '::error::carpet_version must not change in a tick release.'
    exit 1
  fi
  if [[ ! "$current_tick" =~ ^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9]*)$ ]]; then
    echo '::error::tick_version must use SemVer MAJOR.MINOR.PATCH.'
    exit 1
  fi
fi

version="${current_carpet}-tick-${current_tick}"
echo "changed=true" >> "$GITHUB_OUTPUT"
echo "version=${version}" >> "$GITHUB_OUTPUT"
echo "tag=v${version}" >> "$GITHUB_OUTPUT"
echo "Publishing ${version}"
