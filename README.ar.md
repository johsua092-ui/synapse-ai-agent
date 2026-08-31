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

**وكيل الذكاء الاصطناعي المُحسّن ذاتياً الذي بناه Josh Research.** إنه الوكيل الوحيد مع حلقة تعلم مدمجة — يُنشئ مهارات من التجربة، ويحسّنها أثناء الاستخدام، ويُحفّز نفسه على حفظ المعرفة، ويبحث في محادثاته السابقة، ويُبني نموذجاً متعمقاً لصفاتك عبر الجلسات. شغّله على خادم افتراضي بـ 5 دولارات، أو مجموعة وحدات معالجة رسوميات، أو بنية تحتية بدون خادم تكلفة شبه معدومة عند الخمول. إنه غير مرتبط بجهازك المحمول — تحدّثه عبر Telegram وهو يعمل على آلة افتراضية سحابية.

استخدم أي نموذج تريده — OpenRouter، OpenAI، نقطة الوصول الخاصة بك، ومزودين آخرين רבים..badgeswitch باستخدام `synapse model` — بدون تغييرات في الكود، بدون اقفال.

<table>
<tr><td><b>واجهة طرفية حقيقية</b></td><td>واجهة مستخدم كاملة مع تحرير متعدد الأسطر، وإكمال تلقائي للأوامر المنقاطة، وسجل المحادثات، وإيقاف وإعادة توجيه، ومخرجات الأدوات بالتدفق.</td></tr>
<tr><td><b>يعيش حيث أنت</b></td><td>Telegram، Discord، Slack، WhatsApp، Signal، وواجهة طرفية — جميعها من عملية بوابة واحدة. تحويل المذكرات الصوتية، واستمرارية المحادثات عبر المنصات.</td></tr>
<tr><td><b>حلقة تعلم مغلقة</b></td><td>ذاكرة يُديرها الوكيل مع تذكيرات دورية. إنشاء مهارات مستقل بعد المهام المعقدة. تحسين المهارات ذاتياً أثناء الاستخدام. بحث FTS5 مع تلخيص LLM للتذكر عبر الجلسات. نمذجة جدلية للمستخدم عبر <a href="https://github.com/plastic-labs/honcho">Honcho</a>. متوافق مع المعيار المفتوح <a href="https://agentskills.io">agentskills.io</a>.</td></tr>
<tr><td><b>أتمتة مجدولة</b></td><td>مجدول cron مدمج مع التوصيل إلى أي منصة. تقارير يومية، نسخ احتياطي ليلي، مراجعات أسبوعية — جميعها بلغة طبيعية، تعمل دون إشراف.</td></tr>
<tr><td><b>مناوبات و توازي</b></td><td>إنشاء وكيل فرعي معزول لتدفقات العمل المتوازية. اكتب سكريبتات Python تُنادي الأدوات عبر RPC، وتوحيد خطوط أنابيرة متعددة الخطوات في جولات بتكلفة سياق صفرية.</td></tr>
<tr><td><b>يعمل في كل مكان، وليس فقط على جهازك المحمول</b></td><td>سبعة خلفيات طرفية — محلية، Docker، SSH، Singularity، Modal، Daytona، و Vercel Sandbox. Daytona و Modal يوفران استمرارية بدون خادم — بيئة وكيلك تhibernate عند الخمول وتستيقظ عند الطلب، بتكلفة شبه معدومة بين الجلسات. شغّله على خادم افتراضي بـ 5 دولارات أو مجموعة وحدات معالجة رسوميات.</td></tr>
<tr><td><b>جاهز للأبحاث</b></td><td>توليد مسارات مجمعة، ضغط المسارات لتدريب الجيل القادم من نماذج استدعاء الأدوات.</td></tr>
</table>

---

## التثبيت السريع

### npm (جميع المنصات)

```bash
npx synapse-ai-agent
```

يُحمّل ويُشغّل المُثبّت الرسمي لنظام التشغيل الخاص بك — لا حاجة لمعرفة Node، السكتش فقط يقوم بالتحميل الأولي.

### Linux، macOS، WSL2، Termux

```bash
curl -fsSL https://raw.githubusercontent.com/johsua092-ui/synapse-ai-agent/main/scripts/install.sh | bash
```

### Windows (أصلي، PowerShell)

> **تنبيه:** Windows الأصلي يعمل Synapse بدون WSL — واجهة طرفية، بوابة، واجهة مستخدم كاملة، والأدوات جميعها تعمل بشكل أصلي. إذا كنت تفضل استخدام WSL2، فإن سطر Linux/macOS أعلاه يعمل هناك أيضاً. وجدت خللاً؟ يُرجى [تقديم مشاكل](https://github.com/johsua092-ui/synapse-ai-agent/issues).

شغّل هذا في PowerShell:

```powershell
iex (irm https://raw.githubusercontent.com/johsua092-ui/synapse-ai-agent/main/scripts/install.ps1)
```

المُثبّت يتولى كل شيء: uv، Python 3.11، Node.js، ripgrep، ffmpeg، **و Git Bash محمول** (MinGit، مفكك إلى `%LOCALAPPDATA%\synapse\git` — لا يحتاج صلاحيات مدير، معزول تماماً عن أي تثبيت Git للنظام). Synapse يستخدم هذا Git Bash المُضمّن لتنفيذ أوامر shell.

إذا كان لديك Git مُثبّت بالفعل، يكتشفه المُثبّت ويستخدمه. وإلا، فإن حجم MinGit بنحو 45 ميغابايت هو كل ما تحتاجه — لن يلمس أو يُعترض أي Git للنظام.

> **Android / Termux:** المسار اليدوي المُختبر موثق في دليل Termux. على Termux، يُثبّت Synapse حزمة مُختارة `.[termux]` لأن الحزمة الكاملة `.[all]` حالياً تجلب تبعيات صوتية غير متوافقة مع Android.
>
> **Windows:** Windows الأصلي مدعوم بالكامل — سطر PowerShell أعلاه يُثبّت كل شيء. إذا كنت تفضل استخدام WSL2، فإن أمر Linux يعمل هناك أيضاً. التثبيت الأصلي لـ Windows يتواجد تحت `%LOCALAPPDATA%\synapse`؛ التثبيت على WSL2 يتواجد تحت `~/.synapse` كما في Linux.

بعد التثبيت:

```bash
source ~/.bashrc    # إعادة تحميل shell (أو: source ~/.zshrc)
synapse              # ابدأ المحادثة!
```

### استكشاف الأخطاء وإصلاحها

#### Windows Defender أو برنامج مكافحة الفيروسات يُعلّم `uv.exe` كبرنامج ضار

إذا كان برنامج مكافحة الفيروسات (Bitdefender، Windows Defender، إلخ) يُحوّل `uv.exe` من مجلد `bin` الخاص بـ Synapse (`%LOCALAPPDATA%\synapse\bin\uv.exe`) إلى الحجر، فهذا ** alerted **. الملف هو `uv` من Astral — مدير حزم Rust لـ Python الذي يُضمّنه Synapse لإدارة بيئة Python الخاصة به. محركات مكافحة الفيروسات القائمة على التعلم الشامل عادة ما تُعلّم ملفات Rust غير الموقّعة التي تُحمّل وتُثبّت الحزم.

**للتحقق من أن نسختك أصيلة:**

```powershell
# Install GitHub CLI if needed
winget install --id GitHub.cli

# Login to GitHub
gh auth login

# Run verification
$uv = "$env:LOCALAPPDATA\synapse\bin\uv.exe"
$ver = (& $uv --version).Split(' ')[1]
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
$zip = "$env:TEMP\uv.zip"
Invoke-WebRequest "https://github.com/astral-sh/uv/releases/download/$ver/uv-x86_64-pc-windows-msvc.zip" -OutFile $zip -UseBasicParsing
gh attestation verify $zip --repo astral-sh/uv
Expand-Archive $zip "$env:TEMP\uv_x" -Force
(Get-FileHash "$env:TEMP\uv_x\uv.exe").Hash -eq (Get-FileHash $uv).Hash
```

إذا أظهر التوثيق "Verification succeeded" والسطر الأخير طبع `True`، فأنت جاهز.

**لإضافة Synapse إلى القائمة البيضاء:**
- **Windows Defender:** شغّل PowerShell كمسؤول → `Add-MpPreference -ExclusionPath "$env:LOCALAPPDATA\synapse\bin"`
- **Bitdefender:** أضف استثناءً في لوحة تحكم Bitdefender (Protection > Antivirus > Settings > Manage Exceptions)
- أضف **المجلد** إلى القائمة البيضاء وليس بصمة الملف — Synapse يُحدّث `uv` وتتغير البصمة مع كل إصدار

لمزيد من السياق، راجع تقارير Astral الأصلية: [astral-sh/uv#13553](https://github.com/astral-sh/uv/issues/13553)، [astral-sh/uv#15011](https://github.com/astral-sh/uv/issues/15011)، [astral-sh/uv#10079](https://github.com/astral-sh/uv/issues/10079).

---

## النشر على Railway

انشر Synapse Agent على [Railway](https://railway.app) كخدمة حاوية بنقرة واحدة. الصورة تأتي مع نقطة دخول s6-overlay ولوحة تحكم مُراقبة.

[![Deploy on Railway](https://railway.com/button.svg)](https://railway.com/template/synapse-agent?referralCode=QXdhdr)

### ما تحصل عليه

- **لوحة تحكم ويب** على عنوان Railway عام (محمية بالتوثيق، انظر أدناه)
- **مجلد مُثبّت** لحالة الوكيل (قم بتثبيت مجلد على `/opt/data` / `$SYNAPSE_HOME`)
- **فحص صحة** مُتصل بـ `/api/health`

### الإعداد

1. انقر **Deploy on Railway** أعلاه (أو أنشئ خدمة جديدة من هذا المستودع — Railway يكتشف تلقائياً `railway.toml` + `Dockerfile`).
2. أرفق مجلداً مُثبّتاً على `/opt/data`.
3. أضف متغيرات الخدمة المطلوبة (انظر [.env.railway.example](.env.railway.example)). على الأقل:
   - `SYNAPSE_DASHBOARD=1`
   - مُزوّد توثيق — **Basic Auth** (`SYNAPSE_DASHBOARD_BASIC_AUTH_USERNAME` + `SYNAPSE_DASHBOARD_BASIC_AUTH_PASSWORD`) أو OAuth/OIDC. بدون واحد تفشل لوحة التحكم ** Ip封锁 ** على الارتباط العام.
4. أضف مفاتيح API الخاصة بنموذجك/مزوّدك (`OPENROUTER_API_KEY`، `OPENAI_API_KEY`، إلخ).

### Docker (استضافتها بنفسك)

```bash
SYNAPSE_UID=$(id -u) SYNAPSE_GID=$(id -g) docker compose up -d
```

راجع `docker-compose.yml` ودليل `docker/` للإعداد الكامل المُراقب. نسخة Windows compose متاحة في `docker-compose.windows.yml`.

---

## البدء

```bash
synapse              # واجهة طرفية تفاعلية — ابدأ محادثة
synapse model        # اختر مزوّد نموذج اللغة والنموذج
synapse dashboard    # افتح لوحة التحكم في المتصفح (المنفذ 9119)
synapse tools        # اضبط الأدوات المُفعّلة
synapse config set   # اضبط قيم الإعدادات الفردية
synapse config get   // اطبع قيم الإعدادات الفردية
synapse gateway      # ابدأ بوابة الرسائل (Telegram، Discord، إلخ)
synapse setup        # شغّل معالج الإعداد الكامل (يضبط كل شيء مرة واحدة)
synapse claw migrate # انتقل من OpenClaw (إذا كنت قادماً من OpenClaw)
synapse update       # حدّث إلى أحدث إصدار
synapse doctor       # تشخيص أي مشاكل
```

### لوحة التحكم الإدارية

أمر `synapse dashboard` يبدأ لوحة تحكم ويب محلية على `http://127.0.0.1:9119`. توفر واجهة مستخدم متصفح لإعداد المزوّدين، وإدارة القنوات، وعرض السجلات، ومراقبة وكيلك.

```bash
synapse dashboard                        # افتح في المتصفح، المنفذ 9119
synapse dashboard --port 8080            # منفذ مخصص
synapse dashboard --host 0.0.0.0         # ارتباط بجميع الواجهات (للوصول عن بُعد)
synapse dashboard --no-open              # لا تفتح المتصفح تلقائياً
synapse dashboard --skip-build           # تخطى بناء React، استخدم HTML الإداري المُبنى مسبقاً
```

الميزات:
- **الإعداد** — ضبط مزوّدي LLM، ومفاتيح API، وقنوات الرسائل
- **الحالة** — مراقبة حالة البوابة، ووقت التشغيل، والجلسات النشطة
- **السجلات** — عرض سجلات الوكيل في الوقت الفعلي
- **المستخدمون** — إدارة طلبات الاقتران والمستخدمين المُعتمدين
- **النسخ الاحتياطي والاستعادة** — تحميل/رفع لقطات النشر

📖 **التوثيق الكامل مُقدّم في الوثائق أدناه.**

---

## إدارة الجلسات

Synapse يُبقي سجل محادثة لكل جلسة. أمر `synapse session` يُتيح لك س\controllersح وحذف الجلسات من واجهة طرفية، و `/delete` يفعل ذلك من داخل المحادثة. يُعيد استخدام خلفية SessionDB نفسها كاللوحة التحكم، لذا هناك تنفيذ حذف واحد عبر واجهة طرفية، ولوحة التحكم، ومنصات الدردشة.

```bash
synapse session list                    # اعرض جميع الجلسات المحفوظة
synapse session delete <session-id>     # احذف جلسة واحدة نهائياً
synapse session delete --all            # احذف كل الجلسات (يحذّر أولاً)
synapse session delete <session-id> -y  # تخطى طلب التأكيد
synapse session --help                  # الاستخدام الكامل
```

`delete` يتحقق دائماً من وجود الجلسة ويطبع رسالة خطأ إذا لم توجد. الحذف الفردي يعرض معلومات الجلسة ويطلب التأكيد قبل أي إجراء تدميري؛ `delete --all` يتطلب تأكيداً أكثر صرامة (أو `--yes`).

داخل محادثة، `/delete` (أو `/delete -y`) يحذف الجلسة النشطة الحالية نهائياً ويبدأ جلسة جديدة.

صفحة الجلسات في لوحة التحكم توفر العمليات نفسها مع زر الحذف، مربع حوار التأكيد، التحديث بعد الحذف، وأحول/حالات فارغة — مدعومة بنفس SessionDB.

## المهارات المُضمّنة

Synapse يصدر مع مجموعة من المهارات المُضمّنة التي تُزامَن إلى `~/.synapse/skills/` عند التثبيت والتحديث (انظر `tools/skills_sync.py`). كما يُضمّن مهارات تدفق العمل للتطوير من [Superpowers](https://github.com/obra/superpowers) تحت `skills/superpowers/` — بما في ذلك `brainstorming`، `writing-plans`، `executing-plans`، `systematic-debugging` (عبر حزمة التطوير البرمجي الحالية)، `test-driven-development`، والمزيد. تشترك في مزامنة المهارات المُضمّنة نفسها، لذا تتاح تلقائياً في أي ملف تعريف جديد.

بالنسبة للمهارات التي تشترك في اسم مع مهارة مُضمّنة حالية (مثل `systematic-debugging`، `test-driven-development`، `requesting-code-review`)، يحتفظ Synapse بالنسخة المُضمّنة الحالية — هذا يتجنب تضارب الأسماء المُكررة في مانيفست المزامنة.

---

## مُستقل عن المزوّد بالتصميم

Synapse يعمل مع أي مزوّد تريده — هذا لن يتغير. أحضر أي نقطة وصول من OpenRouter أو OpenAI أو مُخصّص وقم بتوصيلها مرة واحدة..badgeswitch باستخدام `synapse model` — بدون تغييرات في الكود، بدون اقفال.

لا يزال بإمكانك أحضر مفاتيحك الخاصة لكل أداة متى شئت — البوابة لكل خلفية، ليست كل شيء أو لا شيء.

---

## التفكير والاستدلال

Synapse يُبقي التفكير والاستدلال مُفعّلاً بشكل افتراضي ولا يسمح لأي قيمة إعداد بتعطيله. هذه هي سياسة **التفكير المُفعّل دائماً** — النماذج التي تدعم رموز الاستدلال تستخدمها دائماً؛ النماذج التي لا تدعمها غير متأثرة (لا تُرسل معايير مزوّد غير قانونية).

### مستويات الجهد

ثلاثة مستويات جهد فقط موجودة، مُرقّمة من الدرج السابق الأوسع:

| المستوى | المفاضلة |
|-------|--------------------------------------------------------|
| متوسط | سرعة وتكلفة متوازنة (الافتراضي) |
| عالٍ | استدلال أعمق — أبطأ وأغلى لكل جولة |
| أقصى | أقوى استدلال — الأبطأ والأغلى لكل جولة |

### ضبط المستوى

- **واجهة طرفية:** `/reasoning medium | high | max`
- **لوحة التحكم:** أداة اختيار الاستدلال في الشريط الجانبي للدردشة (نفس مفتاح الإعداد `agent.reasoning_effort`)
- **الإعدادات:** `agent.reasoning_effort: medium` في `config.yaml`
- **تجاوزات لكل نموذج:** `agent.reasoning_overrides: { "model-id": "high" }`

### ترحيل التعطيل القديم

سابقاً `none`، `false`، `off`، `disabled`، قيمة فارغة، boolean YAML `False`، أو `--reasoning_disabled` كان يُغلق التفكير. ضمن سياسة المفعّل دائماً، جميعها الآن تُحوّل إلى **متوسط** (`{"enabled": true, "effort": "medium"}`) حتى لا يُعطّل الاستدلال بصمت. مستوى غير معروف (مثل `turbo`) لا يزال يعود إلى الافتراضي؛ علّمة `--reasoning_disabled` المُهملة للتشغيل بالدُفعات موجودة فقط للتوافق مع الإصدارات القديمة وتطبع إشعاراً بالإيقاف.

---

## مرجع سريع للواجهة الطرفية مقابل الرسائل

لدي Synapse نقطتا دخول: ابدأ واجهة المستخدم بالطرفية باستخدام `synapse`، أو شغّل البوابة وتحدث إليها من Telegram، Discord، Slack، WhatsApp، Signal، أو البريد الإلكتروني. بمجرد دخولك في محادثة، العديد من أوامر المنقاطة مشتركة بين الواجهتين.

| الإجراء | الواجهة الطرفية | منصات الرسائل |
|---------|--------------|--------------|
| بدء المحادثة | `synapse` | شغّل `synapse gateway setup` + `synapse gateway start`، ثم أرسل رسالة للروبوت |
| فتح لوحة التحكم الإدارية | `synapse dashboard` | — |
| بدء محادثة جديدة | `/new` أو `/reset` | `/new` أو `/reset` |
| تغيير النموذج | `/model [provider:model]` | `/model [provider:model]` |
| ضبط الشخصية | `/personality [name]` | `/personality [name]` |
| إعادة المحاولة أو التراجع عن آخر جولة | `/retry`، `/undo` | `/retry`، `/undo` |
| ضغط السياق / التحقق من الاستخدام | `/compress`، `/usage`، `/insights [--days N]` | `/compress`، `/usage`، `/insights [days]` |
| تصفّح المهارات | `/skills` أو `/<skill-name>` | `/<skill-name>` |
| سرد الجلسات | `synapse session list` | — |
| حذف الجلسة الحالية | `/delete` | — |
| حذف جلسة / الكل | `synapse session delete <id>` / `--all` | — |
| إيقاف العمل الحالي | `Ctrl+C` أو أرسل رسالة جديدة | `/stop` أو أرسل رسالة جديدة |
| حالة خاصة بالمنصة | `/platforms` | `/status`، `/sethome` |

للحصول على قوائم الأوامر الكاملة، راجح دليل الواجهة الطرفية ودليل بوابة الرسائل.

---

---

## الترحيل من OpenClaw

إذا كنت قادماً من OpenClaw، يمكن لـ Synapse استيراد إعداداتك وذكرياتك ومهاراتك ومفاتيح API تلقائياً.

**خلال الإعداد الأولي:** معالج الإعداد (`synapse setup`) يكتشف تلقائياً `~/.openclaw` ويعرض الترحيل قبل بدء الإعداد.

**في أي وقت بعد التثبيت:**

```bash
synapse claw migrate              # الترحيل التفاعلي (الإعداد الكامل)
synapse claw migrate --dry-run    # معاينة ما سيُرحّل
synapse claw migrate --preset user-data   # الترحيل بدون أسرار
synapse claw migrate --overwrite  # الكتابة فوق التعارضات الموجودة
```

ما يُستورد:

- **SOUL.md** — ملف الشخصية
- **الذكريات** — إدخالات MEMORY.md و USER.md
- **المهارات** — مهارات المستخدم المُنشأة → `~/.synapse/skills/openclaw-imports/`
- **قائمة السماح بالأوامر** — أنماط الموافقة
- **إعدادات الرسائل** — إعدادات المنصة، المستخدمون المُسموحون، دليل العمل
- **مفاتيح API** — الأسرار المُسموح بها (Telegram، OpenRouter، OpenAI، Anthropic، ElevenLabs)
- **أصول TTS** — ملفات صوتية لمساحة العمل
- **تعليمات مساحة العمل** — AGENTS.md (مع `--workspace-target`)

راجع `synapse claw migrate --help` لجميع الخيارات، أو استخدم مهارة `openclaw-migration` للترحيل التفاعلي بتوجيه الوكيل مع معاينات التشغيل الجاف.

---

## Google Drive

يمكن لـ Synapse قراءة وكتابة Google Drive الخاص بالمستخدم من خلال مهارة مُضمّنة (`skills/google-drive`). يستخدم Drive REST API مع OAuth — بدون Google SDK ثقيل، فقط `messages` (تبعية أساسية بالفعل).

قم بالإعداد مرة واحدة بتشغيل المساعد المُضمّن:

```bash
python3 skills/google-drive/google-drive/scripts/gdrive.py setup
```

المعالج يُرشد المستخدم عبر Google Cloud Console (تفعيل Drive API، إنشاء عميل OAuth للجهاز المحمول، تنزيل `credentials.json`)، ثم يفتح متصفح للموافقة ويُخزّن الرمز موضعياً. ملفات الاعتماد (`credentials.json`، `token.json`) مُستبعدة من git ولا تُقدم قط.

ثم يمكن للوكيل إدارة Drive نيابة عن المستخدم:

```bash
python3 skills/google-drive/google-drive/scripts/gdrive.py list
python3 skills/google-drive/google-drive/scripts/gdrive.py search "annual report"
python3 skills/google-drive/google-drive/scripts/gdrive.py upload notes.md
python3 skills/google-drive/google-drive/scripts/gdrive.py download <file_id>
```

نفس بيانات الاعتماد تعمل على Windows، Termux، خادم افتراضي، أو Railway — انسخ `credentials.json` (و `token.json`) إلى الفرع وأعد تشغيل `setup`. راجع `skills/google-drive/google-drive/SKILL.md` للتفاصيل الكاملة.

---

## المساهمة

نرحب بالمساهمات! راجح دليل المساهمات لإعداد التطوير، ونمط الكود، وعملية طلب السحب.

بداية سريعة للمساهمين — استخدم المُثبّت العادي، ثم اعمل من الفرع الكامل الذي يُنشئه في `$SYNAPSE_HOME/synapse-agent` (عادة `~/.synapse/synapse-agent`). هذا يتطابق مع التخطيط المستخدم بواسطة `synapse update`، والبيئة الافتراضية المُدارة، والتبعيات الكسولة، والبوابة، وأدوات التوثيق.

```bash
curl -fsSL https://raw.githubusercontent.com/johsua092-ui/synapse-ai-agent/main/scripts/install.sh | bash
cd "${SYNAPSE_HOME:-$HOME/.synapse}/synapse-agent"
uv pip install -e ".[all,dev]"
scripts/run_tests.sh
```

الاستنساخ اليدوي كبديل (للاستنساخ المؤقت/CI حيث لا تريد عمداً تخطيط التثبيت المُدار):

أنشئ البيئة الافتراضية خارج شجرة المصدر المُستنسخة — بيئة افتراضية داخل الدليل الذي يعمل منه الوكيل يمكن مسحها بأمر مسار نسبي يُنفّذه الوكيل ضد فرعه الخاص، مما يُدمّر بيئة التشغيل الحالية أثناء الجلسة.

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
uv venv ~/.synapse/venvs/synapse-dev --python 3.11
source ~/.synapse/venvs/synapse-dev/bin/activate
uv pip install -e ".[all,dev]"
scripts/run_tests.sh
```

---

## الترخيص

MIT — راجح [LICENSE](LICENSE).
