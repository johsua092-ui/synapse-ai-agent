# Peer Link — cara pakai (versi "cuma modal domain")

Dokumen ini menjawab satu pertanyaan: **kalau gw cuma punya domain, orang lain
gimana caranya nyambung?**

Jawaban singkatnya: **orang lain cuma butuh satu perintah.** Tapi ada satu hal
yang harus ada dulu di sisi kamu — dan itu bukan hosting, bukan VPS baru, bukan
biaya tambahan. Itu **satu proses** di mesin yang sudah kamu punya.

---

## 1. Kenapa domain saja tidak cukup (jujur)

Domain itu **alamat**, bukan **yang menjawab**. Analoginya:

| | Analogi | Status |
|---|---|---|
| `synz.zone.id` | nomor rumah | kamu punya |
| port 443 | pintu depan | sudah terbuka |
| **program yang dengerin** | **orang di dalam rumah** | **harus ada** |

Kalau kamu arahkan domain ke mesin kamu tapi **tidak ada program yang
dengerin**, orang yang connect akan ketemu web lain yang kebetulan sudah
menempati port itu — bukan Synapse kamu.

Itu bukan pendapat, itu terukur. Sebelum fitur ini ada:

```
$ curl https://synz.zone.id/peer/tes
404        ← dijawab 216.176.239.254 (webkus), bukan Synapse
```

Dan di dalam kode, tidak ada satu pun yang mendengarkan:

```
$ grep -cE "listen\(|serve_forever|start_server|bind\(" gateway/relay/*.py
0
```

Perintah `synapse peerlink serve` yang ada sekarang **menutup celah itu**.

### Kabar baiknya

Mesin yang kamu pakai sekarang **sudah** punya semua yang dibutuhkan:

| Yang kamu kira perlu beli | Kenyataannya |
|---|---|
| VPS | sudah ada — `213.163.196.48` |
| Hosting | tidak perlu |
| Port forwarding | port 443 sudah terbuka dari luar |
| Web server | nginx sudah jalan |

Jadi **"cuma modal domain" itu benar** — bukan karena domainnya ajaib, tapi
karena mesinnya sudah ada. Yang kurang cuma prosesnya, dan itu satu perintah.

---

## 2. Siapa yang melakukan apa

Ini bagian yang paling penting untuk dipahami, karena di sinilah
"cuma modal domain" jadi masuk akal:

| | Siapa | Perlu apa |
|---|---|---|
| **Kamu** (yang punya domain) | nyalain listener | domain + mesin ini |
| **Orang lain** | `connect` saja | **cuma URL** |

Orang lain **tidak perlu**: VPS, domain sendiri, port forwarding, akun, daftar,
bayar. Mereka jalan satu perintah, selesai. Ini yang bikin "enak buat orang
lain" — bebannya ada di kamu, dan beban itu sudah lunas karena mesinnya ada.

---

## 3. Setup di sisi kamu (sekali saja)

### 3.1 Arahkan domain ke mesin ini

Di panel DNS `my.zone.id`:

```
Type  : A
Host  : @            (atau "synz" kalau mau synz.synz.zone.id)
Value : 213.163.196.48
```

Cek sudah benar:

```bash
dig +short synz.zone.id
# harus keluar: 213.163.196.48
```

### 3.2 Ambil sertifikat TLS (gratis)

Satu sertifikat untuk satu nama. Tidak perlu wildcard, tidak perlu DNS-01:

```bash
certbot --nginx -d synz.zone.id
```

> **Kenapa bukan Cloudflare?** Sudah diuji: 4 cara, semua gagal di
> `synz.zone.id`. Dan DNS-01 tidak bisa di paket gratis (panel menolak TXT).
> HTTP-01 lewat Let's Encrypt jalan — 4.796 dari 4.830 sertifikat `.zone.id`
> memang Let's Encrypt.

### 3.3 Suruh nginx meneruskan `/peer/` ke Synapse

```nginx
location /peer/ {
    proxy_pass http://127.0.0.1:8443;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-Proto $scheme;
}
```

### 3.4 Nyalakan

```bash
synapse peerlink identity          # lihat peer id kamu (boleh dibagikan)
synapse peerlink mode invite       # buka pintu, undangan saja
synapse peerlink endpoint          # URL publik kamu
synapse peerlink serve             # jalankan — biarkan hidup
```

`serve` akan menampilkan URL kamu, misalnya:

```
Peer Link listening on 0.0.0.0:8443
  public url : https://synz.zone.id/peer/axcx825x9eqc5yw9bezpj4z49v
  mode       : invite
  our peer id: pl1zbnoinwul2qidnuwkdg3dzhkjdmcrfw4
```

**URL itulah yang kamu kirim ke orang lain.**

---

## 4. Di sisi orang lain (satu perintah)

```bash
synapse peerlink connect https://synz.zone.id/peer/axcx825x9eqc5yw9bezpj4z49v
```

Selesai. Outputnya:

```
Linked with https://synz.zone.id/peer/axcx825x9eqc5yw9bezpj4z49v
  their peer id : pl1zbnoinwul2qidnuwkdg3dzhkjdmcrfw4
  authenticated : True
  state         : quarantined

  They still have to approve you on their side before anything
  can be shared. That decision is theirs, not the AI's.
```

Perhatikan `state: quarantined`. **Itu memang begitu seharusnya.** Terhubung
bukan berarti dipercaya.

---

## 5. Kamu yang memutuskan

```bash
synapse peerlink pending                  # siapa yang nunggu
synapse peerlink approve pl1yfnkujdq...   # LU yang mutusin
synapse peerlink block   pl1yfnkujdq...   # atau tolak permanen
synapse peerlink list                     # siapa saja yang sudah dipercaya
```

Tidak ada jalur di mana AI menerima peer sendiri. Satu-satunya cara seseorang
jadi dipercaya adalah kamu mengetik `approve`.

---

## 6. Mode — pilih sesuai kebutuhan

| Mode | Siapa boleh mengetuk | Untuk siapa |
|---|---|---|
| `closed` | tidak ada (default) | fitur mati |
| `invite` | yang punya kode undangan | **disarankan** |
| `public_gated` | siapa saja, tapi harus bayar PoW | publik |
| `public_open` | siapa saja | jangan dipakai |

Kalau mode `closed`, `serve` **menolak jalan**. Itu bukan sekadar dokumentasi —
percobaannya:

```
$ synapse peerlink serve
peerlink: refusing to listen while admission mode is 'closed';
run `synapse peerlink mode invite` (or public_gated) first
```

---

## 7. Kalau alamatnya bocor

Label itu acak (26 karakter, ~130 bit), jadi tidak bisa ditebak dari peer id
kamu. Tapi **jangan anggap itu kunci rahasia** — DNS dan Certificate
Transparency itu publik, jadi alamat bisa ketemu.

Yang benar-benar melindungi adalah **mode + persetujuan kamu**. Kalau alamat
bocor:

```bash
synapse peerlink rotate     # alamat baru, alamat lama mati
```

---

## 8. Yang sudah terbukti, dan yang belum

Dijalankan nyata, bukan diklaim (`/root/work/BUKTI_SERVER.py`, exit 0):

| # | Yang diuji | Hasil |
|---|---|---|
| 1 | Dua identitas Ed25519 berbeda, tanpa registry | OK |
| 2 | Mode `closed` menolak listen | OK |
| 3 | Listener benar-benar bind & jawab | OK |
| 4 | `/peerlink/health` tidak bocorkan apa pun | OK |
| 5 | Dua instance saling terautentikasi lewat socket | OK |
| 6 | Pendatang masuk karantina, bukan auto-trusted | OK |
| 7 | PoW 12 bit diminta | OK |
| 8 | Promosi hanya oleh pemilik | OK |
| 9 | Blokir berlaku langsung | OK |
| 10 | Impersonasi / replay / MITM ditolak | OK |
| 11 | Server berhenti bersih | OK |

Serangan yang **gagal** (dan alasannya jelas, bukan crash):

```
mengaku peer_id orang lain -> HTTP 403 peer id does not match public key
confirm tanpa hello        -> HTTP 400 no handshake in progress
versi protokol asing       -> HTTP 409 unsupported protocol version
signature server dipalsukan-> ok=False peer could not prove it holds the key
```

### ⚠️ Yang BELUM

| Belum | Kenapa penting |
|---|---|
| TLS di dalam proses ini | listener bicara HTTP polos; TLS di nginx (langkah 3.2) |
| Sinkronisasi data | handshake dulu; ini fase berikutnya |
| Barter skill / pengalaman | fase berikutnya |
| Transport antar-peer (E2EE) | belum final |
| Jalan otomatis saat boot | sekarang harus dijalankan manual |

**Jangan dibaca sebagai "sudah selesai".** Yang selesai adalah: dua instance
bisa **saling mengenali dan memutuskan**. Belum ada pertukaran data.

---

## 9. Ringkasan satu layar

```
KAMU (sekali):
  dig +short synz.zone.id            → 213.163.196.48
  certbot --nginx -d synz.zone.id
  nginx: location /peer/ → 127.0.0.1:8443
  synapse peerlink mode invite
  synapse peerlink endpoint          → https://synz.zone.id/peer/<acak>
  synapse peerlink serve             → biarkan hidup

ORANG LAIN (satu perintah):
  synapse peerlink connect https://synz.zone.id/peer/<acak>

KAMU:
  synapse peerlink pending
  synapse peerlink approve <peer-id>
```

**Biaya tambahan: nol. Hosting baru: tidak ada. Mesin: yang sudah ada.**
