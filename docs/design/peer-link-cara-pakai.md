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
#   address  : synz.zone.id/peer/pdef6crymbycnjmbm5fuhmjc4v
#   hostname : synz.zone.id

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

## 2. Jawaban: "bisa beda-beda alamat, dan tidak ada yang tahu?"

**Bisa — dan sudah jalan.** Bukti nyata:

```
$ synapse peerlink endpoint
  address  : synz.zone.id/peer/pdef6crymbycnjmbm5fuhmjc4v

$ synapse peerlink rotate
New address: synz.zone.id/peer/s2uft4im5jsxscy7byyia9223z
```

- Label **acak 26 karakter** dari 32 simbol → ~130 bit entropi. 50 instance
  diuji, **nol tabrakan**.
- Label **tidak diturunkan** dari peer id. Peer id kamu publik; label kamu
  tetap rahasia. Sudah ada tesnya (`test_unguessable_from_peer_id`).
- **Stabil**: di-mint sekali, disimpan, sama setelah restart.
- **`rotate`** mengganti alamat kapan saja.

Kalau kamu punya apex zone sendiri (`aikernel.qzz.io`), mode `subdomain` memberi
**satu nama per peer** (`<label>.aikernel.qzz.io`). Kalau tidak (`synz.zone.id`),
mode `path` memberi **satu path per peer** — lihat §3.

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

## 3. ⚠️ JEBAKAN TLS — dan kenapa Peer Link punya **dua mode alamat**

Ini bagian yang paling gampang salah, jadi gw tulis di depan. **Gw sendiri
sempat salah di sini** (dua kali), jadi gw jelaskan aturan yang benar.

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

### Kasus `synz.zone.id` (sudah gw ukur pakai DNS, bukan tebakan)

```
$ dig +short NS zone.id
vip7.alidns.com.                   # <- NS milik Alibaba, bukan punya kamu
$ dig +short NS synz.zone.id
dns.webkus.com.                    # <- bukan delegasi, cuma NS hosting bersama
$ dig +short A synz.zone.id
216.176.239.254                    # <- webkus shared hosting
$ dig +short A apapun-acak.zone.id
... CNAME dns.webkus.com.          # <- SEMUA nama diarahkan sama: ini wildcard
```

→ `synz.zone.id` **bukan zona**, cuma hostname di dalam `zone.id`. Karena itu
`<label>.synz.zone.id` **tidak akan** dapat sertifikat gratis.

**Cloudflare juga tidak bisa ditempel ke sini** — gw cek panel `my.zone.id`
(dari bundle JS-nya), dropdown DNS-nya memang punya tipe `NS`, tapi ada catatan
resmi panel:

> *"NS records are **only** available for premium nett.to domain."*

Jadi NS dikunci hanya untuk domain `nett.to` premium. Tanpa NS, tidak ada jalur
delegasi ke Cloudflare. (Cloudflare sendiri **mau** — `zone.id` ada di Public
Suffix List — yang menolak adalah panel `zone.id`.)

### Solusinya: **mode `path`** — satu hostname untuk semua peer

Karena `<label>.synz.zone.id` tidak bisa, Peer Link **tidak** memaksa bentuk itu.
Ada dua mode alamat:

| Mode | Bentuk alamat | Sertifikat yang dibutuhkan |
|---|---|---|
| `subdomain` | `<label>.<base_domain>` | wildcard `*.<apex>` — butuh base domain = apex milikmu |
| **`path`** | `<base_domain>/peer/<label>` | **satu sertifikat biasa untuk `<base_domain>`** |

Di mode `path`, **semua peer berbagi satu hostname** dan dibedakan lewat path.
Satu sertifikat Let's Encrypt biasa sudah cukup — tidak butuh wildcard, tidak
butuh delegasi NS, tidak butuh Cloudflare.

Yang **tetap** kamu dapat: label acak 26 karakter yang tidak bisa ditebak dari
peer id. Jadi kehilangan wildcard **bukan** kehilangan keamanan — proteksi
aslinya tetap **E2EE + approval manual**, bukan kerahasiaan nama.

### Setel `synz.zone.id`

```yaml
peer_link:
  base_domain: synz.zone.id
  address_mode: path           # <- karena kamu tidak punya apex zone.id
```

Hasilnya:

```
$ synapse peerlink endpoint
Your Peer Link address
  address  : synz.zone.id/peer/pdef6crymbycnjmbm5fuhmjc4v
  hostname : synz.zone.id
  mode     : path
  base     : synz.zone.id
```

### DNS + sertifikat (2 langkah, di panel `my.zone.id`)

**Langkah 1 — A record** (subdomain `synz`):

```
hostname : @            # artinya synz.zone.id itu sendiri
type     : A
content  : <IP-publik-server-kamu>
```

Ini **boleh di plan Free** — panel bilang *"Can set A/CNAME records on @ or www
hostnames only"*, dan `@` = hostname subdomain itu.

**Langkah 2 — sertifikat TLS**, pakai **Let's Encrypt HTTP-01**:

```bash
certbot --nginx -d synz.zone.id
```

Butuh port 80 masuk (untuk validasi). **DNS-01 tidak bisa** — plan Free `zone.id`
tidak mengizinkan record `TXT`.

**Bukti jalur ini nyata** (bukan teori) — user `zone.id` lain sudah melakukannya:

```
$ dig +short A blogs.zone.id
216.198.79.1                     # <- IP Vercel, BUKAN webkus: server sendiri
# dan sertifikatnya terbit dari Let's Encrypt: *.blogs.zone.id, blogs.zone.id
```

Dari 4.830 sertifikat `.zone.id` di Certificate Transparency, **4.796 diterbitkan
Let's Encrypt** — jadi ini CA mayoritas di sana.

### Kalau nanti mau wildcard lagi

Urutan pilihan:

1. **Upgrade Premium `zone.id` (Rp 10.000/th)** → plan Premium bilang *"Can set
   A/CNAME records on any hostnames (subdomains)"*. Masih perlu cek apakah NS
   ikut dibuka; kalau ya, baru bisa delegasi ke Cloudflare.
2. **Daftar `synz.nett.to` premium** → panel bilang NS **diizinkan** untuk
   `nett.to` premium, jadi delegasi NS ke Cloudflare bisa.
3. **Pakai `aikernel.qzz.io`** → NS Cloudflare milikmu, cert wildcard sudah
   terbit. Ini tetap opsi paling siap kalau kamu berubah pikiran.
4. **Beli domain sendiri** (mis. `synz.id`) → daftarkan sebagai zone Cloudflare
   → wildcard `*.synz.id` menutupi semuanya.

Cek sendiri kapan saja:

```bash
dig +short NS <base-domain-kamu>
# nameserver penyediamu      -> itu zona, wildcard menutupinya
# host asing / kosong        -> hostname di zone orang lain, pakai mode path
```

`synapse peerlink endpoint` **tidak menebak** — kalau `zone_apex` belum diisi di
config, dia mencetak perintah `dig` di atas supaya kamu cek sendiri; kalau
`zone_apex` sudah diisi, dia langsung bilang **"aman"** atau **"akan gagal"**
(sekaligus menyarankan pindah ke mode `path`).

---

## 4. Reverse proxy (mode `path`)

Karena mode `path` memakai **satu** hostname, tidak perlu Cloudflare Tunnel dan
tidak perlu record DNS per peer. Cukup arahkan `/peer/<label>` ke instance:

```nginx
server {
    listen 443 ssl;
    server_name synz.zone.id;

    ssl_certificate     /etc/letsencrypt/live/synz.zone.id/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/synz.zone.id/privkey.pem;

    # Peer Link: satu path untuk semua peer
    location /peer/ {
        proxy_pass         http://127.0.0.1:<port-peerlink>;
        proxy_http_version 1.1;
        proxy_set_header   Upgrade    $http_upgrade;   # WebSocket
        proxy_set_header   Connection "upgrade";
        proxy_set_header   Host       $host;
        proxy_set_header   X-Real-IP  $remote_addr;
    }
}
```

**Catatan keamanan:** kalau kamu **memakai Cloudflare** (opsi wildcard di atas),
Cloudflare memutus TLS di edge-nya — artinya Cloudflare *bisa* melihat trafikmu.
Ini persis kasus "TLS saja TIDAK cukup kalau lewat perantara". Karena itu
**E2EE lapisan aplikasi wajib**, dan itu sudah tersedia (`cryptography` sudah
ada, nol dependency baru). Di mode `path` **tanpa** Cloudflare, TLS berakhir di
server kamu sendiri — lebih sederhana dan tidak ada perantara.

---

## 5. Set base domain

Setting perilaku ada di `config.yaml`, bukan environment variable:

```yaml
peer_link:
  base_domain: synz.zone.id
  address_mode: path           # subdomain (default) atau path
  zone_apex: zone.id           # opsional: bikin pesan TLS jadi pasti
```

- `base_domain` — default `aikernel.qzz.io` kalau tidak diisi.
- `address_mode` — `subdomain` (default) atau `path`. Nilai tidak dikenal
  **tidak** membuat error; dia balik ke default, jadi typo tidak merusak command.
- `zone_apex` — opsional. Kalau kosong, `peerlink endpoint` menyuruh kamu cek
  pakai `dig` (tidak menebak).

---

## 6. Referensi perintah

| Perintah | Fungsi |
|---|---|
| `synapse peerlink identity` | peer id kamu (boleh dibagikan) |
| `synapse peerlink endpoint` | alamat acak kamu (mint kalau belum ada) |
| `synapse peerlink endpoint --peek` | lihat saja, jangan mint |
| `synapse peerlink endpoint --address-mode path` | paksa mode path untuk sesi ini |
| `synapse peerlink endpoint --base-domain X` | ganti base domain untuk sesi ini |
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
