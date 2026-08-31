<p align="center">
  <img src="assets/banner.png" alt="Synapse Agent" width="100%">
</p>

# Synapse Agent ☤
<p align="center">
  <b>Synapse Agent</b> | <b>Synapse Desktop</b>
</p>
<p align="center">
  <a href="https://github.com/johsua092-ui/synapse-ai-agent/blob/main/LICENSE"><img src="https://img.shields.io/badge/License-MIT-green?style=for-the-badge" alt="License: MIT"></a>
  <a href="README.md"><img src="https://img.shields.io/badge/Lang-English-blue?style=for-the-badge" alt="English"></a>
  <a href="README.zh-CN.md"><img src="https://img.shields.io/badge/Lang-中文-red?style=for-the-badge" alt="中文"></a>
  <a href="README.ur-pk.md"><img src="https://img.shields.io/badge/Lang-اردو-green?style=for-the-badge" alt="اردو"></a>
  <a href="README.es.md"><img src="https://img.shields.io/badge/Lang-Español-orange?style=for-the-badge" alt="Español"></a>
  <a href="README.ja.md"><img src="https://img.shields.io/badge/Lang-日本語-white?style=for-the-badge" alt="日本語"></a>
  <a href="README.ar.md"><img src="https://img.shields.io/badge/Lang-العربية-blue?style=for-the-badge" alt="العربية"></a>
  <a href="README.id.md"><img src="https://img.shields.io/badge/Lang-Bahasa%20Indonesia-black?style=for-the-badge" alt="Bahasa Indonesia"></a>
  <a href="README.jv.md"><img src="https://img.shields.io/badge/Lang-Basa%20Jawa-yellow?style=for-the-badge" alt="Basa Jawa"></a>
</p>

**Agen AI yang terus menyempurnakan diri (self-improving) yang dibuat oleh Josh Research.** Ini satu-satunya agen dengan loop pembelajaran bawaan — ia menciptakan keterampilan dari pengalaman, memperbaikinya selama digunakan, mendorong dirinya sendiri untuk menyimpan pengetahuan, mencari percakapan masa lalunya sendiri, dan membangun model yang semakin dalam tentang siapa dirimu di lintas sesi. Jalankan di VPS seharga $5, klaster GPU, atau infrastruktur serverless yang hampir tidak memakan biaya saat idle. Ia tidak terikat pada laptopmu — bicaralah dengannya dari Telegram saat dia bekerja di VM cloud.

Gunakan model apa pun yang kamu mau — OpenRouter, OpenAI, endpoint buatanmu sendiri, dan banyak penyedia lainnya. Ganti dengan `synapse model` — tanpa perubahan kode, tanpa terkunci.

<table>
<tr><td><b>Antarmuka terminal sungguhan</b></td><td>TUI lengkap dengan penyuntingan multiline, autocomplete perintah garis-miring, riwayat percakapan, interupsi-dan-alihkan, dan keluaran alat secara streaming.</td></tr>
<tr><td><b>Hidup di tempat kamu hidup</b></td><td>Telegram, Discord, Slack, WhatsApp, Signal, dan CLI — semuanya dari satu proses gateway. Transkripsi pesan suara, keberlanjutan percakapan lintas platform.</td></tr>
<tr><td><b>Loop pembelajaran tertutup</b></td><td>Memori yang dikurasi agen dengan pengingat berkala. Pembuatan keterampilan secara otonom setelah tugas kompleks. Keterampilan menyempurnakan diri selama digunakan. Pencarian sesi FTS5 dengan perangkuman oleh LLM untuk mengingat lintas sesi. Pemodelan pengguna dialektis <a href="https://github.com/plastic-labs/honcho">Honcho</a>. Kompatibel dengan standar terbuka <a href="https://agentskills.io">agentskills.io</a>.</td></tr>
<tr><td><b>Otomatisasi terjadwal</b></td><td>Penjadwal cron bawaan dengan pengiriman ke platform mana pun. Laporan harian, cadangan malam hari, audit mingguan — semuanya dalam bahasa alami, berjalan tanpa pengawasan.</td></tr>
<tr><td><b>Mendelegasikan dan memparalelkan</b></td><td>Luncurkan subagen terisolasi untuk alur kerja paralel. Tulis skrip Python yang memanggil alat melalui RPC, merombak pipeline multi-langkah menjadi giliran tanpa biaya konteks.</td></tr>
<tr><td><b>Berjalan di mana saja, bukan hanya laptopmu</b></td><td>Tujuh backend terminal — local, Docker, SSH, Singularity, Modal, Daytona, dan Vercel Sandbox. Daytona dan Modal menawarkan persistensi serverless — lingkungan agenmu hibernasi saat idle dan bangun sesuai permintaan, hampir tanpa biaya antar sesi. Jalankan di VPS $5 atau klaster GPU.</td></tr>
<tr><td><b>Siap riset</b></td><td>Pembuatan lintasan (trajectory) secara batch, kompresi lintasan untuk melatih generasi berikutnya dari model pemanggil alat.</td></tr>
</table>

---

## Instalasi Cepat

### npm (semua platform)

```bash
npx synapse-ai-agent
```

Mengunduh dan menjalankan installer resmi untuk OS-mu — tanpa perlu tahu Node, shim hanya mem-bootstrap-nya.

### Linux, macOS, WSL2, Termux

```bash
curl -fsSL https://raw.githubusercontent.com/johsua092-ui/synapse-ai-agent/main/scripts/install.sh | bash
```

### Windows (native, PowerShell)

> **Perhatian:** Windows native menjalankan Synapse tanpa WSL — CLI, gateway, TUI, dan alat semuanya berfungsi native. Jika kamu lebih suka WSL2, perintah Linux/macOS satu baris di atas juga berfungsi di sana. Menemukan bug? Silakan [buat laporan](https://github.com/johsua092-ui/synapse-ai-agent/issues).

Jalankan ini di PowerShell:

```powershell
iex (irm https://raw.githubusercontent.com/johsua092-ui/synapse-ai-agent/main/scripts/install.ps1)
```

Installer menangani semuanya: uv, Python 3.11, Node.js, ripgrep, ffmpeg, **dan Git Bash portabel** (MinGit, diekstrak ke `%LOCALAPPDATA%\synapse\git` — tanpa perlu admin, sepenuhnya terisolasi dari instalasi Git sistem mana pun). Synapse menggunakan Git Bash bawaan ini untuk menjalankan perintah shell.

Jika kamu sudah punya Git terpasang, installer akan mendeteksinya dan memakainya. Jika tidak, unduhan MinGit ~45MB adalah semua yang kamu butuh — ia tidak akan menyentuh atau mengganggu Git sistem mana pun.

> **Android / Termux:** Jalur manual yang sudah diuji didokumentasikan di panduan Termux. Di Termux, Synapse memasang ekstra `.[termux]` yang dikurasi karena ekstra `.[all]` lengkap saat ini menarik dependensi suara yang tidak kompatibel dengan Android.
>
> **Windows:** Windows native didukung penuh — perintah PowerShell satu baris di atas memasang semuanya. Jika lebih suka WSL2, perintah Linux berfungsi di sana juga. Instalasi Windows native berada di bawah `%LOCALAPPDATA%\synapse`; WSL2 memasang di bawah `~/.synapse` seperti di Linux.

Setelah instalasi:

```bash
source ~/.bashrc    # muat ulang shell (atau: source ~/.zshrc)
synapse              # mulai mengobrol!
```

### Pemecahan Masalah

#### Windows Defender atau antivirus menandai `uv.exe` sebagai malware

Jika antivirusmu (Bitdefender, Windows Defender, dll.) mengarantina `uv.exe` dari folder `bin` Synapse (`%LOCALAPPDATA%\synapse\bin\uv.exe`), ini **positif palsu**. File itu adalah `uv` milik Astral — manajer paket Python Rust yang dipaketkan Synapse untuk mengelola lingkungan Python-nya. Mesin antivirus berbasis ML umumnya menandai biner Rust yang tidak ditandatangani dan mengunduh/memasang paket.

**Untuk memverifikasi bahwa salinanmu asli:**

```powershell
# Pasang GitHub CLI jika diperlukan
winget install --id GitHub.cli

# Masuk ke GitHub
gh auth login

# Jalankan verifikasi
$uv = "$env:LOCALAPPDATA\synapse\bin\uv.exe"
$ver = (& $uv --version).Split(' ')[1]
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
$zip = "$env:TEMP\uv.zip"
Invoke-WebRequest "https://github.com/astral-sh/uv/releases/download/$ver/uv-x86_64-pc-windows-msvc.zip" -OutFile $zip -UseBasicParsing
gh attestation verify $zip --repo astral-sh/uv
Expand-Archive $zip "$env:TEMP\uv_x" -Force
(Get-FileHash "$env:TEMP\uv_x\uv.exe").Hash -eq (Get-FileHash $uv).Hash
```

Jika attestation menyatakan "Verification succeeded" dan baris terakhir mencetak `True`, berarti aman.

**Untuk memasukkan Synapse ke daftar putih:**
- **Windows Defender:** Jalankan PowerShell sebagai Admin → `Add-MpPreference -ExclusionPath "$env:LOCALAPPDATA\synapse\bin"`
- **Bitdefender:** Tambahkan pengecualian di konsol Bitdefender (Protection > Antivirus > Settings > Manage Exceptions)
- Masukkan **folder** ke daftar putih, bukan hash file — Synapse memperbarui `uv` dan hash-nya berubah di setiap versi

Untuk konteks lebih lanjut, lihat laporan Astral hulu: [astral-sh/uv#13553](https://github.com/astral-sh/uv/issues/13553), [astral-sh/uv#15011](https://github.com/astral-sh/uv/issues/15011), [astral-sh/uv#10079](https://github.com/astral-sh/uv/issues/10079).

---

## Deploy ke Railway

Deploy Synapse Agent ke [Railway](https://railway.app) sebagai layanan container sekali klik. Image-nya sudah dilengkapi entrypoint s6-overlay dan dashboard web yang diawasi.

[![Deploy on Railway](https://railway.com/button.svg)](https://railway.com/template/synapse-agent?referralCode=QXdhdr)

### Yang kamu dapatkan

- **Dashboard web** di URL Railway publik (tergated auth, lihat di bawah)
- **Volume persisten** untuk status agen (mount volume di `/opt/data` / `$SYNAPSE_HOME`)
- **Health check** terhubung ke `/api/health`

### Pengaturan

1. Klik **Deploy on Railway** di atas (atau buat layanan baru dari repo ini — Railway mendeteksi otomatis `railway.toml` + `Dockerfile`).
2. Pasang volume yang dimount di `/opt/data`.
3. Tambahkan variabel layanan yang diperlukan (lihat [.env.railway.example](.env.railway.example)). Setidaknya:
   - `SYNAPSE_DASHBOARD=1`
   - Sebuah penyedia auth — **Basic Auth** (`SYNAPSE_DASHBOARD_BASIC_AUTH_USERNAME` + `SYNAPSE_DASHBOARD_BASIC_AUTH_PASSWORD`) atau OAuth/OIDC. Tanpa itu, dashboard **gagal-tertutup (fails closed)** pada bind publik.
4. Tambahkan kunci API model/providermu (`OPENROUTER_API_KEY`, `OPENAI_API_KEY`, dll.).

### Docker (self-host)

```bash
SYNAPSE_UID=$(id -u) SYNAPSE_GID=$(id -g) docker compose up -d
```

Lihat `docker-compose.yml` dan direktori `docker/` untuk pengaturan terawasi lengkap. Varian kompose Windows ada di `docker-compose.windows.yml`.

---

## Memulai

```bash
synapse              # CLI interaktif — mulai sebuah percakapan
synapse model        # Pilih penyedia dan model LLM-mu
synapse dashboard    # Buka panel admin di browser (port 9119)
synapse tools        # Konfigurasi alat mana yang diaktifkan
synapse config set   # Atur nilai konfigurasi individual
synapse config get   # Cetak nilai konfigurasi individual
synapse gateway      # Mulai gateway pesan (Telegram, Discord, dll.)
synapse setup        # Jalankan wizard penyiapan lengkap (konfigurasi semuanya sekaligus)
synapse claw migrate # Migrasi dari OpenClaw (jika datang dari OpenClaw)
synapse update       # Perbarui ke versi terbaru
synapse doctor       # Diagnosa masalah apa pun
```

### Panel Admin

Perintah `synapse dashboard` memulai panel admin web lokal di `http://127.0.0.1:9119`. Ia menyediakan UI berbasis browser untuk mengonfigurasi penyedia, mengelola kanal, melihat log, dan memantau agenmu.

```bash
synapse dashboard                        # Buka di browser, port 9119
synapse dashboard --port 8080            # Port khusus
synapse dashboard --host 0.0.0.0         # Ikat ke semua antarmuka (untuk akses jarak jauh)
synapse dashboard --no-open              # Jangan buka browser otomatis
synapse dashboard --skip-build           # Lewati build React, gunakan HTML admin pra-build
```

Fitur:
- **Setup** — Konfigurasi penyedia LLM, kunci API, dan kanal pesan
- **Status** — Pantau status gateway, uptime, dan sesi aktif
- **Logs** — Lihat log agen secara real-time
- **Users** — Kelola permintaan pairing dan pengguna yang disetujui
- **Backup & Restore** — Unduh/unggah snapshot deployment

📖 **Dokumentasi lengkap tersedia di dokumen-dokumen di bawah.**

---

## Manajemen Sesi

Synapse menyimpan riwayat percakapan untuk setiap sesi. Perintah `synapse session` memungkinkanmu mencantumkan dan menghapus sesi dari CLI, dan `/delete` melakukannya dari dalam percakapan. Ia memakai ulang backend SessionDB yang sama dengan dashboard, sehingga ada satu implementasi penghapusan di seluruh CLI, dashboard, dan platform chat.

```bash
synapse session list                    # Daftarkan semua sesi yang tersimpan
synapse session delete <session-id>     # Hapus satu sesi secara permanen
synapse session delete --all            # Hapus semua sesi (dengan peringatan dulu)
synapse session delete <session-id> -y  # Lewati prompt konfirmasi
synapse session --help                  # Penggunaan lengkap
```

`delete` selalu memverifikasi bahwa sesi tersebut ada dan mencetak error not-found jika tidak. Penghapusan tunggal menampilkan info sesi dan meminta konfirmasi sebelum melakukan apa pun yang destruktif; `delete --all` memerlukan konfirmasi yang lebih ketat (atau `--yes`).

Di dalam sebuah percakapan, `/delete` (atau `/delete -y`) menghapus sesi aktif saat ini secara permanen dan memulai yang baru.

Halaman Sessions di dashboard menawarkan operasi yang sama dengan tombol hapus, dialog konfirmasi, penyegaran setelah penghapusan, dan status error/kosong — didukung oleh SessionDB yang sama.

## Keterampilan Bawaan (Bundled Skills)

Synapse hadir dengan seperangkat keterampilan bawaan yang disinkronkan ke `~/.synapse/skills/` saat instalasi dan pembaruan (lihat `tools/skills_sync.py`). Ia juga memaketkan keterampilan alur kerja pengembangan [Superpowers](https://github.com/obra/superpowers) di bawah `skills/superpowers/` — termasuk `brainstorming`, `writing-plans`, `executing-plans`, `systematic-debugging` (melalui bundle software-development yang sudah ada), `test-driven-development`, dan lainnya. Keterampilan-keterampilan itu ikut sinkronisasi keterampilan bawaan yang sama, sehingga tersedia otomatis di profil baru mana pun.

Untuk keterampilan yang berbagi nama dengan keterampilan bawaan yang sudah ada (mis. `systematic-debugging`, `test-driven-development`, `requesting-code-review`), Synapse mempertahankan salinan bawaan yang sudah ada — ini menghindari tabrakan nama-duplikat dalam manifest sinkronisasi.

---

## Dirancang tidak bergantung penyedia (provider-agnostic)

Synapse bekerja dengan penyedia apa pun yang kamu mau — itu tidak akan berubah. Bawa OpenRouter, OpenAI, atau endpoint khusus apa pun dan hubungkan sekali. Ganti dengan `synapse model` — tanpa perubahan kode, tanpa terkunci.

Kamu tetap bisa membawa kunci sendiri per-alat kapan pun kamu mau — gateway-nya per-backend, bukan semua-atau-tidak.

---

## Penalaran & Pemikiran (Reasoning & Thinking)

Synapse menjaga reasoning/thinking tetap aktif secara default dan tidak pernah membiarkan nilai konfigurasi mematikannya. Ini adalah kebijakan **reasoning selalu-aktif** — model yang mendukung token reasoning selalu memakainya; model yang tidak mendukungnya tidak terpengaruh (tidak ada parameter penyedia ilegal yang dikirim).

### Level effort

Hanya ada tiga level effort, yang dipetakan dari tangga lama yang lebih lebar:

| Level  | Pertukaran                                       |
|--------|--------------------------------------------------|
| Medium | Kecepatan dan biaya seimbang (default)           |
| High   | Penalaran lebih dalam — lebih lambat dan lebih mahal per giliran |
| Max    | Penalaran terkuat — paling lambat dan paling mahal per giliran  |

### Mengatur levelnya

- **CLI:** `/reasoning medium | high | max`
- **Dashboard:** pemilih Reasoning di sidebar chat (kunci konfigurasi `agent.reasoning_effort` yang sama)
- **Konfigurasi:** `agent.reasoning_effort: medium` di `config.yaml`
- **Override per-model:** `agent.reasoning_overrides: { "model-id": "high" }`

### Migrasi penonaktifan lama (legacy)

Sebelumnya `none`, `false`, `off`, `disabled`, nilai kosong, boolean YAML `False`, atau `--reasoning_disabled` mematikan thinking. Di bawah kebijakan selalu-aktif, semua ini kini diselesaikan menjadi **medium** (`{"enabled": true, "effort": "medium"}`) sehingga reasoning tidak pernah nonaktif secara diam-diam. Level yang tidak dikenal (mis. `turbo`) tetap jatuh kembali ke default pemanggil; flag `--reasoning_disabled` batch-runner yang tidak digunakan lagi hanya ada untuk kompatibilitas mundur dan mencetak notifikasi penonaktifan.

---

## Referensi Cepat CLI vs Messaging

Synapse punya dua titik masuk: mulai antarmuka terminal dengan `synapse`, atau jalankan gateway dan bicara dengannya dari Telegram, Discord, Slack, WhatsApp, Signal, atau Email. Setelah berada dalam percakapan, banyak perintah garis-miring digunakan bersama di kedua antarmuka.

| Aksi                           | CLI                                           | Platform pesan                                                             |
|--------------------------------|-----------------------------------------------|-----------------------------------------------------------------------------|
| Mulai mengobrol                | `synapse`                                     | Jalankan `synapse gateway setup` + `synapse gateway start`, lalu kirim pesan ke bot |
| Buka panel admin               | `synapse dashboard`                           | —                                                                           |
| Mulai percakapan baru          | `/new` atau `/reset`                          | `/new` atau `/reset`                                                        |
| Ganti model                    | `/model [provider:model]`                     | `/model [provider:model]`                                                   |
| Atur kepribadian               | `/personality [nama]`                         | `/personality [nama]`                                                       |
| Coba lagi / batalkan giliran   | `/retry`, `/undo`                             | `/retry`, `/undo`                                                           |
| Kompres konteks / cek usage    | `/compress`, `/usage`, `/insights [--days N]` | `/compress`, `/usage`, `/insights [days]`                                   |
| Jelajahi keterampilan          | `/skills` atau `/<nama-keterampilan>`         | `/<nama-keterampilan>`                                                      |
| Daftarkan sesi                 | `synapse session list`                        | —                                                                           |
| Hapus sesi saat ini            | `/delete`                                     | —                                                                           |
| Hapus satu/semua sesi          | `synapse session delete <id>` / `--all`       | —                                                                           |
| Interupsi pekerjaan berjalan   | `Ctrl+C` atau kirim pesan baru                | `/stop` atau kirim pesan baru                                               |
| Status khusus platform         | `/platforms`                                  | `/status`, `/sethome`                                                       |

Untuk daftar perintah lengkap, lihat panduan CLI dan panduan Messaging Gateway.

---

---

## Migrasi dari OpenClaw

Jika kamu datang dari OpenClaw, Synapse dapat mengimpor pengaturan, memori, keterampilan, dan kunci API-mu secara otomatis.

**Saat penyiapan pertama kali:** Wizard penyiapan (`synapse setup`) mendeteksi `~/.openclaw` secara otomatis dan menawarkan migrasi sebelum konfigurasi dimulai.

**Kapan saja setelah instalasi:**

```bash
synapse claw migrate              # Migrasi interaktif (preset lengkap)
synapse claw migrate --dry-run    # Pratinjau apa yang akan dimigrasi
synapse claw migrate --preset user-data   # Migrasi tanpa secret
synapse claw migrate --overwrite  # Timpa konflik yang ada
```

Yang diimpor:

- **SOUL.md** — file persona
- **Memories** — entri MEMORY.md dan USER.md
- **Skills** — keterampilan buatan pengguna → `~/.synapse/skills/openclaw-imports/`
- **Command allowlist** — pola persetujuan
- **Messaging settings** — konfigurasi platform, pengguna yang diizinkan, direktori kerja
- **API keys** — secret yang masuk daftar putih (Telegram, OpenRouter, OpenAI, Anthropic, ElevenLabs)
- **TTS assets** — file audio workspace
- **Workspace instructions** — AGENTS.md (dengan `--workspace-target`)

Lihat `synapse claw migrate --help` untuk semua opsi, atau gunakan keterampilan `openclaw-migration` untuk migrasi interaktif yang dipandu agen dengan pratinjau dry-run.

---

## Google Drive

Synapse dapat membaca dan menulis Google Drive pengguna melalui keterampilan bawaan
(`skills/google-drive`). Ia menggunakan Drive REST API dengan OAuth — tanpa SDK Google
yang berat, hanya `requests` (sudah merupakan dependensi inti).

Atur sekali dengan menjalankan helper bawaan:

```bash
python3 skills/google-drive/google-drive/scripts/gdrive.py setup
```

Wizard memandu pengguna melalui Google Cloud Console (aktifkan Drive
API, buat Desktop OAuth client, unduh `credentials.json`), lalu membuka
browser untuk persetujuan dan meng-cache token secara lokal. File kredensial
(`credentials.json`, `token.json`) di-ignore git dan tidak pernah di-commit.

Kemudian agen dapat mengemudikan Drive atas nama pengguna:

```bash
python3 skills/google-drive/google-drive/scripts/gdrive.py list
python3 skills/google-drive/google-drive/scripts/gdrive.py search "annual report"
python3 skills/google-drive/google-drive/scripts/gdrive.py upload notes.md
python3 skills/google-drive/google-drive/scripts/gdrive.py download <file_id>
```

Kredensial yang sama bekerja di Windows, Termux, VPS, atau Railway — salin
`credentials.json` (dan `token.json`) ke dalam checkout dan jalankan `setup` lagi.
Lihat `skills/google-drive/google-drive/SKILL.md` untuk detail lengkap.

---

## Berkontribusi

Kami menyambut kontribusi! Lihat Panduan Berkontribusi untuk pengaturan pengembangan, gaya kode, dan proses PR.

Mulai cepat untuk kontributor — gunakan installer standar, lalu bekerja dari
checkout git lengkap yang dibuatnya di `$SYNAPSE_HOME/synapse-agent` (biasanya
`~/.synapse/synapse-agent`). Ini cocok dengan tata letak yang digunakan `synapse update`, venv terkelola, dependensi lazy, gateway, dan tooling docs.

```bash
curl -fsSL https://raw.githubusercontent.com/johsua092-ui/synapse-ai-agent/main/scripts/install.sh | bash
cd "${SYNAPSE_HOME:-$HOME/.synapse}/synapse-agent"
uv pip install -e ".[all,dev]"
scripts/run_tests.sh
```

Fallback clone manual (untuk clone sekali pakai/CI di mana kamu memang tidak
menginginkan tata letak instalasi terkelola):

Buat venv di luar pohon sumber yang dikloning — venv di dalam direktori
tempat agen beroperasi bisa terhapus oleh perintah berbasis path relatif yang dijalankan agen
terhadap checkout-nya sendiri, menghancurkan runtime yang sedang berjalan di tengah sesi.

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
uv venv ~/.synapse/venvs/synapse-dev --python 3.11
source ~/.synapse/venvs/synapse-dev/bin/activate
uv pip install -e ".[all,dev]"
scripts/run_tests.sh
```

---

## Lisensi

MIT — lihat [LICENSE](LICENSE).
