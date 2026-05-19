import { spawn } from "node:child_process";
import * as fs from "node:fs/promises";
import * as os from "node:os";
import * as path from "node:path";

import { downloadAndUnzipVSCode } from "@vscode/test-electron";

const gracefulShutdownDelayMs = 250;
const forceKillDelayMs = 2_000;

async function main(): Promise<void> {
  const extensionDevelopmentPath = path.resolve(__dirname, "../../");
  const extensionTestsPath = path.resolve(__dirname, "./suite/index");
  const doneFile = path.join(os.tmpdir(), `codegopher-vscode-test-${process.pid}.done`);

  delete process.env.ELECTRON_RUN_AS_NODE;
  await fs.rm(doneFile, { force: true });

  const vscodeExecutablePath = await downloadAndUnzipVSCode({ version: "insiders" });
  const exitCode = await runDownloadedVsCodeTests({
    vscodeExecutablePath,
    extensionDevelopmentPath,
    extensionTestsPath,
    doneFile
  });
  if (exitCode !== 0) {
    process.exit(exitCode);
  }
}

interface DownloadedVsCodeTestOptions {
  vscodeExecutablePath: string;
  extensionDevelopmentPath: string;
  extensionTestsPath: string;
  doneFile: string;
}

function runDownloadedVsCodeTests(options: DownloadedVsCodeTestOptions): Promise<number> {
  const profileRoot = path.join(options.extensionDevelopmentPath, ".vscode-test");
  const args = [
    "--disable-workspace-trust",
    "--no-sandbox",
    "--disable-gpu-sandbox",
    "--disable-updates",
    "--skip-welcome",
    "--skip-release-notes",
    `--extensionTestsPath=${options.extensionTestsPath}`,
    `--extensionDevelopmentPath=${options.extensionDevelopmentPath}`,
    `--extensions-dir=${path.join(profileRoot, "extensions")}`,
    `--user-data-dir=${path.join(profileRoot, "user-data")}`
  ];
  const child = spawn(options.vscodeExecutablePath, args, {
    detached: process.platform !== "win32",
    env: {
      ...process.env,
      CODEGOPHER_VSCODE_TEST_DONE_FILE: options.doneFile
    },
    stdio: ["ignore", "pipe", "pipe"]
  });

  let closed = false;
  let testsSucceeded = false;
  let forceKillTimer: ReturnType<typeof setTimeout> | undefined;
  const pollTimer = setInterval(() => {
    void fs
      .access(options.doneFile)
      .then(() => {
        testsSucceeded = true;
        clearInterval(pollTimer);
        setTimeout(() => {
          if (!closed) {
            terminateProcess(child.pid, "SIGTERM");
            forceKillTimer = setTimeout(() => {
              if (!closed) {
                terminateProcess(child.pid, "SIGKILL");
              }
            }, forceKillDelayMs);
          }
        }, gracefulShutdownDelayMs);
      })
      .catch(() => undefined);
  }, 100);

  return new Promise((resolve, reject) => {
    child.stdout.on("data", (chunk: Buffer) => process.stdout.write(chunk));
    child.stderr.on("data", (chunk: Buffer) => process.stderr.write(chunk));
    child.on("error", (error) => {
      clearInterval(pollTimer);
      if (forceKillTimer) {
        clearTimeout(forceKillTimer);
      }
      reject(error);
    });
    child.on("close", (code, signal) => {
      closed = true;
      clearInterval(pollTimer);
      if (forceKillTimer) {
        clearTimeout(forceKillTimer);
      }
      console.log(`Exit code:   ${code ?? signal}`);
      if (code === 0 || testsSucceeded) {
        resolve(0);
        return;
      }
      resolve(typeof code === "number" ? code : 1);
    });
  });
}

function terminateProcess(pid: number | undefined, signal: "SIGTERM" | "SIGKILL"): void {
  if (!pid) {
    return;
  }
  try {
    if (process.platform === "win32") {
      process.kill(pid, signal);
      return;
    }
    process.kill(-pid, signal);
  } catch {
    // The VS Code test process may have already closed on its own.
  }
}

main().catch((error: unknown) => {
  console.error(error);
  process.exit(1);
});
