# Synapse CLI Reference

Live sources when anything looks stale: `synapse --help`, `synapse <command> --help`,
https:///docs/reference/cli-commands

### Global Flags

```
synapse [flags] [command]        (no subcommand = interactive chat)

  --version, -V             Show version
  -z, --oneshot PROMPT      One-shot: print ONLY the final response (for scripts/pipes)
  -m MODEL  --provider P    Model/provider override for this invocation
  -t, --toolsets LIST       Comma-separated toolsets for this invocation
  --resume, -r SESSION      Resume session by ID or title
  --continue, -c [NAME]     Resume by name, or most recent session
  --worktree, -w            Isolated git worktree mode (parallel agents)
  --skills, -s SKILL        Preload skills (comma-separate or repeat)
  --profile, -p NAME        Use a named profile
  --yolo                    Skip dangerous command approval
  --tui / --cli             Force the Ink TUI / classic REPL
  --ignore-rules            Skip AGENTS.md/SOUL.md/memory/skill injection
  --safe-mode               Disable ALL customizations (troubleshooting)
  --pass-session-id         Include session ID in system prompt
```

### Chat

```
synapse chat [flags]
  -q, --query TEXT          Single query, non-interactive
  --image PATH              Attach a local image to a single query
  -Q, --quiet               Suppress banner, spinner, tool previews
  --checkpoints             Enable filesystem checkpoints (/rollback)
  --max-turns N             Cap tool-calling iterations
  --source TAG              Session source tag (default: cli)
```
(plus the global flags above)

### Configuration

```
synapse setup [section]      Wizard (model|tts|terminal|gateway|tools|agent)
synapse model                Interactive model/provider picker
synapse fallback [add|remove|list]  Fallback provider chain
synapse config [show|edit|get|set|unset|path|env-path|check|migrate]
synapse login / logout       OAuth sign-in / clear stored auth
synapse doctor [--fix]       Check dependencies and config
synapse status [--all]       Component status
```

### Tools & Skills

```
synapse tools [list|enable NAME|disable NAME]   Per-platform toolsets (curses UI with no args)

synapse skills list|browse|search QUERY|inspect ID
synapse skills install ID    Hub identifier OR a direct https://…/SKILL.md URL
synapse skills config        Enable/disable skills per platform
synapse skills check|update|uninstall|publish PATH
synapse skills tap add REPO  Add a GitHub repo as a skill source
synapse bundles              Skill bundles (one /<name> alias loads several skills)
```

### MCP Servers

```
synapse mcp add NAME (--url or --command) | remove | list | test NAME
synapse mcp catalog | install NAME     Curated catalog install
synapse mcp configure NAME             Toggle tool selection
synapse mcp serve                      Run Synapse as an MCP server
```
Details (transport, tool discovery, catalog): `references/native-mcp.md`.

### Gateway (Messaging Platforms)

```
synapse gateway run|install|start|stop|restart|status|setup
```

20+ platforms: Telegram, Discord, Slack, WhatsApp (Baileys + Business Cloud API), iMessage (Photon — `synapse photon setup`), Signal, Email, SMS, Matrix, Mattermost, Teams, LINE, SimpleX, ntfy, Google Chat, Home Assistant, DingTalk, Feishu, WeCom, Weixin, API Server, Webhooks. Open WebUI connects via the API Server adapter. Most adapters ship under `plugins/platforms/`.
Docs: https:///docs/user-guide/messaging/

### Sessions

```
synapse sessions list|browse|rename ID TITLE|delete ID|export OUT|prune|stats
```

### Cron / Webhooks

```
synapse cron list|create SCHED|edit ID|pause|resume|run ID|remove|status
    Schedules: '30m', 'every 2h', '0 9 * * *', ISO timestamp
synapse webhook subscribe NAME|list|remove NAME|test NAME
```
Webhook payloads/routes: `references/webhooks.md`.

### Profiles

```
synapse profile list|create NAME (--clone|--clone-all|--clone-from)|use|show|delete
synapse profile rename A B | alias NAME | export NAME | import FILE
```

### Credentials & Pools

```
synapse auth                 Interactive credential manager
synapse auth add [PROVIDER]  Add OAuth or API-key credential (nous, openai-codex, qwen-oauth, …)
synapse auth list|remove P IDX|reset PROVIDER|status
```
Multiple credentials per provider form a pool that rotates automatically and skips exhausted keys.

### Other

```
synapse desktop / gui        Native desktop app
synapse dashboard            Web admin panel + embedded chat (--stop / --status)
synapse proxy                OpenAI-compatible local proxy backed by an OAuth provider
synapse portal               Quick setup / sign in via Nous Portal
synapse kanban <verb>        Multi-agent work-queue board
synapse project              Named multi-folder workspaces
synapse skin list|use|set    Switch/tweak skins (see references/themes.md)
synapse pets <verb>          Pet mascots (see references/petdex.md)
synapse memory setup|status|off|reset   Memory provider
synapse secrets bitwarden|onepassword   External secret stores
synapse moa                  Mixture-of-Agents slots
synapse hooks / security / backup / import / checkpoints / console
synapse logs [-f] [errors]   View agent/error logs
synapse send                 One-off message through a gateway platform
synapse pairing / plugins / insights / journey / computer-use
synapse acp                  ACP server (IDE integration)
synapse completion bash|zsh|fish
synapse update / uninstall / claw migrate
```

Plugin- and provider-supplied subcommands (e.g. `synapse photon setup`) only appear once their plugin is installed/active.

### Where to Find Things

| Looking for... | Location |
|---|---|
| Config options | `synapse config edit` · [Configuration docs](https:///docs/user-guide/configuration) |
| Tools / toolsets | `synapse tools list` · [Tools reference](https:///docs/reference/tools-reference) |
| Skills catalog | `synapse skills browse` · [Skills catalog](https:///docs/reference/skills-catalog) |
| Provider setup | `synapse model` · [Providers guide](https:///docs/integrations/providers) |
| Env variables | `synapse config env-path` · [Env vars reference](https:///docs/reference/environment-variables) |
| Gateway logs | `~/.synapse/logs/gateway.log` (or `synapse logs`) |
| Sessions | `synapse sessions browse` (reads state.db) |
