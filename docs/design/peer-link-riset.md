# RISET_PEER_LINK.md

Riset untuk fitur **Peer Link** — menghubungkan 2 instance Synapse antar pengguna.
Dibuat: hasil verifikasi dokumen `PROMPT_UPGRADE_SYNAPSE_PEER_LINK.txt` (v1.0 FINAL)
terhadap repo nyata di commit `f648a783`.

---

## 0. VERIFIKASI VERSI (BAGIAN 0.5 dokumen)

| Item | Nilai |
|---|---|
| `pyproject.toml` version | **0.20.5** |
| Git HEAD | `f648a783` |
| Dokumen disusun dari | v0.20.5 |

**KESIMPULAN: versi SAMA PERSIS dengan acuan dokumen. Tidak perlu `synapse update`.**

### Tabel fondasi — klaim dokumen vs realita (DIUKUR, bukan ditebak)

| File | Klaim dokumen | Realita | Cocok |
|---|---|---|---|
| `gateway/relay/__init__.py` | 44 KB | 43.4 KB / 967 baris | ✅ |
| `gateway/relay/descriptor.py` | CapabilityDescriptor | 9.5 KB / 193 baris | ✅ |
| `gateway/relay/transport.py` | interface | 6.7 KB / 143 baris | ✅ |
| `gateway/relay/ws_transport.py` | 55 KB | 54.9 KB / 1071 baris | ✅ |
| `gateway/relay/auth.py` | auth | 6.5 KB / 168 baris | ✅ |
| `gateway/relay/adapter.py` | 156/159 KB | 156.0 KB / 3266 baris | ✅ |
| `tools/skills_sync.py` | manifest | 58.5 KB / 1437 baris | ✅ |
| `tools/skills_sync_client.py` | 2187 baris | **2187 baris persis** | ✅ |
| `synapse_cli/subcommands/sync.py` | CLI sync | 4.1 KB / 99 baris | ✅ |
| `synapse_cli/pairing.py` | 120 baris | **120 baris persis** | ✅ |
| `synapse_cli/portal_cli.py` | 246 baris | **246 baris persis** | ✅ |
| `docs/relay-connector-contract.md` | 49/50 KB | 49.0 KB / 781 baris | ✅ |
| `synapse_cli/subcommands/peer.py` | 342 baris | **342 baris persis** | ✅ |

➜ **Dokumen akurat. Semua fondasi ADA. 0 file yang hilang.**

---

## 1. APA YANG SUDAH ADA (bisa dipakai ulang)

### 1.1 `synapse peer` — ADA, tapi LEBIH PRIMITIF dari kesan dokumen

File: `synapse_cli/subcommands/peer.py` (342 baris). Isi nyata:

```
synapse peer add <nama> --url <url> --key <KEY> [--note]
synapse peer list / remove
synapse peer dm <peer>[/<profil>] "pesan" [--json]
```

**Arsitektur nyata (dibaca dari kode, bukan dari deskripsi):**
- Transport = **HTTP POST biasa** ke peer's `api_server`. BUKAN WebSocket, BUKAN relay.
- Auth = **shared API key**, header `Authorization: Bearer <API_SERVER_KEY>`.
- Peer registry = `config.yaml` → `bot_peers` (dict: name → {url, note}).
- Key storage = `<SYNAPSE_HOME>/.env` → `SYNAPSE_PEER_<NAME>_KEY`
  (via `save_env_value`; dibaca via `agent.secret_scope.get_secret` dengan fallback `os.environ`).
- Alur `dm`: resolve remote "Bot Chat" session (by title, `include_hidden=1`,
  create kalau belum ada) → `POST /api/sessions/{id}/chat` → cetak reply.
- Timeout: `DM_TIMEOUT_S = 600` (1 turn agent bisa lama), `LIST_TIMEOUT_S = 30`.
- Exit code: 0 ok, 1 delivery/peer error, 2 usage error.

**⚠️ YANG TIDAK ADA di `peer.py` (dan ini penting):**
- ❌ NOL kriptografi — tidak ada Ed25519, tidak ada tanda tangan, tidak ada X25519
- ❌ NOL E2EE — tidak ada enkripsi aplikasi
- ❌ NOL mTLS — hanya Bearer token
- ❌ NOL state machine — tidak ada `pending/mutual/linked/blocked`
- ❌ NOL approval 2 pihak — tidak ada request/accept/reject
- ❌ NOL audit log
- ❌ NOL rate limit
- ❌ NOL anti-replay (tidak ada nonce/timestamp)

➜ **Ini bukan "80% sudah ada".** Yang ada adalah **pola akses transport**
(cara manggil endpoint, resolve sesi, simpan peer) — berguna sebagai
**contoh gaya kode**, tapi **mesin Peer Link harus dibangun**.

### 1.2 `gateway/relay/` — fondasi LEBIH MATANG (dokumen salah menempatkan ini sebagai "alternatif")

Ini justru punya hampir semua yang dibutuhkan BAGIAN 5:
- `handshake()` di `ws_transport.py` — negosiasi
- `CapabilityDescriptor` di `descriptor.py` — negosiasi kemampuan
- `auth.py` — autentikasi relay (6.5 KB)
- `docs/relay-connector-contract.md` — **kontrak formal v1, 781 baris**
- Status: **EXPERIMENTAL**, contract version = 1
- Aktivasi: env `GATEWAY_RELAY_URL` atau `gateway.relay_url` di config.yaml
- Alur: gateway DIAL OUT ke connector → `handshake()` → terima
  `CapabilityDescriptor` → tukar `MessageEvent` + actions via WebSocket per-turn
- Gateway TIDAK tahu platform di depannya — connector pegang logika platform

➜ **Untuk keamanan Peer Link, `gateway/relay/` adalah acuan arsitektur yang
lebih tepat daripada `peer.py`.** Dokumen menyebutnya "alternatif" — itu
menyesatkan. Yang benar: relay = fondasi transport ber-handshake;
`peer.py` = contoh CLI + pemanggilan api_server.

### 1.3 `tools/skills_sync.py` + `skills_sync_client.py` — pola sinkronisasi

- Manifest format **v2**: `"skill_name:origin_hash"` (MD5)
- **Logic konflik SUDAH ADA**: user ubah skill lokal → **SKIP** (hormati kustomisasi)
- Konsep **"Personal sync"** (antar device sendiri) vs **"Organisation sync"**
  (antar anggota tim)
- `sync_org_auto_propose()` — edit skill org jadi "proposal" dulu
- `FileSyncManager` di `tools/environments/file_sync.py`

➜ **Peer Link = tingkat KETIGA: antar-individu.** Pola `auto_propose` =
langsung cocok untuk "barter skill" (kirim sebagai usulan, bukan paksa).

### 1.4 `synapse_cli/pairing.py` — pola approval

- `PairingStore` di `gateway/pairing.py`
- Alur: user minta akses → dapat code → admin approve
- `list / approve / revoke / clear-pending`
- **Ada rate limit + lockout SUDAH TERIMPLEMENTASI** (lihat `_is_locked_out`,
  `_rate_limit_path()`, lockout message) — bisa jadi acuan pola rate limit
- `looks_like_request_id()` — bedakan request-id vs code

➜ Pola ini persis "aktivasi 2 pihak" yang diminta FASE 2.

### 1.5 `synapse_cli/portal_cli.py` — ⚠️ KONFLIK NAMA

`/portal` **TERPAKAI** untuk Nous Portal (OAuth login, pilih model, Tool Gateway).
Subcommand: `login`, `info`, `open`, `tools`. **JANGAN ditimpa.**

---

## 2. APA YANG KURANG (harus dibangun)

Semua ini BELUM ADA sama sekali:

| Komponen | Status | Catatan |
|---|---|---|
| `gateway/peer/` | **BELUM ADA** | aman dibuat (verified) |
| `synapse_cli/peer_cmds.py` | **BELUM ADA** | aman dibuat (verified) |
| Identitas peer (Ed25519/X25519) | **BELUM ADA** | — |
| E2EE (ChaCha20-Poly1305) | **BELUM ADA** | — |
| mTLS | **BELUM ADA** | — |
| State machine (NONE→PENDING→MUTUAL→LINKED) | **BELUM ADA** | — |
| Join request + accept/reject | **BELUM ADA** | — |
| Anti-replay (nonce+timestamp) | **BELUM ADA** | — |
| Scanner kredensial | **BELUM ADA** | — |
| Karantina data masuk | **BELUM ADA** | — |
| Audit log peer | **BELUM ADA** | — |
| Barter | **BELUM ADA** | — |
| Rate limit peer | **BELUM ADA** | pola ada di pairing.py |

---

## 3. BAGIAN YANG BERISIKO KONFLIK

| Risiko | Detail | Mitigasi |
|---|---|---|
| **`/portal` terpakai** | Nous Portal, `portal_cli.py` | pakai nama lain |
| **`synapse peer` terpakai** | 342 baris, sudah jalan | **PERLUAS**, jangan timpa |
| **`peer add` signature bentrok** | existing: `add <nama> --url --key`<br>dokumen FASE 2 mau: `add <peer-id>` | pakai subcommand BEDA (mis. `peer link <id>`) |
| **`peer list` signature bentrok** | existing: list peer DM (config bot_peers) | jangan overload; pakai `peer status` |
| **`gateway/peer/` vs `gateway/relay/`** | relay sudah ada & matang | JANGAN duplikasi transport — reuse pola relay |
| **CRLF** | file Windows = CRLF | jaga line ending saat tulis config/state |
| **Circular import** | subcommand inject handler | tiru pola `sync.py` / `pairing.py` |

### Nama command — hasil cek nyata

```
Subcommand yang ADA (44): _shared acp approvals auth backup claw config console
  cron dashboard debug doctor dump gateway gui hooks import_agent import_cmd
  insights login logout logs mcp memory model monitoring pairing pause peer
  plugins profile prompt_size security setup skills skin slack status sync
  tools uninstall update verify webhook whatsapp

File synapse_cli/: portal_cli.py  (peer.py ada di subcommands/)

Nama BARU yang masih BEBAS: peerlink, link, federate, synapse-link  ✅
```

---

## 4. RISIKO TEKNIS YANG BELUM DIJAWAB DOKUMEN

Ini temuan gw yang dokumen lu belum bahas:

1. **`peer.py` tidak punya abstraksi transport.** Semua HTTP call inline di
   `_request()`. Untuk "pluggable transport" (FASE 4), perlu interface baru —
   nggak bisa sekadar nambah subcommand.
2. **`peer add` nyimpen URL mentah di config.yaml.** Peer Link butuh
   menyimpan kunci publik, status, trust level — itu butuh store baru
   (`peers.db`), bukan `bot_peers` dict.
3. **Nggak ada tempat naruh key pair.** `peer.py` cuma nyimpen shared secret
   di `.env`. Peer Link butuh file identity 0600 — folder
   `<SYNAPSE_HOME>/peer/` **belum ada**.
4. **`api_server.py` = 8552 baris / 383 KB.** Kalau Peer Link mau nambah
   endpoint di situ, risikonya besar. Cek dulu apakah bisa reuse endpoint
   `/api/sessions/*` yang ada.

---

## 6. TRANSPORT GRATIS — RISET TAMBAHAN (user minta opsi lain di luar 9 dokumen)

User: "gada cara lain? Cari dulu yang lain + free". Hasil riset:

### ⭐⭐ TEMUAN TERPENTING: E2EE TIDAK BUTUH DEPENDENCY BARU

Diverifikasi langsung di venv (bukan asumsi):

```
cryptography version: 50.0.1   <- SUDAH jadi dependency (pyproject.toml:96)
Ed25519          : OK  -> identitas/tanda tangan peer (FASE 1)
X25519           : OK  -> key exchange (BAGIAN 5)
ChaCha20Poly1305 : OK  -> E2EE payload (BAGIAN 5)
HKDF             : OK  -> derivasi kunci sesi
```

➜ **Seluruh primitif kripto BAGIAN 5 SUDAH TERSEDIA.** Nol dependency baru
untuk lapisan keamanan. Ini menghapus risiko terbesar (nambah dep baru =
ditolak reviewer / nambah CVE surface).

### ⭐ TEMUAN BARU #1: `iroh` — paling cocok, karena bisa DITANAM ke Python

Diverifikasi di PyPI:
- **Package `iroh` v1.1.0**, `Python >=3.7`
- Wheels tersedia: `x86_64 manylinux 2_28`, `aarch64 manylinux 2_28`,
  `amd64 win`, `arm64 macosx`
- Bindings resmi via uniffi-rs (dari `n0-computer/iroh-ffi`)
- Rust core: QUIC + NAT hole punching + relay fallback
- **"Dial by public key"** — identitas = kunci publik, bukan IP
  → INI PERSIS konsep "Peer ID" di FASE 1 dokumen
- Enkripsi QUIC (TLS 1.3) bawaan → memenuhi syarat E2EE BAGIAN 5
- Gratis, open source, tanpa akun, tanpa server sendiri
- Download: ~9k/bulan (bukan paket mati)

**Kenapa ini menang:** dokumen lu minta "pluggable transport" (FASE 4) +
E2EE (BAGIAN 5) + Peer ID dari fingerprint kunci (FASE 1). `iroh` memberi
ketiganya dalam satu library yang bisa di-embed. Tailscale/Cloudflare/frp
semuanya butuh daemon eksternal + konfigurasi terpisah.

⚠️ Catatan: relay publik iroh = perantara. Tapi payload sudah terenkripsi
end-to-end (QUIC), jadi perantara buta terhadap isi → sesuai syarat dokumen.
Untuk kontrol penuh, relay iroh bisa di-self-host.

### ⭐ TEMUAN BARU #2: Oracle Cloud Always Free — VPS GRATIS PERMANEN

- **Genuinely free forever** (bukan trial 12 bulan), gratis seumur akun
- Spesifikasi: **2 OCPU / 12 GB RAM ARM** (turun dari 4/24 pada Jun 2026;
  akun baru kabarnya masih dapat 4/24)
- Cukup banget buat host relay sendiri 24/7
- Risiko: proses signup ketat, kadang kartu ditolak, kapasitas ARM sering habis

➜ Kalau user mau relay sendiri tanpa bayar: ini jalannya.

### TEMUAN BARU #3: Yggdrasil — mesh IPv6 tanpa server pusat

- Routing terdesentralisasi, tiap node = router
- **E2EE bawaan** ("cannot be decrypted by intermediate nodes")
- IPv6 stabil dari kriptografi identitas
- Tembus NAT (peering dua arah)
- Gratis, open source
- ⚠️ Status **alpha**, belum diaudit eksternal, jaringan PUBLIK
  (node lain bisa routable ke mesin lu → wajib firewall)

### TEMUAN BARU #4: Cloudflare Quick Tunnel — gratis tanpa domain

- `cloudflared` tunnel, **tanpa akun, tanpa domain** untuk quick mode
- ⚠️ URL acak + resmi dinyatakan "testing and development only"
- Named tunnel (URL tetap) tetap butuh domain
- Unlimited traffic, gratis

### TEMUAN BARU #5: bore.pub / tinyfi.sh / pinggy — TCP tunnel tanpa signup

- `bore` — TCP tunnel, MIT, bisa self-host, zero config
- `tinyfi.sh` — `ssh -R 80:localhost:3000 tinyfi.sh`
- `pinggy` — free URL persist 7 hari
- Cocok buat **testing cepat**, bukan produksi

### Koreksi kecil dari dokumen
- ZeroTier free tier = **10 device** (dokumen bilang 10 device, 1 network — benar)
- Tailscale free = **3 user / 100 device** (dokumen bilang 6 user — cek ulang)

### TABEL PERBANDINGAN (yang gratis)

| Opsi | Butuh VPS? | Butuh akun? | Bisa ditanam ke Python? | E2EE | Cocok Peer Link |
|---|---|---|---|---|---|
| **iroh** | ❌ | ❌ | ✅ **PyPI, embed** | ✅ QUIC | ⭐⭐⭐⭐⭐ |
| Tailscale | ❌ | ✅ | ❌ (daemon) | ✅ WireGuard | ⭐⭐⭐⭐ |
| Cloudflare Tunnel | ❌ | ✅ (named) | ❌ (daemon) | ⚠️ TLS berakhir di CF | ⭐⭐⭐ |
| Oracle Always Free | ✅ gratis | ✅ | ❌ | ⚠️ perlu tambahan | ⭐⭐⭐⭐ (relay sendiri) |
| Yggdrasil | ❌ | ❌ | ❌ (daemon) | ✅ | ⭐⭐⭐ (alpha) |
| bore / tinyfi / pinggy | ❌ | ❌ | ❌ | ⚠️ | ⭐⭐ (testing saja) |
| WireGuard VPS | ✅ bayar | ✅ | ❌ | ✅ | ⭐⭐⭐⭐ |
| Direct LAN | ❌ | ❌ | ❌ | ❌ perlu TLS | ⭐⭐ |

### REKOMENDASI
**Utama: `iroh` (embed).** Alasan:
1. Satu library memenuhi Peer ID + transport + E2EE — tidak ada daemon terpisah
2. Tanpa akun, tanpa VPS, tanpa biaya
3. "Dial by public key" = natural match untuk FASE 1
4. Ada fallback relay → tembus NAT tanpa port terbuka

**Cadangan: Tailscale** (paling mudah kalau iroh bermasalah) atau
**Oracle Always Free + relay sendiri** (kalau mau kontrol penuh tanpa bayar).

➜ KEPUTUSAN TRANSPORT = MILIK USER. Belum diputuskan.

---

### BATCH 2 — user minta "yang lain" (di luar batch 1)

#### ⭐⭐⭐ `libp2p` (py-libp2p) — PURE PYTHON, paling bersih dari sisi repo
- **PyPI `libp2p` v0.7.0**, `Python >=3.10,<4.0` — venv gw 3.11 ✅
- Lisensi **MIT AND Apache-2.0**
- **Implementasi murni Python** → TIDAK perlu wheel binary, TIDAK perlu Rust/Go
- Stack libp2p = standar industri P2P (dipakai IPFS): peer ID dari kunci,
  DHT discovery, hole punching, multiplexing, Noise/TLS
- ⚠️ Status: **"under development"** (belum 1.0) — perlu dinilai risikonya
- ⚠️ Menarik dependency graph lebih besar dari iroh

**vs iroh:** libp2p = pure Python (ramah reviewer, tanpa binary), tapi
belum stabil. iroh = binary wheel (Rust), tapi 1.0 stabil & API kecil.
➜ Dua-duanya bisa di-embed. Trade-off: kematangan vs kemurnian.

#### ⭐⭐⭐ `Nebula` (slackhq) — overlay matang, 17.5k bintang
- **MIT**, Go, 17.5k stars, dibuat Slack untuk produksi
- **Mutually authenticated P2P**, berbasis **Noise Protocol Framework**
- Sertifikat menegaskan IP + nama + grup node
- **Lighthouse** = node discovery + **UDP hole punching**
- ECDH key exchange + **AES-256-GCM** default
- Linux/macOS/Windows/iOS/Android
- ⚠️ Butuh 1 lighthouse (bisa di VPS gratis Oracle) — atau lighthouse publik

#### ⭐⭐ `Headscale` — Tailscale self-hosted, gratis penuh
- Implementasi open source dari Tailscale control server (`juanfont/headscale`)
- **Kontrol penuh tanpa bayar** — tidak perlu akun Tailscale
- Klien tetap `tailscale` (stabil, matang)
- ⚠️ Butuh VPS buat control server (Oracle Always Free cukup)

#### ⭐⭐ `zrok` — zero-trust tunnel, free tier nyata
- Open source (OpenZiti/NetFoundry), bisa SaaS atau **self-host**
- **Free tier: $0/bln — 5 GB/hari, 25 environment, 50 share backend**
- Tanpa kartu kredit
- Tembus firewall/NAT tanpa buka port
- ⚠️ Free tier = SaaS mereka (ada batas harian); self-host = butuh VPS
- ⚠️ Cocok untuk berbagi resource, bukan ideal untuk sync terus-menerus

#### ⭐⭐ `Pangolin` — WireGuard + identity-aware reverse proxy
- `fosrl/pangolin`, open source
- VPN identity-based + tunneled reverse proxy, berbasis WireGuard
- Dirancang untuk "AI agents and infrastructure" (relevan!)
- ⚠️ Butuh VPS untuk host Pangolin

#### ⭐ `chisel` / `rathole` / `frp` / `sish` — reverse tunnel klasik
- `chisel` — TCP/UDP tunnel via HTTP, diamankan SSH, single binary, Go
- `rathole` — Rust, ringan, alternatif frp/ngrok
- `frp` — paling populer, matang
- `sish` — SSH tunnel, bisa publik
- ⚠️ Semua butuh **VPS** sebagai server tunnel

#### ⭐ `OpenZiti` — zero-trust overlay (fondasi di balik zrok)
- Overlay zero-trust penuh, app-embedded atau tunnel
- Berat; zrok = versi praktisnya

### INSIGHT: repo lu SUDAH punya separuh jawabannya

Diverifikasi:
```
pyproject.toml:111  websockets==15.0.1     <- SUDAH ada
gateway/relay/                             <- SUDAH ada, 8 modul
  ws_transport.py   56 KB / 1071 baris     <- WebSocket + handshake
  auth.py            6.6 KB                <- autentikasi relay
  descriptor.py      9.7 KB                <- CapabilityDescriptor
  adapter.py       156 KB / 3266 baris     <- adapter
docs/relay-connector-contract.md  781 baris <- KONTRAK FORMAL v1
```

➜ **Opsi paling hemat (Footprint Ladder):** pakai `gateway/relay/` yang sudah
ada + satu endpoint. Relay ini sudah punya handshake, auth, descriptor,
dan kontrak formal. Yang kurang cuma **cara dua instance saling menemukan**.

➜ Artinya: transport bisa jadi **lapisan pluggable** (sesuai FASE 4 dokumen),
dengan relay sebagai implementasi pertama. iroh/libp2p/Nebula jadi
implementasi alternatif TANPA mengubah inti.

### TABEL BATCH 2

| Opsi | Bahasa | Embed ke Python? | Butuh VPS? | Butuh akun? | Kematangan | Skor |
|---|---|---|---|---|---|---|
| **libp2p** | **Pure Python** | ✅ pip | ❌ | ❌ | ⚠️ pre-1.0 | ⭐⭐⭐⭐ |
| **Nebula** | Go | ❌ daemon | ⚠️ lighthouse | ❌ | ✅ produksi | ⭐⭐⭐⭐ |
| **Headscale** | Go | ❌ | ✅ wajib | ❌ | ✅ | ⭐⭐⭐ |
| **zrok** | Go | ❌ | ⚠️ kalau self-host | ✅ | ✅ | ⭐⭐⭐ |
| **Pangolin** | Go | ❌ | ✅ wajib | ❌ | ✅ | ⭐⭐⭐ |
| **chisel/frp/rathole** | Go/Rust | ❌ | ✅ wajib | ❌ | ✅ | ⭐⭐ |
| **OpenZiti** | Go | ⚠️ SDK ada | ✅ | ✅ | ✅ | ⭐⭐ |

### REKOMENDASI FINAL (gabungan batch 1 + 2)

1. **`libp2p`** — kalau prioritasnya *repo bersih* (pure Python, tanpa binary)
2. **`iroh`** — kalau prioritasnya *stabil & API kecil* (wheel Rust)
3. **`Nebula`** — kalau mau overlay matang + lighthouse sendiri (VPS Oracle gratis)
4. **Reuse `gateway/relay/`** — paling hemat per Footprint Ladder, tapi
   belum menyelesaikan penemuan peer

➜ **Arsitektur yang gw sarankan:** buat transport **pluggable** (FASE 4),
implementasi pertama = `gateway/relay/` yang sudah ada, lalu tambah
backend `iroh` ATAU `libp2p` sebagai opsi. Dengan begitu keputusan ini
TIDAK mengunci lu — bisa ganti nanti tanpa bongkar inti.

➜ KEPUTUSAN TRANSPORT = MILIK USER. Belum diputuskan.

---

### BATCH 3 — USER PUNYA DOMAIN (mengubah kalkulasi)

User: "Gw ada domain sih". Diverifikasi dampaknya:

#### ⭐⭐⭐⭐ Cloudflare Named Tunnel + domain sendiri — INI YANG PALING COCOK

- `cloudflared` tunnel + **domain sendiri** → **URL tetap** (bukan acak)
- **Gratis**, tanpa VPS, tanpa kartu kredit
- Cloudflare Zero Trust: **"$0 forever"** untuk tim <50 user
- Tanpa buka port di router, tembus CGNAT
- Dukungan apex domain + CNAME via Named Tunnel
- Auto-HTTPS

⚠️ **CATATAN KEAMANAN PENTING:** Cloudflare **memutus TLS** di edge mereka
→ Cloudflare bisa melihat traffic. **TAPI** dokumen lu sendiri sudah
mewajibkan: *"TLS saja TIDAK cukup kalau lewat perantara; wajib enkripsi
end-to-end"*. Jadi ini bukan blocker — ini **persis skenario yang dokumen
lu antisipasi**. Solusinya sudah ada di tangan: E2EE lapisan aplikasi
(Ed25519 + X25519 + ChaCha20-Poly1305, **sudah terverifikasi tersedia**).

➜ Dengan E2EE di atas tunnel, Cloudflare jadi buta terhadap isi payload.
   Ini memenuhi syarat BAGIAN 5 secara literal.

#### ⭐⭐⭐ Oracle Always Free VPS + domain + Caddy/Let's Encrypt

- VPS gratis permanen (2 OCPU / 12 GB ARM)
- Domain sendiri + **Certbot/Caddy** → HTTPS otomatis, gratis
- **Tidak ada pihak ketiga** di jalur data → kontrol penuh
- ⚠️ Oracle minta **kartu kredit untuk verifikasi** (tidak ditagih)
- ⚠️ Signup ketat, kapasitas ARM sering habis
- Cocok kalau user mau relay sendiri tanpa perantara sama sekali

#### ⭐⭐ Tailscale Funnel + domain

- Funnel memberi HTTPS publik, tapi hostname = `<mesin>.<tailnet>.ts.net`
- **Domain sendiri TIDAK didukung** untuk Funnel
- ➜ Domain user jadi kurang berguna di jalur ini

### KESIMPULAN: DOMAIN MEMBUKA JALUR TERBAIK

Dengan domain, urutan rekomendasi berubah:

| Opsi | Gratis | Butuh VPS | Butuh kartu | URL tetap | Pihak ketiga lihat traffic |
|---|---|---|---|---|---|
| **CF Named Tunnel + domain** | ✅ | ❌ | ❌ | ✅ | ⚠️ ya (di-mitigasi E2EE) |
| **Oracle Free + domain + Caddy** | ✅ | ✅ gratis | ⚠️ verifikasi | ✅ | ❌ tidak |
| Tailscale Funnel | ✅ | ❌ | ❌ | ⚠️ domain .ts.net | ❌ |
| Direct + port forward | ✅ | ❌ | ❌ | ✅ | ❌ (tapi butuh IP publik) |

### REKOMENDASI FINAL (setelah tahu ada domain)

**Utama: Cloudflare Named Tunnel + domain user + E2EE lapisan aplikasi.**
Alasan: gratis, tanpa VPS, tanpa kartu, URL tetap, dan E2EE yang diwajibkan
dokumen sudah tersedia tanpa dependency baru → memenuhi BAGIAN 5.

**Alternatif: Oracle Always Free + domain + Caddy** kalau user tidak mau
ada pihak ketiga di jalur data sama sekali.

➜ Arsitektur tetap dibuat **pluggable** (FASE 4) supaya pilihan ini bisa
diganti tanpa bongkar inti. Transport hanyalah salah satu implementasi.

➜ **Status: MENUNGGU konfirmasi user untuk mulai koding.**

---

## 5. KESIMPULAN RISET

1. ✅ Versi cocok (0.20.5), semua fondasi ada, tidak perlu update
2. ⚠️ `synapse peer` ADA tapi primitif — "80% sudah ada" itu **terlalu optimistis**
   untuk sisi keamanan; yang ada adalah pola, bukan mesin
3. ⭐ `gateway/relay/` lebih matang dan lebih relevan sebagai acuan arsitektur
4. ✅ `skills_sync` + `pairing` = pola siap pakai untuk sync & approval
5. ✅ Nama `peerlink` / `link` / `federate` masih bebas
6. ❌ NOL komponen keamanan (kripto/E2EE/mTLS/anti-replay/karantina) yang ada

**TIDAK BOLEH mulai koding sebelum 10 pertanyaan BAGIAN 11 dijawab user.**
