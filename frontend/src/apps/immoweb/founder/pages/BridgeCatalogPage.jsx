import React, { useEffect, useState } from "react";
import { api } from "../../../../shared/lib/api";

export default function BridgeCatalogPage() {
  const [data, setData] = useState(null);
  const [err, setErr] = useState(null);
  const [edit, setEdit] = useState(null); // { kind:'b2c'|'b2b', ... }
  const [price, setPrice] = useState("");
  const [yearly, setYearly] = useState("");
  const [credits, setCredits] = useState("");
  const [note, setNote] = useState("");
  const [syncStripe, setSyncStripe] = useState(true);
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

  const openB2c = (p) => {
    setEdit({ kind: "b2c", key: p.key });
    setPrice(String(p.price_eur_effective));
    setNote(p.override_note || "");
  };

  const openB2b = (p) => {
    setEdit({ kind: "b2b", phase: p.phase, tier: p.tier, name: p.name });
    setPrice(String(p.price_monthly));
    setYearly(String(p.price_yearly));
    setCredits(String(p.credits_included_monthly));
    setNote(p.override_note || "");
    setSyncStripe(true);
  };

  const save = async () => {
    if (!edit) return;
    setMsg(null);
    try {
      if (edit.kind === "b2c") {
        const n = Number(price);
        if (!(n > 0)) {
          setMsg("Prezzo non valido.");
          return;
        }
        await api.patch(`/app/ops/bridge/catalog/b2c/${edit.key}`, {
          price_eur: n,
          note,
        });
        setMsg(`B2C aggiornato · ${edit.key}`);
      } else {
        const pm = Number(price);
        const py = Number(yearly);
        const cr = Number(credits);
        if (!(pm > 0) || !(py > 0)) {
          setMsg("Prezzi B2B non validi.");
          return;
        }
        const r = await api.patch(`/app/ops/bridge/catalog/b2b/${edit.phase}/${edit.tier}`, {
          price_monthly: pm,
          price_yearly: py,
          credits_included_monthly: Number.isFinite(cr) ? cr : undefined,
          note,
          sync_stripe: syncStripe,
        });
        const st = r.data?.stripe || {};
        setMsg(
          `B2B ${edit.tier} aggiornato` +
            (st.ok ? " · Stripe sync ok" : st.skipped ? " · Stripe saltato" : ` · Stripe: ${st.error || "ko"}`)
        );
      }
      setEdit(null);
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
          Override auditati B2B e B2C. Per i piani abbonamento puoi sincronizzare i lookup Stripe
          tipizzati come tier_monthly / tier_yearly.
        </p>
      </header>

      {err ? <p className="text-sm text-red-700">{err}</p> : null}
      {msg ? <p className="text-sm text-[#0B1E3F]" data-testid="bridge-catalog-msg">{msg}</p> : null}

      {!data ? (
        !err && <p className="text-sm text-stone-500">Caricamento…</p>
      ) : (
        <>
          <section>
            <h2 className="text-xs uppercase tracking-widest text-stone-500 mb-3">
              B2B · fase Founders
            </h2>
            <PlanGrid plans={data.b2b_founders || []} onEdit={openB2b} />
          </section>

          <section>
            <h2 className="text-xs uppercase tracking-widest text-stone-500 mb-3">
              B2B · fase Standard
            </h2>
            <PlanGrid plans={data.b2b_standard || []} onEdit={openB2b} />
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
                      onClick={() => openB2c(p)}
                      className="text-[10px] uppercase tracking-widest border border-stone-300 rounded px-2 py-1 hover:bg-stone-50"
                    >
                      Modifica
                    </button>
                  </div>
                </li>
              ))}
            </ul>
          </section>

          {edit ? (
            <div
              className="fixed inset-0 z-50 bg-stone-900/40 flex items-center justify-center p-4"
              data-testid="bridge-price-modal"
            >
              <div className="bg-white rounded-lg max-w-md w-full p-5 space-y-4 shadow-xl">
                <h3 className="text-lg text-[#0B1E3F]" style={{ fontFamily: "'Fraunces', Georgia, serif" }}>
                  {edit.kind === "b2c" ? "Override B2C" : `Override B2B · ${edit.name || edit.tier}`}
                </h3>
                <p className="text-xs font-mono text-stone-500">
                  {edit.kind === "b2c" ? edit.key : `${edit.phase}/${edit.tier}`}
                </p>
                <label className="block text-xs uppercase tracking-widest text-stone-500">
                  {edit.kind === "b2c" ? "Prezzo €" : "Mensile €"}
                  <input
                    type="number"
                    step="0.01"
                    min="0.01"
                    value={price}
                    onChange={(e) => setPrice(e.target.value)}
                    className="mt-1 w-full border border-stone-300 rounded px-3 py-2 text-sm"
                  />
                </label>
                {edit.kind === "b2b" ? (
                  <>
                    <label className="block text-xs uppercase tracking-widest text-stone-500">
                      Annuale €
                      <input
                        type="number"
                        step="0.01"
                        min="0.01"
                        value={yearly}
                        onChange={(e) => setYearly(e.target.value)}
                        className="mt-1 w-full border border-stone-300 rounded px-3 py-2 text-sm"
                      />
                    </label>
                    <label className="block text-xs uppercase tracking-widest text-stone-500">
                      Crediti / mese
                      <input
                        type="number"
                        min="0"
                        value={credits}
                        onChange={(e) => setCredits(e.target.value)}
                        className="mt-1 w-full border border-stone-300 rounded px-3 py-2 text-sm"
                      />
                    </label>
                    <label className="flex items-center gap-2 text-xs text-stone-600">
                      <input
                        type="checkbox"
                        checked={syncStripe}
                        onChange={(e) => setSyncStripe(e.target.checked)}
                      />
                      Sincronizza Stripe (lookup {edit.tier}_monthly / _yearly)
                    </label>
                  </>
                ) : null}
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
                    onClick={() => setEdit(null)}
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

function PlanGrid({ plans, onEdit }) {
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
          {p.override ? (
            <p className="text-[10px] uppercase tracking-widest text-amber-700 mt-2">override</p>
          ) : null}
          <button
            type="button"
            onClick={() => onEdit(p)}
            className="mt-3 text-[10px] uppercase tracking-widest border border-stone-300 rounded px-2 py-1 hover:bg-stone-50"
            data-testid={`bridge-edit-b2b-${p.phase}-${p.tier}`}
          >
            Modifica
          </button>
        </div>
      ))}
    </div>
  );
}
