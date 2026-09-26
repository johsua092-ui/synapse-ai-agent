# Synapse Mobile

Aplikasi mobile (Flutter) untuk mengendalikan **agent Synapse** yang berjalan di laptop.

> **Dibuat:** 24-26 September 2026
> **Versi:** 1.2.3
> **Package:** `com.nousresearch.synapse_mobile`

---

## 📁 Isi Folder

| Folder | Isi |
|---|---|
| `kode/` | Kode sumber lengkap (Flutter + Android/Kotlin + assets) |
| `dokumen/` | Kontrak kerja (43 bagian, 82 jebakan) + design + panduan |
| `apk/` | APK siap pasang (`SynapseMobile_v1.2.3.apk`, 58,7 MB) |
| `bukti/` | Screenshot hasil uji (300 file) |

---

## 🔄 Riwayat Versi (ringkas)

| Versi | Isi |
|---|---|
| **1.2.3** | **Update langsung dari GitHub** — "Cek Update" nyata + unduh & pasang APK dari dalam app |
| 1.2.2 | Perbaikan Backup & Restore PENUH (timeout 180s diperbaiki; pakai perintah resmi `synapse backup`/`import`) |
| 1.2.1 | Fix Live2D, CLI nyata, MCP/Skill custom tersimpan, patchnote di APK |
| 1.2.0 | Pengecilan APK 79 → 58 MB |
| 1.1.0 | Suara anime per karakter + fix keyboard avatar |
| 1.0.0 | Special Chat (Open-LLM-VTuber) + badge notifikasi |
| 0.9.0 | Kontrol Perangkat & Mode Otonom |
| 0.5.0 | Katalog 143 skill offline |
| 0.1.0 | Rilis pertama |

### Update dari dalam app (v1.2.3)
Setelah versi **1.2.3** terpasang **sekali**, update berikutnya tidak perlu
kirim file lagi:
`Setelan → Update & Patchnote → Cek Update → Unduh & Pasang Update → Install`.
Data **tidak hilang** (keystore sama). Android tetap menampilkan konfirmasi
"Install" sekali — ini aturan keamanan Android, tidak bisa dilewati.

---

## 🏗️ Arsitektur

```
┌──────────────┐   USB / WiFi (ADB)   ┌─────────────────┐
│ HP Android   │◄────────────────────►│ Laptop          │
│ Synapse      │                      │ Synapse Agent   │
│ Mobile       │  kirim perintah      │ = EKSEKUTOR     │
│ (jendela)    │─────────────────────►│ • 143 skill     │
│              │◄─────────────────────│ • browser       │
│              │  hasil               │ • terminal      │
└──────────────┘                      │ • kontrol HP    │
                                      └─────────────────┘
```

**Prinsip:** app di HP hanya "jendela" — kekuatan sesungguhnya ada di agent
(laptop). Jadi aman (tidak minta izin sensitif) dan maintenance ringan.

---

## ✅ Fitur

### Dasar
- **Chat streaming** ke api_server Synapse (port 8642)
- **Kirim gambar** (galeri/kamera) + **vision** (6 pilihan model)
- **Kirim dokumen** (baca file → teks)
- **Sesi chat**: banyak sesi, pencarian, pin, ganti nama, hapus
- **Panel setengah layar** (ala Gemini, 60%)
- **Tema**: hanya Terang/Gelap (default Terang)
- **Notifikasi latar belakang** (3 fase: bekerja/selesai/gagal)

### Navigasi (6 tab)
```
Chat | Special Chat | Skills | MCP | CLI | Setelan
```
Badge notifikasi (lonceng + bulatan hijau + angka) ada di pojok kanan atas,
**hanya** di Chat & Special Chat.

### Katalog Skill
- **143 skill** dibawa di dalam APK (`assets/katalog_skill.json`)
- Muncul **langsung** tanpa perlu server
- Tombol "i" (info) selalu ada
- Tombol install/uninstall hanya muncul setelah tersambung

### Special Chat (fitur Open-LLM-VTuber)
Setara https://github.com/Open-LLM-VTuber/Open-LLM-VTuber :
- **Avatar Live2D asli** — 8 model resmi Live2D Inc (Hiyori, Haru, Mao,
  Natori, Rice, Mark, Ren, Wanko), dibawa di dalam APK
- **14 background** dari repo Open-LLM-VTuber (sekolah, kelas, kamar, kota,
  pegunungan, malam, dll)
- **Suara anime ASLI per karakter** — 8 suara BERBEDA via Edge TTS
  (Nanami/Keita Jepang, Xiaoyi/Xiaoxiao/Yunjian Cina, HsiaoChen Taiwan,
  Xiaoni Cina-anak, Hyunsu Korea) + cadangan TTS bawaan HP
- **TTS** (AI bersuara) + ganti bahasa/kecepatan/nada
- **ASR** (user bicara lewat mikrofon)
- **Voice interruption** — suara AI dipotong saat user bicara
- **AI proactive speaking** — AI bicara duluan
- **Pemilih model** (8) + **pemilih background** (14) + **pemilih suara**

### Kontrol Perangkat (M13)
12 aksi cepat: daftar aplikasi, buka aplikasi, screenshot, layar sekarang,
ketuk layar, ketik teks, buka URL, info baterai, penyimpanan, rekam layar,
isi klipboard, cek koneksi + kolom "Perintah Bebas".

### Koneksi Perangkat (M14)
- **Kabel (USB)**: `adb reverse` — paling stabil
- **WiFi (nirkabel)**: `adb tcpip 5555` + `adb connect` — tanpa kabel
- Item menu di Setelan, tepat di bawah "Base URL & API Key"

### Mode Otonom (M15)
Agent **LIHAT** layar HP → **PUTUSKAN** → **TAP** sendiri (berulang).
Terbukti: buka Setelan → masuk Wi-Fi dalam 2 langkah.

---

## 📦 Cara Pasang

1. Salin `apk/SynapseMobile_v1.2.0_UNIVERSAL_58MB.apk` ke HP
2. Izinkan "Sumber tidak dikenal"
3. Install → kalau ada peringatan Play Protect → "Tetap instal"
4. Buka app → Setelan → isi Base URL + API Key → Deteksi Model → Simpan
5. Setelan → Koneksi AI Agent Synapse PC ke Mobile → pilih Kabel/WiFi
6. Untuk Special Chat: izinkan mikrofon saat diminta

Panduan lengkap: `dokumen/PANDUAN_INSTALL.txt`

---

## 📋 Spesifikasi Teknis

| Aspek | Nilai |
|---|---|
| Framework | Flutter 3.47.5 |
| Bahasa | Dart + Kotlin (native service) |
| Android minimum | 7.0 (API 24) |
| Android target | 16 (API 36) |
| Arsitektur | **arm64-v8a + armeabi-v7a** (x86_64 dibuang: hanya emulator) |
| Ukuran APK | **58 MB** (dari 79 MB, −26%) |
| Optimasi | R8/minify + shrinkResources + proguard keep rules |
| Sertifikat | CN=Synapse Mobile (self-signed) |
| Izin | 9 (tanpa SMS/kontak/lokasi) |

**Catatan pengecilan:** semua fitur TETAP UTUH 100%. Hanya konfigurasi build
yang diubah (kode Dart tidak disentuh). x86_64 dibuang karena hanya dipakai
emulator — semua HP asli memakai arm64/armeabi.

**Dependency utama:** go_router, flutter_riverpod, webview_flutter,
flutter_tts, audioplayers, speech_to_text, permission_handler, http,
image_picker, file_picker, shared_preferences, path_provider.

---

## 📚 Dokumentasi

| File | Isi |
|---|---|
| `dokumen/ATURAN_KERJA_SYNAPSE_MOBILE.md` | Kontrak kerja lengkap (37 bagian, 73 jebakan) |
| `dokumen/DESIGN_NOTIFIKASI.md` | Design notifikasi latar belakang |
| `dokumen/PANDUAN_INSTALL.txt` | Panduan install untuk pengguna |

---

## 🔒 Keamanan

**Tidak di-commit** (ada di `.gitignore`):
- `*.jks` — kunci penandatangan APK (RAHASIA)
- `key.properties` — password keystore
- `build/` — hasil build (3 GB)
- `.env` — konfigurasi rahasia

**Izin yang diminta (9, semua wajar):**
```
CAMERA, READ_MEDIA_IMAGES, READ_EXTERNAL_STORAGE, POST_NOTIFICATIONS,
FOREGROUND_SERVICE, FOREGROUND_SERVICE_DATA_SYNC, INTERNET,
ACCESS_NETWORK_STATE, RECORD_AUDIO (untuk Special Chat)
```

**Tidak diminta:** SMS, kontak, lokasi, daftar semua aplikasi.

---

## 🐛 Jebakan Tercatat (73)

Terdokumentasi lengkap di `dokumen/ATURAN_KERJA_SYNAPSE_MOBILE.md`.
Yang paling penting:
- Ikon notifikasi harus monokrom (kalau tidak → kotak putih)
- `usesCleartextTraffic="true"` wajib untuk `http://` di foreground service
- `adb` wajib pakai `-s <serial>` kalau ada >1 device
- **Flutter asset TIDAK rekursif** → subfolder harus didaftarkan eksplisit
- **WebView blokir `file://` (CORS)** → pakai server HTTP lokal
- **`registerTicker` wajib** untuk pixi-live2d-display
- **Avatar `Expanded` + WebView → super besar saat keyboard** → tinggi tetap
- **Avatar 50% + keyboard 45% = overflow** → pakai 40% (seimbang)
- **`abiFilters` saja tidak cukup** → pakai `--target-platform` saat build
- **R8 keep rules kurang → fitur rusak senyap** → keep semua paket plugin
