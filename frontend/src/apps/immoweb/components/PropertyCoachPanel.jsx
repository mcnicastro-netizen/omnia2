/** A-028d — HAL contestuale «Cosa manca» sulla scheda immobile. */
import React, { useEffect, useState } from "react";
import { api } from "../../../shared/lib/api";
import AlImproveButton from "../../../shared/components/AlImproveButton";

export default function PropertyCoachPanel({
  propertyId,
  form,
  onApplyField,
  isEdit,
}) {
  const [coach, setCoach] = useState(null);
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState("");

  const load = async () => {
    if (!isEdit || !propertyId) return;
    setLoading(true);
    setErr("");
    try {
      const { data } = await api.get(`/app/properties/${propertyId}/coach`);
      setCoach(data);
    } catch (e) {
      setErr("Impossibile caricare i suggerimenti.");
      setCoach(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [propertyId, isEdit]);

  if (!isEdit) return null;

  return (
    <aside
      data-testid="property-coach-panel"
      className="bg-[#f7f4ef] border border-stone-200 rounded-lg p-5 space-y-3"
    >
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="text-[10px] uppercase tracking-[0.2em] text-stone-500">Suggerimenti</p>
          <h2
            className="text-xl tracking-tight text-[#0B1E3F] mt-1"
            style={{ fontFamily: "'Fraunces', Georgia, serif" }}
          >
            Cosa manca
          </h2>
        </div>
        <button
          type="button"
          data-testid="coach-refresh"
          onClick={load}
          className="text-[10px] uppercase tracking-widest text-stone-600 border border-stone-300 px-2 py-1 rounded hover:border-stone-900"
        >
          Aggiorna
        </button>
      </div>

      {loading && <p className="text-sm text-stone-500">Analisi…</p>}
      {err && <p className="text-sm text-rose-700">{err}</p>}

      {coach && !loading && (
        <>
          <p
            data-testid="coach-summary"
            className={`text-sm ${coach.publishable ? "text-emerald-800" : "text-amber-900"}`}
          >
            {coach.summary}
          </p>
          {coach.gaps?.length === 0 ? (
            <p className="text-xs text-stone-500">Tutto a posto — puoi pubblicare.</p>
          ) : (
            <ul className="space-y-2" data-testid="coach-gaps">
              {coach.gaps.map((g) => (
                <li
                  key={g.code}
                  data-testid={`coach-gap-${g.code}`}
                  className="flex flex-wrap items-center justify-between gap-2 bg-white border border-stone-200 rounded-md px-3 py-2"
                >
                  <div className="min-w-0">
                    <span
                      className={`text-[9px] uppercase tracking-widest mr-2 ${
                        g.severity === "hard" ? "text-rose-700" : "text-amber-700"
                      }`}
                    >
                      {g.severity === "hard" ? "Obbligatorio" : "Consigliato"}
                    </span>
                    <span className="text-sm text-stone-800">{g.label}</span>
                  </div>
                  {g.hal_action && (
                    <AlImproveButton
                      field={g.hal_action}
                      value={form?.[g.hal_action] || ""}
                      propertyData={form}
                      onApply={(text) => {
                        onApplyField?.(g.hal_action, text);
                        setTimeout(load, 400);
                      }}
                      testId={`coach-hal-${g.hal_action}`}
                    />
                  )}
                </li>
              ))}
            </ul>
          )}
          <p className="text-[11px] text-stone-500 leading-snug">{coach.hint}</p>
        </>
      )}
    </aside>
  );
}
