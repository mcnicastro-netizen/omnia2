/**
 * D04 — riferimento commerciale per card ImmobilCloud.
 * Mostra solo `reference_code` valorizzato; mai UUID / ObjectId / agency_id.
 */
export function cardReferenceCode(p) {
  if (!p || typeof p !== "object") return null;
  const raw = p.reference_code;
  if (raw == null) return null;
  const code = String(raw).trim();
  if (!code) return null;
  return code;
}

/**
 * @param {object} p card payload
 * @param {string} [label] es. "Rif."
 * @returns {string|null} es. "Rif. OM-L-ABC123" oppure null se assente
 */
export function cardReferenceLabel(p, label = "Rif.") {
  const code = cardReferenceCode(p);
  if (!code) return null;
  const prefix = String(label || "Rif.").trim() || "Rif.";
  return `${prefix} ${code}`;
}
