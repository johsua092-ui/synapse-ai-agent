"""Worker RESTORE Synapse — dijalankan TERPISAH (detached) oleh ``POST /v1/restore``.

Kenapa harus proses terpisah?
-----------------------------
Restore WAJIB menghentikan gateway lebih dulu (jebakan #81: restore saat
Synapse HIDUP merusak ``state.db`` karena WAL masih dipegang proses hidup).
Kalau gateway berhenti, proses ``api_server`` yang melayani request ikut mati
-> respons HTTP tidak akan pernah sampai ke klien.

Maka seluruh urutan restore dikerjakan oleh proses INI yang berdiri sendiri
(detached), dan hasilnya ditulis ke file status JSON. Klien (app mobile)
membaca status itu lewat ``GET /v1/restore/status`` setelah gateway hidup lagi.

Urutan WAJIB (jangan dibalik):
    1. backup pengaman  -> ~/backup/sebelum-restore-<stamp>.zip
    2. gateway stop
    3. synapse import <zip>
    4. gateway start

Pemakaian:
    python -m synapse_cli.restore_worker <zip_path> <status_json_path>
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path

#: Timeout per langkah (detik).
_T_BACKUP = 1800
_T_STOP = 120
_T_IMPORT = 1800
_T_START = 180


def _tulis_status(path: Path, data: dict) -> None:
    """Tulis status secara atomik supaya klien tidak membaca file separuh."""
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(path.suffix + ".tmp")
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        os.replace(tmp, path)
    except OSError:
        pass


def _jalankan(args: list[str], timeout: int) -> tuple[int, str]:
    """Jalankan perintah NATIVE `synapse <args>` dan kembalikan (exit, output)."""
    cmd = [sys.executable, "-m", "synapse_cli.main", *args]
    try:
        p = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
        )
        return p.returncode, (p.stdout or "") + (p.stderr or "")
    except subprocess.TimeoutExpired as exc:
        keluar = exc.stdout or ""
        if isinstance(keluar, bytes):
            keluar = keluar.decode("utf-8", "replace")
        return 124, f"TIMEOUT setelah {timeout}s\n{keluar}"
    except Exception as exc:  # noqa: BLE001
        return 1, f"gagal menjalankan {args}: {exc}"


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if len(argv) < 2:
        print("pemakaian: python -m synapse_cli.restore_worker <zip> <status.json>")
        return 2

    arsip = Path(argv[0]).expanduser()
    status_path = Path(argv[1]).expanduser()
    mulai = time.monotonic()

    st: dict = {
        "status": "running",
        "step": "mulai",
        "arsip": arsip.name,
        "catatan": [],
        "started": time.time(),
    }
    _tulis_status(status_path, st)

    if not arsip.exists():
        st.update(status="failed", step="validasi",
                  output=f"File backup tidak ditemukan: {arsip}")
        _tulis_status(status_path, st)
        return 1

    backup_dir = arsip.parent

    # 1) BACKUP PENGAMAN — supaya data lama tidak hilang kalau restore gagal
    st["step"] = "backup-pengaman"
    _tulis_status(status_path, st)
    safety = backup_dir / f"sebelum-restore-{time.strftime('%Y%m%d-%H%M%S')}.zip"
    rc, out = _jalankan(["backup", "-o", str(safety)], _T_BACKUP)
    if safety.exists():
        st["catatan"].append(f"Backup pengaman: {safety.name} ({safety.stat().st_size} byte)")
    else:
        st["catatan"].append(f"PERINGATAN: backup pengaman gagal (exit {rc}): {out.strip()[-300:]}")

    # 2) HENTIKAN GATEWAY — WAJIB, kalau tidak state.db bisa rusak (#81)
    st["step"] = "hentikan-gateway"
    _tulis_status(status_path, st)
    rc, out = _jalankan(["gateway", "stop"], _T_STOP)
    st["catatan"].append(f"gateway stop (exit {rc}): {out.strip()[-300:]}")

    # 3) IMPORT — perintah NATIVE
    st["step"] = "import"
    _tulis_status(status_path, st)
    rc_import, out_import = _jalankan(["import", str(arsip)], _T_IMPORT)
    st["output"] = out_import[-6000:]

    # 4) NYALAKAN GATEWAY KEMBALI (selalu, walau import gagal)
    st["step"] = "nyalakan-gateway"
    _tulis_status(status_path, st)
    rc, out = _jalankan(["gateway", "start"], _T_START)
    st["catatan"].append(f"gateway start (exit {rc}): {out.strip()[-300:]}")

    st["step"] = "selesai"
    st["status"] = "ok" if rc_import == 0 else "failed"
    st["import_exit"] = rc_import
    st["duration"] = round(time.monotonic() - mulai, 1)
    st["finished"] = time.time()
    _tulis_status(status_path, st)
    return 0 if rc_import == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
