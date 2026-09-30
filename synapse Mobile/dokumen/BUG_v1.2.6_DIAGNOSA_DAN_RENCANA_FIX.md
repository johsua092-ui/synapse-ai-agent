# 🐛 DIAGNOSA BUG SYNAPSE MOBILE v1.2.6 + RENCANA FIX

> **Dibuat:** 29 Sep 2026 · **Status: DIAGNOSA SAJA — BELUM ADA KODE YANG DIUBAH**
> Menunggu keputusan user sebelum memperbaiki & build.
>
> **Laporan tester (teman user) di v1.2.6:**
> 1. Delete / Pin / Rename sesi **tidak berfungsi** (tidak ada yang terjadi)
> 2. **Tidak bisa** backup / restore
> 3. VTuber **tidak ke-load**
> 4. Kalau ke-load → **VTuber jadi 2** (1 normal + 1 raksasa sampai kaki)
> 5. Tools kadang muncul **"Gagal: Exception: HTTP 404"**

Semua diagnosa di bawah **dari pembacaan kode nyata** (bukan dugaan).

---

## 🎯 RINGKASAN: 5 BUG → 4 AKAR MASALAH

| Bug | Akar | File : baris |
|---|---|---|
| 1. Pin/Rename/Delete mati | **Riverpod salah pakai** (`watch(provider.notifier)`) | `sesi_drawer.dart:21`, `sesi_screen.dart:24`, `special_chat_screen.dart:421` |
| 2. Backup/Restore gagal | **Timeout 180s** + jalur lewat LLM + state.db terkunci | `api_client.dart` (timeout), `backup_screen.dart:36,93` |
| 3. VTuber tak load | **Race condition** muat model | `live2d_view.dart:81` + `viewer.html:118,183` |
| 4. VTuber 2 buah | **Race condition** yang sama (model lama tak terhapus) | `viewer.html:118-136` |
| 5. HTTP 404 di Tools | Bukan bug kode — **error server diteruskan** (koneksi/endpoint) | `tools_screen.dart:60`, `api_client.dart:220` |

---

## 🐛 BUG 1 — PIN / RENAME / DELETE TIDAK BERFUNGSI

### Akar masalah (PASTI)
Pola Riverpod **salah** di 3 tempat:
```dart
final n = ref.watch(sesiProvider.notifier);   // ❌
```
`watch(provider.notifier)` **hanya** me-rebuild saat *notifier* berganti —
**bukan** saat *state*-nya berubah. Jadi `pin()`, `gantiJudul()`, `hapus()`
mengubah data + menyimpan ke SharedPreferences, tapi **layar tidak digambar ulang**
→ terlihat "tidak ada yang terjadi".

**Bukti pembanding (yang BENAR):**
`lib/features/chat/chat_screen.dart:240`
```dart
final semua = ref.watch(sesiProvider);   // ✅ watch STATE
```
→ itulah kenapa di tab Chat perubahan **kelihatan**, tapi di **drawer sesi** dan
**tab Sesi** tidak.

### Lokasi tepat
```
lib/features/sesi/sesi_drawer.dart          :21
lib/features/sesi/sesi_screen.dart          :24
lib/features/special/special_chat_screen.dart :421  (ambil .aktif)
```

### Rencana fix (1 baris per tempat)
```dart
// SEBELUM (salah)
final n = ref.watch(sesiProvider.notifier);
final daftar = n.cari(_cari);

// SESUDAH (benar)
final daftarSemua = ref.watch(sesiProvider);          // watch STATE -> rebuild
final n = ref.read(sesiProvider.notifier);            // notifier hanya untuk AKSI
final daftar = ...cari(_cari, dari: daftarSemua);     // cari() dari state terbaru
```
> `cari()` saat ini adalah method di notifier yang membaca `state` internal —
> aman dipakai, tapi layar harus tetap **watch state** supaya rebuild.

**Risiko fix:** sangat rendah. **Tingkat keberhasilan: tinggi.**

---

## 🐛 BUG 2 — BACKUP / RESTORE GAGAL

### Akar masalah (3 lapis)
1. **Timeout 180 detik** — `ApiClient.perintahAgent()` default `.timeout(180s)`.
   Backup PENUH = **~120–130 detik** + LLM agent berpikir → sering **lewat 180s**
   → `TimeoutException` → app bilang "Gagal" padahal agent masih bekerja.
   (Jebakan #78 sudah tercatat di ATURAN_KERJA_SYNAPSE_MOBILE.md)
2. **Jalur lewat LLM** — backup disuruh ke *agent* (model AI) via teks bebas,
   bukan perintah native langsung → lambat & bisa salah tafsir (Jebakan #79).
3. **Restore saat Synapse hidup** → **`state.db` RUSAK** (Jebakan #81).
   Saat ini `state.db` = **265 MB**, 161 sesi, 40.034 pesan, WAL 6 MB aktif.

### Lokasi tepat
```
lib/core/api/api_client.dart          -> perintahAgent(timeout default 180s)
lib/features/backup/backup_screen.dart:36   (_jalankan)
lib/features/backup/backup_screen.dart:93   (_konfirmasiRestore -> prompt ke agent)
```

### Rencana fix
1. **Naikkan timeout** operasi panjang → **≥ 600s** (atau tanpa batas selama
   koneksi hidup, pakai `chatStream().join()` seperti v1.2.2).
2. **Jangan lewat LLM** — jalankan perintah native langsung:
   ```
   "C:\Users\user\AppData\Local\synapse\bin\synapse.exe" backup -o "<file>.zip"
   ```
   Idealnya tambah **endpoint khusus** di `api_server.py`
   (mis. `POST /v1/backup` + `POST /v1/restore`) supaya cepat & andal.
3. **Restore WAJIB saat Synapse TIDAK AKTIF**:
   - Tampilkan peringatan: *"Gateway harus berhenti dulu"*
   - Urutan: backup pengaman → `synapse gateway stop` → swap `state.db`
     (hapus `-wal`/`-shm`) → verifikasi `integrity_check` → `gateway start`.
4. Tampilkan **progress** (bukan spinner tanpa kabar) + estimasi waktu.

**Risiko fix:** sedang (menyentuh data hidup) → **wajib izin user** sebelum uji restore.

---

## 🐛 BUG 3 & 4 — VTUBER TAK LOAD / JADI 2 (SATU RAKSASA)

### Akar masalah: **RACE CONDITION** memuat model
Dua jalur memuat model **hampir bersamaan**:

```
Jalur A: live2d_view.dart:81
  onPageFinished -> _panggil('gantiModel', modelId)

Jalur B: viewer.html:183
  window 'load' -> mulai() -> (juga memuat model)
```

**viewer.html:118-136** (`muatModel`):
```js
function muatModel(nama){
  if(model){                       // <-- kalau model masih null (belum selesai)
    app.stage.removeChild(model);  //     -> model LAMA TIDAK DIHAPUS
    model.destroy();
    model = null;
  }
  PIXI.live2d.Live2DModel.from(url, {...}).then(function(m){
    model = m;
    app.stage.addChild(model);     // <-- DITAMBAH LAGI -> 2 MODEL MENUMPUK
    aturModel();
  })
}
```

**Kenapa jadi 2 & salah satunya raksasa:**
- `Live2DModel.from()` = **async**. Dua panggilan beruntun → panggilan kedua
  masuk saat `model` masih `null` → tidak menghapus apa pun → `.then()` kedua
  `addChild` model baru di atas yang lama → **2 karakter**.
- `aturModel()` pada model yang **belum selesai dimuat** → `model.width/height`
  belum valid → skala melonjak → **"gede banget sampai cuma kaki"** (JEBAKAN #88).

**Kenapa "kadang tidak load":** tergantung siapa menang balapan.

### Rencana fix
```js
// viewer.html — guard urutan muat (token)
var _urutanMuat = 0;
function muatModel(nama){
  var urut = ++_urutanMuat;
  if(model){ try{app.stage.removeChild(model);}catch(e){}
             try{model.destroy();}catch(e){} model = null; }
  var url = AKAR + nama + '/' + nama + '.model3.json';
  PIXI.live2d.Live2DModel.from(url, { autoInteract:false }).then(function(m){
    if(urut !== _urutanMuat){ try{m.destroy();}catch(e){} return; } // <- buang hasil basi
    model = m; app.stage.addChild(model); aturModel(); sembunyi();
  }).catch(...)
}
```
Plus di Dart (`live2d_view.dart`): **tunggu `mulai()`/`load` selesai** dulu
(flag `_siap`) sebelum memanggil `gantiModel`, dan **hanya panggil sekali** saat
`onPageFinished` (jangan dobel dengan jalur `load`).

**Risiko fix:** sedang (JS + WebView). Perlu uji visual (screenshot).

---

## 🐛 BUG 5 — "Gagal: Exception: HTTP 404" DI TOOLS

### Ini BUKAN bug kode (penting!)
App meneruskan **error dari server**. **Sudah diuji langsung:**
```
GET http://127.0.0.1:8642/v1/toolsets  ->  HTTP 200  ✅ (sekarang sehat)
```
Jadi 404 muncul **kadang**, karena:
| Situasi | Penjelasan |
|---|---|
| HP tidak terhubung | kabel lepas / `adb reverse tcp:8642` mati → tak ada yang menjawab |
| Base URL salah | mis. base `.../v1` + path `/v1/toolsets` → `/v1/v1/toolsets` → 404 |
| Server Synapse lama | versi tanpa endpoint `/v1/toolsets` |
| Toggle toolset | perintah diteruskan ke agent → `synapse tools enable <nama>` → kalau nama salah → error CLI |

### Rencana fix (UX, bukan "menghilangkan 404")
1. **Pesan error spesifik**, jangan tampilkan mentah "Exception: HTTP 404":
   - tidak terhubung → *"Server Synapse tidak terjangkau. Cek kabel/WiFi + jalankan adb reverse."*
   - 404 → *"Endpoint tidak ada di server ini. Pastikan Synapse versi terbaru."*
   - 401/403 → *"API Key ditolak."*
2. **Tombol "Coba lagi"** + **auto-retry** 1x.
3. Tampilkan **status koneksi** di layar Tools.

**Risiko fix:** rendah.

---

## 🗄️ PERTANYAAN USER: "Data disimpan di mana? Ada backend?"

### ✅ ADA BACKEND — tapi **BUKAN Firebase/cloud**, melainkan **server Synapse di laptop**

```
┌───────────────────────┐   HTTP + adb reverse   ┌──────────────────────────────────┐
│  APK (HP)             │ ─────────────────────► │  BACKEND: Synapse api_server     │
│  com.nousresearch.    │      port 8642         │  (laptop user)                   │
│  synapse_mobile       │                        │  ├─ state.db (SQLite) 265 MB     │
│                       │                        │  │   sessions : 161 baris        │
│  LOKAL (di HP):       │                        │  │   messages : 40.034 baris     │
│  • SharedPreferences  │                        │  ├─ config.yaml, .env, SOUL.md   │
│    - daftar_sesi      │                        │  ├─ memories/, skills/, cron/    │
│    - mcp_custom       │                        │  └─ auth.json                    │
│    - skill_custom     │                        └──────────────────────────────────┘
│  • flutter_secure_storage (API key)
└───────────────────────┘
```

| Lapisan | Isi | Lokasi nyata |
|---|---|---|
| **Lokal di HP** | sesi chat, MCP/Skill custom, API key | `SharedPreferences` + secure storage |
| **Backend (laptop)** | **database sungguhan**, config, memori, skill, SOUL, riwayat | `C:\Users\user\AppData\Local\synapse\state.db` |

**Catatan penting & jujur:**
- **Konsep dosen BENAR** (apk wajib punya backend agar data tersimpan) — dan
  Synapse Mobile **sudah punya**.
- **Bedanya:** Firebase = **cloud** (data aman walau HP/laptop rusak).
  Backend Synapse = **lokal** → **kalau laptop mati, data hilang** kecuali di-backup.
- **Karena itu fitur Backup & Restore krusial** → dan itulah kenapa **bug #2
  harus diprioritaskan**.

**Kalimat siap pakai untuk dosen:**
> *"Aplikasi ini punya backend — server Synapse (Python) + database SQLite yang
> berjalan di PC, diakses HP lewat jaringan/ADB. Jadi data tersimpan di backend,
> bukan hanya di HP. Ada juga fitur backup penuh ke file .zip."*

---

## 📋 URUTAN FIX YANG DIUSULKAN

| Urutan | Bug | Alasan | Risiko |
|---|---|---|---|
| 1 | **Pin/Rename/Delete** | akar paling pasti, 3 baris | 🟢 rendah |
| 2 | **VTuber (3&4)** | paling dikeluhkan tester | 🟡 sedang |
| 3 | **Backup/Restore** | krusial (data bisa hilang) | 🟡 sedang |
| 4 | **HTTP 404 (pesan error)** | perbaikan UX | 🟢 rendah |

**Setelah fix → build APK v1.2.7 → uji di HP → tanya user "sudah sesuai?"**
(JANGAN rilis/push sebelum ACC user — ATURAN A0b.)

---

## ⚠️ CATATAN PROSES (WAJIB DIPATUHI)

```
1. BELUM ADA KODE YANG DIUBAH — file ini murni diagnosa.
2. Menunggu keputusan user: (a) mulai dari mana, (b) boleh pakai HP untuk uji?
3. ATURAN A0b: rilis HANYA setelah user bilang "sesuai".
4. ATURAN D: JANGAN sentuh app user selain Synapse; MINTA IZIN untuk operasi HP.
5. Backup dulu (_backup_sebelum_v127_*) sebelum mengubah kode.
6. Setelah selesai: catat jebakan baru ke ATURAN_KERJA_SYNAPSE_MOBILE.md.
```


---

# 🔴 TEMUAN AKHIR (29 Sep 2026) — AKAR BUG #2 & #5: BASE URL 9ROUTER

## Bukti terukur (uji langsung)

| Endpoint | **9router** (Base URL user) | **Synapse lokal (8642)** |
|---|---|---|
| `/v1/models` | ✅ 200 | ✅ 200 |
| `/v1/chat/completions` | ✅ ada | ✅ 200 |
| `/v1/toolsets` | ❌ **404** | ✅ 200 |
| `/v1/skills` | ❌ **404** | ✅ 200 |
| `/health` | ❌ 404 | ✅ 200 |

**Uji akses terminal (agent):**
```
Agent LOKAL (8642) -> "Perintah sudah dijalankan di terminal host.
                       Hasilnya: TEST_AGENT_LOKAL, Exit code 0"   ✅ PUNYA
9router            -> "saya berjalan di lingkungan sandbox Linux,
                       synapse.exe tidak ada"                     ❌ TIDAK
```

## Kesimpulan
**9router = ROUTER MODEL (proxy LLM)** — hanya melayani CHAT. Dia **bukan**
Synapse agent: **tidak punya toolset/skills, dan tidak bisa menjalankan
perintah di host**.

➡️ Karena itu **bug #2 (Backup) dan #5 (HTTP 404) punya akar yang SAMA**:
Base URL app menunjuk ke 9router.

| Fitur | Pakai 9router | Pakai Synapse lokal 8642 |
|---|---|---|
| Chat | ✅ jalan | ✅ jalan |
| VTuber (avatar + /v1/tts) | ✅ jalan | ✅ jalan |
| Tools / Skills / MCP | ❌ 404 | ✅ jalan |
| Backup / Restore | ❌ gagal (sandbox) | ✅ jalan |
| Akses Perangkat / Otonom | ❌ gagal | ✅ jalan |

## SOLUSI untuk user
```
Setelan -> Koneksi AI -> Base URL:
   http://127.0.0.1:8642/v1
lalu di PC:  adb reverse tcp:8642 tcp:8642
(9router tetap bisa dipakai KHUSUS untuk chat kalau mau)
```

## Yang SUDAH diperbaiki di app v1.2.7 (tetap berguna)
- Pesan 404 sekarang menjelaskan: *"Server ini TIDAK punya fitur agent…
  Base URL menunjuk ke ROUTER model, bukan Synapse agent"* + cara perbaiki.
- Pesan error timeout/koneksi/401 juga dibedakan.
