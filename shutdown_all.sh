#!/bin/bash
# Shutdown AegisSOC processes
# Usage: ./shutdown_all.sh [-d|--docker] [--full]
source "$(dirname "$0")/scripts/lib.sh"

DOCKER_STOP=0; FULL=0
for arg in "$@"; do
    case "$arg" in
        -d|--docker) DOCKER_STOP=1 ;;
        --full) FULL=1 ;;
        *) echo "Usage: $0 [-d|--docker] [--full]"; exit 1 ;;
    esac
done

echo "Stopping AegisSOC..."

# Kill by PID files
for pidfile in logs/backend.pid logs/daemon.pid logs/frontend.pid logs/llm_worker.pid \
               logs/agent-worker.pid logs/agent-serve.pid; do
    [ -f "$pidfile" ] && kill "$(cat "$pidfile")" 2>/dev/null && rm -f "$pidfile"
done

# Kill by process pattern.
# Deliberately no `pkill -f ollama`: the running Ollama is often the user's own
# (brew services / Ollama.app), so killing it destroys unrelated state and
# launchd just restarts it. AegisSOC starts Ollama but never stops it.
pkill -f "uvicorn services.api.main:app" 2>/dev/null || true
pkill -f "services/daemon/main.py" 2>/dev/null || true
pkill -f "services.daemon.main" 2>/dev/null || true
pkill -f 'services\.worker' 2>/dev/null || true
pkill -f "vite.*opensoc" 2>/dev/null || true
pkill -f "mcp_servers.*_server" 2>/dev/null || true

# Kill by port — 7787/7788 (AegisSOC AI) and 6987/6988 (legacy)
lsof -ti:7787 | xargs kill -9 2>/dev/null || true
lsof -ti:7788 | xargs kill -9 2>/dev/null || true
lsof -ti:6987 | xargs kill -9 2>/dev/null || true
lsof -ti:6988 | xargs kill -9 2>/dev/null || true

# Docker
if [ "$DOCKER_STOP" -eq 1 ]; then
    if command -v docker &>/dev/null; then
        if [ "$FULL" -eq 1 ]; then
            dc down -v || true
        else
            dc stop || true
        fi
    else
        echo "Docker not found; skipping container shutdown."
    fi
fi

# Status
echo ""
echo "Port 7787 (Backend):  $(lsof -ti:7787 2>/dev/null | wc -l | xargs) process(es)"
echo "Port 7788 (Frontend): $(lsof -ti:7788 2>/dev/null | wc -l | xargs) process(es)"
echo ""
[ "$DOCKER_STOP" -eq 0 ] && echo "Docker left running. Use -d to stop containers."
echo "Done."
