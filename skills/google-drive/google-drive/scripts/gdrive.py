#!/usr/bin/env python3
"""Google Drive CLI helper — REST API (v3) via OAuth, requests-only.

No google-api-python-client required. Uses `requests` (core dep) + stdlib.

Quick start:
    python3 gdrive.py setup
    python3 gdrive.py list
    python3 gdrive.py upload README.md
    python3 gdrive.py download FILE_ID
"""

import json
import os
import sys
import webbrowser
from urllib.parse import quote

try:
    import requests
except ImportError:
    sys.exit("Missing dependency: requests. Install with `pip install requests`.")

TOKEN_URI = "https://oauth2.googleapis.com/token"
DRIVE_BASE = "https://www.googleapis.com/drive/v3"
DRIVE_UPLOAD = "https://www.googleapis.com/upload/drive/v3/files"
SCOPES = ["https://www.googleapis.com/auth/drive"]
REDIRECT_URI = "http://localhost:8080/"


def _here(path):
    # Resolve relative to this script's directory so it works from any CWD.
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), path)


def _load_credentials():
    p = _here("credentials.json")
    if not os.path.exists(p):
        sys.exit(
            "credentials.json not found next to this script.\n"
            "Create a Desktop OAuth client in Google Cloud Console, download the JSON, "
            "and save it here. See SKILL.md for steps."
        )
    with open(p, "r") as f:
        data = json.load(f)
    inst = data.get("installed") or data.get("web")
    if not inst:
        sys.exit("credentials.json has no 'installed'/'web' block.")
    return inst


def _load_token():
    p = _here("token.json")
    if not os.path.exists(p):
        return None
    with open(p, "r") as f:
        return json.load(f)


def _save_token(token):
    with open(_here("token.json"), "w") as f:
        json.dump(token, f, indent=2)
    os.chmod(_here("token.json"), 0o600)


def _header():
    token = _access_token()
    return {"Authorization": "Bearer " + token, "Content-Type": "application/json"}


def _access_token():
    tok = _load_token()
    if not tok:
        sys.exit("Not authenticated. Run `python3 gdrive.py setup` first.")
    # Refresh if expired/near-expiry
    import time
    if "expires_at" in tok and time.time() > tok["expires_at"] - 60:
        tok = _refresh(tok)
    return tok["access_token"]


def _refresh(tok):
    creds = _load_credentials()
    r = requests.post(TOKEN_URI, data={
        "client_id": creds["client_id"],
        "client_secret": creds["client_secret"],
        "refresh_token": tok.get("refresh_token"),
        "grant_type": "refresh_token",
    })
    r.raise_for_status()
    new = r.json()
    new["refresh_token"] = tok.get("refresh_token")
    import time
    new["expires_at"] = time.time() + new.get("expires_in", 3600)
    _save_token(new)
    return new


def setup():
    creds = _load_credentials()
    client_id = creds["client_id"]
    params = "&".join([
        "client_id=" + client_id,
        "redirect_uri=" + quote(REDIRECT_URI, safe=""),
        "response_type=code",
        "scope=" + quote(" ".join(SCOPES), safe=""),
        "access_type=offline",
        "prompt=consent",
    ])
    url = "https://accounts.google.com/o/oauth2/v2/auth?" + params
    print("Opening browser for Google consent. If it doesn't open, visit:\n")
    print(url + "\n")
    webbrowser.open(url)
    code = input("Paste the authorization code from the redirect URL (?code=...): ").strip()
    if not code:
        sys.exit("No code provided.")
    r = requests.post(TOKEN_URI, data={
        "code": code,
        "client_id": creds["client_id"],
        "client_secret": creds["client_secret"],
        "redirect_uri": REDIRECT_URI,
        "grant_type": "authorization_code",
    })
    r.raise_for_status()
    tok = r.json()
    import time
    tok["expires_at"] = time.time() + tok.get("expires_in", 3600)
    _save_token(tok)
    print("Saved token.json. Authenticated.")


def _paginate_files(query=None, page_size=25):
    params = {
        "pageSize": page_size,
        "fields": "nextPageToken,files(id,name,mimeType,size,modifiedTime,parents,webViewLink)",
        "orderBy": "modifiedTime desc",
    }
    if query:
        params["q"] = query
    r = requests.get(DRIVE_BASE + "/files", headers=_header(), params=params)
    r.raise_for_status()
    return r.json().get("files", [])


def cmd_list():
    maxn = int(sys.argv[2]) if len(sys.argv) > 2 else 25
    files = _paginate_files(page_size=min(maxn, 100))
    for f in files:
        name = f.get("name", "(unnamed)")
        fid = f.get("id", "")
        mime = f.get("mimeType", "")
        print(f"{'[DIR] ' if 'folder' in mime else ''}{name}  ->  {fid}")


def cmd_search():
    q = sys.argv[2] if len(sys.argv) > 2 else ""
    files = _paginate_files(query="name contains '%s'" % q.replace("'", "\\'"))
    for f in files:
        print(f"{f.get('name')}  ->  {f.get('id')}")


def cmd_upload():
    if len(sys.argv) < 3:
        sys.exit("Usage: gdrive.py upload <local_path> [parent_id]")
    local = sys.argv[2]
    if not os.path.exists(local):
        sys.exit("File not found: " + local)
    meta = {"name": os.path.basename(local)}
    if len(sys.argv) > 3:
        meta["parents"] = [sys.argv[3]]
    files = {"metadata": ("m", json.dumps(meta), "application/json"),
             "media": (os.path.basename(local), open(local, "rb"))}
    r = requests.post(
        DRIVE_UPLOAD + "?uploadType=multipart",
        headers={"Authorization": "Bearer " + _access_token()},
        files=files,
    )
    r.raise_for_status()
    d = r.json()
    print(f"Uploaded: {d.get('name')}  ->  {d.get('id')}")
    print(f"Link: {d.get('webViewLink')}")


def cmd_download():
    if len(sys.argv) < 3:
        sys.exit("Usage: gdrive.py download <file_id> [output_path]")
    fid = sys.argv[2]
    out = sys.argv[3] if len(sys.argv) > 3 else None
    if out is None:
        meta = requests.get(DRIVE_BASE + "/files/" + fid + "?fields=name", headers=_header()).json()
        out = meta.get("name", "downloaded")
    r = requests.get(DRIVE_BASE + "/files/" + fid + "?alt=media", headers=_header())
    r.raise_for_status()
    with open(out, "wb") as f:
        f.write(r.content)
    print("Downloaded to " + out)


def cmd_mkdir():
    if len(sys.argv) < 3:
        sys.exit("Usage: gdrive.py mkdir <name> [parent_id]")
    meta = {"name": sys.argv[2], "mimeType": "application/vnd.google-apps.folder"}
    if len(sys.argv) > 3:
        meta["parents"] = [sys.argv[3]]
    r = requests.post(DRIVE_BASE + "/files", headers=_header(), data=json.dumps(meta))
    r.raise_for_status()
    d = r.json()
    print(f"Created folder: {d.get('name')}  ->  {d.get('id')}")


def cmd_delete():
    if len(sys.argv) < 3:
        sys.exit("Usage: gdrive.py delete <file_id>")
    fid = sys.argv[2]
    r = requests.delete(DRIVE_BASE + "/files/" + fid, headers=_header())
    r.raise_for_status()
    print("Deleted " + fid)


def cmd_status():
    tok = _load_token()
    if not tok:
        print("Not authenticated. Run `setup`.")
        return
    import time
    ok = time.time() < tok.get("expires_at", 0) - 60 or tok.get("refresh_token")
    print("Authenticated" if ok else "Token expired (will auto-refresh)")


def cmd_me():
    r = requests.get(DRIVE_BASE + "/about?fields=user", headers=_header())
    r.raise_for_status()
    user = r.json().get("user", {})
    print(json.dumps(user, indent=2))


COMMANDS = {
    "setup": setup,
    "list": cmd_list,
    "search": cmd_search,
    "upload": cmd_upload,
    "download": cmd_download,
    "mkdir": cmd_mkdir,
    "delete": cmd_delete,
    "status": cmd_status,
    "me": cmd_me,
}


def main():
    if len(sys.argv) < 2 or sys.argv[1] not in COMMANDS:
        print("Usage: python3 gdrive.py {" + "|".join(COMMANDS) + "}")
        sys.exit(1)
    COMMANDS[sys.argv[1]]()


if __name__ == "__main__":
    main()
