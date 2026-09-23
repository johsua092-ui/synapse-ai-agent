# CARA PAKAI — Peer Link

Panduan praktis. Baca ini setelah `docs/design/peer-link.md`.

---

## 0. Yang perlu kamu tahu dulu (jujur)

**Fitur ini MATI secara default.** Nol port terbuka, nol listener. Sampai kamu
menjalankan `synapse peerlink mode`, tidak ada apa pun yang mendengarkan.

**Belum ada transport jaringan.** Identitas, admission, karantina, dan
penamaan alamat sudah jalan dan teruji (130 tes). Tapi belum ada socket yang
benar-benar menerima koneksi dari instance lain — itu FASE berikutnya. Jadi
perintah di bawah ini **bisa dipakai sekarang** untuk menyiapkan identitas,
alamat, dan kebijakan; menyambungnya ke jaringan belum.

---

## 1. Alur lengkap: dua orang mau pair

### Di sisi kamu (instance A)

```bash
# 1. Lihat identitasmu (peer id ini boleh dibagikan bebas)
synapse peerlink identity
#   our peer id : pl1xkbc2p23vlooz4zunrxqwpzv6kz6galv

# 2. Lihat alamatmu (acak, stabil, tidak bisa ditebak dari peer id)
synapse peerlink endpoint
#   hostname : piug6mzzysaxygv9hmnenyjq4g.synz.zone.id

# 3. Buka pintu — hanya untuk yang punya kode undangan
synapse peerlink mode invite

# 4. Bikin kode undangan, kirim ke temanmu LEWAT JALUR LAIN
#    (WhatsApp, Telegram, tatap muka — bukan lewat Peer Link)
synapse peerlink invite --peer "Budi"
#   invite code : SCS9ZZSV

# 5. Temanmu mengetuk. Kamu lihat siapa yang menunggu.
synapse peerlink pending

# 6. KAMU yang memutuskan. AI tidak pernah auto-approve.
synapse peerlink approve pl1temanmu...
```

### Di sisi temanmu (instance B)

```bash
synapse peerlink identity      # dia lihat peer id-nya
synapse peerlink endpoint      # dia lihat alamatnya
# dia mengetuk alamatmu + kirim peer id + kode undangan
```

Lalu **kamu** menjalankan `approve`. Baru setelah itu dia dipercaya.

---

## 2. Jawaban: "bisa beda-beda subdomain, dan tidak ada yang tahu?"

**Bisa — dan sudah jalan.** Bukti nyata:

```
$ synapse peerlink endpoint
  hostname : piug6mzzysaxygv9hmnenyjq4g.synz.zone.id

$ synapse peerlink rotate
New address: dhhrxmcxnqqxmbs8ggygn33g9t.synz.zone.id
```

- Label **acak 26 karakter** dari 32 simbol → ~130 bit entropi. 50 instance
  diuji, **nol tabrakan**.
- Label **tidak diturunkan** dari peer id. Peer id kamu publik; label kamu
  tetap rahasia. Sudah ada tesnya (`test_unguessable_from_peer_id`).
- **Stabil**: di-mint sekali, disimpan, sama setelah restart.
- **`rotate`** mengganti alamat kapan saja.

### Tapi jujur: "tidak ada yang tahu" ada batasnya

DNS dan Certificate Transparency itu **publik**. Kalau seseorang menebak-nebak
nama, dia bisa menemukan alamatmu. Label acak membuat itu **mahal**, bukan
mustahil. Jadi:

> **Alamat acak = penambah biaya pencarian, BUKAN kunci.**

Yang benar-benar melindungi adalah: **E2EE** (isi percakapan tidak bisa dibaca
siapa pun di tengah) + **admission** (alamat ditemukan pun tetap tidak bisa
masuk tanpa kamu setujui). Jangan bergantung pada kerahasiaan alamat saja —
itu jebakan *security by obscurity*.

---

## 3. ⚠️ JEBAKAN BESAR: sertifikat TLS untuk `synz.zone.id`

Ini bisa bikin semuanya gagal, jadi gw tulis di depan.

**Wildcard TLS hanya menutup SATU tingkat label.**

| Yang kamu mau | Wildcard gratis nutup? |
|---|---|
| `abc.zone.id` | ✅ ya (`*.zone.id`) |
| `abc.synz.zone.id` | ❌ **tidak** (`*.zone.id` cuma satu tingkat) |

Kalau zone Cloudflare kamu adalah **`zone.id`**, maka
`blablabla.synz.zone.id` adalah subdomain **tingkat kedua** → sertifikat gratis
**tidak** menutupinya → koneksi gagal validasi TLS.

**Solusi (pilih satu):**

1. **Daftarkan `synz.zone.id` sebagai zone sendiri di Cloudflare** (gratis).
   Lalu wildcard `*.synz.zone.id` menutupi `blablabla.synz.zone.id`. ← rekomendasi
2. Pakai Advanced Certificate Manager (bayar) — bisa multi-tingkat.
3. Pakai `*.zone.id` langsung tanpa lapisan `synz` (`blablabla.zone.id`).

Cek sendiri setelah DNS jadi:

```bash
curl -svI https://<label>.synz.zone.id 2>&1 | grep -i 'subject\|SSL\|error'
```

Perintah `synapse peerlink endpoint` **sudah memperingatkan ini otomatis**
kalau base domain kamu lebih dari 2 label.

---

## 4. Setup Cloudflare Tunnel (setelah zone siap)

Ringkas — detailnya di dokumen Cloudflare.

```bash
# 1. Install cloudflared, login
cloudflared tunnel login

# 2. Buat tunnel
cloudflared tunnel create synapse-peerlink

# 3. Route wildcard: SEMUA subdomain -> satu tunnel
cloudflared tunnel route dns synapse-peerlink "*.synz.zone.id"

# 4. config.yml
#    tunnel: <id>
#    credentials-file: /root/.cloudflared/<id>.json
#    ingress:
#      - hostname: "*.synz.zone.id"
#        service: http://localhost:<port-peerlink>
#      - service: http_status:404

# 5. Jalan
cloudflared tunnel run synapse-peerlink
```

Wildcard DNS (`*.synz.zone.id`) berarti **kamu tidak perlu menambah record
tiap peer baru** — setiap instance cukup memilih label acaknya sendiri.

**Catatan keamanan:** Cloudflare **memutus TLS di edge-nya** — artinya
Cloudflare *bisa* melihat trafikmu. Ini persis kasus "TLS saja TIDAK cukup
kalau lewat perantara". Karena itu **E2EE lapisan aplikasi wajib**, dan itu
sudah tersedia (`cryptography` sudah ada, nol dependency baru).

---

## 5. Set base domain

Setting perilaku ada di `config.yaml`, bukan environment variable:

```yaml
peer_link:
  base_domain: synz.zone.id
```

Kalau tidak diisi, defaultnya `synz.zone.id`.

---

## 6. Referensi perintah

| Perintah | Fungsi |
|---|---|
| `synapse peerlink identity` | peer id kamu (boleh dibagikan) |
| `synapse peerlink endpoint` | alamat acak kamu (mint kalau belum ada) |
| `synapse peerlink endpoint --peek` | lihat saja, jangan mint |
| `synapse peerlink rotate` | ganti alamat (yang lama mati) |
| `synapse peerlink mode` | lihat mode |
| `synapse peerlink mode invite` | buka pintu (undangan saja) |
| `synapse peerlink invite --peer Budi` | bikin kode undangan |
| `synapse peerlink pending` | siapa yang menunggu keputusanmu |
| `synapse peerlink approve <peer_id>` | terima (keputusanmu) |
| `synapse peerlink block <peer_id>` | tolak permanen |
| `synapse peerlink list` | peer dipercaya + diblokir |
| `synapse peerlink status` | ringkasan |

Semua perintah menerima `--json` untuk scripting.

---

## 7. Mode

| Mode | Arti |
|---|---|
| `closed` | **default** — tidak ada yang bisa masuk |
| `invite` | hanya pemegang kode undangan |
| `public_gated` | siapa saja, wajib proof-of-work, lalu karantina |
| `public_open` | siapa saja (tidak disarankan) |

**Di semua mode, tidak ada yang otomatis dipercaya.** Peer baru selalu masuk
karantina sampai kamu `approve`.
