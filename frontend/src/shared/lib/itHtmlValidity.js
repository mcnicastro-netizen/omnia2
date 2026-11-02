/**
 * Force Italian messages for native HTML5 constraint validation
 * (browsers may show English tooltips when UI lang ≠ browser lang).
 */
const IT = {
  valueMissing: "Compila questo campo.",
  typeMismatch: "Inserisci un valore valido.",
  patternMismatch: "Formato non valido.",
  tooShort: "Testo troppo corto.",
  tooLong: "Testo troppo lungo.",
  rangeUnderflow: "Valore troppo basso.",
  rangeOverflow: "Valore troppo alto.",
  stepMismatch: "Valore non valido.",
  badInput: "Valore non riconosciuto.",
};

export function italianValidityMessage(el) {
  if (!el || !el.validity) return "";
  const v = el.validity;
  if (v.valueMissing) return IT.valueMissing;
  if (v.typeMismatch) return IT.typeMismatch;
  if (v.patternMismatch) return IT.patternMismatch;
  if (v.tooShort) return IT.tooShort;
  if (v.tooLong) return IT.tooLong;
  if (v.rangeUnderflow) return IT.rangeUnderflow;
  if (v.rangeOverflow) return IT.rangeOverflow;
  if (v.stepMismatch) return IT.stepMismatch;
  if (v.badInput) return IT.badInput;
  return el.validationMessage || "Controlla questo campo.";
}

/** Attach to a <form> (or use as onInvalid bubbling handler). */
export function onInvalidItalian(e) {
  const el = e.target;
  if (!el || typeof el.setCustomValidity !== "function") return;
  el.setCustomValidity(italianValidityMessage(el));
}

export function onInputClearCustomValidity(e) {
  const el = e.target;
  if (el && typeof el.setCustomValidity === "function") {
    el.setCustomValidity("");
  }
}
