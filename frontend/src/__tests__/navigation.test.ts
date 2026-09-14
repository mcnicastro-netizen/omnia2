import { sanitizeNextParam, resolveLangRedirect, switchLangInPath } from "../shared/lib/navigation";

describe("sanitizeNextParam (C3 — anti open-redirect)", () => {
  const fb = "/it/app/dashboard";
  test("null → fallback", () => {
    expect(sanitizeNextParam(null, fb)).toBe(fb);
  });
  test("path relativo valido → accettato", () => {
    expect(sanitizeNextParam("/it/app/properties", fb)).toBe("/it/app/properties");
  });
  test("URL assoluto esterno → fallback", () => {
    expect(sanitizeNextParam("https://evil.com", fb)).toBe(fb);
  });
  test("protocol-relative //evil.com → fallback", () => {
    expect(sanitizeNextParam("//evil.com", fb)).toBe(fb);
  });
  test("encoded https%3A%2F%2Fevil.com → fallback", () => {
    expect(sanitizeNextParam("https%3A%2F%2Fevil.com", fb)).toBe(fb);
  });
  test("backslash trick → fallback", () => {
    expect(sanitizeNextParam("/\\evil.com", fb)).toBe(fb);
  });
  test("percent malformato → fallback (no crash)", () => {
    expect(sanitizeNextParam("%E0%A4%A", fb)).toBe(fb);
  });
});

describe("resolveLangRedirect (M10)", () => {
  test("lang supportata → nessun redirect", () => {
    expect(resolveLangRedirect("/it/login")).toBeNull();
    expect(resolveLangRedirect("/en/cloud/search")).toBeNull();
  });
  test("lang sconosciuta a 2 lettere → sostituita", () => {
    expect(resolveLangRedirect("/fr/login")).toBe("/it/login");
  });
  test("primo segmento non-lang → prefissato", () => {
    expect(resolveLangRedirect("/verifica-dominio")).toBe("/it/verifica-dominio");
  });
});

describe("switchLangInPath (M1)", () => {
  test("sostituisce il segmento lingua", () => {
    expect(switchLangInPath("/it/app/dashboard", "en")).toBe("/en/app/dashboard");
  });
  test("antepone se manca", () => {
    expect(switchLangInPath("/pricing", "es")).toBe("/es/pricing");
  });
});
