import React from "react";
import { MIN_VISIT_PROPOSED_SLOTS, fromDatetimeLocal } from "./visitSlots";

/**
 * UI per proporre ≥3 date/orari visita (CMJ-02).
 */
export default function VisitSlotsPicker({ slots, onChange, disabled = false, testId = "visit-slots" }) {
  const update = (idx, value) => {
    const next = slots.map((s, i) => (i === idx ? fromDatetimeLocal(value) : s));
    onChange(next);
  };

  const add = () => {
    if (slots.length >= 10) return;
    onChange([...slots, ""]);
  };

  const remove = (idx) => {
    if (slots.length <= MIN_VISIT_PROPOSED_SLOTS) return;
    onChange(slots.filter((_, i) => i !== idx));
  };

  return (
    <div className="space-y-2" data-testid={testId}>
      <p className="text-[10px] uppercase tracking-widest text-crm-muted">
        Orari proposti (minimo {MIN_VISIT_PROPOSED_SLOTS})
      </p>
      {slots.map((slot, idx) => (
        <div key={idx} className="flex gap-2 items-center">
          <input
            type="datetime-local"
            className="border rounded px-2 py-1 text-sm flex-1"
            value={slot}
            disabled={disabled}
            onChange={(e) => update(idx, e.target.value)}
            data-testid={`${testId}-input-${idx}`}
            required
          />
          <button
            type="button"
            className="text-xs px-2 py-1 border rounded disabled:opacity-40"
            disabled={disabled || slots.length <= MIN_VISIT_PROPOSED_SLOTS}
            onClick={() => remove(idx)}
            data-testid={`${testId}-remove-${idx}`}
          >
            Rimuovi
          </button>
        </div>
      ))}
      <button
        type="button"
        className="text-xs px-2 py-1 border rounded"
        disabled={disabled || slots.length >= 10}
        onClick={add}
        data-testid={`${testId}-add`}
      >
        Aggiungi orario
      </button>
    </div>
  );
}
