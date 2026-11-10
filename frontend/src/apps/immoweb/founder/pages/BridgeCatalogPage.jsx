import React, { useEffect, useState } from "react";
import { api } from "../../../../shared/lib/api";

export default function BridgeCatalogPage() {
  const [data, setData] = useState(null);
  const [err, setErr] = useState(null);
  const [editKey, setEditKey] = useState(null);
  const [price, setPrice] = useState("");
  const [note, setNote] = useState("");
  const [msg, setMsg] = useState(null);

  const load = async () => {
    try {
      const r = await api.get("/app/ops/bridge/catalog");
      setData(r.data);
    } catch {
      setErr("Catalogo non disponibile.");
    }
  };

  useEffect(() => {
    load();
  }, []);

  const save = async () => {
    if (!editKey) return;
    const n = Number(price);
    if (!(n > 0)) {
      setMsg("Prezzo non valido.");
      return;
    }
    setMsg(null);
    try {
      await api.patch(`/app/ops/bridge/catalog/b2c/${editKey}`, {
        price_eur: n,
        note,
      });
      setMsg(`Aggiornato ${editKey}`);
      setEditKey(null);
      await load();
    } catch {
      setMsg("Salvataggio non riuscito.");
    }
  };

  return (
    <div data-testid="bridge-catalog" className="space-y-10">
      <header>
        <h1
          className="text-3xl text-[#0B1E3F] tracking-tight"
          style={{ fontFamily: "'Fraunces', Georgia, serif" }}
        >
          Listino
        </h1>
        <p className="mt-2 text-sm text-stone-600 max-w-2xl">
          Piani B2B (SoT codice/Stripe) e prodotti B2C. Puoi correggere i prezzi B2C con override
          auditati — i piani abbonamento restano allineati a Stripe lookup_key.
        </p>
      </header>

      {err ? <p className="text-sm text-red-700">{err}</p> : null}
      {msg ? <p className="text-sm text-[#0B1E3F]">{msg}</p> : null}

      {!data ? (
        !err && <p className="text-sm text-stone-500">Caricamento…</p>
      ) : (
        <>
          <section>
            <h2 className="text-xs uppercase tracking-widest text-stone-500 mb-3">
              B2B · fase Founders
            </h2>
            <PlanGrid plans={data.b2b_founders || []} />
          </section>

          <section>
            <h2 className="text-xs uppercase tracking-widest text-stone-500 mb-3">
              B2B · fase Standard
            </h2>
            <PlanGrid plans={data.b2b_standard || []} />
          </section>

          <section>
            <h2 className="text-xs uppercase tracking-widest text-stone-500 mb-3">
              Pacchetti crediti
            </h2>
            <div className="grid sm:grid-cols-3 gap-2">
              {(data.credit_packages || []).map((p) => (
                <div key={p.key} className="bg-white border border-stone-200 rounded-lg px-3 py-3 text-sm">
                  <p className="font-medium">{p.credits} crediti</p>
                  <p className="text-stone-600">€ {Number(p.price_eur).toFixed(2)}</p>
                </div>
              ))}
            </div>
          </section>

          <section>
            <h2 className="text-xs uppercase tracking-widest text-stone-500 mb-3">
              Consumi crediti (B2B)
            </h2>
            <div className="bg-white border border-stone-200 rounded-lg overflow-hidden">
              <table className="w-full text-sm">
                <tbody>
                  {Object.entries(data.credit_costs || {}).map(([k, v]) => (
                    <tr key={k} className="border-b border-stone-100 last:border-0">
                      <td className="px-3 py-2 font-mono text-xs">{k}</td>
                      <td className="px-3 py-2 text-right">{v} cr</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>

          <section>
            <h2 className="text-xs uppercase tracking-widest text-stone-500 mb-3">
              B2C one-shot
            </h2>
            <ul className="space-y-2" data-testid="bridge-b2c-catalog">
              {(data.b2c || []).map((p) => (
                <li
                  key={p.key}
                  className="bg-white border border-stone-200 rounded-lg px-4 py-3 flex flex-wrap items-center justify-between gap-3"
                >
                  <div className="min-w-0">
                    <p className="font-medium text-stone-900">{p.label_it}</p>
                    <p className="text-[10px] font-mono text-stone-400">{p.key}</p>
                    {p.override ? (
                      <p className="text-[10px] uppercase tracking-widest text-amber-700 mt-1">
                        override attivo
                      </p>
                    ) : null}
                  </div>
                  <div className="flex items-center gap-3">
                    <span className="text-lg text-[#0B1E3F]" style={{ fontFamily: "'Fraunces', Georgia, serif" }}>
                      € {Number(p.price_eur_effective).toFixed(2)}
                    </span>
                    <button
                      type="button"
                      onClick={() => {
                        setEditKey(p.key);
                        setPrice(String(p.price_eur_effective));
                        setNote(p.override_note || "");
                      }}
                      className="text-[10px] uppercase tracking-widest border border-stone-300 rounded px-2 py-1 hover:bg-stone-50"
                    >
                      Modifica
                    </button>
                  </div>
                </li>
              ))}
            </ul>
          </section>

          {editKey ? (
            <div
              className="fixed inset-0 z-50 bg-stone-900/40 flex items-center justify-center p-4"
              data-testid="bridge-price-modal"
            >
              <div className="bg-white rounded-lg max-w-md w-full p-5 space-y-4 shadow-xl">
                <h3 className="text-lg text-[#0B1E3F]" style={{ fontFamily: "'Fraunces', Georgia, serif" }}>
                  Override B2C
                </h3>
                <p className="text-xs font-mono text-stone-500">{editKey}</p>
                <label className="block text-xs uppercase tracking-widest text-stone-500">
                  Prezzo €
                  <input
                    type="number"
                    step="0.01"
                    min="0.01"
                    value={price}
                    onChange={(e) => setPrice(e.target.value)}
                    className="mt-1 w-full border border-stone-300 rounded px-3 py-2 text-sm"
                  />
                </label>
                <label className="block text-xs uppercase tracking-widest text-stone-500">
                  Nota
                  <input
                    value={note}
                    onChange={(e) => setNote(e.target.value)}
                    className="mt-1 w-full border border-stone-300 rounded px-3 py-2 text-sm"
                  />
                </label>
                <div className="flex justify-end gap-2">
                  <button
                    type="button"
                    onClick={() => setEditKey(null)}
                    className="text-xs uppercase tracking-widest px-3 py-2"
                  >
                    Annulla
                  </button>
                  <button
                    type="button"
                    onClick={save}
                    className="text-xs uppercase tracking-widest px-4 py-2 rounded bg-[#0B1E3F] text-white"
                  >
                    Salva
                  </button>
                </div>
              </div>
            </div>
          ) : null}

          {data.note ? (
            <p className="text-xs text-stone-500 border-t border-stone-200 pt-4">{data.note}</p>
          ) : null}
        </>
      )}
    </div>
  );
}

function PlanGrid({ plans }) {
  return (
    <div className="grid md:grid-cols-3 gap-3">
      {plans.map((p) => (
        <div key={`${p.phase}-${p.tier}`} className="bg-white border border-stone-200 rounded-lg px-4 py-4">
          <p className="text-[10px] uppercase tracking-widest text-stone-400">{p.tier}</p>
          <p className="text-xl text-[#0B1E3F] mt-1" style={{ fontFamily: "'Fraunces', Georgia, serif" }}>
            {p.name}
          </p>
          <p className="mt-3 text-sm">
            € {p.price_monthly}/mese · € {p.price_yearly}/anno
          </p>
          <p className="text-xs text-stone-500 mt-1">{p.credits_included_monthly} crediti/mese</p>
        </div>
      ))}
    </div>
  );
}
