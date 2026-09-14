/*
 * OMNIA — M5.S4.2 Virtual Staging page (agent tool)
 *
 * Reverse Staging + varianti parallele + prompt CRM-aware (immobile collegabile).
 * Watermark "Render virtuale OMNIA" server-side (AGCM 2024 + Art. 21 Codice Consumo).
 */
import React, { useEffect, useState } from "react";
import { api } from "../../../shared/lib/api";
import AgencyShell from "../components/AgencyShell";
import StagingStudio from "../components/StagingStudio";

export default function VirtualStagingPage() {
  const [properties, setProperties] = useState([]);
  const [selectedPropertyId, setSelectedPropertyId] = useState("");
  const [history, setHistory] = useState([]);

  useEffect(() => {
    (async () => {
      try {
        const r = await api.get("/app/properties?page_size=100");
        setProperties(r.data.items || []);
      } catch (e) {
        console.error("Failed to load properties:", e);
      }
      try {
        const h = await api.get("/app/staging/history");
        setHistory(h.data.items || []);
      } catch (e) {
        console.error("Failed to load history:", e);
      }
    })();
  }, []);

  return (
    <AgencyShell current="staging">
      <div
        data-testid="virtual-staging-page"
        className="min-h-screen bg-stone-50 text-stone-900"
        style={{ fontFamily: "'Fraunces', Georgia, serif" }}
      >
        <div className="max-w-6xl mx-auto px-5 sm:px-8 py-10">
          <header className="mb-8">
            <p className="text-[10px] font-sans uppercase tracking-[0.3em] text-amber-700 mb-2">
              OMNIA · Virtual Staging AI
            </p>
            <h1 className="text-4xl sm:text-5xl leading-tight tracking-tight mb-3">
              Arreda le foto con l&apos;AI
            </h1>
            <p className="text-base font-sans text-stone-600 max-w-2xl">
              Pipeline professionale: segmentazione SAM 2 → arredamento AI Flux →
              upscale 4x. Reverse Staging per stanze già arredate, fino a 4 varianti
              in parallelo, prompt ottimizzato dal CRM.
            </p>
          </header>

          {/* Optional CRM property link */}
          <section className="bg-white border border-stone-200 p-6 mb-6 font-sans">
            <h2 className="text-sm font-semibold uppercase tracking-widest text-stone-700 mb-3">
              Collega a un immobile (opzionale)
            </h2>
            <p className="text-xs text-stone-500 mb-3">
              Collegando un immobile, l&apos;AI genera un prompt su misura per zona, prezzo e
              target buyer, e potrai salvare i render direttamente tra le foto dell&apos;annuncio.
            </p>
            <select
              value={selectedPropertyId}
              onChange={(e) => setSelectedPropertyId(e.target.value)}
              data-testid="staging-property-select"
              className="w-full sm:w-96 border border-stone-300 px-3 py-2 text-sm bg-white"
            >
              <option value="">— Nessun immobile —</option>
              {properties.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.title || p.reference_code || p.id.slice(0, 8)} {p.city ? `· ${p.city}` : ""}
                </option>
              ))}
            </select>
          </section>

          <StagingStudio key={selectedPropertyId} propertyId={selectedPropertyId || null} />

          {/* History */}
          {history.length > 0 && (
            <section className="bg-white border border-stone-200 p-6 mt-6 font-sans">
              <h2 className="text-sm font-semibold uppercase tracking-widest text-stone-700 mb-4">
                Cronologia render ({history.length})
              </h2>
              <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-3">
                {history.slice(0, 12).map((h) => (
                  <div
                    key={h.id}
                    data-testid={`staging-history-${h.id.slice(0, 8)}`}
                    className="border border-stone-100"
                  >
                    {h.variant_url ? (
                      <img src={h.variant_url} alt={h.style} className="w-full h-32 object-cover" />
                    ) : (
                      <div className="w-full h-32 bg-stone-100 flex items-center justify-center text-xs text-stone-400">
                        {h.status}
                      </div>
                    )}
                    <div className="p-2 text-[11px] text-stone-500">
                      {h.style} · {h.room_type}
                      {h.mode === "reverse" && " · 🔄"}
                      {(h.variants || []).length > 1 && ` · ${h.variants.length} varianti`}
                    </div>
                  </div>
                ))}
              </div>
            </section>
          )}
        </div>
      </div>
    </AgencyShell>
  );
}
