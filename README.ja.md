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

**Josh Research が開発した自己改善型 AI エージェント。** 組み込みの学習ループを持つ唯一のエージェントです。経験からスキルを生成し、使用中に改善し、知識を永続化するために自らを促し、過去の会話を検索し、セッションを越えてユーザーのモデルを深めます。月5ドルの VPS、GPU クラスター、アイドル時にコストほぼゼロのサーバーレスインフラで実行できます。ラップトップに縛られず、クラウド VM で作業しながら Telegram から会話できます。

OpenRouter、OpenAI、独自のエンドポイントなど、任意のモデルを使用できます。`synapse model` で切り替え可能です。コード変更不要、ロックインなし。

<table>
<tr><td><b>リアルなターミナルインターフェース</b></td><td>複数行編集、スラッシュコマンドの自動補完、会話履歴、割り込みとリダイレクト、ストリーミングツール出力を持つフル TUI。</td></tr>
<tr><td><b>お使いの環境に合わせて動作</b></td><td>Telegram、Discord、Slack、WhatsApp、Signal、CLI — すべて単一のゲートウェイプロセスから。ボイスメモの文字起こし、クロスプラットフォームの会話の連続性。</td></tr>
<tr><td><b>閉じた学習ループ</b></td><td>定期的な促しによるエージェント管理のメモリ。複雑なタスク後の自律的なスキル作成。スキルは使用中に自己改善。LLM 要約による FTS5 セッション検索でクロスセッション回顧。<a href="https://github.com/plastic-labs/honcho">Honcho</a> 論証的ユーザーモデリング。<a href="https://agentskills.io">agentskills.io</a> オープン規格と互換性あり。</td></tr>
<tr><td><b>スケジュール自動化</b></td><td>組み込みの cron スケジューラーと任意のプラットフォームへの配信。日次レポート、夜間バックアップ、週次監査 — すべて自然言語で、無人で実行。</td></tr>
<tr><td><b>委譲と並列化</b></td><td>並列ワークストリーム用の分離されたサブエージェントを生成。RPC 経由でツールを呼び出す Python スクリプトを作成し、マルチステップパイプラインをゼロコンテキストコストのターンに圧縮。</td></tr>
<tr><td><b>ラップトップだけでなくどこでも実行</b></td><td>7 つのターミナルバックエンド — ローカル、Docker、SSH、Singularity、Modal、Daytona、Vercel Sandbox。Daytona と Modal はサーバーレス永続性を提供 — エージェントの環境はアイドル時にヒバーテーションし、オンデマンドで起動。セッション間のコストはほぼゼロ。月5ドルの VPS や GPU クラスターで実行可能。</td></tr>
<tr><td><b>研究に最適</b></td><td>バッチ軌跡生成、ツール呼び出しモデルの次世代トレーニング用の軌跡圧縮。</td></tr>
</table>

---

## クイックインストール

### npm（全プラットフォーム）

```bash
npx synapse-ai-agent
```

お使いの OS 用の公式インストーラーをダウンロードして実行します。Node の知識は不要で、shim がブートストラップします。

### Linux、macOS、WSL2、Termux

```bash
curl -fsSL https://raw.githubusercontent.com/johsua092-ui/synapse-ai-agent/main/scripts/install.sh | bash
```

### Windows（ネイティブ、PowerShell）

> **注意:** ネイティブ Windows は WSL なしで Synapse を実行します。CLI、ゲートウェイ、TUI、ツールすべてがネイティブに動作します。WSL2 を使用したい場合は、上記の Linux/macOS 用ワンライナーがそのまま使えます。バグを見つけましたか？[Issue を作成](https://github.com/johsua092-ui/synapse-ai-agent/issues)してください。

PowerShell で以下を実行:

```powershell
iex (irm https://raw.githubusercontent.com/johsua092-ui/synapse-ai-agent/main/scripts/install.ps1)
```

インストーラーがすべてを処理します。uv、Python 3.11、Node.js、ripgrep、ffmpeg、**およびポータブル Git Bash**（MinGit、`%LOCALAPPDATA%\synapse\git` に展開 — 管理者権限不要、システムの Git インストールと完全に分離）。Synapse はこのバンドル Git Bash を使用してシェルコマンドを実行します。

既に Git がインストールされている場合、インストーラーはそれを検出して使用します。なければ、約45MB の MinGit ダウンロードだけで済みます。システムの Git に影響を与えません。

> **Android / Termux:** テスト済みの手動パスは Termux ガイドに記載されています。Termux では、完全な `.[all]` エクストラが現在 Android 互換性のない音声依存関係を含むため、Synapse は厳選された `.[termux]` エクストラをインストールします。
>
> **Windows:** ネイティブ Windows は完全サポートされています。上記の PowerShell ワンライナーですべてがインストールされます。WSL2 を使用したい場合は、Linux コマンドがそのまま使えます。ネイティブ Windows インストールは `%LOCALAPPDATA%\synapse` 配下にあり、WSL2 インストールは Linux と同様に `~/.synapse` 配下にあります。

インストール後:

```bash
source ~/.bashrc    # シェルをリロード（または: source ~/.zshrc）
synapse              # チャットを開始！
```

### トラブルシューティング

#### Windows Defender やウイルス対策ソフトが `uv.exe` を malware として検出する場合

ウイルス対策ソフト（Bitdefender、Windows Defender など）が Synapse の `bin` フォルダ（`%LOCALAPPDATA%\synapse\bin\uv.exe`）内の `uv.exe` を隔離した場合、これは**誤検知**です。このファイルは Astral の `uv` — Synapse が Python 環境の管理にバンドルしている Rust 製の Python パッケージマネージャーです。ML ベースのウイルス対策エンジンは、パッケージをダウンロードしてインストールする署名なしの Rust バイナリを頻繁に検出します。

**コピーが正規であることを確認するには:**

```powershell
# 必要に応じて GitHub CLI をインストール
winget install --id GitHub.cli

# GitHub にログイン
gh auth login

# 検証を実行
$uv = "$env:LOCALAPPDATA\synapse\bin\uv.exe"
$ver = (& $uv --version).Split(' ')[1]
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
$zip = "$env:TEMP\uv.zip"
Invoke-WebRequest "https://github.com/astral-sh/uv/releases/download/$ver/uv-x86_64-pc-windows-msvc.zip" -OutFile $zip -UseBasicParsing
gh attestation verify $zip --repo astral-sh/uv
Expand-Archive $zip "$env:TEMP\uv_x" -Force
(Get-FileHash "$env:TEMP\uv_x\uv.exe").Hash -eq (Get-FileHash $uv).Hash
```

アテステーションが "Verification succeeded" を返し、最後の行が `True` を出力すれば OK です。

**Synapse をホワイトリストに登録するには:**
- **Windows Defender:** 管理者として PowerShell を実行 → `Add-MpPreference -ExclusionPath "$env:LOCALAPPDATA\synapse\bin"`
- **Bitdefender:** Bitdefender コンソールで例外を追加（Protection > Antivirus > Settings > Manage Exceptions）
- ファイルハッシュではなく**フォルダ**をホワイトリストに登録してください。Synapse が `uv` を更新するたびにハッシュが変わるためです。

詳細については、Astral の上流レポートを参照: [astral-sh/uv#13553](https://github.com/astral-sh/uv/issues/13553)、[astral-sh/uv#15011](https://github.com/astral-sh/uv/issues/15011)、[astral-sh/uv#10079](https://github.com/astral-sh/uv/issues/10079).

---

## Railway へのデプロイ

Synapse Agent をワンクリックコンテナサービスとして [Railway](https://railway.app) にデプロイします。イメージには s6-overlay エントリポイントと管理型 Web ダッシュボードが同梱されています。

[![Deploy on Railway](https://railway.com/button.svg)](https://railway.com/template/synapse-agent?referralCode=QXdhdr)

### 得られるもの

- **Web ダッシュボード**（パブリック Railway URL で、認証付き — 詳細は以下）
- **永続ボリューム**（`/opt/data` / `$SYNAPSE_HOME` にマウントしてエージェント状態を保存）
- **ヘルスチェック**（`/api/health` に接続）

### セットアップ

1. 上の **Deploy on Railway** をクリックする（またはこのリポジトリから新しいサービスを作成 — Railway が `railway.toml` + `Dockerfile` を自動検出します）。
2. `/opt/data` にマウントされたボリュームをアタッチします。
3. 必要なサービス変数を追加します（[.env.railway.example](.env.railway.example) を参照）。最低限:
   - `SYNAPSE_DASHBOARD=1`
   - 認証プロバイダー — **Basic Auth**（`SYNAPSE_DASHBOARD_BASIC_AUTH_USERNAME` + `SYNAPSE_DASHBOARD_BASIC_AUTH_PASSWORD`）または OAuth/OIDC。設定がない場合、パブリックバインドでダッシュボードは**安全に失敗**します。
4. モデル/プロバイダーの API キーを追加します（`OPENROUTER_API_KEY`、`OPENAI_API_KEY` など）。

### Docker（セルフホスト）

```bash
SYNAPSE_UID=$(id -u) SYNAPSE_GID=$(id -g) docker compose up -d
```

完全な管理型セットアップについては `docker-compose.yml` と `docker/` ディレクトリを参照。Windows 用の compose バリアントは `docker-compose.windows.yml` にあります。

---

## はじめに

```bash
synapse              # インタラクティブ CLI — 会話を開始
synapse model        # LLM プロバイダーとモデルを選択
synapse dashboard    # ブラウザで管理パネルを開く（ポート 9119）
synapse tools        # 有効なツールを設定
synapse config set   # 個別の設定値を設定
synapse config get   # 個別の設定値を表示
synapse gateway      # メッセージングゲートウェイを起動（Telegram、Discord など）
synapse setup        # セットアップウィザードを実行（すべてをまとめて設定）
synapse claw migrate # OpenClaw から移行（OpenClaw から移行する場合）
synapse update       # 最新バージョンに更新
synapse doctor       # 課題を診断
```

### 管理パネル

`synapse dashboard` コマンドは `http://127.0.0.1:9119` にローカル Web 管理パネルを起動します。プロバイダーの設定、チャンネルの管理、ログの表示、エージェントの監視ができるブラウザベースの UI を提供します。

```bash
synapse dashboard                        # ブラウザで開く、ポート 9119
synapse dashboard --port 8080            # カスタムポート
synapse dashboard --host 0.0.0.0         # 全インターフェースにバインド（リモートアクセス用）
synapse dashboard --no-open              # ブラウザを自動で開かない
synapse dashboard --skip-build           # React ビルドをスキップし、事前ビルド済みの管理 HTML を使用
```

機能:
- **Setup** — LLM プロバイダー、API キー、メッセージングチャネルの設定
- **Status** — ゲートウェイの状態、稼働時間、アクティブセッションの監視
- **Logs** — リアルタイムのエージェントログを表示
- **Users** — ペアリングリクエストと承認済みユーザーの管理
- **Backup & Restore** — デプロイメントスナップショットのダウンロード/アップロード

📖 **完全なドキュメントは以下の docs で提供されています。**

---

## セッション管理

Synapse はすべてのセッションの会話履歴を保持します。`synapse session` コマンドで CLI からセッションの一覧表示と削除が可能で、`/delete` で会話内から削除できます。ダッシュボードと同じ SessionDB バックエンドを再利用するため、CLI、ダッシュボード、チャットプラットフォームで単一の削除実装が共有されます。

```bash
synapse session list                    # 永続化されたすべてのセッションを一覧表示
synapse session delete <session-id>     # 1つのセッションを完全に削除
synapse session delete --all            # すべてのセッションを削除（確認あり）
synapse session delete <session-id> -y  # 確認プロンプトをスキップ
synapse session --help                  # 完全な使用方法
```

`delete` は常にセッションの存在を確認し、存在しない場合はエラーを出力します。単一削除ではセッション情報を表示し、破壊的な操作前に確認を求めます。`delete --all` はより厳格な確認が必要です（または `--yes`）。

会話内で `/delete`（または `/delete -y`）を実行すると、現在のアクティブセッションが完全に削除され、新しいセッションが開始されます。

ダッシュボードの Sessions ページでは、削除ボタン、確認ダイアログ、削除後の更新、エラー/空の状態を備えた同じ操作が同じ SessionDB で提供されます。

## 同梱スキル

Synapse は一組の同梱スキルを搭載しており、インストールと更新時に `~/.synapse/skills/` に同期されます（`tools/skills_sync.py` を参照）。また、`skills/superpowers/` 配下に [Superpowers](https://github.com/obra/superpowers) 開発ワークフロースキルも同梱されています。`brainstorming`、`writing-plans`、`executing-plans`、`systematic-debugging`（既存のソフトウェア開発バンドル経由）、`test-driven-development` などが含まれます。これらのスキルは同じ同梱スキル同期に参加するため、新しいプロフィールでも自動的に利用可能です。

既存の同梱スキルと同じ名前を共有するスキル（例: `systematic-debugging`、`test-driven-development`、`requesting-code-review`）について、Synapse は既存の同梱コピーを保持します。これにより、同期マニフェストでの名前衝突を回避します。

---

## デザイン上プロバイダー非依存

Synapse はお使いのプロバイダーと動作します。これは変わりません。OpenRouter、OpenAI、カスタムエンドポイントを接続し、一度設定すれば OK。`synapse model` で切り替え可能。コード変更不要、ロックインなし。

ツールごとにカスタムキーを引き続き使用できます。ゲートウェイはバックエンド単位であり、all-or-nothing ではありません。

---

## 推論と思考

Synapse はデフォルトで推論/思考を有効にし、設定値で無効にすることはありません。これは**常時有効推論**ポリシーです。推理トークンをサポートするモデルは常にそれらを使用し、サポートしないモデルは影響を受けません（不正なプロバイダーパラメータは送信されません）。

### 努力レベル

古い幅広いラダーからマッピングされ、3つの努力レベルのみが存在します:

| レベル | トレードオフ                                             |
|-------|--------------------------------------------------------|
| Medium | 速度とコストのバランス（デフォルト）                     |
| High  | より深い推論 — より遅く、ターンごとにコストが高い        |
| Max   | 最強の推論 — 最も遅く、ターンごとにコストが最も高い      |

### レベルの設定

- **CLI:** `/reasoning medium | high | max`
- **Dashboard:** チャットサイドバーの推論ピッカー（同じ `agent.reasoning_effort` 設定キー）
- **Config:** `config.yaml` の `agent.reasoning_effort: medium`
- **モデルごとの上書き:** `agent.reasoning_overrides: { "model-id": "high" }`

### レガシー無効化の移行

以前は `none`、`false`、`off`、`disabled`、空の値、YAML ブール値 `False`、または `--reasoning_disabled` で思考がオフになっていました。常時有効ポリシーの下、これらはすべて **medium**（`{"enabled": true, "effort": "medium"}`）に解決され、推論が無効にされることはありません。認識されないレベル（例: `turbo`）は呼び出し元のデフォルトにフォールバックします。非推奨の `--reasoning_disabled` バッチランナーフラグは後方互換性のためにのみ存在し、非推奨通知を出力します。

---

## CLI とメッセージング クイックリファレンス

Synapse には2つのエントリポイントがあります。`synapse` でターミナル UI を起動するか、ゲートウェイを実行して Telegram、Discord、Slack、WhatsApp、Signal、Email から会話します。会話中は、多くのスラッシュコマンドが両方のインターフェースで共通です。

| アクション                       | CLI                                           | メッセージングプラットフォーム                                                       |
|---------------------------------|-----------------------------------------------|-------------------------------------------------------------------------------------|
| チャット開始                     | `synapse`                                     | `synapse gateway setup` + `synapse gateway start` を実行し、ボットにメッセージを送信  |
| 管理パネルを開く                 | `synapse dashboard`                           | —                                                                                   |
| 新しい会話を開始                 | `/new` または `/reset`                        | `/new` または `/reset`                                                              |
| モデルを変更                     | `/model [provider:model]`                     | `/model [provider:model]`                                                           |
| ペルソナを設定                   | `/personality [name]`                         | `/personality [name]`                                                               |
| 最後のターンをやり直す/取り消す   | `/retry`、`/undo`                             | `/retry`、`/undo`                                                                   |
| コンテキスト圧縮 / 使用量確認    | `/compress`、`/usage`、`/insights [--days N]` | `/compress`、`/usage`、`/insights [days]`                                           |
| スキルを閲覧                    | `/skills` または `/<skill-name>`              | `/<skill-name>`                                                                     |
| セッション一覧                  | `synapse session list`                        | —                                                                                   |
| 現在のセッションを削除           | `/delete`                                     | —                                                                                   |
| セッション削除 / 全削除          | `synapse session delete <id>` / `--all`       | —                                                                                   |
| 現在の作業を中断                 | `Ctrl+C` または新しいメッセージを送信          | `/stop` または新しいメッセージを送信                                                 |
| プラットフォーム固有のステータス   | `/platforms`                                  | `/status`、`/sethome`                                                               |

完全なコマンドリストについては、CLI ガイドとメッセージングゲートウェイガイドを参照してください。

---

---

## OpenClaw からの移行

OpenClaw から移行する場合、Synapse は設定、メモリ、スキル、API キーを自動的にインポートできます。

**初回セットアップ時:** セットアップウィザード（`synapse setup`）は `~/.openclaw` を自動検出し、設定開始前に移行を提案します。

**インストール後いつでも:**

```bash
synapse claw migrate              # インタラクティブ移行（フルプリセット）
synapse claw migrate --dry-run    # 移行内容をプレビュー
synapse claw migrate --preset user-data   # シークレットなしで移行
synapse claw migrate --overwrite  # 既存の競合を上書き
```

インポートされる内容:

- **SOUL.md** — パーソナファイル
- **メモリ** — MEMORY.md と USER.md のエントリ
- **スキル** — ユーザー作成スキル → `~/.synapse/skills/openclaw-imports/`
- **コマンド許可リスト** — 承認パターン
- **メッセージング設定** — プラットフォーム設定、許可ユーザー、作業ディレクトリ
- **API キー** — 許可されたシークレット（Telegram、OpenRouter、OpenAI、Anthropic、ElevenLabs）
- **TTS アセット** — ワークスペースのオーディオファイル
- **ワークスペース指示** — AGENTS.md（`--workspace-target` を使用）

すべてのオプションについては `synapse claw migrate --help` を参照するか、`openclaw-migration` スキルを使用してエージェントガイド付きのインタラクティブ移行と dry-run プレビューを実行できます。

---


## Google Drive

Synapse は同梱スキル（`skills/google-drive`）を通じてユーザーの Google Drive の読み書きが可能です。Drive REST API を OAuth で使用します。重い Google SDK は不要で、`requests`（すでにコア依存関係）のみ使用します。

同梱のヘルパーを実行して一度セットアップ:

```bash
python3 skills/google-drive/google-drive/scripts/gdrive.py setup
```

ウィザードが Google Cloud Console の手順をガイドします（Drive API を有効にし、Desktop OAuth クライアントを作成し、`credentials.json` をダウンロード）。その後、同意のためにブラウザを開き、トークンをローカルにキャッシュします。認証ファイル（`credentials.json`、`token.json`）は git-ignored で、コミットされません。

その後、エージェントはユーザーの代わりに Drive を操作できます:

```bash
python3 skills/google-drive/google-drive/scripts/gdrive.py list
python3 skills/google-drive/google-drive/scripts/gdrive.py search "annual report"
python3 skills/google-drive/google-drive/scripts/gdrive.py upload notes.md
python3 skills/google-drive/google-drive/scripts/gdrive.py download <file_id>
```

同じ認証情報は Windows、Termux、VPS、Railway で動作します。`credentials.json`（と `token.json`）をチェックアウトにコピーし、再度 `setup` を実行してください。完全な詳細については `skills/google-drive/google-drive/SKILL.md` を参照してください。

---

## コントリビューション

コントリビューション歓迎します！開発セットアップ、コードスタイル、PR プロセスについてはコントリビューションガイドを参照してください。

コントリビューター向けクイックスタート — 標準インストーラーを使用し、`$SYNAPSE_HOME/synapse-agent`（通常は `~/.synapse/synapse-agent`）に作成される完全な git チェックアウトから作業します。これは `synapse update`、管理された venv、遅延依存関係、ゲートウェイ、ドキュメントツールが使用するレイアウトと一致します。

```bash
curl -fsSL https://raw.githubusercontent.com/johsua092-ui/synapse-ai-agent/main/scripts/install.sh | bash
cd "${SYNAPSE_HOME:-$HOME/.synapse}/synapse-agent"
uv pip install -e ".[all,dev]"
scripts/run_tests.sh
```

マニュアルクローンフォールバック（管理されたインストールレイアウトを意図的に使用しない使い捨てクローン/CI 向け）:

クローンされたソースツリーの外に venv を作成してください。エージェントが操作するディレクトリ内の venv は、エージェントが自身のチェックアウトに対して実行する相対パスコマンドによって削除される可能性があり、セッション中のランタイムが破壊されます。

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
uv venv ~/.synapse/venvs/synapse-dev --python 3.11
source ~/.synapse/venvs/synapse-dev/bin/activate
uv pip install -e ".[all,dev]"
scripts/run_tests.sh
```

---

## ライセンス

MIT — [LICENSE](LICENSE) を参照。
