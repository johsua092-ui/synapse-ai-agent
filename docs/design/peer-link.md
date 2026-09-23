# DESAIN — Peer Link (Synapse)

Status: **DIIMPLEMENTASI di sandbox** (`feat/pending-user-request`). Belum di-push.
Dasar: `PROMPT_UPGRADE_SYNAPSE_PEER_LINK.txt` v1.0 + riset (`peer-link-riset.md`).

---

## 1. Pertanyaan inti: "orang random yang pengen pakai gimana?"

Jawaban singkat: **mereka tidak bisa asal pakai.** Itu memang disengaja, dan
sesuai prinsip dokumen: *USER selalu di loop — AI TIDAK PERNAH auto-approve.*

Ada empat mode, default **paling tertutup**:

| Mode | Siapa yang boleh mengetuk | Biaya penyerang |
|---|---|---|
| `closed` **(default)** | Tidak ada. Nol permukaan. | Tidak berlaku |
| `invite` | Hanya yang punya kode undangan valid | Harus dapat kode dulu |
| `public_gated` | Siapa saja, tapi wajib proof-of-work | CPU per identitas |
| `public_open` | Siapa saja (tidak disarankan) | Nol — hanya untuk uji coba |

**Tidak ada mode yang langsung memberi akses.** Bahkan di `public_gated`, peer
yang lolos hanya masuk **karantina** dan menunggu pemilik menekan
`peerlink approve`. Karantina bukan persetujuan.

## 2. Yang ditemukan di repo, dan diperbaiki

### Temuan: lockout di `gateway/pairing.py` adalah vektor DoS

```python
def _is_locked_out(self, platform: str):
    lockout_key = f"_loc...rm}"     # ← per PLATFORM, bukan per peer
```

Konsekuensinya (dibuktikan di `/root/work/BUKTI_DOS.py`):

```
1) Peer jujur minta kode          -> DAPAT KODE
2) Penyerang 5x kode salah        -> biaya: 1 perintah, ~0 detik
3) Status platform 'peerlink'     -> TERKUNCI
4) Peer jujur coba lagi           -> DITOLAK   ← korban yang tidak salah
```

**Aman untuk Telegram/WhatsApp** (chat privat, satu platform = satu percakapan).
**Bahaya kalau dibuka ke publik**: siapa pun bisa melumpuhkan penerimaan peer
baru selama 1 jam, gratis.

### Perbaikan: kunci lockout per identitas kriptografis

`gateway/peer_link/policy.py` menghitung kegagalan **per `peer_id`**, bukan per
platform. Hasil yang sama dijalankan ulang:

```
3) penyerang terkunci? True     korban terkunci? False
4) Peer jujur BARU masuk        -> allowed = True
```

### Perbaikan tambahan: identitas tidak lagi gratis

Proof-of-work mengikat biaya ke identitas (SHA-256 atas `public_key || nonce`):

| Bit | Waktu | Hash rata-rata |
|---|---|---|
| 12 | 0.1 ms | 4.096 |
| 16 | 27.9 ms | 65.536 |
| 18 | 332.5 ms | 262.144 |

Kesulitan **naik otomatis** saat banjir (jendela 60 detik), dibatasi 28 bit.
Ini menutup **serangan Sybil**: membuat 100.000 identitas palsu butuh ~7 miliar
hash, bukan gratis.

## 3. Keputusan desain penting

**Semua additive. Nol file lama diubah** — kecuali satu baris daftar di
`synapse_cli/main.py` (`_BUILTIN_SUBCOMMANDS`), yang wajib agar plugin
discovery tidak error.

`gateway/pairing.py` **tidak disentuh**, karena tes
`test_lockout_blocks_code_approval` mengunci perilaku per-platform untuk
Telegram/WhatsApp. Mengubahnya akan merusak fitur yang sudah jalan.

**Verifikasi kode undangan dibuat read-only** (`gateway/peer_link/invite.py`).
`PairingStore.approve_code` sengaja **tidak** dipakai di jalur publik karena:
1. ia **mengubah state** (menghapus kode + menulis ke allowlist platform), dan
2. ia **tunduk pada lockout per-platform** — persis vektor DoS di atas.

Verifikasi read-only membaca file, membandingkan dengan `hmac.compare_digest`,
dan **tidak menulis apa pun**. Terbukti: 20 kode salah tidak mengunci platform.

**Nol dependency baru.** `cryptography 50.0.1` sudah ada di `pyproject.toml:96`
(Ed25519, X25519, ChaCha20Poly1305, HKDF semua tersedia).

## 4. Berkas

| Berkas | Baris | Isi |
|---|---|---|
| `gateway/peer_link/identity.py` | 222 | Identitas Ed25519, peer id `pl1…`, sign/verify |
| `gateway/peer_link/policy.py` | 496 | Admission: mode, PoW, rate limit, lockout per-peer, karantina |
| `gateway/peer_link/invite.py` | 155 | Verifikasi kode undangan read-only |
| `gateway/peer_link/__init__.py` | 42 | Ekspor paket |
| `synapse_cli/subcommands/peerlink.py` | 366 | CLI `synapse peerlink` |
| `tests/gateway/test_peer_link_identity.py` | 164 | 25 tes |
| `tests/gateway/test_peer_link_policy.py` | 399 | 38 tes (termasuk regresi DoS) |
| `tests/gateway/test_peer_link_invite.py` | 168 | 16 tes (termasuk read-only) |

**Total 79 tes, 0 gagal.**

## 5. Yang BELUM dibangun (jujur)

Ini penting supaya tidak ada klaim berlebih:

- **Transport jaringan belum ada.** Belum ada socket/HTTP yang benar-benar
  menerima koneksi dari instance lain. Fondasinya (identitas, admission,
  karantina) sudah ada dan teruji, tapi belum tersambung ke jaringan.
- **Sinkronisasi data (FASE 3–4) belum ada.** Barter skill/pengalaman belum
  diimplementasi.
- **E2EE antar-peer belum ada.** `cryptography` sudah tersedia, tapi jalur
  handshake-nya belum ditulis.
- **Integrasi gateway belum ada.** Belum ada endpoint di `api_server.py`.

Transport yang direkomendasikan: **Cloudflare Named Tunnel + domain** (user
punya domain) + **E2EE aplikasi**, karena Cloudflare memutus TLS di edge.

## 6. Cara pakai (yang sudah bisa)

```bash
synapse peerlink status                 # mode + jumlah peer
synapse peerlink identity               # peer id kita (bagikan ini)
synapse peerlink mode invite            # buka pintu, undangan saja
synapse peerlink invite --peer budi     # bikin kode, kirim di luar jalur
synapse peerlink pending                # siapa yang menunggu
synapse peerlink approve pl1abc...      # pemilik yang memutuskan
synapse peerlink block pl1abc...        # tolak permanen
```
