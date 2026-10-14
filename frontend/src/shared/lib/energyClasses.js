/**
 * Classi energetiche APE allineate ai portali IT (Immobiliare.it / Idealista)
 * e a VALID_ENERGY_CLASSES (compliance HARD pubblicazione).
 *
 * Due riferimenti normativi ancora in circolazione sugli attestati:
 *  - APE vigente: DM 26 giugno 2015 (Linee guida nazionali) → scala A4…G
 *  - Scala precedente ACE / APE ante-2015 → A+ e A…G (attestati ancora validi fino a scadenza)
 *
 * Stato documento (come Idealista / Immobiliare):
 *  - in_atto · in_definizione · esente
 */
export const ENERGY_CLASS_OPTIONS = [
  { value: "A4", label: "A4", scale: "ape_2015" },
  { value: "A3", label: "A3", scale: "ape_2015" },
  { value: "A2", label: "A2", scale: "ape_2015" },
  { value: "A1", label: "A1", scale: "ape_2015" },
  { value: "A+", label: "A+", scale: "ace_legacy" },
  { value: "A", label: "A", scale: "ace_legacy" },
  { value: "B", label: "B", scale: "ape_2015" },
  { value: "C", label: "C", scale: "ape_2015" },
  { value: "D", label: "D", scale: "ape_2015" },
  { value: "E", label: "E", scale: "ape_2015" },
  { value: "F", label: "F", scale: "ape_2015" },
  { value: "G", label: "G", scale: "ape_2015" },
  { value: "EXEMPT_IN_PROGRESS", label: "In via di definizione", scale: "status" },
  { value: "EXEMPT_NOT_APPLICABLE", label: "Non soggetto / Esente", scale: "status" },
];

/** Solo lettere (filtri ricerca / preferenza minima cliente). */
export const ENERGY_CLASS_LETTER_OPTIONS = ENERGY_CLASS_OPTIONS.filter(
  (o) => !o.value.startsWith("EXEMPT"),
);

/** Scale UI senza overlap: APE 2015 = A4–A1 + B–G; legacy = A+ e A. */
export const ENERGY_CLASS_APE_2015 = ENERGY_CLASS_OPTIONS.filter(
  (o) => o.scale === "ape_2015",
);

export const ENERGY_CLASS_ACE_LEGACY = ENERGY_CLASS_OPTIONS.filter(
  (o) => o.scale === "ace_legacy",
);

/** Stato APE richiesto in form (portali IT). */
export const APE_STATUS_OPTIONS = [
  { value: "in_atto", labelKey: "valuator.ape_status_in_atto" },
  { value: "in_definizione", labelKey: "valuator.ape_status_in_definizione" },
  { value: "esente", labelKey: "valuator.ape_status_esente" },
];

export const ENERGY_CLASSES = ENERGY_CLASS_OPTIONS.map((o) => o.value);
export const ENERGY_CLASS_LETTERS = ENERGY_CLASS_LETTER_OPTIONS.map((o) => o.value);

export function energyClassLabel(value) {
  if (!value) return "";
  const hit = ENERGY_CLASS_OPTIONS.find((o) => o.value === value);
  if (hit) return hit.label;
  if (value === "exempt") return "Non soggetto / Esente";
  return value;
}
