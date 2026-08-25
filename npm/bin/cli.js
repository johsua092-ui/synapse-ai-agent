#!/usr/bin/env node
/**
 * Synapse Agent installer shim.
 *
 * Zero-dependency bootstrap: downloads the official installer for the current
 * platform from the synapse-ai-agent repository and executes it, forwarding
 * any extra arguments.
 *
 *   Windows            -> scripts/install.ps1  (via PowerShell)
 *   Linux/macOS/WSL    -> scripts/install.sh   (via bash)
 *
 * Usage:
 *   npx synapse-ai-agent              # latest main branch
 *   npx synapse-ai-agent --ref dev    # install from a specific branch/tag
 */

"use strict";

const https = require("https");
const fs = require("fs");
const os = require("os");
const path = require("path");
const { spawn } = require("child_process");

const REPO = "johsua092-ui/synapse-ai-agent";
const RAW_BASE = `https://raw.githubusercontent.com/${REPO}/`;

const CYAN = process.stdout.isTTY ? "\x1b[36m" : "";
const GREEN = process.stdout.isTTY ? "\x1b[32m" : "";
const YELLOW = process.stdout.isTTY ? "\x1b[33m" : "";
const RED = process.stdout.isTTY ? "\x1b[31m" : "";
const RESET = process.stdout.isTTY ? "\x1b[0m" : "";

function log(msg) {
  console.log(`${CYAN}->${RESET} ${msg}`);
}
function ok(msg) {
  console.log(`${GREEN}\u2713${RESET} ${msg}`);
}
function warn(msg) {
  console.warn(`${YELLOW}\u26a0 ${RESET}${msg}`);
}
function die(msg) {
  console.error(`${RED}\u2717 ${RESET}${msg}`);
  process.exit(1);
}

function parseArgs(argv) {
  const args = { ref: "main", passthrough: [] };
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a === "--ref" || a === "-r") {
      const val = argv[++i];
      if (!val) die("--ref requires a value (branch or tag name)");
      args.ref = val;
    } else {
      args.passthrough.push(a);
    }
  }
  return args;
}

function download(url, dest, redirects) {
  return new Promise((resolve, reject) => {
    if (redirects > 5) return reject(new Error("too many redirects"));
    https
      .get(url, (res) => {
        if (res.statusCode >= 300 && res.statusCode < 400 && res.headers.location) {
          res.resume();
          const next = new URL(res.headers.location, url).toString();
          return resolve(download(next, dest, redirects + 1));
        }
        if (res.statusCode !== 200) {
          res.resume();
          return reject(new Error(`HTTP ${res.statusCode} for ${url}`));
        }
        const file = fs.createWriteStream(dest);
        res.pipe(file);
        file.on("finish", () => file.close(resolve));
        file.on("error", reject);
      })
      .on("error", reject);
  });
}

function run(cmd, cmdArgs) {
  return new Promise((resolve, reject) => {
    const child = spawn(cmd, cmdArgs, { stdio: "inherit" });
    child.on("error", reject);
    child.on("exit", (code) =>
      code === 0 ? resolve() : reject(new Error(`exited with code ${code}`))
    );
  });
}

async function main() {
  const args = parseArgs(process.argv.slice(2));
  const isWindows = process.platform === "win32";
  const scriptName = isWindows ? "install.ps1" : "install.sh";
  const url = `${RAW_BASE}${encodeURIComponent(args.ref)}/scripts/${scriptName}`;
  const tmp = path.join(os.tmpdir(), `synapse-install-${Date.now()}-${scriptName}`);

  console.log(`
  ____                       _____
 / ___| _   _ _ __   ___ _ _|___  | ___ _ __ ___
 \\___ \\| | | | '_ \\ / _ \\ '__/ \\/ / '_ \\ '_ ' _ \\
  ___) | |_| | |_) |  __/ |  /  / |  __/ | | | | |
 |____/ \\__,_| .__/ \\___|_|  \\/   \\___|_| |_| |_|
             |_|  installer via npm
`);

  log(`Downloading ${scriptName} (ref: ${args.ref}) ...`);
  try {
    await download(url, tmp, 0);
  } catch (err) {
    die(`Download failed: ${err.message}\n  Check your connection, or the ref "${args.ref}" may not exist.`);
  }
  ok(`Downloaded to ${tmp}`);

  try {
    if (isWindows) {
      // Prefer PowerShell 7 when present; stock powershell.exe always exists.
      let psExe = "powershell.exe";
      try {
        fs.accessSync("C:\\Program Files\\PowerShell\\7\\pwsh.exe");
        psExe = "C:\\Program Files\\PowerShell\\7\\pwsh.exe";
      } catch (_) {}

      log("Running Windows installer ...");
      await run(psExe, [
        "-NoProfile",
        "-ExecutionPolicy", "Bypass",
        "-File", tmp,
        ...args.passthrough,
      ]);
    } else {
      if (process.env.PREFIX && process.env.PREFIX.includes("com.termux") && !fs.existsSync("/bin/bash")) {
        die("bash not found. Install it first: pkg install bash");
      }

      fs.chmodSync(tmp, 0o755);
      log("Running installer (Linux/macOS/WSL/Termux) ...");
      await run("bash", [tmp, ...args.passthrough]);
    }
  } catch (err) {
    die(`Installer failed: ${err.message}`);
  } finally {
    fs.unlink(tmp, () => {});
  }

  ok("Done! Start Synapse with:  synapse");
}

process.on("SIGINT", () => process.exit(130));

main().catch((err) => die(err.message));
