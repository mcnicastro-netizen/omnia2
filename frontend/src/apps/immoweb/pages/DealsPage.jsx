import React, { useCallback, useEffect, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { useTranslation } from "react-i18next";
import AgencyShell from "../components/AgencyShell";
import EntitySearch from "../components/EntitySearch";
import { api } from "../../../shared/lib/api";

/**
 * Deal — ciclo opportunità. CMJ-01: ricerca per nome, nessun UUID manuale.
 * CMJ-04: precompilazione da visita via query params.
 */
export default function DealsPage() {
  const { i18n } = useTranslation();
  const lang = (i18n.language || "it").slice(0, 2);
  const [params] = useSearchParams();
  const [items, setItems] = useState([]);
  const [err, setErr] = useState("");
  const [busy, setBusy] = useState(false);
  const [form, setForm] = useState({
    property_id: params.get("property_id") || "",
    client_id: params.get("client_id") || "",
    visit_id: params.get("visit_id") || "",
    collaboration_id: params.get("collaboration_id") || "",
    notes: "",
  });
  const propertyLocked = Boolean(params.get("property_id") && (params.get("visit_id") || params.get("collaboration_id")));
  const propertyInitialLabel = params.get("property_label") || "";
  const [proposalAmount, setProposalAmount] = useState("");
  const [selected, setSelected] = useState(null);

  const load = useCallback(async () => {
    setErr("");
    try {
      const { data } = await api.get("/app/deals");
      setItems(data.items || []);
    } catch (e) {
      setErr(e?.response?.data?.detail || "Caricamento Deal fallito");
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const openDeal = async (e) => {
    e.preventDefault();
    if (!form.property_id || !form.client_id) {
      setErr("Seleziona immobile e cliente dalla ricerca");
      return;
    }
    setBusy(true);
    setErr("");
    try {
      const body = {
        property_id: form.property_id,
        client_id: form.client_id,
        notes: form.notes || undefined,
      };
      if (form.visit_id) body.visit_id = form.visit_id;
      if (form.collaboration_id) body.collaboration_id = form.collaboration_id;
      const { data } = await api.post("/app/deals", body);
      setSelected(data);
      await load();
    } catch (ex) {
      setErr(ex?.response?.data?.detail || "Apertura Deal fallita");
    } finally {
      setBusy(false);
    }
  };

  const addProposal = async (dealId) => {
    const amount = Number(proposalAmount);
    if (!(amount >= 0)) {
      setErr("Importo proposta non valido");
      return;
    }
    setBusy(true);
    try {
      const { data } = await api.post(`/app/deals/${dealId}/proposals`, { amount });
      setSelected(data);
      await load();
    } catch (e) {
      setErr(e?.response?.data?.detail || "Proposta fallita");
    } finally {
      setBusy(false);
    }
  };

  const sendProposal = async (dealId) => {
    setBusy(true);
    try {
      const { data } = await api.post(`/app/deals/${dealId}/send-proposal`);
      setSelected(data);
      await load();
    } catch (e) {
      setErr(e?.response?.data?.detail || "Invio proposta fallito");
    } finally {
      setBusy(false);
    }
  };

  const setStatus = async (dealId, status) => {
    setBusy(true);
    try {
      const { data } = await api.patch(`/app/deals/${dealId}`, { status });
      setSelected(data);
      await load();
    } catch (e) {
      setErr(e?.response?.data?.detail || "Transizione Deal fallita");
    } finally {
      setBusy(false);
    }
  };

  const partnerRespond = async (dealId, action) => {
    setBusy(true);
    try {
      const body = { action };
      if (action === "counter") {
        const amount = Number(proposalAmount);
        if (!(amount >= 0)) {
          setErr("Importo controproposta non valido");
          setBusy(false);
          return;
        }
        body.counter_amount = amount;
      }
      const { data } = await api.post(`/app/deals/${dealId}/partner-respond`, body);
      setSelected(data);
      await load();
    } catch (e) {
      setErr(e?.response?.data?.detail || "Risposta partner fallita");
    } finally {
      setBusy(false);
    }
  };

  return (
    <AgencyShell current="deals">
      <div className="crm-desk max-w-5xl mx-auto space-y-6" data-testid="deals-page">
        <header className="space-y-2">
          <p className="crm-eyebrow">Ciclo commerciale</p>
          <h1 className="crm-title text-3xl md:text-4xl">Deal</h1>
          <p className="text-crm-muted max-w-2xl text-sm">
            Cerca immobile e cliente per nome. Nessun identificativo tecnico da digitare.
            Azioni filtrate dai permessi backend.
          </p>
          <p className="text-xs">
            <Link className="underline" to={`/${lang}/app/collaborations`}>
              ← Collaborazioni / visite / chat
            </Link>
          </p>
        </header>

        {err ? (
          <div className="rounded-md border border-rose-200 bg-rose-50 px-4 py-3 text-rose-800 text-sm">
            {typeof err === "string" ? err : JSON.stringify(err)}
          </div>
        ) : null}

        <form
          onSubmit={openDeal}
          className="border rounded-lg p-4 space-y-3 bg-white/60"
          data-testid="deal-open-form"
        >
          <h2 className="font-semibold">Apri Deal</h2>
          {form.visit_id ? (
            <p className="text-xs text-emerald-800 bg-emerald-50 border border-emerald-100 rounded px-2 py-1" data-testid="deal-from-visit-banner">
              Da visita completata — immobile precompilato. Seleziona il cliente e conferma.
            </p>
          ) : null}
          <div className="grid md:grid-cols-2 gap-3">
            <EntitySearch
              kind="property"
              value={form.property_id}
              required
              disabled={propertyLocked}
              initialLabel={propertyInitialLabel}
              testId="deal-property-search"
              label="Immobile"
              placeholder="Cerca per titolo o indirizzo…"
              onChange={(id) => setForm((f) => ({ ...f, property_id: id || "" }))}
            />
            <EntitySearch
              kind="client"
              value={form.client_id}
              required
              testId="deal-client-search"
              label="Cliente"
              placeholder="Cerca per nome o email…"
              onChange={(id) => setForm((f) => ({ ...f, client_id: id || "" }))}
            />
          </div>
          {form.collaboration_id || form.visit_id ? (
            <p className="text-[11px] text-crm-muted" data-testid="deal-context-meta">
              Contesto MLS
              {form.collaboration_id ? " · collaborazione collegata" : ""}
              {form.visit_id ? " · visita collegata" : ""}
            </p>
          ) : null}
          <textarea
            className="w-full border rounded px-2 py-1 text-sm"
            placeholder="Note / interesse espresso"
            value={form.notes}
            onChange={(e) => setForm({ ...form, notes: e.target.value })}
            data-testid="deal-notes"
          />
          <button
            type="submit"
            disabled={busy || !form.property_id || !form.client_id}
            className="text-sm px-4 py-2 bg-slate-800 text-white rounded disabled:opacity-50"
            data-testid="deal-open-submit"
          >
            Apri Deal
          </button>
        </form>

        <section className="space-y-3" data-testid="deals-list">
          <h2 className="text-lg font-semibold">Deal</h2>
          {(items || []).length === 0 ? (
            <p className="text-sm text-crm-muted">Nessun Deal.</p>
          ) : (
            <ul className="space-y-3">
              {items.map((d) => {
                const allowed = d.allowed_transitions || [];
                const role = d.role;
                return (
                  <li key={d.id} className="border rounded-lg p-4 space-y-2 bg-white/60" data-testid={`deal-item-${d.id}`}>
                    <button type="button" className="text-left w-full" onClick={() => setSelected(d)}>
                      <p className="font-medium text-sm">
                        {d.property_title || "Immobile"} · {d.client_label || "Cliente"}
                      </p>
                      <p className="text-xs text-crm-muted">
                        {d.status} · ruolo {role || "—"} · collab {d.collaboration_id ? "sì" : "no"}
                      </p>
                    </button>
                    <div className="flex flex-wrap gap-2 items-center">
                      {role === "owner" ? (
                        <>
                          <input
                            className="border rounded px-2 py-1 text-xs w-28"
                            placeholder="Importo"
                            value={proposalAmount}
                            onChange={(e) => setProposalAmount(e.target.value)}
                            data-testid={`deal-proposal-amount-${d.id}`}
                          />
                          <button
                            type="button"
                            className="text-xs px-2 py-1 border rounded"
                            disabled={busy}
                            onClick={() => addProposal(d.id)}
                          >
                            Prepara proposta
                          </button>
                          {allowed.includes("proposal_sent") ? (
                            <button
                              type="button"
                              className="text-xs px-2 py-1 border rounded"
                              disabled={busy}
                              onClick={() => sendProposal(d.id)}
                              data-testid={`deal-send-proposal-${d.id}`}
                            >
                              Invia proposta
                            </button>
                          ) : null}
                        </>
                      ) : null}
                      {role === "partner" && d.status === "proposal_sent" ? (
                        <>
                          {["accepted", "rejected"].map((a) =>
                            allowed.includes(a) ? (
                              <button
                                key={a}
                                type="button"
                                className="text-xs px-2 py-1 border rounded"
                                disabled={busy}
                                onClick={() => partnerRespond(d.id, a)}
                                data-testid={`deal-partner-${a}-${d.id}`}
                              >
                                {a === "accepted" ? "Accetta" : "Rifiuta"}
                              </button>
                            ) : null
                          )}
                          {allowed.includes("counter") ? (
                            <button
                              type="button"
                              className="text-xs px-2 py-1 border rounded"
                              disabled={busy}
                              onClick={() => partnerRespond(d.id, "counter")}
                            >
                              Controproposta
                            </button>
                          ) : null}
                        </>
                      ) : null}
                      {allowed
                        .filter((st) => !["proposal_sent", "accepted", "rejected", "counter"].includes(st) || role === "owner")
                        .filter((st) => role === "owner")
                        .map((st) => (
                          <button
                            key={st}
                            type="button"
                            className="text-xs px-2 py-1 border rounded"
                            disabled={busy}
                            onClick={() => setStatus(d.id, st)}
                          >
                            → {st}
                          </button>
                        ))}
                    </div>
                  </li>
                );
              })}
            </ul>
          )}
        </section>

        {selected ? (
          <section className="border rounded-lg p-4 text-sm space-y-2" data-testid="deal-detail">
            <h2 className="font-semibold">Dettaglio</h2>
            <p>
              <strong>{selected.property_title || "Immobile"}</strong>
              {" · "}
              {selected.client_label || "Cliente"}
            </p>
            <p className="text-xs text-crm-muted">
              Stato {selected.status} · ruolo {selected.role}
            </p>
            {(selected.proposals || []).length ? (
              <ul className="text-xs space-y-1">
                {selected.proposals.map((p, i) => (
                  <li key={i}>
                    Proposta {p.amount} {p.notes ? `— ${p.notes}` : ""}
                  </li>
                ))}
              </ul>
            ) : null}
          </section>
        ) : null}
      </div>
    </AgencyShell>
  );
}
