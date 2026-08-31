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

**由 Josh Research 打造的自我进化 AI 智能体。** 它是唯一一个内置学习闭环的智能体——从经验中创建技能，在使用过程中自我改进，主动持久化知识，搜索自身历史对话，并随会话深入构建对用户的认知模型。可运行在 5 美元的 VPS、GPU 集群或几乎零闲置成本的无服务器基础设施上。它不绑定你的笔记本电脑——可以在云端 VM 上工作，同时通过 Telegram 与它对话。

可使用任意模型——OpenRouter、OpenAI、自定义端点及众多其他提供商。通过 `synapse model` 即可切换——无需更改代码，无锁定。

<table>
<tr><td><b>真正的终端界面</b></td><td>完整的 TUI，支持多行编辑、斜杠命令自动补全、对话历史、中断重定向和流式工具输出。</td></tr>
<tr><td><b>融入你的日常平台</b></td><td>Telegram、Discord、Slack、WhatsApp、Signal 和 CLI——全部通过单个网关进程接入。支持语音备忘录转写、跨平台对话连续性。</td></tr>
<tr><td><b>闭环学习</b></td><td>智能体自主管理记忆并定期主动巩固。复杂任务后自主创建技能。技能在使用中自我改进。基于 FTS5 的会话搜索配合 LLM 摘要实现跨会话回忆。兼容 <a href="https://github.com/plastic-labs/honcho">Honcho</a> 辩证用户建模。兼容 <a href="https://agentskills.io">agentskills.io</a> 开放标准。</td></tr>
<tr><td><b>定时自动化</b></td><td>内置 cron 调度器，可向任意平台投递。日报、夜间备份、周度审计——全部以自然语言配置，无需值守运行。</td></tr>
<tr><td><b>委派与并行</b></td><td>可派生隔离子智能体进行并行工作流。编写通过 RPC 调用工具的 Python 脚本，将多步流水线折叠为零上下文开销的回合。</td></tr>
<tr><td><b>随处运行，不限于笔记本电脑</b></td><td>七种终端后端——本地、Docker、SSH、Singularity、Modal、Daytona 和 Vercel Sandbox。Daytona 和 Modal 提供无服务器持久化——智能体环境空闲时休眠，按需唤醒，会话间几乎零成本。可运行在 5 美元的 VPS 或 GPU 集群上。</td></tr>
<tr><td><b>研究就绪</b></td><td>批量轨迹生成、轨迹压缩，用于训练下一代工具调用模型。</td></tr>
</table>

---

## 快速安装

### npm（全平台）

```bash
npx synapse-ai-agent
```

下载并运行适用于你操作系统的官方安装程序——无需了解 Node，该引导程序仅用于启动。

### Linux、macOS、WSL2、Termux

```bash
curl -fsSL https://raw.githubusercontent.com/johsua092-ui/synapse-ai-agent/main/scripts/install.sh | bash
```

### Windows（原生，PowerShell）

> **注意：** Windows 原生环境可在不使用 WSL 的情况下运行 Synapse——CLI、网关、TUI 和工具均可原生工作。如果更倾向于使用 WSL2，上方的 Linux/macOS 一键命令同样适用。发现 Bug？请[提交 Issue](https://github.com/johsua092-ui/synapse-ai-agent/issues)。

在 PowerShell 中运行：

```powershell
iex (irm https://raw.githubusercontent.com/johsua092-ui/synapse-ai-agent/main/scripts/install.ps1)
```

安装程序处理所有内容：uv、Python 3.11、Node.js、ripgrep、ffmpeg 以及**便携式 Git Bash**（MinGit，解压至 `%LOCALAPPDATA%\synapse\git`——无需管理员权限，与系统 Git 完全隔离）。Synapse 使用此捆绑 Git Bash 运行 shell 命令。

如果系统已安装 Git，安装程序会检测并使用已有版本。否则只需下载约 45MB 的 MinGit——不会影响或干扰系统中的任何 Git 安装。

> **Android / Termux：** 经过测试的手动路径已记录在 Termux 指南中。在 Termux 上，Synapse 会安装精选的 `.[termux]` 额外依赖，因为完整的 `.[all]` 额外依赖当前会引入不兼容 Android 的语音依赖。
>
> **Windows：** Windows 原生环境完全受支持——上方 PowerShell 一键命令可安装所有组件。如果更倾向于使用 WSL2，Linux 命令同样适用。Windows 原生安装位于 `%LOCALAPPDATA%\synapse`；WSL2 安装位于 `~/.synapse`，与 Linux 一致。

安装完成后：

```bash
source ~/.bashrc    # 重新加载 shell（或：source ~/.zshrc）
synapse              # 开始聊天！
```

### 故障排除

#### Windows Defender 或杀毒软件将 `uv.exe` 标记为恶意软件

如果你的杀毒软件（Bitdefender、Windows Defender 等）将 Synapse `bin` 文件夹中的 `uv.exe`（`%LOCALAPPDATA%\synapse\bin\uv.exe`）隔离，这是**误报**。该文件是 Astral 的 `uv`——即 Synapse 用于管理 Python 环境的 Rust Python 包管理器。基于机器学习的杀毒引擎常会标记未签名的 Rust 二进制文件，因其会下载并安装包。

**验证你的副本是否为正版：**

```powershell
# 如需要，先安装 GitHub CLI
winget install --id GitHub.cli

# 登录 GitHub
gh auth login

# 运行验证
$uv = "$env:LOCALAPPDATA\synapse\bin\uv.exe"
$ver = (& $uv --version).Split(' ')[1]
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
$zip = "$env:TEMP\uv.zip"
Invoke-WebRequest "https://github.com/astral-sh/uv/releases/download/$ver/uv-x86_64-pc-windows-msvc.zip" -OutFile $zip -UseBasicParsing
gh attestation verify $zip --repo astral-sh/uv
Expand-Archive $zip "$env:TEMP\uv_x" -Force
(Get-FileHash "$env:TEMP\uv_x\uv.exe").Hash -eq (Get-FileHash $uv).Hash
```

如果验证显示 "Verification succeeded" 且最后一行输出 `True`，则确认无误。

**将 Synapse 加入白名单：**
- **Windows Defender：** 以管理员身份运行 PowerShell → `Add-MpPreference -ExclusionPath "$env:LOCALAPPDATA\synapse\bin"`
- **Bitdefender：** 在 Bitdefender 控制台中添加例外（防护 > 杀毒 > 设置 > 管理例外）
- 将**文件夹**加入白名单，而非文件哈希——Synapse 会更新 `uv`，哈希值随版本变化

更多信息请参阅上游 Astral 报告：[astral-sh/uv#13553](https://github.com/astral-sh/uv/issues/13553)、[astral-sh/uv#15011](https://github.com/astral-sh/uv/issues/15011)、[astral-sh/uv#10079](https://github.com/astral-sh/uv/issues/10079)。

---

## 部署到 Railway

将 Synapse Agent 一键部署为 [Railway](https://railway.app) 容器服务。镜像已内置 s6-overlay 入口点和受管 Web 仪表盘。

[![Deploy on Railway](https://railway.com/button.svg)](https://railway.com/template/synapse-agent?referralCode=QXdhdr)

### 你将获得

- **Web 仪表盘**，通过公开 Railway URL 访问（需认证，见下文）
- **持久化卷**用于智能体状态存储（在 `/opt/data` / `$SYNAPSE_HOME` 挂载卷）
- **健康检查**已接入 `/api/health`

### 设置步骤

1. 点击上方 **Deploy on Railway**（或从本仓库创建新服务——Railway 自动检测 `railway.toml` + `Dockerfile`）。
2. 附加挂载在 `/opt/data` 的卷。
3. 添加所需的服务变量（参见 [.env.railway.example](.env.railway.example)）。至少需要：
   - `SYNAPSE_DASHBOARD=1`
   - 认证提供者——**基本认证**（`SYNAPSE_DASHBOARD_BASIC_AUTH_USERNAME` + `SYNAPSE_DASHBOARD_BASIC_AUTH_PASSWORD`）或 OAuth/OIDC。未配置时仪表盘在公网绑定下会**拒绝访问**。
4. 添加你的模型/提供商 API 密钥（`OPENROUTER_API_KEY`、`OPENAI_API_KEY` 等）。

### Docker（自托管）

```bash
SYNAPSE_UID=$(id -u) SYNAPSE_GID=$(id -g) docker compose up -d
```

完整受管设置请参阅 `docker-compose.yml` 和 `docker/` 目录。Windows compose 变体位于 `docker-compose.windows.yml`。

---

## 入门

```bash
synapse              # 交互式 CLI——开始对话
synapse model        # 选择 LLM 提供商和模型
synapse dashboard    # 在浏览器中打开管理面板（端口 9119）
synapse tools        # 配置已启用的工具
synapse config set   # 设置单个配置值
synapse config get   # 获取单个配置值
synapse gateway      # 启动消息网关（Telegram、Discord 等）
synapse setup        # 运行完整设置向导（一次性配置所有内容）
synapse claw migrate # 从 OpenClaw 迁移（如果来自 OpenClaw）
synapse update       # 更新到最新版本
synapse doctor       # 诊断所有问题
```

### 管理面板

`synapse dashboard` 命令在 `http://127.0.0.1:9119` 启动本地 Web 管理面板。提供基于浏览器的 UI，用于配置提供商、管理渠道、查看日志和监控智能体。

```bash
synapse dashboard                        # 在浏览器中打开，端口 9119
synapse dashboard --port 8080            # 自定义端口
synapse dashboard --host 0.0.0.0         # 绑定所有接口（用于远程访问）
synapse dashboard --no-open              # 不自动打开浏览器
synapse dashboard --skip-build           # 跳过 React 构建，使用预构建的管理面板 HTML
```

功能：
- **设置** — 配置 LLM 提供商、API 密钥和消息渠道
- **状态** — 监控网关状态、运行时间和活跃会话
- **日志** — 查看实时智能体日志
- **用户** — 管理配对请求和已批准用户
- **备份与恢复** — 下载/上传部署快照

📖 **完整文档见下方。**

---

## 会话管理

Synapse 为每个会话保留对话历史。`synapse session` 命令允许在 CLI 中列出和删除会话，`/delete` 则可在对话内操作。它与仪表盘使用相同的 SessionDB 后端，因此 CLI、仪表盘和聊天平台之间共享统一的删除实现。

```bash
synapse session list                    # 列出所有持久化会话
synapse session delete <session-id>     # 永久删除一个会话
synapse session delete --all            # 删除所有会话（会先警告）
synapse session delete <session-id> -y  # 跳过确认提示
synapse session --help                  # 完整用法
```

`delete` 始终验证会话是否存在，若不存在则输出未找到错误。单个删除会显示会话信息并在执行破坏性操作前请求确认；`delete --all` 需要更严格的确认（或使用 `--yes`）。

在对话中，`/delete`（或 `/delete -y`）永久删除当前活跃会话并启动新会话。

仪表盘的会话页面提供相同操作，包括删除按钮、确认对话框、删除后刷新以及错误/空状态——由同一 SessionDB 支撑。

## 捆绑技能

Synapse 附带一组捆绑技能，在安装和更新时同步到 `~/.synapse/skills/`（参见 `tools/skills_sync.py`）。它还将 [Superpowers](https://github.com/obra/superpowers) 开发工作流技能捆绑在 `skills/superpowers/` 下——包括 `brainstorming`、`writing-plans`、`executing-plans`、`systematic-debugging`（通过现有软件开发包）、`test-driven-development` 等。它们使用相同的捆绑技能同步机制，因此在任何新配置中自动可用。

对于与现有捆绑技能同名的技能（例如 `systematic-debugging`、`test-driven-development`、`requesting-code-review`），Synapse 保留现有的捆绑副本——以避免同步清单中的重复名称冲突。

---

## 提供商无关的设计

Synapse 与你选择的任何提供商配合工作——这一点不会改变。接入任何 OpenRouter、OpenAI 或自定义端点，配置一次即可。通过 `synapse model` 切换——无需更改代码，无锁定。

你仍然可以随时为每个工具自带密钥——网关是按后端配置的，而非全部或全无。

---

## 推理与思考

Synapse 默认启用推理/思考功能，且不会让任何配置值将其关闭。这是**始终开启推理**策略——支持推理令牌的模型始终使用它们；不支持的模型不受影响（不会发送非法的提供商参数）。

### 力度等级

仅有三个力度等级，从旧的更宽泛等级映射而来：

| 等级 | 权衡                                             |
|-------|--------------------------------------------------------|
| 中等| 速度与成本的平衡（默认）                  |
| 高  | 更深的推理——每回合更慢且成本更高        |
| 极限   | 最强推理——每回合最慢且成本最高   |

### 设置力度

- **CLI：** `/reasoning medium | high | max`
- **仪表盘：** 聊天侧边栏中的推理选择器（同一配置键 `agent.reasoning_effort`）
- **配置：** `config.yaml` 中的 `agent.reasoning_effort: medium`
- **按模型覆盖：** `agent.reasoning_overrides: { "model-id": "high" }`

### 旧版禁用迁移

此前使用 `none`、`false`、`off`、`disabled`、空值、YAML 布尔值 `False` 或 `--reasoning_disabled` 可关闭思考。在始终开启策略下，这些值现在全部解析为**中等**（`{"enabled": true, "effort": "medium"}`），因此推理永远不会被静默禁用。未识别的等级（如 `turbo`）仍回退到调用方默认值；已弃用的 `--reasoning_disabled` 批量运行器标志仅为向后兼容而保留，并会输出弃用通知。

---

## CLI 与消息平台速查

Synapse 有两个入口：通过 `synapse` 启动终端 UI，或运行网关并通过 Telegram、Discord、Slack、WhatsApp、Signal 或 Email 与之对话。进入对话后，许多斜杠命令在两个界面间通用。

| 操作                         | CLI                                           | 消息平台                                                              |
| 开始聊天                 | `synapse`                                      | 运行 `synapse gateway setup` + `synapse gateway start`，然后向机器人发送消息 |
| 打开管理面板               | `synapse dashboard`                            | —                                                                                |
| 开始新对话       | `/new` 或 `/reset`                            | `/new` 或 `/reset`                                                               |
| 切换模型                   | `/model [provider:model]`                     | `/model [provider:model]`                                                        |
| 设置人设              | `/personality [name]`                         | `/personality [name]`                                                            |
| 重试或撤销上一轮    | `/retry`、`/undo`                             | `/retry`、`/undo`                                                                |
| 压缩上下文 / 查看用量 | `/compress`、`/usage`、`/insights [--days N]` | `/compress`、`/usage`、`/insights [days]`                                        |
| 浏览技能                  | `/skills` 或 `/<skill-name>`                  | `/<skill-name>`                                                                  |
| 列出会话                  | `synapse session list`                        | —                                                                                |
| 删除当前会话         | `/delete`                                     | —                                                                                |
| 删除会话 / 全部         | `synapse session delete <id>` / `--all`       | —                                                                                |
| 中断当前工作         | `Ctrl+C` 或发送新消息                | `/stop` 或发送新消息                                                    |
| 平台特定状态       | `/platforms`                                  | `/status`、`/sethome`                                                            |

完整命令列表请参阅 CLI 指南和消息网关指南。

---

---

## 从 OpenClaw 迁移

如果来自 OpenClaw，Synapse 可自动导入你的设置、记忆、技能和 API 密钥。

**首次设置期间：** 设置向导（`synapse setup`）会自动检测 `~/.openclaw` 并在配置开始前提供迁移选项。

**安装后随时可执行：**

```bash
synapse claw migrate              # 交互式迁移（完整预设）
synapse claw migrate --dry-run    # 预览将要迁移的内容
synapse claw migrate --preset user-data   # 迁移不含密钥的数据
synapse claw migrate --overwrite  # 覆盖现有冲突
```

导入内容：

- **SOUL.md** — 人设文件
- **记忆** — MEMORY.md 和 USER.md 条目
- **技能** — 用户创建的技能 → `~/.synapse/skills/openclaw-imports/`
- **命令白名单** — 审批模式
- **消息设置** — 平台配置、允许的用户、工作目录
- **API 密钥** — 白名单中的密钥（Telegram、OpenRouter、OpenAI、Anthropic、ElevenLabs）
- **TTS 资源** — 工作区音频文件
- **工作区指令** — AGENTS.md（使用 `--workspace-target`）

完整选项请参阅 `synapse claw migrate --help`，或使用 `openclaw-migration` 技能进行智能体引导的交互式迁移并预览干运行。

---


## Google Drive

Synapse 可通过捆绑技能（`skills/google-drive`）读写用户的 Google Drive。使用 Drive REST API 与 OAuth——无重型 Google SDK，仅使用 `requests`（已是核心依赖）。

通过运行捆绑的辅助程序一次性设置：

```bash
python3 skills/google-drive/google-drive/scripts/gdrive.py setup
```

向导将引导用户完成 Google Cloud 控制台（启用 Drive API、创建 Desktop OAuth 客户端、下载 `credentials.json`），然后打开浏览器进行授权并将令牌缓存到本地。凭证文件（`credentials.json`、`token.json`）已被 git 忽略，不会被提交。

之后智能体即可代用户操作 Drive：

```bash
python3 skills/google-drive/google-drive/scripts/gdrive.py list
python3 skills/google-drive/google-drive/scripts/gdrive.py search "annual report"
python3 skills/google-drive/google-drive/scripts/gdrive.py upload notes.md
python3 skills/google-drive/google-drive/scripts/gdrive.py download <file_id>
```

相同凭证在 Windows、Termux、VPS 或 Railway 上均可使用——将 `credentials.json`（及 `token.json`）复制到检出目录并重新运行 `setup`。详见 `skills/google-drive/google-drive/SKILL.md`。

---

## 贡献

欢迎贡献！请参阅贡献指南了解开发设置、代码规范和 PR 流程。

贡献者快速入门——使用标准安装程序，然后在它创建的完整 git 检出目录中工作，位于 `$SYNAPSE_HOME/synapse-agent`（通常为 `~/.synapse/synapse-agent`）。这与 `synapse update`、受管 venv、延迟依赖、网关和文档工具使用的布局一致。

```bash
curl -fsSL https://raw.githubusercontent.com/johsua092-ui/synapse-ai-agent/main/scripts/install.sh | bash
cd "${SYNAPSE_HOME:-$HOME/.synapse}/synapse-agent"
uv pip install -e ".[all,dev]"
scripts/run_tests.sh
```

手动克隆备选方案（适用于临时克隆/CI，不希望使用受管安装布局的情况）：

在克隆的源代码树之外创建 venv——在智能体运行目录内的 venv 可能被智能体针对自身检出执行的相对路径命令清除，导致会话中途运行时被销毁。

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
uv venv ~/.synapse/venvs/synapse-dev --python 3.11
source ~/.synapse/venvs/synapse-dev/bin/activate
uv pip install -e ".[all,dev]"
scripts/run_tests.sh
```

---

## 许可证

MIT — 参见 [LICENSE](LICENSE)。
