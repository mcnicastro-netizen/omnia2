/**
 * L1 — parità delle chiavi i18n: EN e ES devono avere le stesse chiavi di IT.
 * Evita regressioni silenziose quando si aggiungono stringhe solo in italiano.
 */
const it = require("../shared/i18n/locales/it.json");
const en = require("../shared/i18n/locales/en.json");
const es = require("../shared/i18n/locales/es.json");

function flatten(obj, prefix = "") {
  return Object.entries(obj).flatMap(([k, v]) =>
    v && typeof v === "object" ? flatten(v, `${prefix}${k}.`) : [`${prefix}${k}`]
  );
}

describe("i18n locales parity", () => {
  const itKeys = new Set(flatten(it));

  test.each([
    ["en", en],
    ["es", es],
  ])("%s ha tutte le chiavi di it.json", (_name, locale) => {
    const keys = new Set(flatten(locale));
    const missing = [...itKeys].filter((k) => !keys.has(k));
    expect(missing).toEqual([]);
  });
});
