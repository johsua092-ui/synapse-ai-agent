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

**Agen AI sing terus maju dhéwé (self-improving) digawé déning Josh Research.** Iki siji-sijiné agen sing nduwé puteran pamulangan (learning loop) ing njero — dhèwèké nggawé katrampilan (skill) saka pengalaman, ndandani nalika dienggo, nyurung awaké dhéwé kanggo nyimpen kawruh, nggolèki obrolané dhéwé sing wis kepungkur, lan mbangun pamahaman sing saya jero bab sapa kowé ing lintas sesi. Lakokna ing VPS rega $5, kluster GPU, utawa infrastruktur serverless sing meh ora mbebayani biaya nalika nganggur. Ora kaiket ing laptopmu — omongana karo dhèwèké saka Telegram nalika dhèwèké makarya ing VM awang-awang (cloud).

*Kaca iki nganggo aksara latin. Versi aksara Jawa (Hanacaraka) bisa ditambahaké ing sabanjuré.*

Gunakna model apa waé sing kokkarep — OpenRouter, OpenAI, endpoint gawéanmu dhéwé, lan akèh panyedhiya liyané. Ganti nganggo `synapse model` — tanpa ngowahi kode, tanpa kaiket.

<table>
<tr><td><b>Antarmuka terminal tenanan</b></td><td>TUI lengkap kanthi éditan multiline, autocomplete perintah garis-miring, riwayat obrolan, interupsi-lan-alihake, lan asil alat kanthi streaming.</td></tr>
<tr><td><b>Urip ing panggonanmu</b></td><td>Telegram, Discord, Slack, WhatsApp, Signal, lan CLI — kabèh saka siji prosès gateway. Transkripsi cathetan swara, kelanjutan obrolan lintas platform.</td></tr>
<tr><td><b>Puteran pamulangan tertutup</b></td><td>Memori sing diurus agen kanthi pangéling-éling périodik. Gawé katrampilan kanthi otonom sawisé tugas rumit. Katrampilan saya apik dhéwé nalika dienggo. Panggolèkan sesi FTS5 kanthi rangkuman LLM kanggo ngéling-éling lintas sesi. Pemodelan pangguna dialektis <a href="https://github.com/plastic-labs/honcho">Honcho</a>. Kompatibel karo standar kabukak <a href="https://agentskills.io">agentskills.io</a>.</td></tr>
<tr><td><b>Otomatisasi terjadwal</b></td><td>Penjadwal cron ing njero kanthi pangiriman menyang platform apa waé. Laporan saben dina, cadhangan bengi, audit saben minggu — kabèh nganggo basa alami, mlaku tanpa dijaga.</td></tr>
<tr><td><b>Delegasi lan pararel</b></td><td>Bukak subagen terisolasi kanggo alur kerja pararel. Tulis skrip Python sing nggolèki alat liwat RPC, ngowahi pipeline pirang-pirang langkah dadi giliran tanpa biaya konteks.</td></tr>
<tr><td><b>Mlaku ing ngendi waé, ora mung laptopmu</b></td><td>Pitu backend terminal — local, Docker, SSH, Singularity, Modal, Daytona, lan Vercel Sandbox. Daytona lan Modal nawakake persistensi serverless — lingkungan agenmu turu nalika nganggur lan tangi yèn perlu, meh tanpa biaya antar sesi. Lakokna ing VPS $5 utawa kluster GPU.</td></tr>
<tr><td><b>Siap riset</b></td><td>Nggawé lintasan (trajectory) sacara batch, kompresi lintasan kanggo nglatih generasi sabanjuré saka model pemanggil alat.</td></tr>
</table>

---

## Instalasi Cepet

### npm (kabèh platform)

```bash
npx synapse-ai-agent
```

Ngundhuh lan mlakokaké installer resmi kanggo OS-mu — tanpa prelu ngerti Node, shim mung nggawé bootstrap.

### Linux, macOS, WSL2, Termux

```bash
curl -fsSL https://raw.githubusercontent.com/johsua092-ui/synapse-ai-agent/main/scripts/install.sh | bash
```

### Windows (native, PowerShell)

> **Cathetan:** Windows native mlakokaké Synapse tanpa WSL — CLI, gateway, TUI, lan alat kabèh mlaku native. Yèn kowé luwih seneng WSL2, perintah Linux/macOS siji baris ing ndhuwur uga bisa ana ing kana. Nggolèki bug? Mangga [gawe laporan](https://github.com/johsua092-ui/synapse-ai-agent/issues).

Lakokna iki ing PowerShell:

```powershell
iex (irm https://raw.githubusercontent.com/johsua092-ui/synapse-ai-agent/main/scripts/install.ps1)
```

Installer ngurusi kabèh: uv, Python 3.11, Node.js, ripgrep, ffmpeg, **lan Git Bash portabel** (MinGit, diekstrak menyang `%LOCALAPPDATA%\synapse\git` — tanpa prelu admin, terisolasi sakabehe saka instalasi Git sistem). Synapse nganggo Git Bash sing dibundel iki kanggo mlakokaké perintah shell.

Yèn kowé wis duwé Git kepasang, installer bakal ndeteksi lan nganggo kuwi. Yèn ora, undhuhan MinGit ~45MB kuwi sing perlu — ora bakal ndemek utawa ngganggu Git sistem.

> **Android / Termux:** Jalur manual sing wis diuji didokumentasikake ing pandhuan Termux. Ing Termux, Synapse masang ekstra `.[termux]` sing dikurasi amarga ekstra `.[all]` lengkap saiki narik dependensi swara sing ora kompatibel karo Android.
>
> **Windows:** Windows native didukung penuh — perintah PowerShell siji baris ing ndhuwur masang kabèh. Yèn luwih seneng WSL2, perintah Linux bisa ana ing kana uga. Instalasi Windows native dumunung ing `%LOCALAPPDATA%\synapse`; WSL2 masang ing `~/.synapse` kaya ing Linux.

Sawisé instalasi:

```bash
source ~/.bashrc    # muat ulang shell (utawa: source ~/.zshrc)
synapse              # wiwiti ngobrol!
```

### Ngatasi Masalah

#### Windows Defender utawa antivirus nandai `uv.exe` minangka malware

Yèn antivirusmu (Bitdefender, Windows Defender, lsp.) ngkarantina `uv.exe` saka folder `bin` Synapse (`%LOCALAPPDATA%\synapse\bin\uv.exe`), iki **positif palsu**. File kuwi `uv` darbèké Astral — manajer pakèt Python Rust sing dipaket Synapse kanggo ngatur lingkungan Python-é. Mesin antivirus adhedhasar ML umume nandai biner Rust sing ora ditandatangani lan ngundhuh/masang pakèt.

**Kanggo verifikasi yèn salinanmu asli:**

```powershell
# Pasang GitHub CLI yèn perlu
winget install --id GitHub.cli

# Mlebu menyang GitHub
gh auth login

# Lakokaké verifikasi
$uv = "$env:LOCALAPPDATA\synapse\bin\uv.exe"
$ver = (& $uv --version).Split(' ')[1]
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
$zip = "$env:TEMP\uv.zip"
Invoke-WebRequest "https://github.com/astral-sh/uv/releases/download/$ver/uv-x86_64-pc-windows-msvc.zip" -OutFile $zip -UseBasicParsing
gh attestation verify $zip --repo astral-sh/uv
Expand-Archive $zip "$env:TEMP\uv_x" -Force
(Get-FileHash "$env:TEMP\uv_x\uv.exe").Hash -eq (Get-FileHash $uv).Hash
```

Yèn attestation ujar "Verification succeeded" lan baris pungkasan nyithak `True`, berarti aman.

**Kanggo mlebuake Synapse ing dhaftar putih:**
- **Windows Defender:** Lakokaké PowerShell minangka Admin → `Add-MpPreference -ExclusionPath "$env:LOCALAPPDATA\synapse\bin"`
- **Bitdefender:** Tambahaké pangecualian ing konsol Bitdefender (Protection > Antivirus > Settings > Manage Exceptions)
- Lebokna **folder** menyang dhaftar putih, dudu hash file — Synapse nggawé anyar `uv` lan hash-é ganti saben versi

Kanggo konteks luwih lanjut, deleng laporan Astral hulu: [astral-sh/uv#13553](https://github.com/astral-sh/uv/issues/13553), [astral-sh/uv#15011](https://github.com/astral-sh/uv/issues/15011), [astral-sh/uv#10079](https://github.com/astral-sh/uv/issues/10079).

---

## Deploy menyang Railway

Deploy Synapse Agent menyang [Railway](https://railway.app) minangka layanan container sekali-klik. Image-é wis dilengkapi entrypoint s6-overlay lan dashboard web sing diawasi.

[![Deploy on Railway](https://railway.com/button.svg)](https://railway.com/template/synapse-agent?referralCode=QXdhdr)

### Sing kokoleh

- **Dashboard web** ing URL Railway publik (tergated auth, deleng ing ngisor)
- **Volume persisten** kanggo status agen (mount volume ing `/opt/data` / `$SYNAPSE_HOME`)
- **Health check** nyambung menyang `/api/health`

### Pengaturan

1. Klik **Deploy on Railway** ing ndhuwur (utawa gawé layanan anyar saka repo iki — Railway ndeteksi otomatis `railway.toml` + `Dockerfile`).
2. Pasang volume sing dimount ing `/opt/data`.
3. Tambahaké variabel layanan sing dibutuhaké (deleng [.env.railway.example](.env.railway.example)). Saorèng-orèngé:
   - `SYNAPSE_DASHBOARD=1`
   - Sawijining panyedhiya auth — **Basic Auth** (`SYNAPSE_DASHBOARD_BASIC_AUTH_USERNAME` + `SYNAPSE_DASHBOARD_BASIC_AUTH_PASSWORD`) utawa OAuth/OIDC. Tanpa kuwi, dashboard bakal **gagal-nutup (fails closed)** ing bind publik.
4. Tambahaké kunci API model/panyedhiya (`OPENROUTER_API_KEY`, `OPENAI_API_KEY`, lsp.).

### Docker (self-host)

```bash
SYNAPSE_UID=$(id -u) SYNAPSE_GID=$(id -g) docker compose up -d
```

Deleng `docker-compose.yml` lan direktori `docker/` kanggo pengaturan lengkap sing diawasi. Varian kompose Windows ana ing `docker-compose.windows.yml`.

---

## Miwiti

```bash
synapse              # CLI interaktif — miwiti obrolan
synapse model        # Pilih panyedhiya lan model LLM-mu
synapse dashboard    # Bukak panel admin ing browser (port 9119)
synapse tools        # Konfigurasi alat endi sing diaktifaké
synapse config set   # Atur nilai konfigurasi individual
synapse config get   # Cetak nilai konfigurasi individual
synapse gateway      # Miwiti gateway pesen (Telegram, Discord, lsp.)
synapse setup        # Lakokaké wizard penyiapan lengkap (konfigurasi kabèh bebarengan)
synapse claw migrate # Migrasi saka OpenClaw (yèn teka saka OpenClaw)
synapse update       # Nggawé anyar menyang versi paling anyar
synapse doctor       # Diagnosa masalah apa waé
```

### Panel Admin

Perintah `synapse dashboard` miwiti panel admin web lokal ing `http://127.0.0.1:9119`. Dhèwèké nyediakaké UI adhedhasar browser kanggo ngonfigurasi panyedhiya, ngatur kanal, ndeleng log, lan ngawasi agenmu.

```bash
synapse dashboard                        # Bukak ing browser, port 9119
synapse dashboard --port 8080            # Port khusus
synapse dashboard --host 0.0.0.0         # Ikat menyang kabèh antarmuka (kanggo akses adoh)
synapse dashboard --no-open              # Aja bukak browser otomatis
synapse dashboard --skip-build           # Liwati build React, gunakna HTML admin pra-build
```

Fitur:
- **Setup** — Konfigurasi panyedhiya LLM, kunci API, lan kanal pesen
- **Status** — Ngawasi status gateway, uptime, lan sesi aktif
- **Logs** — Deleng log agen sacara real-time
- **Users** — Ngatur panyuwunan pairing lan pangguna sing disetujoni
- **Backup & Restore** — Ngundhuh/ngunggah snapshot deployment

📖 **Dokumentasi lengkap kasedhiya ing dokumen-dokumen ing ngisor iki.**

---

## Manajemen Sesi

Synapse nyimpen riwayat obrolan kanggo saben sesi. Perintah `synapse session` ngidini kowé nglumpukaké lan mbusak sesi saka CLI, lan `/delete` nindakaké saka njero obrolan. Dhèwèké nganggo ulang backend SessionDB sing padha karo dashboard, dadi ana siji implementasi pambusakan ing kabèh CLI, dashboard, lan platform chat.

```bash
synapse session list                    # Dhaftarake kabèh sesi sing disimpen
synapse session delete <session-id>     # Busak siji sesi sacara permanen
synapse session delete --all            # Busak kabèh sesi (kanthi pènget dhisik)
synapse session delete <session-id> -y  # Liwati prompt konfirmasi
synapse session --help                  # Panganggoan lengkap
```

`delete` tansah verifikasi yèn sesi kuwi ana lan nyithak error not-found yèn ora ana. Pambusakan tunggal nuduhaké info sesi lan njaluk konfirmasi sadurunge nindakaké apa waé sing destruktif; `delete --all` mbutuhaké konfirmasi sing luwih ketat (utawa `--yes`).

Ing njero obrolan, `/delete` (utawa `/delete -y`) mbusak sesi aktif saiki sacara permanen lan miwiti sing anyar.

Kaca Sessions ing dashboard nawakake operasi sing padha kanthi tombol busak, dialog konfirmasi, penyegaran sawisé pambusakan, lan status error/kosong — didhukung SessionDB sing padha.

## Katrampilan Bawaan (Bundled Skills)

Synapse teka kanthi sakumpulan katrampilan bawaan sing disinkronake menyang `~/.synapse/skills/` nalika instalasi lan pembaruan (deleng `tools/skills_sync.py`). Dhèwèké uga ngepaket katrampilan alur kerja pangembangan [Superpowers](https://github.com/obra/superpowers) ing `skills/superpowers/` — kalebu `brainstorming`, `writing-plans`, `executing-plans`, `systematic-debugging` (liwat bundle software-development sing wis ana), `test-driven-development`, lan liya-liyané. Katrampilan-katrampilan iku melu sinkronisasi katrampilan bawaan sing padha, dadi kasedhiya otomatis ing profil anyar apa waé.

Kanggo katrampilan sing nuduhaké jeneng karo katrampilan bawaan sing wis ana (mis. `systematic-debugging`, `test-driven-development`, `requesting-code-review`), Synapse njaga salinan bawaan sing wis ana — iki ngindari tabrakan jeneng-duplikat ing manifest sinkronisasi.

---

## Dirancang ora gumantung panyedhiya (provider-agnostic)

Synapse makarya karo panyedhiya apa waé sing kokkarep — iku ora bakal ganti. Bawa OpenRouter, OpenAI, utawa endpoint khusus apa waé lan sambungake sepisan. Ganti nganggo `synapse model` — tanpa ngowahi kode, tanpa kaiket.

Kowé tetep bisa nggawa kunci dhéwé saben-alat kapan waé — gateway-é per-backend, ora kabèh-utawa-ora.

---

## Penalaran & Pikiran (Reasoning & Thinking)

Synapse njaga reasoning/thinking tetep aktif minangka default lan ora nate ngidini nilai konfigurasi mateni. Iki kabijakan **reasoning tansah-aktif** — model sing ndhukung token reasoning tansah nganggo; model sing ora ndhukung ora kena pangaruh (ora ana parameter panyedhiya ilegal sing dikirim).

### Level effort

Mung ana telung level effort, sing dipetakake saka tangga lawas sing luwih amba:

| Level   | Pertukaran                                      |
|---------|-------------------------------------------------|
| Medium  | Kacepetan lan biaya seimbang (default)          |
| High    | Penalaran luwih jero — luwih alon lan luwih larang saben giliran |
| Max     | Penalaran paling kuat — paling alon lan paling larang saben giliran |

### Ngatur level-é

- **CLI:** `/reasoning medium | high | max`
- **Dashboard:** pamilih Reasoning ing sidebar chat (kunci konfigurasi `agent.reasoning_effort` sing padha)
- **Konfigurasi:** `agent.reasoning_effort: medium` ing `config.yaml`
- **Override per-model:** `agent.reasoning_overrides: { "model-id": "high" }`

### Migrasi pematian lawas

Sadurunge `none`, `false`, `off`, `disabled`, nilai kosong, boolean YAML `False`, utawa `--reasoning_disabled` mateni thinking. Ing kabijakan tansah-aktif, kabèh iki saiki rampung dadi **medium** (`{"enabled": true, "effort": "medium"}`) dadi reasoning ora nate mati kanthi sepi. Level sing ora dikenal (mis. `turbo`) tetep bali menyang default pemanggil; flag `--reasoning_disabled` batch-runner sing wis ora dienggo mung ana kanggo kompatibilitas mundur lan nyithak notifikasi pematian.

---

## Referensi Cepet CLI vs Messaging

Synapse nduwé rong titik mlebu: miwiti antarmuka terminal nganggo `synapse`, utawa mlakokaké gateway lan omongan karo dhèwèké saka Telegram, Discord, Slack, WhatsApp, Signal, utawa Email. Sawisé ana ing obrolan, akèh perintah garis-miring dienggo bareng ing loro antarmuka.

| Aksi                          | CLI                                           | Platform pesen                                                            |
|-------------------------------|-----------------------------------------------|----------------------------------------------------------------------------|
| Miwiti ngobrol                | `synapse`                                     | Lakokaké `synapse gateway setup` + `synapse gateway start`, banjur kirim pesen menyang bot |
| Bukak panel admin             | `synapse dashboard`                           | —                                                                          |
| Miwiti obrolan anyar          | `/new` utawa `/reset`                         | `/new` utawa `/reset`                                                      |
| Ganti model                   | `/model [provider:model]`                     | `/model [provider:model]`                                                  |
| Atur kapribaden              | `/personality [name]`                         | `/personality [name]`                                                      |
| Coba manèh / mbatalake giliran | `/retry`, `/undo`                             | `/retry`, `/undo`                                                          |
| Kompres konteks / cek usage   | `/compress`, `/usage`, `/insights [--days N]` | `/compress`, `/usage`, `/insights [days]`                                  |
| Golèki katrampilan            | `/skills` utawa `/<jeneng-katrampilan>`       | `/<jeneng-katrampilan>`                                                    |
| Dhaftarake sesi               | `synapse session list`                        | —                                                                          |
| Busak sesi saiki             | `/delete`                                     | —                                                                          |
| Busak siji/kabèh sesi         | `synapse session delete <id>` / `--all`       | —                                                                          |
| Interupsi pekerjaan mlaku     | `Ctrl+C` utawa kirim pesen anyar              | `/stop` utawa kirim pesen anyar                                           |
| Status khusus platform        | `/platforms`                                  | `/status`, `/sethome`                                                      |

Kanggo daftar perintah lengkap, deleng pandhuan CLI lan pandhuan Messaging Gateway.

---

---

## Migrasi saka OpenClaw

Yèn kowé teka saka OpenClaw, Synapse bisa ngimpor setelan, memori, katrampilan, lan kunci API-mu sacara otomatis.

**Nalika penyiapan pisanan:** Wizard penyiapan (`synapse setup`) ndeteksi `~/.openclaw` sacara otomatis lan nawakake migrasi sadurunge konfigurasi diwiwiti.

**Kapan waé sawisé instalasi:**

```bash
synapse claw migrate              # Migrasi interaktif (preset lengkap)
synapse claw migrate --dry-run    # Pratinjau apa sing bakal dimigrasi
synapse claw migrate --preset user-data   # Migrasi tanpa secret
synapse claw migrate --overwrite  # Timpa konflik sing ana
```

Sing diimpor:

- **SOUL.md** — file persona
- **Memories** — entri MEMORY.md lan USER.md
- **Skills** — katrampilan gawéan pangguna → `~/.synapse/skills/openclaw-imports/`
- **Command allowlist** — pola persetujuan
- **Messaging settings** — konfigurasi platform, pangguna sing diidini, direktori kerja
- **API keys** — secret sing mlebu dhafar putih (Telegram, OpenRouter, OpenAI, Anthropic, ElevenLabs)
- **TTS assets** — file audio workspace
- **Workspace instructions** — AGENTS.md (kanthi `--workspace-target`)

Deleng `synapse claw migrate --help` kanggo kabèh opsi, utawa gunakna katrampilan `openclaw-migration` kanggo migrasi interaktif sing dipandu agen kanthi pratinjau dry-run.

---

## Google Drive

Synapse bisa maca lan nulis Google Drive pangguna liwat katrampilan bawaan
(`skills/google-drive`). Dhèwèké nganggo Drive REST API karo OAuth — tanpa SDK Google
sing abot, mung `requests` (wis dadi dependensi inti).

Atur sepisan kanthi nglakokaké helper bawaan:

```bash
python3 skills/google-drive/google-drive/scripts/gdrive.py setup
```

Wizard nuntun pangguna liwat Google Cloud Console (aktifake Drive
API, gawé Desktop OAuth client, undhuh `credentials.json`), banjur mbukak
browser kanggo idin lan nyimpen token sacara lokal. File kredensial
(`credentials.json`, `token.json`) di-ignore git lan ora nate di-commit.

Banjur agen bisa nyopir Drive atas nama pangguna:

```bash
python3 skills/google-drive/google-drive/scripts/gdrive.py list
python3 skills/google-drive/google-drive/scripts/gdrive.py search "annual report"
python3 skills/google-drive/google-drive/scripts/gdrive.py upload notes.md
python3 skills/google-drive/google-drive/scripts/gdrive.py download <file_id>
```

Kredensial sing padha makarya ing Windows, Termux, VPS, utawa Railway — salin
`credentials.json` (lan `token.json`) dadi njero checkout lan lakokaké `setup` manèh.
Deleng `skills/google-drive/google-drive/SKILL.md` kanggo detail lengkap.

---

## Nyumbang

Kita nampa kontribusi! Deleng Pandhuan Nyumbang kanggo pengaturan pangembangan, gaya kode, lan prosès PR.

Miwiti cepet kanggo kontributor — gunakna installer standar, banjur makarya saka
checkout git lengkap sing digawé ing `$SYNAPSE_HOME/synapse-agent` (biasane
`~/.synapse/synapse-agent`). Iki cocog karo tata letak sing dienggo `synapse update`, venv sing dikelola, dependensi lazy, gateway, lan tooling docs.

```bash
curl -fsSL https://raw.githubusercontent.com/johsua092-ui/synapse-ai-agent/main/scripts/install.sh | bash
cd "${SYNAPSE_HOME:-$HOME/.synapse}/synapse-agent"
uv pip install -e ".[all,dev]"
scripts/run_tests.sh
```

Fallback clone manual (kanggo clone sekali-pakai/CI ing ngendi kowé pancen ora
pengin tata letak instalasi sing dikelola):

Gawé venv ing njaba pohon sumber sing dikloning — venv ing njero direktori
ing ngendi agen makarya bisa dibusak déning perintah adhedhasar path relatif sing dilakokaké agen
marang checkout-é dhéwé, ngrusak runtime sing lagi mlaku ing tengah sesi.

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
uv venv ~/.synapse/venvs/synapse-dev --python 3.11
source ~/.synapse/venvs/synapse-dev/bin/activate
uv pip install -e ".[all,dev]"
scripts/run_tests.sh
```

---

## Lisènsi

MIT — deleng [LICENSE](LICENSE).
