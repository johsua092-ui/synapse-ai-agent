# Synapse Mobile

Aplikasi mobile (Flutter) untuk mengendalikan **agent Synapse** yang berjalan di laptop.

> **Dibuat:** 24-25 September 2026
> **Versi:** 1.1.0
> **Package:** `com.nousresearch.synapse_mobile`

---

## 📁 Isi Folder

| Folder | Isi |
|---|---|
| `kode/` | Kode sumber lengkap (Flutter + Android/Kotlin + assets) |
| `dokumen/` | Kontrak kerja (36 bagian, 70 jebakan) + design + panduan |
| `apk/` | APK siap pasang (universal 79 MB) |
| `bukti/` | Screenshot hasil uji (282 file) |

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
  Xiaoni Cina-anak, Hyunsu Korea), dengan cadangan TTS bawaan HP
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

1. Salin `apk/SynapseMobile_v1.1.0_UNIVERSAL_79MB.apk` ke HP
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
| Arsitektur | arm64-v8a, armeabi-v7a, x86_64 |
| Ukuran APK | 79 MB (universal, termasuk 8 model Live2D + 14 background) |
| Sertifikat | CN=Synapse Mobile (self-signed) |
| Izin | 9 (tanpa SMS/kontak/lokasi) |

**Dependency utama:** go_router, flutter_riverpod, webview_flutter,
flutter_tts, audioplayers, speech_to_text, permission_handler, http,
image_picker, file_picker, shared_preferences, path_provider.

---

## 📚 Dokumentasi

| File | Isi |
|---|---|
| `dokumen/ATURAN_KERJA_SYNAPSE_MOBILE.md` | Kontrak kerja lengkap (36 bagian, 70 jebakan) |
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

## 🐛 Jebakan Tercatat (70)

Terdokumentasi lengkap di `dokumen/ATURAN_KERJA_SYNAPSE_MOBILE.md`.
Yang paling penting:
- Ikon notifikasi harus monokrom (kalau tidak → kotak putih)
- `usesCleartextTraffic="true"` wajib untuk `http://` di foreground service
- `adb` wajib pakai `-s <serial>` kalau ada >1 device
- **Flutter asset TIDAK rekursif** → subfolder harus didaftarkan eksplisit
- **WebView blokir `file://` (CORS)** → pakai server HTTP lokal
- **`registerTicker` wajib** untuk pixi-live2d-display
- **Avatar `Expanded` + WebView → super besar saat keyboard** → pakai tinggi tetap
- **Avatar 50% + keyboard 45% = overflow** → pakai 40% (seimbang)
- Skala model Live2D pakai **0.92** (bukan 0.98) agar kepala tidak terpotong
