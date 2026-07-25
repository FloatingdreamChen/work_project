#!/usr/bin/env bash
set -euo pipefail

echo "== Port listeners =="
frontend_listener="$(lsof -nP -iTCP:3000 -sTCP:LISTEN || true)"
if [ -n "$frontend_listener" ]; then
  echo "$frontend_listener"
  if echo "$frontend_listener" | grep -q "TCP [0-9].*:3000 (LISTEN)"; then
    echo "note: frontend is bound to a single LAN IP. Restart with npm run dev:lan to support both localhost and LAN."
  fi
else
  echo "frontend port 3000 is not listening"
fi
lsof -nP -iTCP:8000 -sTCP:LISTEN || echo "backend port 8000 is not listening"

echo
echo "== Active IPv4 addresses =="
ifconfig | awk '
  /^[a-zA-Z0-9]+:/ { iface=$1; sub(":", "", iface); status="" }
  /status: / { status=$2 }
  /inet / && $2 != "127.0.0.1" {
    note="candidate"
    if (iface ~ /^utun/ || iface ~ /^ppp/) note="VPN/PPP, usually not for browser LAN access"
    if (iface ~ /^bridge/) note="bridge/shared network, only usable from devices on that subnet"
    print iface, $2, note
  }
'

echo
echo "== Suggested URLs =="
echo "Local:   http://localhost:3000"
ifconfig | awk '
  /^[a-zA-Z0-9]+:/ { iface=$1; sub(":", "", iface) }
  /inet / && $2 ~ /^192\.168\./ && iface !~ /^bridge/ {
    print "LAN:     http://" $2 ":3000"
  }
'

echo
echo "If Local works but LAN does not:"
echo "1. Restart frontend with the LAN helper: cd frontend && npm run dev:lan"
echo "2. Use the LAN URL above, not VPN/PPP or bridge URLs."
echo "3. Make sure the other device is on the same subnet and macOS firewall allows node/npm incoming connections."
