import path from "node:path";
import { fileURLToPath } from "node:url";
import { loginToEKlase } from "./lib/eklase-client.mjs";
import { loadDotEnv, requireEnv } from "./lib/env.mjs";
import { writeJson } from "./lib/json-store.mjs";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const rootDir = path.resolve(__dirname, "..");
const storageDir = path.join(rootDir, "storage");

loadDotEnv(path.join(rootDir, ".env"));
requireEnv(["EKLASE_USER", "EKLASE_PASS"]);

try {
  const result = await loginToEKlase({
    username: process.env.EKLASE_USER,
    password: process.env.EKLASE_PASS,
    profileId: process.env.EKLASE_PROFILE_ID || "",
    cdpEndpoint: process.env.OBSCURA_CDP_ENDPOINT || "http://127.0.0.1:9222",
  });

  writeJson(path.join(storageDir, "tokens.json"), result.tokens);
  writeJson(path.join(storageDir, "profiles.json"), result.profiles);
  writeJson(path.join(storageDir, "selected-profile.json"), result.selectedProfile);
  console.log(`Login complete. First profile selected: ${result.selectedProfile.profileId}`);
} catch (err) {
  if (err.debug) {
    writeJson(path.join(storageDir, "login-debug.json"), err.debug);
  }
  throw err;
}
