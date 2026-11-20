import React, { useCallback, useEffect, useState } from "react";
import AgencyShell from "../components/AgencyShell";
import { api } from "../../../shared/lib/api";

/**
 * Deal — ciclo opportunità di compravendita (distinto da matching / offerta MLS).
 */
export default function DealsPage() {
  const [items, setItems] = useState([]);
  const [err, setErr] = useState("");
  const [busy, setBusy] = useState(false);
  const [form, setForm] = useState({
    property_id: "",
    client_id: "",
    visit_id: "",
    collaboration_id: "",
    notes: "",
  });
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
    setBusy(true);
    setErr("");
    try {
      const body = {
        property_id: form.property_id.trim(),
        client_id: form.client_id.trim(),
        notes: form.notes || undefined,
      };
      if (form.visit_id.trim()) body.visit_id = form.visit_id.trim();
      if (form.collaboration_id.trim()) body.collaboration_id = form.collaboration_id.trim();
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

  return (
    <AgencyShell current="deals">
      <div className="crm-desk max-w-5xl mx-auto space-y-6" data-testid="deals-page">
        <header className="space-y-2">
          <p className="crm-eyebrow">Ciclo commerciale</p>
          <h1 className="crm-title text-3xl md:text-4xl">Deal</h1>
          <p className="text-crm-muted max-w-2xl text-sm">
            Gestione opportunità post-visita: apertura, proposta, accettazione/rifiuto, chiusura.
            Non sostituisce matching né accettazione offerta MLS.
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
          <div className="grid md:grid-cols-2 gap-3">
            <input
              required
              className="border rounded px-2 py-1 text-sm"
              placeholder="property_id"
              value={form.property_id}
              onChange={(e) => setForm({ ...form, property_id: e.target.value })}
            />
            <input
              required
              className="border rounded px-2 py-1 text-sm"
              placeholder="client_id"
              value={form.client_id}
              onChange={(e) => setForm({ ...form, client_id: e.target.value })}
            />
            <input
              className="border rounded px-2 py-1 text-sm"
              placeholder="visit_id (completata)"
              value={form.visit_id}
              onChange={(e) => setForm({ ...form, visit_id: e.target.value })}
            />
            <input
              className="border rounded px-2 py-1 text-sm"
              placeholder="collaboration_id"
              value={form.collaboration_id}
              onChange={(e) => setForm({ ...form, collaboration_id: e.target.value })}
            />
          </div>
          <textarea
            className="w-full border rounded px-2 py-1 text-sm"
            placeholder="Note / interesse espresso"
            value={form.notes}
            onChange={(e) => setForm({ ...form, notes: e.target.value })}
          />
          <button
            type="submit"
            disabled={busy}
            className="text-sm px-4 py-2 bg-slate-800 text-white rounded"
          >
            Apri
          </button>
        </form>

        <section className="space-y-3" data-testid="deals-list">
          <h2 className="text-lg font-semibold">Deal aperti</h2>
          {(items || []).length === 0 ? (
            <p className="text-sm text-crm-muted">Nessun Deal.</p>
          ) : (
            <ul className="space-y-3">
              {items.map((d) => (
                <li key={d.id} className="border rounded-lg p-4 space-y-2 bg-white/60">
                  <button
                    type="button"
                    className="text-left w-full"
                    onClick={() => setSelected(d)}
                  >
                    <p className="font-medium text-sm">
                      {d.property_title || d.property_id} · {d.client_label || d.client_id}
                    </p>
                    <p className="text-xs text-crm-muted">
                      {d.status} · visit {d.visit_id || "—"} · collab {d.collaboration_id || "—"}
                    </p>
                  </button>
                  <div className="flex flex-wrap gap-2 items-center">
                    <input
                      className="border rounded px-2 py-1 text-xs w-28"
                      placeholder="Importo"
                      value={proposalAmount}
                      onChange={(e) => setProposalAmount(e.target.value)}
                    />
                    <button
                      type="button"
                      className="text-xs px-2 py-1 border rounded"
                      disabled={busy}
                      onClick={() => addProposal(d.id)}
                    >
                      Prepara proposta
                    </button>
                    <button
                      type="button"
                      className="text-xs px-2 py-1 border rounded"
                      disabled={busy}
                      onClick={() => sendProposal(d.id)}
                    >
                      Invia proposta
                    </button>
                    {["accepted", "rejected", "won", "lost", "counter"].map((st) => (
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
              ))}
            </ul>
          )}
        </section>

        {selected ? (
          <section className="border rounded-lg p-4 text-sm space-y-2" data-testid="deal-detail">
            <h2 className="font-semibold">Dettaglio {selected.id}</h2>
            <pre className="text-xs overflow-auto bg-slate-50 p-2 rounded max-h-64">
              {JSON.stringify(
                {
                  status: selected.status,
                  history: selected.history,
                  proposals: selected.proposals,
                  proposal_amount: selected.proposal_amount,
                },
                null,
                2
              )}
            </pre>
          </section>
        ) : null}
      </div>
    </AgencyShell>
  );
}
