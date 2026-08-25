# synapse-ai-agent (npm installer shim)

Install [Synapse Agent](https://github.com/johsua092-ui/synapse-ai-agent) with a single command — no Python, uv, or Git knowledge required.

```bash
npx synapse-ai-agent
```

or, pinned globally:

```bash
npm install -g synapse-ai-agent
synapse-ai-agent
```

## What it does

This package is a **zero-dependency bootstrap**: it detects your OS, downloads the official installer from the Synapse repository, and runs it with the right interpreter.

| Platform | Installer | Interpreter |
|---|---|---|
| Windows | `scripts/install.ps1` | PowerShell (`pwsh` 7 if present, else `powershell.exe`) |
| Linux / macOS / WSL2 | `scripts/install.sh` | bash |
| Termux (Android) | `scripts/install.sh` | bash |

The real installer handles everything else: uv, Python 3.11, Node.js, ripgrep, ffmpeg, a portable Git on Windows, the setup wizard — and now also an optional one-prompt GitHub push setup (paste a personal access token once and Synapse can clone / commit / push for you with no further config).

## Options

```
--ref <branch-or-tag>   Install from a specific branch or tag (default: main)
--help                  Show this help
```

All other arguments are forwarded to the underlying installer untouched, e.g.:

```bash
npx synapse-ai-agent --skip-setup
npx synapse-ai-agent --ref dev
```

## Publishing (maintainers)

```bash
cd npm
npm login
npm publish --access public
```

Check name availability first: `npm view synapse-ai-agent version` (should 404 before the first publish).
