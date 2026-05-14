import net from "node:net";
import path from "node:path";
import { spawn } from "node:child_process";

let spawnedProcess = null;

export async function ensureObscuraServer({
  rootDir,
  port = 9222,
  stealth = false,
  timeoutMs = 10_000,
}) {
  if (await isPortOpen(port)) return false;

  const obscuraBin = path.resolve(rootDir, "..", "obscura");
  const args = ["serve", "--port", String(port)];
  if (stealth) args.push("--stealth");

  spawnedProcess = spawn(obscuraBin, args, {
    cwd: path.dirname(obscuraBin),
    stdio: ["ignore", "ignore", "pipe"],
    detached: false,
  });

  let stderr = "";
  spawnedProcess.stderr.on("data", (chunk) => {
    stderr += chunk.toString();
  });

  const startedAt = Date.now();
  while (Date.now() - startedAt < timeoutMs) {
    if (spawnedProcess.exitCode !== null) {
      throw new Error(`Obscura failed to start: ${stderr.trim()}`);
    }
    if (await isPortOpen(port)) return true;
    await sleep(250);
  }

  throw new Error(`Obscura did not become ready on port ${port}`);
}

export function stopSpawnedObscura() {
  if (spawnedProcess && spawnedProcess.exitCode === null) {
    spawnedProcess.kill();
  }
}

function isPortOpen(port) {
  return new Promise((resolve) => {
    const socket = net.createConnection({ host: "127.0.0.1", port }, () => {
      socket.destroy();
      resolve(true);
    });
    socket.on("error", () => resolve(false));
    socket.setTimeout(750, () => {
      socket.destroy();
      resolve(false);
    });
  });
}

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}
