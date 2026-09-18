/**
 * Classi energetiche APE allineate ai portali IT (Immobiliare.it / Idealista)
 * e a VALID_ENERGY_CLASSES (compliance HARD pubblicazione).
 *
 * Scala: A4→A1 (DM 2015) · A+ · A→G · esenzioni dichiarate.
 */
export const ENERGY_CLASS_OPTIONS = [
  { value: "A4", label: "A4" },
  { value: "A3", label: "A3" },
  { value: "A2", label: "A2" },
  { value: "A1", label: "A1" },
  { value: "A+", label: "A+" },
  { value: "A", label: "A" },
  { value: "B", label: "B" },
  { value: "C", label: "C" },
  { value: "D", label: "D" },
  { value: "E", label: "E" },
  { value: "F", label: "F" },
  { value: "G", label: "G" },
  { value: "EXEMPT_IN_PROGRESS", label: "In corso" },
  { value: "EXEMPT_NOT_APPLICABLE", label: "Non soggetto / Esente" },
];

/** Solo lettere (filtri ricerca / preferenza minima cliente). */
export const ENERGY_CLASS_LETTER_OPTIONS = ENERGY_CLASS_OPTIONS.filter(
  (o) => !o.value.startsWith("EXEMPT"),
);

export const ENERGY_CLASSES = ENERGY_CLASS_OPTIONS.map((o) => o.value);
export const ENERGY_CLASS_LETTERS = ENERGY_CLASS_LETTER_OPTIONS.map((o) => o.value);

export function energyClassLabel(value) {
  if (!value) return "";
  const hit = ENERGY_CLASS_OPTIONS.find((o) => o.value === value);
  if (hit) return hit.label;
  if (value === "exempt") return "Non soggetto / Esente";
  return value;
}
