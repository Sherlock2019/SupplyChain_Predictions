#!/usr/bin/env bash
# Check the launcher's requirements and install what is missing (Linux: Ubuntu/Debian with apt, Amazon Linux/RHEL with dnf).
#
#   scripts/ensure-prereqs.sh [--no-llm] [--lite]
#
# Installs: curl, python3, git, Docker Engine + compose v2 plugin, Ollama (skipped with --no-llm). Starts Docker, enables it on
# boot and adds you to the docker group. Runs in the foreground before the launcher detaches, because installing needs sudo.
# Exit 0: ready. Exit 3: ready, but this shell is not yet in the docker group (the launcher re-runs itself with `sg docker`).
set -euo pipefail

NOLLM=0; LITE=0
for arg in "$@"; do
  case "$arg" in --no-llm) NOLLM=1 ;; --lite) LITE=1 ;; esac
done

ok() { printf '  \033[32m✔\033[0m %s\n' "$*"; }
info() { printf '  \033[36m→\033[0m %s\n' "$*"; }
warn() { printf '  \033[33m!\033[0m %s\n' "$*"; }
die() { printf '  \033[31m✘ %s\033[0m\n' "$*"; exit 1; }
have() { command -v "$1" >/dev/null 2>&1; }

printf '\n\033[1m▶ Requirements\033[0m\n'
[ "$(uname -s)" = Linux ] || {
  have docker && docker info >/dev/null 2>&1 && { ok "Docker"; exit 0; }
  die "automatic install is for Linux only — install Docker Desktop, start it, then re-run"
}

SUDO=""
if [ "$(id -u)" != 0 ]; then
  have sudo || die "sudo is required to install missing packages"
  SUDO=sudo
fi

PM=""
if have apt-get; then PM=apt; elif have dnf; then PM=dnf; elif have yum; then PM=yum; fi
APT_UPDATED=0
pkg_install() {  # pkg_install PACKAGE...
  case "$PM" in
    apt) [ "$APT_UPDATED" = 1 ] || { $SUDO apt-get update -qq; APT_UPDATED=1; }
         $SUDO env DEBIAN_FRONTEND=noninteractive apt-get install -y -qq "$@" >/dev/null ;;
    dnf|yum) $SUDO "$PM" install -y -q "$@" >/dev/null ;;
    *) die "no supported package manager (apt/dnf/yum) — install $* yourself" ;;
  esac
}

# Basic tools
for tool in curl python3 git; do
  if have "$tool"; then ok "$tool"; else info "installing $tool"; pkg_install "$tool"; ok "$tool installed"; fi
done
if [ "$PM" = apt ] && ! python3 -c 'import venv' 2>/dev/null; then pkg_install python3-venv; fi

# Docker Engine
if have docker; then
  ok "Docker $(docker --version 2>/dev/null | awk '{print $3}' | tr -d ,)"
else
  info "installing Docker Engine (2-3 min)"
  if [ "$PM" = apt ]; then
    curl -fsSL https://get.docker.com | $SUDO sh >/dev/null
  else  # Amazon Linux 2023 / RHEL family: get.docker.com does not support Amazon Linux
    pkg_install docker
  fi
  have docker || die "Docker install failed — see https://docs.docker.com/engine/install/"
  ok "Docker installed"
fi

# docker compose v2 plugin
if docker compose version >/dev/null 2>&1 || $SUDO docker compose version >/dev/null 2>&1; then
  ok "docker compose"
else
  info "installing the docker compose plugin"
  if [ "$PM" = apt ] && pkg_install docker-compose-plugin 2>/dev/null; then :; else
    case "$(uname -m)" in aarch64|arm64) arch=aarch64 ;; *) arch=x86_64 ;; esac
    $SUDO mkdir -p /usr/local/lib/docker/cli-plugins
    $SUDO curl -fsSL "https://github.com/docker/compose/releases/download/v2.29.7/docker-compose-linux-${arch}" -o /usr/local/lib/docker/cli-plugins/docker-compose
    $SUDO chmod +x /usr/local/lib/docker/cli-plugins/docker-compose
  fi
  $SUDO docker compose version >/dev/null 2>&1 || die "docker compose plugin install failed"
  ok "docker compose installed"
fi

# Daemon running and started on boot
if have systemctl && systemctl list-unit-files docker.service >/dev/null 2>&1; then
  if systemctl is-active --quiet docker && systemctl is-enabled --quiet docker; then ok "Docker running (starts on boot)"
  elif $SUDO systemctl enable --now docker >/dev/null 2>&1; then ok "Docker started (starts on boot)"
  else warn "could not start Docker with systemctl"; fi
fi

# Ollama (local Qwen); skipped with --no-llm
if [ "$NOLLM" = 1 ]; then
  ok "Ollama not needed (--no-llm)"
elif have ollama; then
  ok "Ollama"
else
  info "installing Ollama (local LLM runtime, 1-2 min)"
  if curl -fsSL https://ollama.com/install.sh | sh >/dev/null 2>&1 && have ollama; then ok "Ollama installed"
  else warn "Ollama install failed — the demo starts without an LLM (deterministic fallback)"; fi
fi
if have ollama && ! curl -fs -m 3 http://127.0.0.1:11434/api/tags >/dev/null; then
  { have systemctl && $SUDO -n systemctl enable --now ollama >/dev/null 2>&1; } || (nohup ollama serve >/dev/null 2>&1 &)
  for _ in $(seq 1 15); do curl -fs -m 2 http://127.0.0.1:11434/api/tags >/dev/null && break; sleep 1; done
  curl -fs -m 2 http://127.0.0.1:11434/api/tags >/dev/null && ok "Ollama running" || warn "Ollama is not answering on :11434"
fi

# Resources
mem=$(awk '/MemTotal/ {printf "%.0f", $2/1048576}' /proc/meminfo)  # rounded: a 4 GB instance reports ~3.8
disk=$(df -Pk . | awk 'NR==2 {printf "%d", $4/1048576}')
cpus=$(nproc)
# Swap on small machines: the image build and the model load peak above the steady state.
swap=$(awk '/SwapTotal/ {printf "%d", $2/1048576}' /proc/meminfo)
if [ "$mem" -lt 15 ] && [ "$swap" -lt 2 ] && [ "$disk" -ge 30 ]; then
  info "adding 8 GB of swap (${mem} GB RAM)"
  { $SUDO fallocate -l 8G /swapfile || $SUDO dd if=/dev/zero of=/swapfile bs=1M count=8192 status=none; } \
    && $SUDO chmod 600 /swapfile && $SUDO mkswap /swapfile >/dev/null && $SUDO swapon /swapfile \
    && { grep -q '^/swapfile' /etc/fstab || echo '/swapfile none swap sw 0 0' | $SUDO tee -a /etc/fstab >/dev/null; } \
    && ok "8 GB swap on (kept after reboot)" || warn "could not add swap"
  disk=$(df -Pk . | awk 'NR==2 {printf "%d", $4/1048576}')
fi
# Too small to ever finish: stop here instead of failing 15 minutes into the build (SKIP_RESOURCE_CHECK=1 to try anyway).
need=7; [ "$LITE" = 1 ] && need=4   # measured: core stack ~1.8 GB, observability ~3 GB more, Qwen 3B ~2.5 GB more
if [ "${SKIP_RESOURCE_CHECK:-0}" != 1 ]; then
  [ "$disk" -ge 15 ] || die "only ${disk} GB free disk — the images alone need about 15 GB (30 GB with the LLM). Enlarge the EBS volume to 40 GB+"
  [ "$mem" -ge "$need" ] || die "only ${mem} GB RAM — needs ${need} GB with these options. On 4 GB use --lite --no-llm; 16 GB (t3.xlarge) runs everything"
fi
if [ "$mem" -ge 15 ]; then ok "${mem} GB RAM, ${cpus} CPUs"
elif [ "$NOLLM" = 0 ]; then warn "${mem} GB RAM: the LLM will be slow and may swap — --no-llm is safer, 16 GB recommended for Qwen"
else ok "${mem} GB RAM, ${cpus} CPUs (enough without the LLM)"; fi
[ "$disk" -ge 30 ] && ok "${disk} GB free disk" || warn "only ${disk} GB free disk: images + model need about 30 GB"

# Docker access for this user
if docker info >/dev/null 2>&1; then ok "Docker access"; exit 0; fi
[ "$(id -u)" = 0 ] && die "the Docker daemon is not answering"
id -nG "$USER" | tr ' ' '\n' | grep -qx docker || { $SUDO usermod -aG docker "$USER"; ok "added $USER to the docker group"; }
$SUDO docker info >/dev/null 2>&1 || die "the Docker daemon is not answering (sudo systemctl status docker)"
exit 3  # in the group, but this login session predates it
