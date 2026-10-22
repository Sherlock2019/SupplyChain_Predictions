#!/usr/bin/env bash
# Start every project in this folder with its own launcher, each in the background with its own log.
#
#   ./Start-all.sh                  start all projects (one after another), then show each app's URLs as it comes up
#   ./Start-all.sh start A B        start only projects A and B (folder names)
#   ./Start-all.sh list             projects found and the launcher each one uses
#   ./Start-all.sh urls [A B]       each app's URLs (read from its log, localhost replaced by the public IP)
#   ./Start-all.sh status           running or not, last log line, listening ports, URLs
#   ./Start-all.sh logs NAME        follow one project's log (Ctrl-C stops following only)
#   ./Start-all.sh stop [A B]       stop all (or some) projects
#
# Launcher per project, first found: start.sh, start-demo.sh, start-aws.sh, start-localdemo.sh.
# Logs and pids: ./.start-all/. Startups keep running after you log out of SSH.
set -uo pipefail
ROOT=$(cd "$(dirname "$0")" && pwd)
STATE="$ROOT/.start-all"; mkdir -p "$STATE"
LAUNCHERS=(start.sh start-demo.sh start-aws.sh start-localdemo.sh)
GAP=${START_ALL_GAP:-20}   # seconds between two startups, so builds do not all hit CPU/RAM at once

ok() { printf '  \033[32m✔\033[0m %s\n' "$*"; }
warn() { printf '  \033[33m!\033[0m %s\n' "$*"; }
err() { printf '  \033[31m✘\033[0m %s\n' "$*"; }

launcher_of() { local l; for l in "${LAUNCHERS[@]}"; do [ -f "$ROOT/$1/$l" ] && { echo "$l"; return; }; done; }
projects() {  # folder names that have a launcher (or the ones given, checked)
  local d
  if [ "$#" -gt 0 ]; then for d in "$@"; do d=${d%/}; [ -n "$(launcher_of "$d")" ] && echo "$d" || err "$d: no launcher (${LAUNCHERS[*]})" >&2; done
  else for d in "$ROOT"/*/; do d=$(basename "$d"); [ -n "$(launcher_of "$d")" ] && echo "$d"; done; fi
}
running() { [ -f "$STATE/$1.pid" ] && kill -0 "$(cat "$STATE/$1.pid")" 2>/dev/null; }

public_ip() {  # EC2 metadata (IMDSv2), then a public echo service; cached
  [ -s "$STATE/public-ip" ] && { cat "$STATE/public-ip"; return; }
  local t ip
  t=$(curl -fsS -m 2 -X PUT http://169.254.169.254/latest/api/token -H 'X-aws-ec2-metadata-token-ttl-seconds: 60' 2>/dev/null)
  ip=$(curl -fsS -m 2 -H "X-aws-ec2-metadata-token: $t" http://169.254.169.254/latest/meta-data/public-ipv4 2>/dev/null)
  [ -n "$ip" ] || ip=$(curl -fsS -m 5 https://checkip.amazonaws.com 2>/dev/null | tr -d '\n')
  [ -n "$ip" ] && echo "$ip" | tee "$STATE/public-ip"
}

urls_of() {  # the app's own addresses printed in its log, rewritten to the public IP
  local ip; ip=$(public_ip)
  [ -f "$STATE/$1.log" ] || return
  sed 's/\x1b\[[0-9;]*m//g' "$STATE/$1.log" \
    | grep -aoE 'https?://(localhost|127\.0\.0\.1|0\.0\.0\.0|172\.[0-9.]+|10\.[0-9.]+|'"${ip:-x}"')(:[0-9]+)?(/[^ )"'"'"'<>,]*)?' \
    | sed -E "s#//(localhost|127\.0\.0\.1|0\.0\.0\.0|172\.[0-9.]+|10\.[0-9.]+)#//${ip:-localhost}#" \
    | sed -E 's#[.:;]+$##' | awk '!seen[$0]++' | head -15
}

show_one() {  # show_one NAME URLS
  printf '  \033[32m●\033[0m \033[1m%s\033[0m\n' "$1"; echo "$2" | sed 's/^/      /'
}

show_urls() {
  local p u
  for p in "$@"; do
    u=$(urls_of "$p")
    if [ -n "$u" ]; then show_one "$p" "$u"
    else printf '  \033[90m○\033[0m \033[1m%s\033[0m  \033[90m(no address in its log yet — ./Start-all.sh logs %s)\033[0m\n' "$p" "$p"; fi
  done
}

wait_urls() {  # print each app's links as soon as it shows them; give up after START_ALL_WAIT seconds
  local limit=${START_ALL_WAIT:-900} poll=${START_ALL_POLL:-15} p u next pending=("$@")
  local end=$((SECONDS + limit))
  printf '\n\033[1mWaiting for the links of %d more app(s)\033[0m (up to %d min; Ctrl-C stops waiting, not the apps)\n' "${#pending[@]}" $((limit / 60))
  while [ "${#pending[@]}" -gt 0 ]; do
    next=()
    for p in "${pending[@]}"; do
      u=$(urls_of "$p")
      if [ -n "$u" ]; then show_one "$p" "$u"
      elif ! running "$p"; then
        printf '  \033[31m✘\033[0m \033[1m%s\033[0m  stopped without showing an address — last lines:\n' "$p"; tail -n 4 "$STATE/$p.log" | sed 's/^/      /'
      else next+=("$p"); fi
    done
    pending=("${next[@]+"${next[@]}"}")
    [ "${#pending[@]}" -gt 0 ] || break
    if [ "$SECONDS" -ge "$end" ]; then
      for p in "${pending[@]}"; do printf '  \033[33m○\033[0m \033[1m%s\033[0m  still starting — later: ./Start-all.sh urls %s\n' "$p" "$p"; done
      break
    fi
    sleep "$poll"
  done
  printf '\n  Each link needs its port open to your IP in the EC2 security group.\n'
}

start_one() {
  local p=$1 l; l=$(launcher_of "$p")
  if running "$p"; then warn "$p already running (pid $(cat "$STATE/$p.pid"))"; return; fi
  # The launcher records its own pid (= its session id after setsid), so stop can end everything it started.
  ( cd "$ROOT/$p" && nohup setsid bash -c 'echo $$ >"$1"; exec bash "./$2"' _ "$STATE/$p.pid" "$l" >"$STATE/$p.log" 2>&1 </dev/null & )
  sleep 3
  if running "$p" || ! grep -qiE 'error|fail|✘|denied|not found' "$STATE/$p.log"; then ok "$p  ($l)  log: .start-all/$p.log"
  else err "$p failed at once — last lines:"; tail -n 5 "$STATE/$p.log" | sed 's/^/      /'; fi
}

stop_one() {
  local p=$1 pid s used=""
  for s in stop.sh stop-demo.sh stop-localdemo.sh; do  # the project's own stop script first (stops its containers)
    if [ -f "$ROOT/$p/$s" ]; then (cd "$ROOT/$p" && bash "./$s" >>"$STATE/$p.log" 2>&1 </dev/null); used=$s; break; fi
  done
  if [ -f "$STATE/$p.pid" ]; then
    pid=$(cat "$STATE/$p.pid")
    pkill -TERM -s "$pid" 2>/dev/null; kill "$pid" 2>/dev/null   # its whole session (setsid), then the launcher itself
    for _ in 1 2 3 4 5 6 7 8 9 10; do pgrep -s "$pid" >/dev/null 2>&1 || break; sleep 1; done
    pkill -KILL -s "$pid" 2>/dev/null
    rm -f "$STATE/$p.pid"
  fi
  ok "$p stopped${used:+ (via $used)}"
}

case "${1:-start}" in
  list)
    for p in $(projects); do printf '  %-28s %s\n' "$p" "$(launcher_of "$p")"; done ;;
  urls)
    shift; mapfile -t list < <(projects "$@")
    printf '\033[1mApp URLs\033[0m (public IP %s)\n' "$(public_ip)"; show_urls "${list[@]}" ;;
  status)
    for p in $(projects); do
      if running "$p"; then state="\033[32mrunning\033[0m"; else state="\033[90mexited \033[0m"; fi
      printf "  %-28b %-28s %s\n" "$state" "$p" "$(tail -n 1 "$STATE/$p.log" 2>/dev/null | cut -c1-90)"
    done
    echo; echo "  Listening ports:"; ss -ltnH 2>/dev/null | awk '{print $4}' | sed 's/.*://' | sort -un | tr '\n' ' '; echo
    printf '  RAM free: %s · disk free: %s\n\n' "$(free -h | awk '/Mem:/ {print $7}')" "$(df -h "$ROOT" | awk 'NR==2 {print $4}')"
    mapfile -t list < <(projects); show_urls "${list[@]}" ;;
  logs)
    [ -f "$STATE/${2:-}.log" ] || { err "no log for '${2:-}' — names: $(projects | tr '\n' ' ')"; exit 1; }
    exec tail -n 50 -f "$STATE/$2.log" ;;
  stop)
    shift; for p in $(projects "$@"); do stop_one "$p"; done ;;
  start|*)
    [ "${1:-}" = start ] && shift
    rm -f "$STATE/public-ip"   # the public IP changes after an instance stop/start
    mapfile -t list < <(projects "$@")
    [ "${#list[@]}" -gt 0 ] || { err "no project with a launcher in $ROOT"; exit 1; }
    mem=$(awk '/MemTotal/ {printf "%.0f", $2/1048576}' /proc/meminfo)
    printf '\033[1mStarting %d project(s) from %s\033[0m  (%s GB RAM, public IP %s)\n' "${#list[@]}" "$ROOT" "$mem" "$(public_ip)"
    [ "${#list[@]}" -gt 2 ] && [ "$mem" -lt 16 ] && warn "${#list[@]} projects on ${mem} GB RAM will likely run out of memory — start a few: ./Start-all.sh start A B"
    later=()
    for i in "${!list[@]}"; do
      p=${list[$i]}; start_one "$p"
      # Use the gap before the next start to catch this app's links, and show them right away.
      u=""; for ((t = 0; t < GAP; t += 2)); do u=$(urls_of "$p"); [ -n "$u" ] && break; running "$p" || break; sleep 2; done
      if [ -n "$u" ]; then show_one "$p" "$u"; elif running "$p"; then later+=("$p"); fi  # a failed start was reported above
    done
    [ "${#later[@]}" -gt 0 ] && wait_urls "${later[@]}"
    echo; echo "  URLs: ./Start-all.sh urls   ·   status: ./Start-all.sh status   ·   one log: ./Start-all.sh logs NAME   ·   stop: ./Start-all.sh stop"
    echo "  Two projects on the same port cannot both run: check 'status' for errors like 'address already in use'." ;;
esac
