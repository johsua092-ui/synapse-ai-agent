# DESIGN NOTIFIKASI LATAR BELAKANG — Synapse Mobile

Dokumen design (matang) sebelum implementasi. Tujuan: user menjalankan tugas
panjang, menutup app, lalu **dapat notifikasi di HP** saat tugas selesai.

---

## 1. MASALAH YANG DISELESAIKAN

**Skenario nyata (kata user):**
> *"misal saya ngelakuin urusan disini lalu saya tutup dia kerja di latar
> belakang lalu dia selesai maka kirim notif kan? muncul di hp user kan?"*

| Masalah | Akibat kalau tidak ada |
|---|---|
| App ditutup → tugas "hilang" tanpa kabar | User tidak tahu kapan selesai |
| Harus buka app & cek manual | Tidak praktis |
| Tugas lama (analisis file, laporan) | User menunggu tanpa kepastian |

---

## 2. FONDASI TEKNIS (hasil riset api_server)

```
POST /v1/runs                    -> {"run_id": "run_xxx", "status": "started"}
GET  /v1/runs/{run_id}           -> {"status": "running"|"completed"|"failed",
                                     "output": "...", "last_event": "run.completed"}
GET  /v1/runs/{run_id}/events    -> SSE stream (message.delta, run.completed)
```

**Bukti uji nyata:**
```
POST /v1/runs  {"input":"Sebutkan 3 warna dasar"} 
  -> {"run_id":"run_925eb57db92e4d39b0e536fc7077861e","status":"started"}

GET /v1/runs/run_925eb...
  -> {"status":"completed","output":"Merah, biru, kuning.",
      "last_event":"run.completed","usage":{...}}
```

**Kesimpulan:** tugas dijalankan **oleh api_server** (di laptop). App hanya perlu
memantau status -> **app tidak perlu memegang proses berat**.

---

## 3. DESIGN NOTIFIKASI (3 FASE)

### FASE 1 — SEDANG BEKERJA (ongoing / tidak bisa dihapus)

```
┌─────────────────────────────────────────────┐
│  ⚙ Synapse sedang bekerja                   │  <- judul
│  Menganalisis laporan.pdf...                │  <- cuplikan tugas
│  ▓▓▓▓▓▓▓▓░░░░░░░░░░░░░░░░  (indeterminate)  │  <- progress
│  ─────────────────────────────────────────  │
│  [ Hentikan ]                               │  <- aksi
└─────────────────────────────────────────────┘
```
- Channel : `synapse_progress` (importance LOW, tanpa suara)
- Ongoing : **YA** (tidak bisa di-swipe)
- Warna aksen : emas `#DCB363`
- Ikon status bar : **monokrom** (siluet caduceus)

### FASE 2 — SELESAI

```
┌─────────────────────────────────────────────┐
│  ✓ Synapse selesai                          │
│  Merah, biru, kuning.                       │
│  ┌───────────────────────────────────────┐  │
│  │ (hasil panjang, bisa di-expand)       │  │  <- BigTextStyle
│  └───────────────────────────────────────┘  │
│  ─────────────────────────────────────────  │
│  [ Buka ]                    [ Salin ]      │
└─────────────────────────────────────────────┘
```
- Channel : `synapse_done` (importance DEFAULT, ada suara)
- Auto-cancel saat di-tap
- Aksi : **Buka** (ke sesi itu) + **Salin hasil**
- Warna aksen : hijau `#2E7D32`

### FASE 3 — GAGAL

```
┌─────────────────────────────────────────────┐
│  ⚠ Synapse gagal menyelesaikan tugas        │
│  Koneksi ke server terputus.                │
│  ─────────────────────────────────────────  │
│  [ Coba lagi ]              [ Lihat detail ]│
└─────────────────────────────────────────────┘
```
- Channel : `synapse_error` (importance HIGH)
- Aksi : **Coba lagi** + **Lihat detail**
- Warna aksen : merah `#C62828`

---

## 4. PRINSIP DESIGN (kenapa begini)

| Prinsip | Alasan |
|---|---|
| **3 fase berbeda** (kerja/selesai/gagal) | User tahu status tanpa buka app |
| **Progress ongoing tidak bisa dihapus** | Mencegah user "kehilangan" jejak tugas |
| **Importance berbeda per channel** | Tidak mengganggu saat kerja, bersuara saat selesai |
| **Aksi cepat (Buka/Salin/Hentikan)** | Hemat langkah, tidak perlu buka app untuk hal sederhana |
| **Ikon status bar monokrom** | Wajib Android 5+ (ikon berwarna akan jadi kotak putih) |
| **BigTextStyle** | Hasil AI sering panjang -> bisa di-expand |
| **Warna aksen emas** | Sesuai brand Synapse (caduceus emas) |
| **Group summary** | Kalau banyak tugas, tidak menumpuk berantakan |

---

## 5. ARSITEKTUR ANDROID

```
[Flutter/Dart]                        [Android Native - Kotlin]
  Kirim tugas                           
  POST /v1/runs  ──────┐                
  dapat run_id         │                
                       ▼                
  MethodChannel  ──> TaskService (Foreground Service)
  "startWatch"          │
                        ├─ tampilkan notif FASE 1 (ongoing)
                        ├─ polling GET /v1/runs/{id} tiap 3 detik
                        ├─ kalau completed -> notif FASE 2
                        ├─ kalau failed    -> notif FASE 3
                        └─ stopForeground saat selesai
```

**Kenapa Foreground Service (bukan worker biasa)?**
- Android membunuh proses biasa saat app di-swipe
- Foreground service **dijamin hidup** + wajib tampilkan notifikasi (sesuai kebutuhan)

**Izin yang dibutuhkan:**
```
FOREGROUND_SERVICE
FOREGROUND_SERVICE_DATA_SYNC   (Android 14+)
POST_NOTIFICATIONS             (Android 13+)
INTERNET                       (sudah ada)
```

---

## 6. DETAIL TEKNIS PENTING

| # | Hal | Nilai |
|---|---|---|
| 1 | Interval polling | 3 detik (cukup responsif, hemat baterai) |
| 2 | Timeout maksimal | 10 menit (lalu tandai gagal) |
| 3 | ID notifikasi progress | 1001 (tetap, agar di-update) |
| 4 | ID notifikasi hasil | 2000 + nomor urut (agar tidak saling menimpa) |
| 5 | Channel ID | `synapse_progress`, `synapse_done`, `synapse_error` |
| 6 | Ikon kecil | `ic_stat_synapse` (monokrom, wajib) |
| 7 | Ikon besar | `ic_notif_logo` (caduceus emas) |

---

## 7. KASUS TEPI (harus ditangani)

| Kasus | Penanganan |
|---|---|
| User menutup app saat tugas jalan | Foreground service tetap jalan |
| Server mati saat polling | Tandai gagal -> notif FASE 3 |
| HP restart | Tugas hilang (batasan Android) -> tandai di dokumentasi |
| Banyak tugas sekaligus | Group summary + nomor urut ID |
| Hasil sangat panjang | BigTextStyle + potong 500 karakter |
| User tap "Hentikan" | POST /v1/runs/{id}/stop + hapus notif |
| Izin notifikasi ditolak | Tampilkan peringatan di app |

---

## 8. RENCANA UJI (harus lolos semua)

```
1. Kirim tugas panjang dari app
2. TUTUP app (swipe dari recent apps)
3. Tunggu tugas selesai
4. Cek: notifikasi muncul di HP?          <- inti permintaan user
5. Tap "Buka" -> app terbuka ke sesi itu
6. Tap "Salin" -> hasil masuk clipboard
7. Uji gagal: matikan server -> notif gagal muncul
8. Uji "Hentikan": tugas berhenti + notif hilang
```

---

## 9. JEBAKAN YANG DIPERKIRAKAN (akan diverifikasi)

| # | Jebakan | Solusi |
|---|---|---|
| 34 | Ikon notifikasi berwarna -> jadi kotak putih | Pakai ikon **monokrom** (alpha saja) |
| 35 | Foreground service tidak jalan di Android 14+ | Deklarasi `foregroundServiceType="dataSync"` |
| 36 | Notifikasi tidak muncul (Android 13+) | Minta izin `POST_NOTIFICATIONS` runtime |
| 37 | Service dibunuh HyperOS | Minta user izinkan "Autostart" + "No restrictions" |
| 38 | Polling HTTP di service butuh izin | Pakai `INTERNET` (sudah ada) |
| 39 | Notif menimpa satu sama lain | Pakai ID berbeda per tugas |
| 40 | Service tidak berhenti -> baterai boros | `stopSelf()` setelah selesai |
