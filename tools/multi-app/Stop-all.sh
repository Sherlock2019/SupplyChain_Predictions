#!/usr/bin/env bash
# Stop what Start-all.sh started, in reverse order (last started is stopped first).
#
#   ./Stop-all.sh            stop all projects
#   ./Stop-all.sh A B        stop only projects A and B (folder names)
#
# Each project: its own stop script (stop.sh / stop-demo.sh / stop-localdemo.sh) if it has one, then the launcher's processes.
set -uo pipefail
ROOT=$(cd "$(dirname "$0")" && pwd)
[ -f "$ROOT/Start-all.sh" ] || { echo "Start-all.sh not found next to this script ($ROOT)"; exit 1; }

if [ "$#" -gt 0 ]; then names=("$@")
else mapfile -t names < <(bash "$ROOT/Start-all.sh" list | awk '{print $1}'); fi
[ "${#names[@]}" -gt 0 ] || { echo "nothing to stop"; exit 0; }

reversed=()
for ((i=${#names[@]}-1; i>=0; i--)); do reversed+=("${names[$i]}"); done

before=$(ss -ltnH 2>/dev/null | awk '{print $4}' | sed 's/.*://' | sort -un | tr '\n' ' ')
printf '\033[1mStopping %d project(s), last started first\033[0m\n' "${#reversed[@]}"
for p in "${reversed[@]}"; do bash "$ROOT/Start-all.sh" stop "$p"; done

after=$(ss -ltnH 2>/dev/null | awk '{print $4}' | sed 's/.*://' | sort -un | tr '\n' ' ')
freed=$(comm -23 <(tr ' ' '\n' <<<"$before" | sed '/^$/d' | sort) <(tr ' ' '\n' <<<"$after" | sed '/^$/d' | sort) | sort -n | tr '\n' ' ')
echo
echo "  Ports freed:        ${freed:-none}"
echo "  Still listening:    ${after:-none}"
running=$(docker ps --format '{{.Names}}' 2>/dev/null | head -20 | tr '\n' ' ')
[ -n "$running" ] && echo "  Containers still up: $running  (stop one: docker stop NAME · all: docker stop \$(docker ps -q))"
echo "  Start again: ./Start-all.sh"
