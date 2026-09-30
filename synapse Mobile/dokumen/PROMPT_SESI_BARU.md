# PROMPT UNTUK SESI BARU — LANJUTAN SYNAPSE MOBILE v1.2.1

> **Cara pakai:** copy SELURUH isi file ini, tempel sebagai pesan pertama di sesi baru.
> File ini dibuat 26 September 2026 oleh sesi sebelumnya (yang kehabisan 150 langkah).

---

## ⚠️ BACA DULU — ATURAN MUTLAK (JANGAN DILANGGAR)

### 🔴 A0. PERINTAH MUTLAK: WAJIB PAKAI VISION GEMINI (27 Sep 2026)

> Untuk MELIHAT gambar **WAJIB pakai Gemini**:
> - Tugas/laporan: `baca_gambar.py` (jalur Gemini langsung)
> - Synapse: `auxiliary.vision = ag/gemini-3.8-flash-high`
>   (provider custom, base_url `https://9router.consoleapi.qzz.io/v1`)
>
> **DILARANG** menyimpulkan isi gambar tanpa melihat. **DILARANG** memakai model
> buta gambar — `cbai/deepseek-v4.1-flash` **terbukti** bilang gambar "rusak".
> `vision_analyze` default **sering halusinasi** → jangan dipercaya sendirian.
> Detail: `Aturan Kerja Kuliah.md` Bagian 13.11 + `ATURAN_KERJA_SYNAPSE_MOBILE.md` Bagian 48.

### 🔴🔴 A0b. MUTLAK: RILIS HARUS TUNGGU ACC USER (27 Sep 2026)

> Rilis/update versi **HANYA** setelah user berkata "sudah/sesuai/ACC" — setelah
> user **VERIFIKASI SENDIRI**. **DILARANG sebelum ACC:** commit+push, GitHub
> Release/tag, taruh APK di folder rilis (`synapse Mobile/apk`), sync kode rilis,
> APK ke Download HP. Menyiapkan artefak rilis = **sudah termasuk rilis**.
> Kerjakan fix BUKAN izin rilis. Urutan: kerjakan → **BERHENTI** → tanya
> "sudah sesuai?" → **TUNGGU jawaban**.
> (Insiden: sesi hampir merilis v1.2.6 tanpa ACC — user hentikan paksa.)

### A. ATURAN 3 HAL WAJIB (paling penting)
Pekerjaan **BELUM dinyatakan selesai**. Ada **3 hal wajib** yang **HANYA BOLEH** dikerjakan
**SETELAH user bilang "sudah sesuai/selesai"**:

1. Tulis **patchnote / log update resmi** di APK versi terbaru
2. Siapkan **APK terbaru di folder Download HP** user
3. **Push normal ke GitHub pakai token**

> **URUTAN YANG BENAR:**
> 1. Selesaikan 3 item yang belum tuntas (uji Simpan MCP/Skill, Backup PENUH, Restore)
> 2. **BERHENTI** dan tanya user: *"Apakah sudah sesuai?"*
> 3. Kalau user bilang **SUDAH** → baru kerjakan 3 hal wajib
> 4. Kalau user bilang **BELUM** → perbaiki dulu, jangan kerjakan 3 hal wajib

**Tanpa izin user, DILARANG melakukan 3 hal itu.**

### B. ATURAN PUSH GITHUB (verbatim user)
- **DILARANG FORCE PUSH** — HARAM. Hanya **push normal**.
- Format: **1 folder bernama `synapse Mobile`** di root repo.
- Isi folder **SANGAT LENGKAP**: kode + dokumen + apk + bukti + README.
- **Kawal sampai LIVE & SUKSES** (verifikasi nyata, bukan klaim).
- **Pakai TOKEN** GitHub (user bilang: *"push normal ke github pakai token ya!"*).
- Setelah tiap fitur selesai → langsung siapkan & push (jangan menumpuk).

### C. ATURAN VERSI
- Versi pakai **angka bertahap**: `1.2.1` → `1.2.2` → `1.2.3` (hemat, tidak boros).
- **Wajib**: patchnote/log update di APK + dialog update saat install
  (tampil "Update dari X ke Y"), dan install **TIDAK boleh bentrok** dengan paket lama.

### D. ATURAN HP USER (Bagian 22 kontrak — KERAS)
- **DILARANG** uninstall/membuka/mengubah/menghapus APK/app user **selain Synapse**.
- **DILARANG** install APK lain. **DILARANG** menyentuh data app user.
- Diizinkan HANYA untuk `com.nousresearch.synapse_mobile`.
- **WAJIB MINTA IZIN DULU** untuk operasi apa pun yang menyentuh HP.
  (User pernah bilang: *"anda sangat bagus tanya dulu karena ini menyangkut aplikasi di hp saya"*)

### E. ATURAN LAIN (keras)
- **DILARANG** `taskkill /F /IM chrome.exe` dkk. **DILARANG** mematikan Word user.
- **DILARANG** AI menyentuh/meng-update **Table of Content** di Word.
- **Password = batas keras AI** — AI TIDAK mengetik password user; user login sendiri.
- **PANDUAN/DAFTAR FILE HARUS JADI FILE** (bukan hanya di chat) — Bagian 13.11 kontrak kuliah.
- Semua pengalaman/jebakan baru **WAJIB dicatat ke file kontrak .md** (lihat path di bawah).
- **429 ≠ kuota habis** — kuota terpisah per model. **BIJAKSANA & SEIMBANG.**
- Kerjakan **satu per satu, berurutan, sampai sempurna** (Opsi D user).

---

## 📁 PATH PENTING (hafalkan)

| Apa | Path |
|---|---|
| **Kontrak kuliah** | `C:\File Kuliah\Materi Semester 5\Area Kerja Synapse\Aturan Kerja Kuliah.md` |
| **MD Synapse Mobile** | `C:\File Kuliah\Materi Semester 5\Area Kerja Synapse\Pemrograman Aplikasi Mobile\folder pengembangan synapse\ATURAN_KERJA_SYNAPSE_MOBILE.md` |
| **Folder bukti** | `...\folder pengembangan synapse\bukti\` |
| **Folder APK** | `...\folder pengembangan synapse\apk\` |
| **Proyek Flutter** | `C:\Users\user\synapse-ai-agent\apps\mobile` |
| **APK hasil build** | `C:\Users\user\synapse-ai-agent\apps\mobile\build\app\outputs\flutter-apk\app-release.apk` |
| **Folder GitHub** | `C:\Users\user\synapse-ai-agent\synapse Mobile\` |
| **Repo GitHub** | `github.com/johsua092-ui/synapse-ai-agent` (branch `main`) |
| **Skrip baca gambar** | `C:\File Kuliah\Materi Semester 5\Area Kerja Synapse\baca_gambar.py` |
| **Backup sebelum kecilkan** | `...\apps\mobile\_backup_sebelum_kecilkan\` |
| **Config Synapse** | `C:\Users\user\AppData\Local\synapse\config.yaml` + `.env` |

**Status MD saat ini:** 39 bagian, ~135.411 byte, CRLF. **74+ jebakan terdokumentasi.**

---

## 📱 HP & KONEKSI

```
HP user   : serial IJW8EII77HJVOVZ5  (POCO X6 Pro 2311DRK48G, Android 16)
Package   : com.nousresearch.synapse_mobile
WiFi HP   : 192.168.1.7   |  Laptop: 192.168.1.5
Wireless ADB aktif: 192.168.1.7:5555

ADB       : C:\Users\user\AppData\Local\Android\Sdk\platform-tools\adb.exe
            (SELALU pakai -s IJW8EII77HJVOVZ5 kalau ada 2 device)

Base URL app : http://127.0.0.1:8642   (api_server Synapse, port 8642)
Wajib jalankan: adb -s IJW8EII77HJVOVZ5 reverse tcp:8642 tcp:8642
API Key      : baca dari C:\Users\user\AppData\Local\synapse\.env (API_SERVER_KEY)
               (nilai: alfanumerik 32 karakter — JANGAN tulis di dokumen publik)
```

### Cara build (PENTING — sudah dioptimasi)
```bash
export PATH="/c/dev/flutter/bin:$PATH"
export JAVA_HOME='C:\Program Files\Android\Android Studio\jbr'
cd /c/Users/user/synapse-ai-agent/apps/mobile
flutter build apk --release --target-platform android-arm,android-arm64
# Hasil: ~58,6 MB (universal 2 ABI; x86_64 dibuang, R8 aktif)
```

### Cara install ke HP
```bash
ADB="/c/Users/user/AppData/Local/Android/Sdk/platform-tools/adb.exe"
"$ADB" -s IJW8EII77HJVOVZ5 install -r \
  'C:\Users\user\synapse-ai-agent\apps\mobile\build\app\outputs\flutter-apk\app-release.apk'
# Kalau gagal: pastikan mode USB = "Transfer file (MTP)" (JEBAKAN #46)
```

### Cara kirim APK ke Download HP (untuk dibagikan via WhatsApp)
```bash
"$ADB" -s IJW8EII77HJVOVZ5 push \
  'C:\Users\user\synapse-ai-agent\apps\mobile\build\app\outputs\flutter-apk\app-release.apk' \
  /sdcard/Download/SynapseMobile_v1.2.2.apk
# lalu scan media + verifikasi md5 (md5sum di PC & HP harus SAMA)
```

---

## 🔍 CARA VERIFIKASI YANG TERBUKTI BEKAS

### 1. Melihat layar HP (untuk uji UI)
```bash
"$ADB" -s IJW8EII77HJVOVZ5 shell screencap -p /sdcard/x.png
"$ADB" -s IJW8EII77HJVOVZ5 pull /sdcard/x.png  /path/lokal.png
```

### 2. Membaca isi layar (vision)
```bash
cd "/c/File Kuliah/Materi Semester 5/Area Kerja Synapse"
export GOOGLE_API_KEY=$(grep -m1 "^GOOGLE_API_KEY=" "/c/Users/user/AppData/Local/synapse/.env" | cut -d= -f2-)
export GOOGLE_API_KEY_2=$(grep -m1 "^GOOGLE_API_KEY_2=" "/c/Users/user/AppData/Local/synapse/.env" | cut -d= -f2-)
export GOOGLE_API_KEY_3=$(grep -m1 "^GOOGLE_API_KEY_3=" "/c/Users/user/AppData/Local/synapse/.env" | cut -d= -f2-)
export GOOGLE_API_KEY_4=$(grep -m1 "^GOOGLE_API_KEY_4=" "/c/Users/user/AppData/Local/synapse/.env" | cut -d= -f2-)
python baca_gambar.py "path/gambar.png"
```

> **MODEL VISION (hasil uji nyata 26 Sep 2026):**
> - ✅ **`gemini-flash-lite-latest`** → HTTP 200, HIDUP
> - ⚠️ `gemini-flash-latest`, `gemini-3-flash-preview`, `gemini-3.5-flash` → 429 (rate limit **sementara**, pesan "retry in 42s")
> - ❌ `gemini-2.5-flash`, `gemini-2.0-flash`, `gemini-2.5-flash-lite` → **404 (model DITUTUP Google)**
> - **Keempat API key masih hidup** — bukan kuota habis, hanya rate limit (20/menit free tier).
> - `baca_gambar.py` **sudah diperbaiki** untuk pakai urutan model yang benar + jeda.

### 3. Tap di HP (koordinat)
- Layar HP: **1220 x 2712 px**
- Flutter **TIDAK mengekspos teks** ke `uiautomator` (0 elemen) → pakai screenshot + vision, atau
  deteksi warna piksel dengan PIL (cara paling andal).
- `adb shell input tap X Y` ; `input text "..."` ; `input keyevent KEYCODE_TAB`
- **JEBAKAN**: tap sering meleset kalau pakai perkiraan vision → **verifikasi tiap langkah**
  (cek `dumpsys input_method | grep mInputShown` untuk tahu keyboard muncul = field kena).

### 4. Uji CLI (perintah nyata)
Ketik di layar CLI app, misal `uname` → hasilnya harus `MINGW64_NT-10.0-26200`.
(Bukti ini sudah pernah berhasil — CLI benar-benar jalan.)

---

## ✅ YANG SUDAH SELESAI (jangan diulang)

### Perbaikan v1.2.1 (semua kode SUDAH ditulis & ter-build & terinstall)
| # | Item | Status |
|---|---|---|
| 1 | **Bug Live2D** kaki/tangan jadi 3 + patah-patah | ✅ Diperbaiki (antialias:false, resolution:1, autoDensity:false) |
| 2 | **CLI palsu → NYATA** | ✅ Terbukti (`uname` → MINGW64) |
| 3 | **MCP Custom** (tambah/edit/hapus, tersimpan) | ✅ Ada (FAB + dialog + SharedPreferences) |
| 4 | **Skill Custom** (buat/edit/hapus) | ✅ Ada (tombol + + dialog + bagian "Skill Saya") |
| 5 | **Backup & Restore PENUH** | ✅ Ada (backup ~/.synapse → zip, tombol Restore dari backup) |
| 6 | **Patchnote di APK** | ✅ `assets/patchnote.json` + dialog update otomatis |
| 7 | **Layar Update** | ✅ Baca versi asli dari APK (bukan hardcode 0.1.0 lagi) |
| 8 | **Versi 1.2.1** + install tanpa bentrok | ✅ versionCode 2201, install "Success" |
| 9 | **Judul AppBar TENGAH** ("Special Chat") | ✅ Terbukti ukur piksel (selisih 6 px) |
| 10 | **Pengecilan APK** 79 MB → 58 MB (−26%) | ✅ Buang x86_64 + R8 + kompres aset, fitur 100% utuh |
| 11 | **Koneksi HP** (Base URL + API Key) | ✅ Model terdeteksi: "synapse-agent v0.20.5 — 1 model" |

### Fitur lain yang sudah ada (dari sesi-sesi sebelumnya)
- 6 tab: **Chat | Special Chat | Skills | MCP | CLI | Setelan**
- **Special Chat** = fitur 100% Open-LLM-VTuber: avatar Live2D (8 model resmi),
  14 background (unduh dari repo Open-LLM-VTuber), suara anime berbeda per karakter
  (Edge TTS, 8 suara unik — sudah diuji)
- **Badge notifikasi** (lonceng + bulatan hijau + angka) di pojok kanan atas,
  **hanya muncul di Chat & Special Chat**
- Chat streaming, kirim gambar/dokumen/vision, sesi chat, notifikasi latar 3 fase
- Skills: katalog offline 143 skill (dibawa di APK)
- Panel Perangkat (M13: 12 aksi cepat via ADB), Koneksi Perangkat (M14: Kabel/WiFi),
  Mode Otonom (M15: agent lihat → putuskan → tap sendiri)
- Icon caduceus emas, tema 2 mode (Terang/Gelap, default Terang)

---

## ⏳ YANG BELUM TUNTAS — KERJAKAN INI DULU (3 item)

> Ketiganya **butuh HP terhubung + app terinstall v1.2.1**. Koneksi sudah terpasang
> (Base URL + API Key sudah diisi & model terdeteksi), jadi bisa langsung diuji.

### Item 1 — VERIFIKASI SIMPAN MCP & SKILL
**Yang harus dibuktikan:** setelah isi form lalu tekan "Simpan", datanya benar-benar tersimpan
dan muncul di daftar ("MCP Saya" / "Skill Saya").

**Langkah:**
1. Buka app → tab **MCP** (posisi tab ke-4) → tap **FAB "Tambah MCP"** (kanan bawah)
2. Isi: Nama = `mcp_uji`, URL = `http://127.0.0.1:8642/mcp`, Tipe = `http`
3. Tap **Simpan** → verifikasi muncul kartu "MCP Saya (1)"
4. Buka tab **Skills** (tab ke-3) → tap **tombol +** (kanan atas AppBar)
5. Isi: Nama = `skill_uji`, Keterangan = `uji`, Isi = `tes`
6. Tap **Simpan** → verifikasi muncul di bagian **"Skill Saya"**
7. **Bonus bukti:** baca SharedPreferences HP
   (`adb shell run-as com.nousresearch.synapse_mobile cat /data/data/.../shared_prefs/*.xml`)
   atau restart app → data harus **masih ada** (bukti tersimpan permanen)

**Simpan bukti:** screenshot ke `...\folder pengembangan synapse\bukti\` dengan nama
`V121_MCP_simpan.png` dan `V121_SKILL_simpan.png`.

### Item 2 — JALANKAN BACKUP PENUH
**Langkah:**
1. Setelan → **Backup & Restore** (item menu di bagian "Lain-lain")
2. Tap **"Buat Backup PENUH"**
3. Tunggu → verifikasi muncul pesan sukses + info lokasi file backup
4. **Bukti nyata:** cek file backup ada
   (`adb shell ls -la /sdcard/` atau folder yang ditampilkan app)
5. Screenshot → `V121_BACKUP.png`

### Item 3 — UJI RESTORE
**Langkah:**
1. Di halaman yang sama, tap **"Restore dari Backup"**
2. Pilih file backup hasil Item 2
3. Konfirmasi dialog (ada peringatan data akan DITIMPA)
4. Verifikasi hasil restore + screenshot → `V121_RESTORE.png`

> **Catatan teman user (verbatim):** *"yang restore itu sebenarnya bukan itu aja,
> itu restore 1 dirinya full"* → maksudnya **restore SELURUH isi `~/.synapse`**
> (config.yaml, .env, memories/, skills/, SOUL.md, sessions.db, cron/).
> Halaman Backup & Restore v1.2.1 sudah dibuat untuk ini — **pastikan benar-benar full**.

---

## 🎯 SETELAH 3 ITEM SELESAI → BERHENTI & TANYA USER

Kirim pesan kira-kira begini:

> "3 item sudah tuntas: (1) Simpan MCP & Skill terbukti tersimpan,
> (2) Backup PENUH berhasil, (3) Restore berhasil.
> Bukti ada di folder bukti.
>
> **Apakah sudah sesuai?** Kalau sudah, saya lanjut 3 hal wajib:
> patchnote resmi, APK ke Download HP, push GitHub pakai token."

**JANGAN** mengerjakan 3 hal wajib sebelum user menjawab "sudah sesuai".

---

## 🚀 3 HAL WAJIB (kerjakan SETELAH user bilang "sesuai")

### Wajib 1 — Patchnote resmi di APK
- Perbarui `C:\Users\user\synapse-ai-agent\apps\mobile\assets\patchnote.json`:
  tambah entri versi baru (misal **1.2.2**) berisi daftar perbaikan yang benar-benar dikerjakan.
- Naikkan versi di `android/app/build.gradle.kts` (`versionCode` +1, `versionName` `1.2.1`→`1.2.2`).
- Build ulang → dialog "Update ke v1.2.2" harus muncul saat buka app.

### Wajib 2 — APK terbaru ke folder Download HP
```bash
"$ADB" -s IJW8EII77HJVOVZ5 push <apk> /sdcard/Download/SynapseMobile_v1.2.2.apk
# verifikasi: md5sum PC == md5sum HP, lalu scan media agar muncul di Files
```

### Wajib 3 — Push normal ke GitHub (PAKAI TOKEN, TANPA FORCE)
```bash
# 1. Siapkan folder "synapse Mobile" LENGKAP (kode+dokumen+apk+bukti+README)
# 2. Pastikan TIDAK ada rahasia ikut (cek: .jks, key.properties, .env → harus 0)
# 3. git add "synapse Mobile" ; git commit ; git push origin main   ← TANPA --force
# 4. Verifikasi LIVE: git rev-parse HEAD == git rev-parse origin/main
#    + buka GitHub / pakai API untuk lihat folder & isinya
```

---

## 🐛 JEBAKAN PENTING (sudah terdokumentasi, 74+)

Ringkasan yang paling sering kena:
| # | Jebakan | Solusi |
|---|---|---|
| 45 | `INSTALL_FAILED_VERSION_DOWNGRADE` | naikkan `versionCode` eksplisit |
| 46 | HP putus saat install | ubah mode USB ke **"Transfer file (MTP)"** |
| 50 | `adb: more than one device` | selalu pakai `-s <serial>` |
| 53 | `vision_analyze` rusak/timeout | pakai `baca_gambar.py` (Gemini REST) |
| 54 | uiautomator pada app Flutter = 0 elemen | screenshot + deteksi piksel |
| 60 | aset subfolder **tidak** masuk APK | daftarkan **setiap** subfolder di `pubspec.yaml` |
| 61 | `file://` diblokir CORS di WebView | **server HTTP lokal** di app (127.0.0.1:8765) |
| 62 | `Maximum call stack size exceeded` | jangan muat cubism2+cubism4+index sekaligus |
| 66 | avatar membesar saat keyboard | avatar **tinggi tetap** (bukan `Expanded`) |
| 68 | overflow avatar 50% + keyboard 45% > 100% | avatar **40%** |
| 71 | `abiFilters` saja tidak cukup | pakai `--target-platform android-arm,android-arm64` |
| 73 | R8 bisa rusak fitur **senyap** | keep rules lengkap (plugin + kelas app + TaskService) |
| 74 | judul AppBar tidak simetris kalau ada `actions` | `centerTitle:true` + `leading` lebar sama + `titleSpacing:0` + `SizedBox(width:double.infinity)` |

---

## 📌 CATATAN AKHIR

- **Working dir**: `C:\File Kuliah\Materi Semester 5\Area Kerja Synapse\`
- **User**: M. RIZAL KURNIAWAN, NIM 244101060094, Absen 07, Kelas 3C JTD,
  Prodi Jaringan Telekomunikasi Digital, Teknik Elektro, Politeknik Negeri Malang 2026.
- **Dosen PAM**: Putri Elfa Mas'udia (MUTLAK). **Dosen pembimbing**: Prof. Dr. M. Sarosa, Dipl.Ing., M.T.
- **Aturan kerja kuliah**: semua file kerja di Area Kerja Synapse; baca materi penuh dulu;
  verifikasi nyata; jangan menyuruh user kerja teknis; **lapor Telegram saat selesai/stuck**.
- **Prinsip verifikasi**: percayai **angka objektif** (aapt, md5, ukuran, piksel), bukan
  persepsi vision semata. Vision sering keliru (pernah salah lapor posisi judul).
- **Selalu catat jebakan baru ke MD** (`ATURAN_KERJA_SYNAPSE_MOBILE.md`) setelah selesai.

## 🔬 DETAIL TEKNIS (biar tidak perlu investigasi ulang)

### Kunci SharedPreferences (untuk verifikasi Simpan)
```
MCP    : file  lib/features/mcp/mcp_screen.dart
         kunci = 'mcp_aktif'   (StringList — MCP yang aktif)
                 'mcp_custom'  (String JSON — daftar MCP buatan user)

Skills : file  lib/features/skills/skills_screen.dart
         kunci = 'skill_custom' (String JSON — daftar skill buatan user)
```
**Cara baca bukti dari HP:**
```bash
"$ADB" -s IJW8EII77HJVOVZ5 shell run-as com.nousresearch.synapse_mobile \
  cat /data/data/com.nousresearch.synapse_mobile/shared_prefs/*.xml
```
Kalau kunci `mcp_custom` / `skill_custom` berisi JSON data uji → **TERBUKTI tersimpan**.

### Fungsi Backup & Restore
```
File: lib/features/backup/backup_screen.dart
Isi backup (LENGKAP = seluruh "diri" Synapse ~/.synapse):
  config.yaml, .env, memories/, skills/, SOUL.md, sessions.db, cron/, folder lain
Mekanisme: mengirim perintah ke agent (klien.perintahAgent) → agent yang mengeksekusi
```
**Catatan:** backup/restore **dijalankan oleh agent di laptop** (bukan app menyimpan sendiri).
Jadi saat uji, **agent harus hidup** + `adb reverse tcp:8642 tcp:8642` aktif.

### Navigasi app (untuk uji UI)
```
6 tab bawah: Chat(1) | Special Chat(2) | Skills(3) | MCP(4) | CLI(5) | Setelan(6)
Setelan → item menu: Tampilan, Base URL & API Key, Koneksi AI Agent Synapse PC ke Mobile,
                     Update & Patchnote, Backup & Restore, Akses Perangkat, Notifikasi, Status
Badge lonceng (pojok kanan atas) HANYA di tab Chat & Special Chat.
```
**Layar HP 1220 x 2712 px.** Flutter **tidak mengekspos teks** ke uiautomator → pakai
screenshot + deteksi piksel (PIL). Tap sering meleset → **verifikasi tiap langkah**
(cek `dumpsys input_method | grep mInputShown` untuk tahu field benar-benar kena).

---

## 🧭 LANGKAH PERTAMA WAJIB (sebelum kerja apa pun)

Sesi baru **WAJIB** mengirim pesan konfirmasi ke user **sebelum** melakukan apa pun.
Isinya kira-kira:

> "Saya sudah membaca `PROMPT_SESI_BARU.md`. Ringkasan pemahaman saya:
> (1) 3 item belum tuntas: Verifikasi Simpan MCP & Skill, Backup PENUH, Uji Restore full.
> (2) Urutan: kerjakan 3 item → BERHENTI → tanya user → baru 3 hal wajib.
> (3) DILARANG force push; wajib pakai token; folder `synapse Mobile` harus lengkap.
> (4) Jangan sentuh app user selain Synapse; minta izin dulu untuk operasi yang menyentuh HP.
> **Sudah benar pemahaman saya? Kalau ya, saya mulai dari item 1.**"

**Tujuan:** memastikan ingatan benar **sebelum** kerja (mencegah salah paham/halusinasi).
**JANGAN** langsung kerja tanpa konfirmasi ini.

---

## 📞 ATURAN PELAPORAN & CARA KERJA

- **Bahasa:** Indonesia.
- **Lapor Telegram** ke user saat **SELESAI** atau **STUCK** (aturan kerja kuliah).
- Kerjakan **SATU PER SATU, berurutan, sampai sempurna** (Opsi D user).
- **JANGAN menyuruh user melakukan kerja teknis.**
- Kalau macet: **LAPOR**, jangan diam-diam berhenti.

---

## ⚠️ KALAU HP TIDAK TERHUBUNG

```
1. Cek: adb devices  → HP IJW8EII77HJVOVZ5 harus muncul
2. Kalau kosong  → minta user ubah mode USB ke "Transfer file (MTP)"  (JEBAKAN #46)
3. Cek wireless  → adb connect 192.168.1.7:5555
4. Kalau tetap gagal → LAPOR ke user, jangan diam-diam berhenti
```

---

## 💰 HEMAT LANGKAH (jangan buang iterasi)

- **JANGAN build ulang** kalau kode tidak berubah — APK v1.2.1 **sudah ada & terinstall**.
- **JANGAN ulangi investigasi** yang sudah selesai (lihat tabel "YANG SUDAH SELESAI").
- Uji langsung: **item 1 → 2 → 3**.
- Kalau 3 item sudah terbukti, **JANGAN uji fitur lain** yang tidak diminta.
- Sesi punya batas **150 langkah** — pakai efisien (batch beberapa perintah dalam 1 panggilan).

---

## 🧾 FORMAT LAPORAN AKHIR (saat tanya "sudah sesuai?")

Sertakan bukti **objektif**, bukan klaim:
```
ITEM 1 — Simpan MCP & Skill
  MCP  : mcp_uji tersimpan ✅ (bukti: SharedPreferences / screenshot)
  Skill: skill_uji tersimpan ✅ (bukti: muncul di "Skill Saya")
  Bertahan setelah restart? ✅ / ❌

ITEM 2 — Backup PENUH
  File backup: <path> (<ukuran> byte) ✅
  Isi: config.yaml, .env, memories/, skills/, SOUL.md, sessions.db, cron/ ✅

ITEM 3 — Restore
  Hasil: ✅ berhasil memulihkan seluruh isi ~/.synapse

Bukti screenshot: V121_MCP_simpan.png, V121_SKILL_simpan.png,
                  V121_BACKUP.png, V121_RESTORE.png (di folder bukti)

Apakah sudah sesuai? Kalau sudah, saya lanjut 3 hal wajib.
```

**SELESAI. Mulai dari "🧭 LANGKAH PERTAMA WAJIB" lalu "⏳ YANG BELUM TUNTAS (3 item)".**
