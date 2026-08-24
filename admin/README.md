# Synapse Agent — Admin Server & Setup Wizard

A self-contained admin server + web setup wizard for **Synapse Agent**, ported
from the upstream admin-server template and fully rebranded to Synapse.

It provides:

- **Setup wizard / admin UI** at `/setup` (Starlette + Jinja, cookie-auth guarded)
- **Management API** at `/setup/api/*` — config, status, logs, gateway, pairing
- **Reverse proxy** at `/` and `/*` → the native Synapse dashboard
  (`synapse_cli/web_server`, on `127.0.0.1:9119`)
- **Managed subprocesses**: `synapse gateway` (agent) and `synapse dashboard`
  (native UI)
- **Cookie-based session auth** at `/login` (HMAC-signed, 7-day expiry, httponly)

## Layout

```
admin/
  server.py               # Starlette admin server + reverse proxy
  templates/index.html    # Setup wizard UI (Alpine.js, no build step)
  start.sh                # Seed data dirs & launch the server
  requirements.txt        # Python deps (starlette, uvicorn, jinja2, httpx, websockets)
```

## Requirements

- A Synapse install with the `synapse` CLI on `PATH` (`synapse gateway`,
  `synapse dashboard`, `synapse import`, `synapse update`, …).
- The native Synapse dashboard running on `127.0.0.1:9119` (default port).
- Python 3.12+.

## Run locally

```bash
cd admin
pip install -r requirements.txt
# Optionally set SYNAPSE_HOME (defaults to ~/.synapse)
export SYNAPSE_HOME="$HOME/.synapse"
uvicorn server:app --host 0.0.0.0 --port 8000
```

> The native dashboard is reverse-proxied from `SYNAPSE_DASHBOARD_URL`
> (default `http://127.0.0.1:9119`).

## Environment

| Variable | Purpose | Default |
|---|---|---|
| `SYNAPSE_HOME` | Synapse data directory | `~/.synapse` |
| `SYNAPSE_REF` | Pinned Synapse release (shown in the UI badge) | *(empty)* |
| `SYNAPSE_DASHBOARD_HOST` / `PORT` | Native dashboard bind | `127.0.0.1` / `9119` |
| `SYNAPSE_DASHBOARD_PUBLIC_URL` | External URL the dashboard reports for OAuth | *(empty)* |

## Notes

- Provider keys are written to `$SYNAPSE_HOME/.env` and `config.yaml`, matching
  the native Synapse CLI conventions.
- An emergency-stop sentinel (`$SYNAPSE_HOME/ESTOP`) pauses the agent while
  keeping `/health` green; the wizard surfaces this state in the header.
