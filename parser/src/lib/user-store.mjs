import fs from "node:fs";
import path from "node:path";
import { ensureDir, readJson, removeDir, writeJson } from "./json-store.mjs";

export class UserStore {
  constructor(rootDir) {
    this.rootDir = rootDir;
    ensureDir(rootDir);
  }

  userDir(telegramId) {
    return path.join(this.rootDir, String(telegramId));
  }

  paths(telegramId) {
    const dir = this.userDir(telegramId);
    return {
      dir,
      credentials: path.join(dir, "credentials.json"),
      tokens: path.join(dir, "tokens.json"),
      profiles: path.join(dir, "profiles.json"),
      selectedProfile: path.join(dir, "selected-profile.json"),
      grades: path.join(dir, "grades.json"),
      notifiedGrades: path.join(dir, "notified-grades.json"),
      debug: path.join(dir, "login-debug.json"),
    };
  }

  listUserIds() {
    if (!fs.existsSync(this.rootDir)) return [];
    return fs
      .readdirSync(this.rootDir, { withFileTypes: true })
      .filter((entry) => entry.isDirectory())
      .map((entry) => entry.name);
  }

  saveCredentials(telegramUser, eKlaseUsername, eKlasePassword, profileId = "") {
    const paths = this.paths(telegramUser.id);
    ensureDir(paths.dir);
    const existing = readJson(paths.credentials, {});
    const now = new Date().toISOString();
    const credentials = {
      telegramId: telegramUser.id,
      telegramUsername: telegramUser.username || null,
      telegramFirstName: telegramUser.first_name || null,
      telegramLastName: telegramUser.last_name || null,
      eKlaseUsername,
      eKlasePassword,
      profileId,
      createdAt: existing.createdAt || now,
      updatedAt: now,
    };
    writeJson(paths.credentials, credentials);
    return credentials;
  }

  getCredentials(telegramId) {
    return readJson(this.paths(telegramId).credentials);
  }

  saveLoginResult(telegramId, result) {
    const paths = this.paths(telegramId);
    writeJson(paths.tokens, result.tokens);
    writeJson(paths.profiles, result.profiles);
    writeJson(paths.selectedProfile, result.selectedProfile);
  }

  getTokens(telegramId) {
    return readJson(this.paths(telegramId).tokens);
  }

  getSelectedProfile(telegramId) {
    return readJson(this.paths(telegramId).selectedProfile);
  }

  saveGrades(telegramId, payload) {
    writeJson(this.paths(telegramId).grades, payload);
  }

  getGradesPayload(telegramId) {
    return readJson(this.paths(telegramId).grades);
  }

  getNotifiedGradeIds(telegramId) {
    return readJson(this.paths(telegramId).notifiedGrades, []);
  }

  saveNotifiedGradeIds(telegramId, ids) {
    writeJson(this.paths(telegramId).notifiedGrades, Array.from(new Set(ids.map(String))));
  }

  saveDebug(telegramId, debug) {
    writeJson(this.paths(telegramId).debug, debug);
  }

  deleteUser(telegramId) {
    removeDir(this.userDir(telegramId));
  }
}
