/**
 * Navigation helpers (TypeScript — L2 incrementale).
 * Pure functions: nessuna dipendenza dal router, facilmente testabili (L1).
 */

/** C3 — anti open-redirect: accetta solo path relativi same-origin. */
export function sanitizeNextParam(raw: string | null, fallback: string): string {
  if (!raw) return fallback;
  let decoded: string;
  try {
    decoded = decodeURIComponent(raw);
  } catch {
    return fallback;
  }
  if (!/^\/(?!\/)/.test(decoded)) return fallback;
  if (decoded.includes("://") || decoded.includes("\\")) return fallback;
  return decoded;
}

export const SUPPORTED_LANGS = ["it", "en", "es"] as const;
export type Lang = (typeof SUPPORTED_LANGS)[number];

/** M10 — dato un pathname con prefisso lingua sconosciuto, calcola il redirect. */
export function resolveLangRedirect(pathname: string, defaultLang: Lang = "it"): string | null {
  const seg = pathname.split("/").filter(Boolean)[0] || "";
  if ((SUPPORTED_LANGS as readonly string[]).includes(seg)) return null;
  const rest = pathname.replace(/^\/[^/]+/, "");
  if (/^[a-z]{2}(-[A-Za-z]{2})?$/.test(seg)) return `/${defaultLang}${rest}`;
  return `/${defaultLang}${pathname}`;
}

/** M1 — sostituisce (o antepone) il segmento lingua in un pathname. */
export function switchLangInPath(pathname: string, nextLang: string): string {
  const segments = pathname.split("/").filter(Boolean);
  if ((SUPPORTED_LANGS as readonly string[]).includes(segments[0])) {
    segments[0] = nextLang;
  } else {
    segments.unshift(nextLang);
  }
  return "/" + segments.join("/");
}
