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

**خود بہتر ہونے والا AI ایجنٹ جو Josh Research نے بنایا۔** یہ واحد ایجنٹ ہے جس میں داخلی لرننگ لوپ ہے — یہ تجربے سے مہارتیں بناتا ہے، استعمال کے دوران انہیں بہتر بناتا ہے، خود کو معلومات برقرار رکھنے کی ترغیب دیتا ہے، اپنی ماضی کی گفتگو تلاش کرتا ہے، اور آپ کے بارے میں سیشنز میں گہرتا ہوا ماڈل بناتا رہتا ہے۔ اسے $5 کے VPS، GPU کلسٹر، یا سرورلیس انفراسٹرکچر پر چلائیں جہاں سکونت پر تقریباً کچھ بھی خرچ نہیں ہوتا۔ یہ آپ کے لیپ ٹاپ سے بندھا ہوا نہیں — جب یہ کلاوڈ VM پر کام کر رہا ہو تو Telegram سے اس سے بات کریں۔

کوئی بھی ماڈل استعمال کریں — OpenRouter، OpenAI، اپنا اینڈپوائنٹ، اور بہت سے دیگر پرووائیڈرز۔ `synapse model` سے تبدیل کریں — کوڈ میں تبدیلی نہیں، کوئی لاک ان نہیں۔

<table>
<tr><td><b>اصل ٹرمINAL انٹرفیس</b></td><td>ملٹی لائن ایڈیٹنگ، سلیش کمانڈ آٹو کمپلیٹ، گفتگو کی تاریخ، رک کر نیچے جانے اور سٹریمنگ ٹول آؤٹ پٹ کے ساتھ مکمل TUI۔</td></tr>
<tr><td><b>جہاں آپ ہیں وہیں رہتا ہے</b></td><td>Telegram، Discord، Slack، WhatsApp، Signal، اور CLI — سب ایک صرف گیٹ way پروسیس سے۔ وائس میمو ٹرانسکرپشن، کراس پلیٹ فارم گفتگو کا تسلسل۔</td></tr>
<tr><td><b>بند لرننگ لوپ</b></td><td>ایجنٹ-منتخب معموری باوقات پیروشر کے ساتھ۔ پیچیدہ کاموں کے بعد خودکار مہارت تخلیق۔ مہارتیں استعمال کے دوران خود بہتر ہوتی ہیں۔ کراس سیشن یادداشت کے لیے LLM خلاصہ بندی کے ساتھ FTS5 سیشن تلاش۔ <a href="https://github.com/plastic-labs/honcho">Honcho</a> جدید صارف ماڈلنگ۔ <a href="https://agentskills.io">agentskills.io</a> کھلے معیار سے مطابقت۔</td></tr>
<tr><td><b>شیڈول خودکاریاں</b></td><td>داخلی کرون شیڈولر جو کسی بھی پلیٹ فارم پر ڈیلیوری کرتا ہے۔ روزانہ رپورٹس، رات کی بیک اپ، ہفتہ وار آڈٹ — سب قدرتی زبان میں، بے سر اجرا ہو رہا ہے۔</td></tr>
<tr><td><b>تفویض اور پیراللائزیشن</b></td><td>پیرالل ورک اسٹریمز کے لیے الگ تھلگ سب ایجنٹ بنائیں۔ پائTHON اسکرپٹس لکھیں جو RPC کے ذریعے ٹولز کو بلاتی ہیں، کثیر مرحلہ پائپ لائنز کو صفر کنٹیکسٹ کاسٹ ٹرنس میں بنا دیتی ہیں۔</td></tr>
<tr><td><b>کہیں بھی چلتا ہے، صرف آپ کے لیپ ٹاپ پر نہیں</b></td><td>سات ٹرمINAL بیک اینڈز — لوکل، Docker، SSH، Singularity، Modal، Daytona، اور Vercel Sandbox۔ Daytona اور Modal سرورلیس معموری پیشکش کرتے ہیں — آپ کے ایجنٹ کا ماحول سکونت پر سو جاتا ہے اور ضرورت پر جاگتا ہے، سیشنز کے درمیان تقریباً کچھ بھی خرچ نہیں ہوتا۔ اسے $5 کے VPS یا GPU کلسٹر پر چلائیں۔</td></tr>
<tr><td><b>research کے لیے تیار</b></td><td>بیچ ٹریجیکٹری تخلیق، ٹول کالنگ ماڈلز کی نسل بڑھانے کی تربیت کے لیے ٹریجیکٹری کمپریشن۔</td></tr>
</table>

---

## فوری انسٹالیشن

### npm (تمام پلیٹ فارمز)

```bash
npx synapse-ai-agent
```

آپ کے OS کے لیے سرکاری انسٹالر ڈاؤن لوڈ اور چلاتا ہے — Node کا معلومات ضروری نہیں، شِم صرف اسے بوٹسٹریپ کرتا ہے۔

### Linux، macOS، WSL2، Termux

```bash
curl -fsSL https://raw.githubusercontent.com/johsua092-ui/synapse-ai-agent/main/scripts/install.sh | bash
```

### Windows (native، PowerShell)

> **نوٹ:** Native Windows Synapse کو WSL کے بغیر چلاتا ہے — CLI، گیٹ way، TUI، اور ٹولز سب native طریقے سے کام کرتے ہیں۔ اگر آپ WSL2 استعمال کرنا چاہتے ہیں تو اوپر والا Linux/macOS ڈبہ وہاں بھی کام کرتا ہے۔ کوئی باگ ملا؟ براہ کرم [issues درج کریں](https://github.com/johsua092-ui/synapse-ai-agent/issues)۔

PowerShell میں یہ چلائیں:

```powershell
iex (irm https://raw.githubusercontent.com/johsua092-ui/synapse-ai-agent/main/scripts/install.ps1)
```

انسٹالر سب سambھال لیتا ہے: uv، Python 3.11، Node.js، ripgrep، ffmpeg، **اور ایک پورٹیبل Git Bash** (MinGit، `%LOCALAPPDATA%\synapse\git` پر ان پیک — ایڈمن کی ضرورت نہیں، کسی بھی سسٹم Git انسٹال سے مکمل طور پر الگ)۔ Synapse اس بنڈل Git Bash کو شیل کمانڈز چلانے کے لیے استعمال کرتا ہے۔

اگر آپ کے پاس پہلے Git انسٹال ہے تو انسٹالر اس کا پتہ لگا لیتا ہے اور اسی کو استعمال کرتا ہے۔ ورنہ صرف ~45MB MinGit ڈاؤن لوڈ کی ضرورت ہے — یہ کسی بھی سسٹم Git کو چھوئے گا یا مداخلت نہیں کرے گا۔

> **Android / Termux:** ٹیسٹ کی گئی دستی راہ Termux گائیڈ میں دستاویزی شدہ ہے۔ Termux پر، Synapse ایک منتخب `.[termux]` ایکسٹرا انسٹال کرتا ہے کیونکہ مکمل `.[all]` ایکسٹرا فی الحال Android سے غیر مطابقت پذیر وائس منڈیٹوں کو کھینچتا ہے۔
>
> **Windows:** Native Windows مکمل طور پر سپورٹ ہے — اوپر والا PowerShell ڈبہ سب کچھ انسٹال کرتا ہے۔ اگر آپ WSL2 استعمال کرنا چاہتے ہیں تو Linux کمانڈ وہاں بھی کام کرتی ہے۔ Native Windows انسٹالیشن `%LOCALAPPDATA%\synapse` کے تحت ہوتی ہے؛ WSL2 انسٹالیشن Linux کی طرح `~/.synapse` کے تحت ہوتی ہے۔

انسٹالیشن کے بعد:

```bash
source ~/.bashrc    # ریلوڈ شیل (یا: source ~/.zshrc)
synapse              # گفتگو شروع کریں!
```

### ٹربleshootنگ

#### Windows Defender یا اینٹی وائرس `uv.exe` کو مالویئر کے طور پر فلیگ کرتا ہے

اگر آپ کا اینٹی وائرس (Bitdefender، وغیرہ) Synapse کے `bin` فولڈر (`%LOCALAPPDATA%\synapse\bin\uv.exe`) سے `uv.exe` کو قید کر لیتا ہے تو یہ **غلط پوزیٹو** ہے۔ فائل Astral کا `uv` ہے — روست Python پیکج مینیجر جو Synapse اپنا Python ماحول منظم کرنے کے لیے بنڈل کرتا ہے۔ ML-محور اینٹی وائرس انجنز عام طور پر signed نہ ہونے والی روست بائینریز کو فلیگ کرتے ہیں جو پیکج ڈاؤن لوڈ اور انسٹال کرتی ہیں۔

**اپنی کاپی کی تصدیق کے لیے:**

```powershell
# GitHub CLI انسٹال کریں اگر ضروری ہو
winget install --id GitHub.cli

# GitHub پر لاگ ان کریں
gh auth login

# تصدیق چلائیں
$uv = "$env:LOCALAPPDATA\synapse\bin\uv.exe"
$ver = (& $uv --version).Split(' ')[1]
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
$zip = "$env:TEMP\uv.zip"
Invoke-WebRequest "https://github.com/astral-sh/uv/releases/download/$ver/uv-x86_64-pc-windows-msvc.zip" -OutFile $zip -UseBasicParsing
gh attestation verify $zip --repo astral-sh/uv
Expand-Archive $zip "$env:TEMP\uv_x" -Force
(Get-FileHash "$env:TEMP\uv_x\uv.exe").Hash -eq (Get-FileHash $uv).Hash
```

اگر attestation "Verification succeeded" کہتا ہے اور آخری لائن `True` پرنٹ کرتی ہے تو آپ ٹھیک ہیں۔

**Synapse کو وائٹ لسٹ میں شامل کرنے کے لیے:**
- **Windows Defender:** PowerShell کو ایڈمن کے طور پر چلائیں → `Add-MpPreference -ExclusionPath "$env:LOCALAPPDATA\synapse\bin"`
- **Bitdefender:** Bitdefender کنسول میں ایکسیپشن شامل کریں (Protection > Antivirus > Settings > Manage Exceptions)
- **فولڈر** کو وائٹ لسٹ میں شامل کریں، فائل ہیش نہیں — Synapse `uv` کو اپ ڈیٹ کرتا ہے اور ہر ورژن میں ہیش بدل جاتا ہے

مزید سیاقت کے لیے، Astral رپورٹس دیکھیں: [astral-sh/uv#13553](https://github.com/astral-sh/uv/issues/13553)، [astral-sh/uv#15011](https://github.com/astral-sh/uv/issues/15011)، [astral-sh/uv#10079](https://github.com/astral-sh/uv/issues/10079)۔

---

## Railway پر ڈیپلوی

Synapse Agent کو [Railway](https://railway.app) پر ون کلک کنٹینر سروس کے طور پر ڈیپلوی کریں۔ تصویر پہلے سے s6-overlay entrypoint اور supervised ویب ڈیش بورڈ کے ساتھ آتی ہے۔

[![Deploy on Railway](https://railway.com/button.svg)](https://railway.com/template/synapse-agent?referralCode=QXdhdr)

### آپ کو کیا ملتا ہے

- **ویب ڈیش بورڈ** عوامی Railway URL پر (auth-gated، نیچے دیکھیں)
- **مستقل والیوم** ایجنٹ سٹیٹ کے لیے (`/opt/data` / `$SYNAPSE_HOME` پر والیوم ماؤنٹ کریں)
- **صحت جانچ** `/api/health` سے جڑی ہوئی

### سیٹ اپ

1. اوپر **Deploy on Railway** پر کلک کریں (یا اس ریپو سے نئی سروس بنائیں — Railway خود `railway.toml` + `Dockerfile` کا پتہ لگا لیتا ہے)۔
2. `/opt/data` پر ماؤنٹ کیا ہوا والیوم منسلک کریں۔
3. ضروری سروس متغیرات شامل کریں ([.env.railway.example](.env.railway.example) دیکھیں۔) کم از کم:
   - `SYNAPSE_DASHBOARD=1`
   - ایک auth پروائیڈر — **Basic Auth** (`SYNAPSE_DASHBOARD_BASIC_AUTH_USERNAME` + `SYNAPSE_DASHBOARD_BASIC_AUTH_PASSWORD`) یا OAuth/OIDC۔ اس کے بغیر ڈیش بورڈ عوامی بائنڈ پر **بند** ہو جاتا ہے۔
4. اپنی ماڈل/پروائیڈر API کلیدیں شامل کریں (`OPENROUTER_API_KEY`، `OPENAI_API_KEY`، وغیرہ)۔

### Docker (خود میزبانی)

```bash
SYNAPSE_UID=$(id -u) SYNAPSE_GID=$(id -g) docker compose up -d
```

مکمل supervised سیٹ اپ کے لیے `docker-compose.yml` اور `docker/` ڈائریکٹری دیکھیں۔ Windows compose ویریئنٹ `docker-compose.windows.yml` میں ہے۔

---

## شروع کیسے کریں

```bash
synapse              # انٹراکٹو CLI — گفتگو شروع کریں
synapse model        # اپنا LLM پروائیڈر اور ماڈل منتخب کریں
synapse dashboard    # اپنے براؤزر میں ایڈمن پینل کھولیں (پورٹ 9119)
synapse tools        # کون سے ٹولز فعال ہیں ترتیب دیں
synapse config set   # انفرادی کنفیگریشن ویلیز سیٹ کریں
synapse config get   # انفرادی کنفیگریشن ویلیز پرنٹ کریں
synapse gateway      # میسجنگ گیٹ way شروع کریں (Telegram، Discord، وغیرہ)
synapse setup        # مکمل سیٹ اپ وizard چلائیں (ایک ساتھ سب کچھ ترتیب دیتا ہے)
synapse claw migrate # OpenClaw سے مائیگریٹ کریں (اگر OpenClaw سے آ رہے ہیں)
synapse update       # تازہ ترین ورژن پر اپ ڈیٹ کریں
synapse doctor       # کوئی بھی مسائل تشخیص کریں
```

### ایڈمن پینل

`synapse dashboard` کمانڈ `http://127.0.0.1:9119` پر ایک مقامی ویب ایڈمن پینل شروع کرتی ہے۔ یہ پرووائیڈرز ترتیب دینے، چینلز منظم کرنے، لاگز دیکھنے، اور اپنے ایجنٹ کی نگرانی کے لیے براؤزر-محور UI فراہم کرتا ہے۔

```bash
synapse dashboard                        # براؤزر میں کھولیں، پورٹ 9119
synapse dashboard --port 8080            # حسب ضرورت پورٹ
synapse dashboard --host 0.0.0.0         # تمام انٹرفیسز پر بائنڈ (ریموٹ رسائی کے لیے)
synapse dashboard --no-open              # براؤزر خود نہ کھولیں
synapse dashboard --skip-build           # React بلڈ سکیپ کریں، پہلے سے بلڈ شدہ ایڈمن HTML استعمال کریں
```

خصوصیات:
- **سیٹ اپ** — LLM پروائیڈرز، API کلیدیں، اور میسجنگ چینلز ترتیب دیں
- **سٹیٹس** — گیٹ way کی حالت، اپ ٹائم، اور فعال سیشنز کی نگرانی کریں
- **لاگز** — ریئل ٹائم ایجنٹ لاگز دیکھیں
- **صارفین** — جوڑنے کی درخواستیں اور تسلیم شدہ صارفین منظم کریں
- **بیک اپ اور بحالی** — ڈیپلوی اسنیپ شاٹ ڈاؤن لوڈ/اپ لوڈ کریں

📖 **مکمل دستاویزات نیچے دی گئی ہیں۔**

---

## سیشن مینجمنٹ

Synapse ہر سیشن کے لیے گفتگو کی تاریخ رکھتا ہے۔ `synapse session` کمانڈ CLI سے سیشنز کی فہرست بنانے اور حذف کرنے کی اجازت دیتی ہے، اور `/delete` گفتگو کے اندر سے یہ کام کرتا ہے۔ یہ ڈیش بورڈ کے ساتھ SessionDB بیک اینڈ کا استعمال کرتا ہے، اس لیے CLI، ڈیش بورڈ، اور چیٹ پلیٹ فارمز میں ایک ہی حذف تحمیل ہے۔

```bash
synapse session list                    # تمام مستقبل سیشنز کی فہرست
synapse session delete <session-id>     # ایک سیشن مستقل طور پر حذف کریں
synapse session delete --all            # ہر سیشن حذف کریں (پہلے وارننگ)
synapse session delete <session-id> -y  # تصدیق کی پرامپٹ سکیپ کریں
synapse session --help                  # مکمل استعمال
```

`delete` ہمیشہ تصدیق کرتا ہے کہ سیشن موجود ہے اور اگر نہیں ہے تو نہیں ملا ایرر پرنٹ کرتا ہے۔ واحد حذف سیشن کی معلومات دکھاتا ہے اور تکلفناک کام کرنے سے پہلے تصدیق مانگتا ہے؛ `delete --all` کو مزید سخت تصدیق کی ضرورت ہوتی ہے (یا `--yes`)۔

گفتگو کے اندر، `/delete` (یا `/delete -y`) موجودہ فعال سیشن کو مستقل طور پر حذف کرتا ہے اور ایک تازہ شروع کرتا ہے۔

ڈیش بورڈ کے سیشنز صفحے پر حذف بٹن، تصدیق ڈائیلاگ، حذف کے بعد ریفریش، اور ایرر/خالی حالت کے ساتھ وہی آپریشنز دستیاب ہیں — سب SessionDB کی حمایت سے۔

## بنڈل مہارتیں

Synapse ایک سیٹ بنڈل مہارتیں کے ساتھ آتا ہے جو انسٹالیشن اور اپ ڈیٹ پر `~/.synapse/skills/` میں سنک ہوتی ہیں (`tools/skills_sync.py` دیکھیں۔)۔ یہ `skills/superpowers/` کے تحت [Superpowers](https://github.com/obra/superpowers) ڈیوپلمنٹ ورک فلو مہارتیں بھی بنڈل کرتا ہے — جس میں `brainstorming`، `writing-plans`، `executing-plans`، `systematic-debugging` (موجودہ سافٹ ویئر ڈیوپلمنٹ بنڈل کے ذریعے)، `test-driven-development`، اور مزید شامل ہیں۔ یہ وہی بنڈل-مہارت سنک کا استعمال کرتے ہیں، اس لیے یہ ہر تازہ پروفائل میں خودکار طور پر دستیاب ہیں۔

جیسے `systematic-debugging`، `test-driven-development`، `requesting-code-review` جیسی مہارتیں جو پہلے سے موجودہ بنڈل مہارت کے ساتھ نام شریک رکھتی ہیں، Synapse موجودہ بنڈل کاپی رکھتا ہے — اس سے sync مانیفیسٹ میں ڈوبلیٹ نام ٹکرنا ت避免 ہوتا ہے۔

---

## ڈیزائن سے پروائیڈر-آگنسٹک

Synapse آپ کے پسندیدہ پروائیڈر کے ساتھ کام کرتا ہے — یہ نہیں بدل رہا۔ کوئی بھی OpenRouter، OpenAI، یا کسٹم اینڈپوائنٹ لائیں اور ایک بار جوڑیں۔ `synapse model` سے تبدیل کریں — کوڈ میں تبدیلی نہیں، کوئی لاک ان نہیں۔

آپ ہر ٹول کے لیے اپنی کلیدیں بھی لا سکتے ہیں — گیٹ way ہر بیک اینڈ کے لیے ہے، سب یا کچھ نہیں۔

---

## سوچ اور استدلال

Synapse ڈیفالٹ پر سوچ/استدلال فعال رکھتا ہے اور کبھی نہیں ہونے دیتا کہ کوئی کنفیگریشن ویلیے اسے بند کر دے۔ یہ **ہمیشہ فعال استدلال** پالیسی ہے — جو ماڈلز استدلال ٹوکن کی معاونت کرتے ہیں وہ ہمیشہ استعمال کرتے ہیں؛ جو نہیں کرتے ان پر کوئی اثر نہیں پڑتا (کوئی غیر قانونی پروائیڈر پیرامیٹرز نہیں بھیجے جاتے)۔

### کوشش کی سطحیں

صرف تین کوشش کی سطحیں ہیں، پرانی چوڑی سیڑھی سے نکالی گئی:

| سطح | تSubview                                               |
|-------|--------------------------------------------------------|
| درمیانی| متوازن رفتار اور قیمت (ڈیفالٹ)                  |
| زیادہ  | گہرا استدلال — ہر ٹرن پر سست اور مہنگا        |
| زیادہ سے زیادہ   | طاقتور استدلال — ہر ٹرن پر سب سے سست اور مہنگا   |

### سطح مقرر کریں

- **CLI:** `/reasoning medium | high | max`
- **ڈیش بورڈ:** چیٹ سائیڈ بار میں Reasoning پکار (وہی `agent.reasoning_effort` کنفیگریشن کلید)
- **کنفیگریشن:** `config.yaml` میں `agent.reasoning_effort: medium`
- **ہر ماڈل اوور رائیڈ:** `agent.reasoning_overrides: { "model-id": "high" }`

### پرانی بند تحمیل

پہلے `none`، `false`، `off`، `disabled`، خالی ویلیہ، YAML بولین `False`، یا `--reasoning_disabled` سوچ کو بند کرتا تھا۔ ہمیشہ فعال پالیسی کے تحت ان میں سے سب اب **درمیانی** (`{"enabled": true, "effort": "medium"}`) پر حل ہوتے ہیں تاکہ استدلال کبھی خاموشی سے بند نہ ہو۔ نامعلوم سطح (جیسے `turbo`) ابھی بھی بلانے والے کے ڈیفالٹ پر واپس جاتی ہے؛ deprecated `--reasoning_disabled` بیچ رنر فلیگ صرف پچھلی مطابقت کے لیے ہے اور ایک deprecated نوٹس پرنٹ کرتا ہے۔

---

## CLI بنسبت میسجنگ فوری حوالہ

Synapse کے دو انٹری پوائنٹس ہیں: `synapse` سے ٹرمINAL UI شروع کریں، یا گیٹ way چلائیں اور Telegram، Discord، Slack، WhatsApp، Signal، یا Email سے بات کریں۔ ایک بار جب آپ گفتگو میں ہوں، بہت سے سلیش کمانڈز دونوں انٹرفیسز میں شریک ہیں۔

| عمل                         | CLI                                           | میسجنگ پلیٹ فارمز                                                              |
| گفتگو شروع کریں                 | `synapse`                                      | `synapse gateway setup` + `systhesis gateway start` چلائیں، پھر بوٹ کو پیغام بھیجیں |
| ایڈمن پینل کھولیں               | `synapse dashboard`                            | —                                                                                |
| نئی گفتگو شروع کریں       | `/new` یا `/reset`                            | `/new` یا `/reset`                                                               |
| ماڈل تبدیل کریں                   | `/model [provider:model]`                     | `/model [provider:model]`                                                        |
| شخصیت سیٹ کریں              | `/personality [name]`                         | `/personality [name]`                                                            |
| پچھلی ٹرن دہرائیں یا کالعدم کریں    | `/retry`، `/undo`                             | `/retry`، `/undo`                                                                |
| کنٹیکسٹ کمپریس کریں / استعمال جانچیں | `/compress`، `/usage`، `/insights [--days N]` | `/compress`، `/usage`، `/insights [days]`                                        |
| مہارتیں دیکھیں                  | `/skills` یا `/<skill-name>`                  | `/<skill-name>`                                                                  |
| سیشنز کی فہرست                  | `synapse session list`                        | —                                                                                |
| موجودہ سیشن حذف کریں         | `/delete`                                     | —                                                                                |
| سیشن / سب حذف کریں         | `synapse session delete <id>` / `--all`       | —                                                                                |
| موجودہ کام میں رکاوٹ         | `Ctrl+C` یا نیا پیغام بھیجیں                | `/stop` یا نیا پیغام بھیجیں                                                    |
| پلیٹ فارم خاص سٹیٹس       | `/platforms`                                  | `/status`، `/sethome`                                                            |

مکمل کمانڈ لسٹ کے لیے CLI گائیڈ اور Messaging Gateway گائیڈ دیکھیں۔

---

---

## OpenClaw سے مائیگریشن

اگر آپ OpenClaw سے آ رہے ہیں تو Synapse خودکار طور پر آپ کی ترتیبات، یادداشتیں، مہارتیں، اور API کلیدیں درآمد کر سکتا ہے۔

**پہلی بار سیٹ اپ کے دوران:** سیٹ اپ وizard (`synapse setup`) خودکار طور پر `~/.openclaw` کا پتہ لگاتا ہے اور ترتیب شروع ہونے سے پہلے مائیگریشن کی پیشکش کرتا ہے۔

**انسٹالیشن کے بعد کسی بھی وقت:**

```bash
synapse claw migrate              # انٹراکٹو مائیگریشن (مکمل پری سیٹ)
synapse claw migrate --dry-run    # پیش نظارہ کریں کہ کیا مائیگریٹ ہوگا
synapse claw migrate --preset user-data   # رازداری کے بغیر مائیگریٹ کریں
synapse claw migrate --overwrite  # موجودہ تصادمات اوور رائیڈ کریں
```

کیا درآمد ہوتا ہے:

- **SOUL.md** — شخصیت فائل
- **یادداشتیں** — MEMORY.md اور USER.md اندراجات
- **مہارتیں** — صارف-تخلیق شدہ مہارتیں → `~/.synapse/skills/openclaw-imports/`
- **کمانڈ اجازت فہرست** — تصدیق کے نمونے
- **میسجنگ ترتیبات** — پلیٹ فارم کنفیگریشن، اجازت یافتہ صارفین، کام کا ڈائریکٹری
- **API کلیدیں** — اجازت یافتہ راز (Telegram، OpenRouter، OpenAI، Anthropic، ElevenLabs)
- **TTS اثاثے** — ورک اسپیس آڈیو فائلز
- **ورک اسپیس ہدایات** — AGENTS.md (`--workspace-target` کے ساتھ)

تمام اختیارات کے لیے `synapse claw migrate --help` دیکھیں، یا ڈرائی رن پیش نظارے کے ساتھ انٹراکٹو ایجنٹ-ہدایت مائیگریشن کے لیے `openclaw-migration` مہارت استعمال کریں۔

---


## Google Drive

Synapse بنڈل مہارت (`skills/google-drive`) کے ذریعے صارف کے Google Drive کو پڑھ اور لکھ سکتا ہے۔ یہ OAuth کے ساتھ Drive REST API استعمال کرتا ہے — کوئی بھاری Google SDK نہیں، صرف `requests` (پہلے سے ایک بنیادی منڈی)۔

اسے ایک بار ترتیب دینے کے لیے بنڈل شدہ مددگار چلائیں:

```bash
python3 skills/google-drive/google-drive/scripts/gdrive.py setup
```

وizard صارف کو Google Cloud Console میں لے جاتا ہے (Drive API فعال کریں، Desktop OAuth client بنائیں، `credentials.json` ڈاؤن لوڈ کریں)، پھر رضامندی کے لیے براؤزر کھولتا ہے اور ٹوکن مقامی طور پر کیش کرتا ہے۔ سیکرٹ فائلز (`credentials.json`، `token.json`) سے ignore ہوتے ہیں اور کبھی commit نہیں ہوتے۔

پھر ایجنٹ صارف کی نمائندگی میں Drive چلا سکتا ہے:

```bash
python3 skills/google-drive/google-drive/scripts/gdrive.py list
python3 skills/google-drive/google-drive/scripts/gdrive.py search "annual report"
python3 skills/google-drive/google-drive/scripts/gdrive.py upload notes.md
python3 skills/google-drive/google-drive/scripts/gdrive.py download <file_id>
```

وہی سیکرٹ Windows، Termux، VPS، یا Railway پر بھی کام کرتے ہیں — `credentials.json` (اور `token.json`) کو چیک آؤٹ میں کاپی کریں اور دوبارہ `setup` چلائیں۔ مکمل تفصیلات کے لیے `skills/google-drive/google-drive/SKILL.md` دیکھیں۔

---

## شراکت

ہم شراکت کا خوش آمدید کرتے ہیں! ڈیوپلمنٹ سیٹ اپ، کوڈ اسٹائل، اور PR عمل کے لیے شراکت گائیڈ دیکھیں۔

شراکت کاروں کے لیے فوری شروع — معیاری انسٹالر استعمال کریں، پھر `$SYNAPSE_HOME/synapse-agent` (عام طور پر `~/.synapse/synapse-agent`) میں بنائے گئے مکمل git چیک آؤٹ سے کام کریں۔ یہ `synapse update`، managed venv، lazy منڈیز، گیٹ way، اور دستاویزات ٹولز کے لیے استعمال ہونے والا لے آؤٹ ملتا ہے۔

```bash
curl -fsSL https://raw.githubusercontent.com/johsua092-ui/synapse-ai-agent/main/scripts/install.sh | bash
cd "${SYNAPSE_HOME:-$HOME/.synapse}/synapse-agent"
uv pip install -e ".[all,dev]"
scripts/run_tests.sh
```

دستی کلون fallback ( Ala وقتی کلونز/CI کے لیے جہاں آپ جان بوجھ کر managed انسٹال لے آؤٹ نہیں چاہتے):

کلون کی گئی سورس ٹری کے باہر venv بنائیں — ایجنٹ کے چلنے والے ڈائریکٹری کے اندر venv ایجنٹ کے اپنے چیک آؤٹ کے خلاف relative-path کمانڈ سے مٹایا جا سکتا ہے، جو سیشن کے درمیان چلنے والا run-time تباہ کر سکتا ہے۔

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
uv venv ~/.synapse/venvs/synapse-dev --python 3.11
source ~/.synapse/venvs/synapse-dev/bin/activate
uv pip install -e ".[all,dev]"
scripts/run_tests.sh
```

---

## لائسنس

MIT — [LICENSE](LICENSE) دیکھیں۔
