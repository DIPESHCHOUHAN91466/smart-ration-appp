import { describe, it, expect } from "vitest";
import { readFileSync, readdirSync, statSync } from "node:fs";
import { join } from "node:path";
import { translations } from "../../src/i18n/translations";
import { publicStrings } from "../../src/i18n/publicStrings";

const LANGS = ["en", "hi", "mr"];

function sourceFiles(dir) {
  return readdirSync(dir).flatMap((name) => {
    const path = join(dir, name);
    return statSync(path).isDirectory() ? sourceFiles(path) : /\.(jsx?)$/.test(name) ? [path] : [];
  });
}

describe("translations", () => {
  it("public strings exist in English, Hindi and Marathi", () => {
    const en = Object.keys(publicStrings.en).sort();
    for (const lang of ["hi", "mr"]) {
      expect(Object.keys(publicStrings[lang]).sort()).toEqual(en);
      for (const key of en) expect(publicStrings[lang][key].trim(), `${lang}.${key}`).not.toBe("");
    }
  });

  it("every language in the main dictionary has the same keys", () => {
    const en = Object.keys(translations.en).sort();
    for (const lang of LANGS) expect(Object.keys(translations[lang]).sort()).toEqual(en);
  });

  it("every t('key') used by the public pages and the chatbot exists", () => {
    const roots = ["src/components/chatbot", "src/components/layout", "src/pages/landing", "src/pages/public-help"];
    const used = new Set();
    for (const root of roots) {
      for (const file of sourceFiles(root)) {
        for (const match of readFileSync(file, "utf8").matchAll(/\bt\(\s*"([a-z0-9_]+)"/g)) used.add(match[1]);
        for (const match of readFileSync(file, "utf8").matchAll(/(?:title|text): "((?:land|help|chat)_[a-z0-9_]+)"/g)) used.add(match[1]);
      }
    }
    expect(used.size).toBeGreaterThan(40);
    const missing = [...used].filter((key) => LANGS.some((lang) => !(key in translations[lang])));
    expect(missing).toEqual([]);
  });
});
