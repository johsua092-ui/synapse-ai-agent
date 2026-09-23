#!/usr/bin/env bash
# ============================================================
# Peer Link Setup Script
# Jalanin di VPS temen: curl -fsSL <url> | bash
# ============================================================
set -euo pipefail

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

log()  { echo -e "${BLUE}[*]${NC} $*"; }
ok()   { echo -e "${GREEN}[+]${NC} $*"; }
warn() { echo -e "${YELLOW}[!]${NC} $*"; }
die()  { echo -e "${RED}[x]${NC} $*"; exit 1; }

echo ""
echo "============================================"
echo "  Synapse Peer Link — Setup Otomatis"
echo "============================================"
echo ""

# ── 0. Root check ────────────────────────────────────────────
[[ $EUID -eq 0 ]] || die "Jalanin sebagai root: sudo bash $0"

# ── 1. Cek / Install dependencies ───────────────────────────
log "Cek dependencies..."
MISSING=()
for cmd in curl git python3 nginx; do
    command -v "$cmd" &>/dev/null || MISSING+=("$cmd")
done

if [[ ${#MISSING[@]} -gt 0 ]]; then
    log "Install: ${MISSING[*]}"
    apt-get update -qq
    apt-get install -y -qq "${MISSING[@]}" 2>/dev/null || \
        yum install -y -q "${MISSING[@]}" 2>/dev/null || \
        die "Gagal install deps: ${MISSING[*]}"
fi
ok "Dependencies OK"

# ── 2. Install Synapse ───────────────────────────────────────
if command -v synapse &>/dev/null; then
    ok "Synapse sudah terinstall: $(synapse --version 2>/dev/null | head -1)"
else
    log "Install Synapse..."
    curl -fsSL https://synapseagent.com/install.sh | bash
    # Reload PATH
    export PATH="$HOME/.local/bin:$HOME/.synapse/bin:$PATH"
    command -v synapse &>/dev/null || die "Install Synapse gagal. Install manual: https://synapseagent.com"
    ok "Synapse installed"
fi

# Pastiin synapse di PATH
export PATH="$HOME/.local/bin:$HOME/.synapse/bin:/usr/local/bin:$PATH"

# ── 3. Config Peer Link ──────────────────────────────────────
# Prioritas: argumen $1 > env PEERLINK_DOMAIN > auto-detect public IP > fallback
DETECTED_IP=$(curl -s4 --max-time 3 ifconfig.me 2>/dev/null || curl -s4 --max-time 3 icanhazip.com 2>/dev/null || curl -s4 --max-time 3 api.ipify.org 2>/dev/null || hostname -I 2>/dev/null | awk '{print $1}')
DOMAIN="${1:-${PEERLINK_DOMAIN:-$DETECTED_IP}}"
[[ -n "$DOMAIN" ]] || DOMAIN="95.111.199.131"
PEER_PORT=8443
DASHBOARD_PORT=7070

log "Set config Peer Link (target: $DOMAIN)..."
synapse config set peer_link.base_domain "$DOMAIN"
synapse config set peer_link.address_mode path
ok "Config set (base_domain: $DOMAIN)"

# ── 4. Bikin identity kalau belum ada ───────────────────────
log "Setup identity..."
synapse peerlink identity --json > /tmp/pl_identity.json 2>/dev/null || true
PEER_ID=$(python3 -c "import json; d=json.load(open('/tmp/pl_identity.json')); print(d.get('peer_id',''))" 2>/dev/null || echo "")
if [[ -z "$PEER_ID" ]]; then
    synapse peerlink identity > /dev/null 2>&1 || true
    PEER_ID=$(synapse peerlink identity --json 2>/dev/null | python3 -c "import sys,json; print(json.load(sys.stdin).get('peer_id','unknown'))" 2>/dev/null || echo "unknown")
fi
ok "Peer ID: $PEER_ID"

# ── 5. Set mode invite ───────────────────────────────────────
log "Set admission mode: invite..."
synapse peerlink mode invite > /dev/null 2>&1 || true
ok "Mode: invite"

# ── 6. Setup nginx untuk dashboard ──────────────────────────
log "Setup nginx proxy untuk dashboard..."
rm -f /etc/nginx/sites-enabled/default 2>/dev/null || true

NGINX_CONF="/etc/nginx/sites-available/peerlink-dashboard"
cat > "$NGINX_CONF" <<NGINX
server {
    listen 80 default_server;
    listen [::]:80 default_server;
    server_name _ $DOMAIN;

    # Auto-redirect root ke dashboard
    location = / {
        return 302 /dashboard;
    }

    # Dashboard web UI
    location /dashboard {
        proxy_pass http://127.0.0.1:$DASHBOARD_PORT;
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }

    # Peer Link handshake endpoint
    location /peer/ {
        proxy_pass http://127.0.0.1:$PEER_PORT;
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_read_timeout 60s;
    }

    # Healthcheck
    location /health {
        return 200 'ok';
        add_header Content-Type text/plain;
    }
}
NGINX

ln -sf "$NGINX_CONF" /etc/nginx/sites-enabled/peerlink-dashboard 2>/dev/null || true
nginx -t && systemctl reload nginx
ok "Nginx configured"

# ── 7. Bikin systemd service buat Peer Link ──────────────────
log "Bikin systemd service..."
SYNAPSE_BIN=$(command -v synapse)
cat > /etc/systemd/system/synapse-peerlink.service <<SERVICE
[Unit]
Description=Synapse Peer Link Server
After=network.target
Wants=network.target

[Service]
Type=simple
User=root
ExecStart=$SYNAPSE_BIN peerlink serve --host 0.0.0.0 --port $PEER_PORT --dashboard --dashboard-port $DASHBOARD_PORT
Restart=on-failure
RestartSec=5
Environment=PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:$HOME/.local/bin

[Install]
WantedBy=multi-user.target
SERVICE

systemctl daemon-reload
systemctl enable synapse-peerlink --now
sleep 2

if systemctl is-active --quiet synapse-peerlink; then
    ok "Peer Link service berjalan"
else
    warn "Service belum aktif, cek: journalctl -u synapse-peerlink -n 20"
fi

# ── 8. Generate invite link ──────────────────────────────────
log "Generate invite link (24 jam)..."
sleep 1

# Generate invite
INVITE_JSON=$(synapse peerlink invite --peer "temen" --json 2>/dev/null || echo '{}')
CODE=$(echo "$INVITE_JSON" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('code',''))" 2>/dev/null || echo "")
SHARE_LINK=$(echo "$INVITE_JSON" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('share_link',''))" 2>/dev/null || echo "")

# Build link manual kalau share_link kosong atau fix scheme jika IP
if [[ -z "$SHARE_LINK" && -n "$CODE" ]]; then
    LABEL=$(synapse peerlink endpoint --json 2>/dev/null | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('address','').split('/')[-1] if d.get('address') else '')" 2>/dev/null || echo "")
    SHARE_LINK="http://$DOMAIN/peer/$LABEL#c=$CODE"
fi
if [[ "$DOMAIN" =~ ^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$ && "$SHARE_LINK" =~ ^https:// ]]; then
    SHARE_LINK="${SHARE_LINK/https:\/\//http:\/\/}"
fi

# ── 9. Summary ───────────────────────────────────────────────
echo ""
echo "============================================"
echo -e "  ${GREEN}SETUP SELESAI${NC}"
echo "============================================"
echo ""
echo -e "  Dashboard  : ${BLUE}http://$DOMAIN/dashboard${NC}"
echo -e "  Peer ID    : ${YELLOW}$PEER_ID${NC}"
echo ""
if [[ -n "$SHARE_LINK" ]]; then
    echo -e "  ${GREEN}Invite Link (kirim ke temen via WA/Telegram):${NC}"
    echo ""
    echo -e "  ${YELLOW}$SHARE_LINK${NC}"
    echo ""
else
    echo -e "  Generate invite manual:"
    echo -e "  ${YELLOW}synapse peerlink invite --peer temen --qr${NC}"
    echo ""
fi
echo "  Temen jalanin:"
echo "    synapse peerlink connect \"$SHARE_LINK\""
echo ""
echo "  Approve temen:"
echo "    synapse peerlink pending"
echo "    synapse peerlink approve pl1_..."
echo ""
echo "  Atau approve lewat dashboard:"
echo "    http://$DOMAIN/dashboard"
echo ""
echo "  Cek status service:"
echo "    systemctl status synapse-peerlink"
echo "    journalctl -u synapse-peerlink -f"
echo ""
echo "============================================"
echo ""
if [[ "$DOMAIN" =~ ^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
    ok "Dashboard aktif di IP: http://$DOMAIN/dashboard (atau http://$DOMAIN)"
else
    warn "Pastiin DNS A record $DOMAIN sudah diarahkan ke IP VPS ini"
    IP=$(curl -s --max-time 3 ifconfig.me 2>/dev/null || echo "?")
    warn "IP VPS ini: $IP"
fi
echo ""
