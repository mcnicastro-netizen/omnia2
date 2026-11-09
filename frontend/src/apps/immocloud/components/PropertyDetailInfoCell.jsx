/* OMNIA — PropertyDetail InfoCell (MOVE-ONLY). */
import React from "react";

export function InfoCell({ label, value, testid }) {
  return (
    <div data-testid={testid}>
      <div className="text-[11px] uppercase tracking-widest text-stone-500">{label}</div>
      <div className="text-sm font-medium text-stone-900 mt-0.5">{value}</div>
    </div>
  );
}

