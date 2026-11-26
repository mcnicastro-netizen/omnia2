/** CMJ-02 — validazione orari proposti visita (FE, allineata al backend). */
export const MIN_VISIT_PROPOSED_SLOTS = 3;

/**
 * @param {string[]} slots
 * @returns {{ ok: boolean, slots: string[], error?: string }}
 */
export function normalizeProposedSlots(slots) {
  const out = [];
  const seen = new Set();
  for (const raw of slots || []) {
    if (typeof raw !== "string") {
      return { ok: false, slots: [], error: "Formato orario non valido" };
    }
    const slot = raw.trim();
    if (!slot) continue;
    if (seen.has(slot)) {
      return { ok: false, slots: [], error: "Orari duplicati non ammessi" };
    }
    seen.add(slot);
    if (Number.isNaN(Date.parse(slot))) {
      return { ok: false, slots: [], error: "Data/ora non valida" };
    }
    out.push(slot);
  }
  if (out.length < MIN_VISIT_PROPOSED_SLOTS) {
    return {
      ok: false,
      slots: out,
      error: `Servono almeno ${MIN_VISIT_PROPOSED_SLOTS} orari proposti (ora: ${out.length})`,
    };
  }
  return { ok: true, slots: out };
}

/** Tre slot di default a partire da domani 10:00, 14:00, 16:00 (local ISO-like). */
export function defaultProposedSlots(base = new Date()) {
  const day = new Date(base.getTime());
  day.setDate(day.getDate() + 1);
  day.setSeconds(0, 0);
  const hours = [10, 14, 16];
  return hours.map((h) => {
    const d = new Date(day.getTime());
    d.setHours(h, 0, 0, 0);
    const pad = (n) => String(n).padStart(2, "0");
    return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`;
  });
}

/** Converte valore datetime-local in stringa stabile per l'API. */
export function fromDatetimeLocal(value) {
  if (!value || typeof value !== "string") return "";
  return value.trim();
}
