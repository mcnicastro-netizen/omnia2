/**
 * Soft checks for Italian fiscal identifiers (format / checksum).
 * Not a substitute for VIES / Agenzia Entrate — dogfood honesty.
 */

/** Normalize P.IVA: strip spaces, optional IT prefix. */
export function normalizeVat(raw) {
  const s = String(raw || "")
    .trim()
    .toUpperCase()
    .replace(/\s+/g, "");
  if (s.startsWith("IT") && s.length === 13) return s.slice(2);
  return s.replace(/^IT/, "");
}

/**
 * Italian VAT (Partita IVA) checksum — 11 digits.
 * @returns {{ ok: boolean, reason?: string }}
 */
export function validateItalianVat(raw) {
  const v = normalizeVat(raw);
  if (!v) return { ok: true }; // empty = optional
  if (!/^\d{11}$/.test(v)) {
    return { ok: false, reason: "format" };
  }
  let sum = 0;
  for (let i = 0; i < 10; i++) {
    let n = parseInt(v[i], 10);
    if (i % 2 === 1) {
      n *= 2;
      if (n > 9) n -= 9;
    }
    sum += n;
  }
  const check = (10 - (sum % 10)) % 10;
  if (check !== parseInt(v[10], 10)) return { ok: false, reason: "checksum" };
  return { ok: true };
}

/** Soft CF length check (16 alphanum or 11 digits for companies). */
export function validateFiscalCodeSoft(raw) {
  const s = String(raw || "")
    .trim()
    .toUpperCase()
    .replace(/\s+/g, "");
  if (!s) return { ok: true };
  if (/^\d{11}$/.test(s)) return validateItalianVat(s); // società spesso = P.IVA
  if (/^[A-Z0-9]{16}$/.test(s)) return { ok: true };
  return { ok: false, reason: "format" };
}

/** Italian mobile/landline soft check (digits, optional +39). */
export function validateItalianPhone(raw) {
  const s = String(raw || "").trim();
  if (!s) return { ok: false, reason: "required" };
  const digits = s.replace(/[\s./()-]/g, "").replace(/^\+39/, "").replace(/^0039/, "");
  if (!/^\d{8,12}$/.test(digits)) return { ok: false, reason: "format" };
  return { ok: true, normalized: digits };
}

/** PEC: email with typical Italian PEC domains preferred; any email format accepted if has @. */
export function validatePecEmail(raw) {
  const s = String(raw || "").trim().toLowerCase();
  if (!s) return { ok: false, reason: "required" };
  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(s)) return { ok: false, reason: "format" };
  return { ok: true, normalized: s };
}
