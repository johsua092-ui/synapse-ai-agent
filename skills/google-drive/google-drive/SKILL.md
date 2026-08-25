---
name: google-drive
description: "Google Drive access (OAuth) setup and operations: list, search, upload, download, folders, and sharing via the Drive REST API (requests-only, no heavy Google SDK)."
version: 1.0.0
author: Josh Research
license: MIT
platforms: [linux, macos, windows]
metadata:
  synapse:
    tags: [Google Drive, OAuth, Google API, Cloud Storage, Files]
    related_skills: []
---

# Google Drive

This skill lets the agent read and write to the user's Google Drive using the official Drive REST API (v3). It uses only the Python standard library plus `requests` (already a core dependency) — no heavy `google-api-python-client` install needed.

## Setup Flow (Agent-Guided)

The agent guides the user through the setup once. The credential files stay on the user's machine and (if configured) in `.gitignore` — they are never committed to the repo.

The wizard script is `scripts/gdrive.py`. Run it interactively:

```bash
python3 skills/google-drive/google-drive/scripts/gdrive.py setup
```

It takes the user through these steps:

1. Open the Google Cloud Console and create / pick a project:
   https://console.cloud.google.com
2. Enable the Drive API:
   APIs & Services → Library → search "Google Drive API" → Enable
3. Configure the OAuth consent screen:
   OAuth consent screen → External → add the user's email as a test user
4. Create desktop credentials:
   Credentials → Create Credentials → OAuth client ID → Desktop app → Download JSON
5. Save the downloaded JSON as `credentials.json` in the current directory
6. The script opens a browser to Google consent; accept to finish. The token is cached locally in `token.json`.

The same credentials work on any machine (Windows, Termux, VPS, Railway) — just copy `credentials.json` in and run `setup` again (or copy `token.json` over).

## Operations

Every operation rides through the CLI (`scripts/gdrive.py`):

```bash
python3 scripts/gdrive.py list [max]            # list files (default 25)
python3 scripts/gdrive.py list 50               # list 50 files
python3 scripts/gdrive.py search "annual report" # full-text search
python3 scripts/gdrive.py upload local.pdf [parent_id] [export_mime]
python3 scripts/gdrive.py download FILE_ID [output_path]
python3 scripts/gdrive.py mkdir FOLDER_NAME [parent_id]
python3 scripts/gdrive.py delete FILE_ID
python3 scripts/gdrive.py status                # show current auth status
python3 scripts/gdrive.py me                    # who am I (user info)
```

The agent should use the full repo-relative or absolute path to `scripts/gdrive.py`, since the agent may run from any directory.

## Scopes

The script requests the `https://www.googleapis.com/auth/drive` scope (full read/write) so the user can ask the agent to do anything with their Drive.

## Requirements

- `requests` installed (`pip install requests`), already a core dependency of this repo.
- No credential files committed to the repo.

---

To set up quickly on a new machine, just copy `credentials.json` (and the cached `token.json` if present) into your project directory, then run:

```bash
python3 scripts/gdrive.py setup
```
