# Synapse Mobile

Aplikasi mobile (Flutter) untuk mengendalikan **agent Synapse** yang berjalan di laptop.

> **Dibuat:** 24-25 September 2026
> **Versi:** 0.9.0
> **Package:** `com.nousresearch.synapse_mobile`

---

## 📁 Isi Folder

| Folder | Isi |
|---|---|
| `kode/` | Kode sumber lengkap (Flutter + Android/Kotlin) |
| `dokumen/` | Kontrak kerja + design + panduan |
| `apk/` | APK siap pasang (universal, arm64, armeabi) |
| `bukti/` | Screenshot hasil uji (236 file) |

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
(laptop). Jadi:
- Aman (tidak minta izin sensitif seperti SMS/kontak/lokasi)
- Tidak kena Play Protect separah app yang minta semua izin
- Maintenance ringan (90% kekuatan di agent, bukan di APK)

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

### Katalog Skill
- **143 skill** dibawa di dalam APK (`assets/katalog_skill.json`)
- Muncul **langsung** tanpa perlu server
- Tombol "i" (info) selalu ada
- Tombol install/uninstall hanya muncul setelah tersambung

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

1. Salin `apk/SynapseMobile_v0.9.0_UNIVERSAL_58MB.apk` ke HP
2. Izinkan "Sumber tidak dikenal"
3. Install → kalau ada peringatan Play Protect → "Tetap instal"
4. Buka app → Setelan → isi Base URL + API Key → Deteksi Model → Simpan
5. Setelan → Koneksi AI Agent Synapse PC ke Mobile → pilih Kabel/WiFi

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
| Ukuran APK | 58 MB (universal) / 24 MB (arm64) |
| Sertifikat | CN=Synapse Mobile (self-signed) |
| Izin | 8 (tanpa SMS/kontak/lokasi) |

---

## 📚 Dokumentasi

| File | Isi |
|---|---|
| `dokumen/ATURAN_KERJA_SYNAPSE_MOBILE.md` | Kontrak kerja lengkap (33 bagian, 55 jebakan) |
| `dokumen/DESIGN_NOTIFIKASI.md` | Design notifikasi latar belakang |
| `dokumen/PANDUAN_INSTALL.txt` | Panduan install untuk pengguna |

---

## 🔒 Keamanan

**Tidak di-commit** (ada di `.gitignore`):
- `*.jks` — kunci penandatangan APK (RAHASIA)
- `key.properties` — password keystore
- `build/` — hasil build (3 GB)
- `.env` — konfigurasi rahasia

**Izin yang diminta (8, semua wajar):**
```
CAMERA, READ_MEDIA_IMAGES, READ_EXTERNAL_STORAGE,
POST_NOTIFICATIONS, FOREGROUND_SERVICE,
FOREGROUND_SERVICE_DATA_SYNC, INTERNET, ACCESS_NETWORK_STATE
```

**Tidak diminta:** SMS, kontak, lokasi, daftar semua aplikasi.

---

## 🐛 Jebakan Tercatat

**55 jebakan** terdokumentasi lengkap di
`dokumen/ATURAN_KERJA_SYNAPSE_MOBILE.md` (bagian 7 + tiap milestone),
termasuk:
- Ikon notifikasi harus monokrom (kalau tidak → kotak putih)
- `usesCleartextTraffic="true"` wajib untuk `http://` di foreground service
- `adb` wajib pakai `-s <serial>` kalau ada >1 device
- Tombol pengaturan koneksi harus jadi item menu Setelan (bukan di dalam grup)
- `vision_analyze` agent rusak → pakai `uiautomator dump`
