import path from "node:path";
import { fileURLToPath } from "node:url";
import { fetchGrades, tokenExpired } from "./lib/eklase-client.mjs";
import { readJson, writeJson } from "./lib/json-store.mjs";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const rootDir = path.resolve(__dirname, "..");

const tokensPath = path.join(rootDir, "storage", "tokens.json");
const selectedProfilePath = path.join(rootDir, "storage", "selected-profile.json");
const outputPath = path.join(rootDir, "data", "grades.json");

const tokens = readJson(tokensPath);
if (!tokens) {
  throw new Error("Missing storage/tokens.json. Run login first: bash scripts/login.sh");
}
if (tokenExpired(tokens)) {
  throw new Error("Stored access token is expired. Run login again: bash scripts/login.sh");
}

const selectedProfile = readJson(selectedProfilePath);
const fetched = await fetchGrades(tokens.access_token);
const payload = {
  fetchedAt: new Date().toISOString(),
  profile: selectedProfile,
  count: fetched.grades.length,
  grades: fetched.grades,
  raw: fetched.raw,
};

writeJson(outputPath, payload);
console.log(`Grades saved to ${outputPath}. Records: ${payload.count}`);
