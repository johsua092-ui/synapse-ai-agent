#!/bin/bash
set -e

# Mirror dashboard-ref-only's startup: create every directory synapse expects
# and seed a default config.yaml if the volume is empty. Without these,
# `synapse dashboard` endpoints that hit logs/, sessions/, cron/, etc. can fail
# with opaque errors even though no auth is actually involved.
# NOTE (synapse >= v2026.7.1): several dirs were consolidated and are now
# resolved via get_synapse_dir("<new>", "<old>"), which returns the NEW path
# unless the OLD one already has *content*. Seeding an empty legacy stub no
# longer "claims" it — synapse ignores empty stubs and writes to the new path
# (upstream #27602). So we seed the NEW paths: pairing -> platforms/pairing,
# image_cache -> cache/images, audio_cache -> cache/audio. A populated legacy
# dir from a pre-v2026.7.1 deploy still wins on both sides, so no migration is
# needed. server.py:_resolve_pairing_dir() mirrors this same rule for the
# admin panel's Users tab — keep the two in sync on future bumps.
mkdir -p /data/.synapse/cron /data/.synapse/sessions /data/.synapse/logs \
         /data/.synapse/memories /data/.synapse/skills /data/.synapse/platforms/pairing \
         /data/.synapse/hooks /data/.synapse/cache/images /data/.synapse/cache/audio \
         /data/.synapse/workspace /data/.synapse/skins /data/.synapse/plans \
         /data/.synapse/home

# Stamp the install method as "docker" so synapse treats this as an immutable
# container image, not a pip checkout. synapse's detect_install_method() reads
# $SYNAPSE_HOME/.install_method FIRST (before any .git / pip fallback). Without
# this stamp the template falls through to "pip" — because the Dockerfile strips
# /opt/synapse-agent/.git — and the dashboard's "Update Synapse" button then runs
# a real `synapse update` (PyPI pip-upgrade) INSIDE the running container. That
# upgrade is ephemeral (reverts on the next redeploy) and can desync the Python
# package from the image's pre-built web_dist/ui-tui bundles. Stamping "docker"
# makes that button correctly refuse with "pull a fresh image / redeploy", which
# matches the real upgrade path here (bump SYNAPSE_REF in Railway + redeploy).
# Written unconditionally each boot so it stays correct and self-heals.
printf 'docker\n' > /data/.synapse/.install_method

if [ ! -f /data/.synapse/config.yaml ] && [ -f /opt/synapse-agent/cli-config.yaml.example ]; then
  cp /opt/synapse-agent/cli-config.yaml.example /data/.synapse/config.yaml
fi

[ ! -f /data/.synapse/.env ] && touch /data/.synapse/.env

# Bootstrap OAuth tokens from env var (e.g. xAI Grok SuperGrok).
# Set SYNAPSE_AUTH_JSON_BOOTSTRAP to the contents of a locally-generated
# ~/.synapse/auth.json. Written only once — subsequent token refreshes update
# the file in place on the persistent volume.
if [ ! -f /data/.synapse/auth.json ] && [ -n "${SYNAPSE_AUTH_JSON_BOOTSTRAP}" ]; then
  printf '%s' "${SYNAPSE_AUTH_JSON_BOOTSTRAP}" > /data/.synapse/auth.json
  chmod 600 /data/.synapse/auth.json
fi

# Clear any stale gateway PID file left over from the previous container.
# `synapse gateway` writes /data/.synapse/gateway.pid on start but does not
# remove it on SIGTERM. Since /data is a persistent volume, the file
# survives container restarts and causes every subsequent boot to exit with
# "ERROR gateway.run: PID file race lost to another gateway instance".
# No synapse process can be running at this point (we're pre-exec in a fresh
# container), so removing the file unconditionally is safe.
rm -f /data/.synapse/gateway.pid

# Tell the dashboard its externally reachable URL.
# synapse >= v2026.7.20 builds the MCP OAuth redirect_uri from the request's own
# Host header. Our reverse proxy must strip that Host (synapse 400s anything but
# loopback on a loopback bind), so synapse would otherwise hand the OAuth
# provider `http://127.0.0.1:9119/...` — a URL only reachable inside this
# container, leaving the browser on a dead tab after consent with nothing in the
# logs. resolve_public_url() checks SYNAPSE_DASHBOARD_PUBLIC_URL first, so
# setting it is the supported fix. Railway injects RAILWAY_PUBLIC_DOMAIN; `:=`
# keeps an operator-set value (e.g. a custom domain) winning.
if [ -n "${RAILWAY_PUBLIC_DOMAIN:-}" ]; then
  : "${SYNAPSE_DASHBOARD_PUBLIC_URL:=https://${RAILWAY_PUBLIC_DOMAIN}}"
  export SYNAPSE_DASHBOARD_PUBLIC_URL
fi

exec python /app/server.py
