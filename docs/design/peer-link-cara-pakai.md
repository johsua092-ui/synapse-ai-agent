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
#   hostname : piug6mzzysaxygv9hmnenyjq4g.aikernel.qzz.io

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
  hostname : piug6mzzysaxygv9hmnenyjq4g.aikernel.qzz.io

$ synapse peerlink rotate
New address: dhhrxmcxnqqxmbs8ggygn33g9t.aikernel.qzz.io
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

## 3. ⚠️ JEBAKAN TLS — dan cara keluar buat `synz.zone.id`

Ini bagian yang paling gampang salah, jadi gw tulis di depan. **Gw sendiri
sempat salah di sini**, jadi gw jelaskan aturan yang benar.

### Aturannya: wildcard diukur dari *apex zone*, bukan dari jumlah titik

Sertifikat wildcard `*.X` menutup **satu tingkat tepat di bawah `X`** — dan `X`
harus **apex zone** (nama yang NS-nya punya kamu), bukan sembarang hostname.

| Hostname | Zone apex | Wildcard gratis nutup? |
|---|---|---|
| `abc.aikernel.qzz.io` | `aikernel.qzz.io` | ✅ ya |
| `abc.zone.id` | `zone.id` | ✅ ya |
| `abc.synz.zone.id` | `zone.id` | ❌ **tidak** |

Perhatikan: `aikernel.qzz.io` punya **3 label** tapi **✅ jalan**, sedangkan
`synz.zone.id` juga **3 label** tapi **❌ gagal**. Jadi **menghitung jumlah titik
itu menyesatkan** — yang menentukan adalah: *nama itu apex zone, atau hostname
di dalam zone orang lain?*

**Kasus kamu (sudah gw ukur pakai DNS, bukan tebakan):**

```
$ dig +short NS synz.zone.id
dns.webkus.com.                    # <- NS milik orang lain, bukan punya kamu
$ dig +short A synz.zone.id
dns.webkus.com. 216.176.239.254    # <- ini CNAME ke hosting bersama
```

→ `synz.zone.id` **bukan zona**, cuma hostname di dalam `zone.id` (NS-nya
`alidns.com`). Jadi `blablabla.synz.zone.id` **tidak akan** dapat sertifikat
gratis. **Tidak ada cara "daftarkan synz.zone.id sebagai zone"** — kamu bukan
pemilik `zone.id`, jadi kamu tidak bisa menambah record NS untuk mendelegasikan
`synz` ke Cloudflare.

### Solusinya: pakai domain yang **sudah kamu miliki sebagai zona**

Kamu **sudah punya** yang benar — `aikernel.qzz.io`. Gw buktikan sudah jalan:

```
$ dig +short NS aikernel.qzz.io
angelina.ns.cloudflare.com.        # <- NS Cloudflare, punya kamu
yoxall.ns.cloudflare.com.
$ dig +short SOA aikernel.qzz.io
angelina.ns.cloudflare.com. ...    # <- ada SOA = benar-benar zona

# dan sertifikat wildcard-nya SUDAH terbit:
$ echo | openssl s_client -connect 9router.aikernel.qzz.io:443 2>/dev/null \
    | openssl x509 -noout -ext subjectAltName
    DNS:aikernel.qzz.io, DNS:*.aikernel.qzz.io     # <- wildcard ADA
```

Artinya **`<label>.aikernel.qzz.io` langsung bisa dipakai, gratis, tanpa beli
apa pun.** Ini yang gw set jadi default sekarang.

**Urutan pilihan (dari yang paling gampang):**

1. **Pakai `aikernel.qzz.io`** ← rekomendasi, sudah siap, wildcard sudah ada.
2. Kalau tetap mau `synz.zone.id`: minta pemilik `zone.id` menambahkan **NS
   record** `synz.zone.id` → nameserver Cloudflare kamu (butuh kerjasama mereka),
   **atau** pindahkan `synz.zone.id` ke penyedia yang izinkan kelola DNS penuh.
3. Beli domain sendiri (mis. `synz.id`), daftarkan sebagai zone di Cloudflare →
   wildcard `*.synz.id` menutupi semuanya.
4. Advanced Certificate Manager (bayar) — bisa multi-tingkat, tapi tidak perlu
   karena opsi 1 gratis.

Cek sendiri kapan saja:

```bash
dig +short NS <base-domain-kamu>
# nameserver penyediamu      -> itu zona, wildcard menutupinya
# host asing / kosong        -> hostname di zone orang lain, TLS akan gagal
```

`synapse peerlink endpoint` **tidak menebak** — kalau `zone_apex` belum diisi di
config, dia mencetak perintah `dig` di atas supaya kamu cek sendiri; kalau
`zone_apex` sudah diisi, dia langsung bilang **"aman"** atau **"akan gagal"**.

---

## 4. Setup Cloudflare Tunnel (setelah zone siap)

Ringkas — detailnya di dokumen Cloudflare.

```bash
# 1. Install cloudflared, login
cloudflared tunnel login

# 2. Buat tunnel
cloudflared tunnel create synapse-peerlink

# 3. Route wildcard: SEMUA subdomain -> satu tunnel
cloudflared tunnel route dns synapse-peerlink "*.aikernel.qzz.io"

# 4. config.yml
#    tunnel: <id>
#    credentials-file: /root/.cloudflared/<id>.json
#    ingress:
#      - hostname: "*.aikernel.qzz.io"
#        service: http://localhost:<port-peerlink>
#      - service: http_status:404

# 5. Jalan
cloudflared tunnel run synapse-peerlink
```

Wildcard DNS (`*.aikernel.qzz.io`) berarti **kamu tidak perlu menambah record
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
  base_domain: aikernel.qzz.io
  zone_apex: aikernel.qzz.io   # opsional: bikin pesan TLS jadi pasti
```

Kalau tidak diisi, defaultnya `aikernel.qzz.io`. `zone_apex` opsional — kalau
kosong, `peerlink endpoint` menyuruh kamu cek pakai `dig` (tidak menebak).

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
