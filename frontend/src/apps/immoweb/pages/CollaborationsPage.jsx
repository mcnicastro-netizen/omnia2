import React, { useCallback, useEffect, useState } from "react";
import AgencyShell from "../components/AgencyShell";
import { api } from "../../../shared/lib/api";

/**
 * Collaborazioni MLS operative: visite, mini-dossier (feedback), richiesta documentale,
 * chat contestuale. Non confonde accettazione collaborazione con condivisione documenti.
 */
export default function CollaborationsPage() {
  const [items, setItems] = useState([]);
  const [visits, setVisits] = useState([]);
  const [feedback, setFeedback] = useState([]);
  const [docReqs, setDocReqs] = useState([]);
  const [selected, setSelected] = useState(null);
  const [thread, setThread] = useState(null);
  const [messages, setMessages] = useState([]);
  const [msg, setMsg] = useState("");
  const [rating, setRating] = useState(5);
  const [fbText, setFbText] = useState("");
  const [err, setErr] = useState("");
  const [busy, setBusy] = useState(false);

  const load = useCallback(async () => {
    setErr("");
    try {
      const [c, v, f, d] = await Promise.all([
        api.get("/app/collaborations"),
        api.get("/app/visits"),
        api.get("/app/visit-feedback"),
        api.get("/app/document-requests"),
      ]);
      setItems(c.data.items || []);
      setVisits(v.data.items || []);
      setFeedback(f.data.items || []);
      setDocReqs(d.data.items || []);
    } catch (e) {
      setErr(e?.response?.data?.detail || "Caricamento collaborazioni fallito");
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const respond = async (id, action) => {
    setBusy(true);
    try {
      await api.post(`/app/collaborations/${id}/respond`, { action });
      await load();
    } catch (e) {
      setErr(e?.response?.data?.detail || "Azione collaborazione fallita");
    } finally {
      setBusy(false);
    }
  };

  const requestVisit = async (collaborationId) => {
    setBusy(true);
    try {
      await api.post("/app/visits", { collaboration_id: collaborationId, proposed_slots: [] });
      await load();
    } catch (e) {
      setErr(e?.response?.data?.detail || "Richiesta visita fallita");
    } finally {
      setBusy(false);
    }
  };

  const patchVisit = async (visitId, status) => {
    setBusy(true);
    try {
      await api.patch(`/app/visits/${visitId}`, { status });
      await load();
    } catch (e) {
      setErr(e?.response?.data?.detail || "Aggiornamento visita fallito");
    } finally {
      setBusy(false);
    }
  };

  const submitFeedback = async (visitId) => {
    setBusy(true);
    try {
      await api.post("/app/visit-feedback", {
        visit_id: visitId,
        rating: Number(rating),
        feedback_text: fbText || undefined,
      });
      setFbText("");
      await load();
    } catch (e) {
      setErr(e?.response?.data?.detail || "Feedback post-visita fallito");
    } finally {
      setBusy(false);
    }
  };

  const createDocRequest = async (collaborationId, visitId) => {
    setBusy(true);
    try {
      await api.post("/app/document-requests", {
        collaboration_id: collaborationId,
        visit_id: visitId || undefined,
        document_keys: ["ape", "planimetria"],
        message: "Richiesta documentale esplicita post-interesse",
      });
      await load();
    } catch (e) {
      setErr(e?.response?.data?.detail || "Richiesta documentale fallita");
    } finally {
      setBusy(false);
    }
  };

  const fulfillDoc = async (requestId) => {
    setBusy(true);
    try {
      await api.post(`/app/document-requests/${requestId}/respond`, {
        action: "fulfill",
        shared_document_ids: ["doc-ape-1"],
      });
      await load();
    } catch (e) {
      setErr(e?.response?.data?.detail || "Condivisione documenti fallita");
    } finally {
      setBusy(false);
    }
  };

  const openChat = async (collaborationId, visitId) => {
    setBusy(true);
    setErr("");
    try {
      const { data } = await api.post("/app/collab-chat/threads", {
        collaboration_id: collaborationId,
        visit_id: visitId || undefined,
      });
      setThread(data);
      setSelected(collaborationId);
      const m = await api.get(`/app/collab-chat/threads/${data.id}/messages`);
      setMessages(m.data.items || []);
    } catch (e) {
      setErr(e?.response?.data?.detail || "Apertura chat contestuale fallita");
    } finally {
      setBusy(false);
    }
  };

  const sendMsg = async () => {
    if (!thread?.id || !msg.trim()) return;
    setBusy(true);
    try {
      await api.post(`/app/collab-chat/threads/${thread.id}/messages`, { body: msg.trim() });
      setMsg("");
      const m = await api.get(`/app/collab-chat/threads/${thread.id}/messages`);
      setMessages(m.data.items || []);
    } catch (e) {
      setErr(e?.response?.data?.detail || "Invio messaggio fallito");
    } finally {
      setBusy(false);
    }
  };

  return (
    <AgencyShell current="collaborations">
      <div className="crm-desk max-w-6xl mx-auto space-y-6" data-testid="collaborations-page">
        <header className="space-y-2">
          <p className="crm-eyebrow">MLS operativo</p>
          <h1 className="crm-title text-3xl md:text-4xl">Collaborazioni</h1>
          <p className="text-crm-muted max-w-2xl text-sm">
            Accettazione collaborazione, visite, mini-dossier (solo feedback/rating), richiesta
            documentale esplicita e chat contestuale. Nessuna condivisione automatica di fascicolo.
          </p>
        </header>

        {err ? (
          <div className="rounded-md border border-rose-200 bg-rose-50 px-4 py-3 text-rose-800 text-sm">
            {typeof err === "string" ? err : JSON.stringify(err)}
          </div>
        ) : null}

        <section className="space-y-3" data-testid="collab-list">
          <h2 className="text-lg font-semibold">Collaborazioni</h2>
          {(items || []).length === 0 ? (
            <p className="text-sm text-crm-muted">Nessuna collaborazione.</p>
          ) : (
            <ul className="space-y-3">
              {items.map((c) => (
                <li
                  key={c.id}
                  className="border border-crm-border rounded-lg p-4 space-y-2 bg-white/60"
                  data-testid={`collab-item-${c.id}`}
                >
                  <div className="flex flex-wrap gap-2 justify-between items-start">
                    <div>
                      <p className="text-sm font-medium">Immobile {c.property_id}</p>
                      <p className="text-xs text-crm-muted">
                        Owner {c.owner_agency_id} · Partner {c.partner_agency_id} · {c.status}
                      </p>
                      <p className="text-xs text-emerald-700">
                        auto_doc={String(!!c.document_request_auto)} · auto_share=
                        {String(!!c.auto_document_share)}
                      </p>
                    </div>
                    <div className="flex flex-wrap gap-2">
                      {c.status === "pending" ? (
                        <>
                          <button
                            type="button"
                            disabled={busy}
                            className="text-xs px-3 py-1 rounded bg-emerald-700 text-white"
                            onClick={() => respond(c.id, "accept")}
                          >
                            Accetta
                          </button>
                          <button
                            type="button"
                            disabled={busy}
                            className="text-xs px-3 py-1 rounded border"
                            onClick={() => respond(c.id, "reject")}
                          >
                            Rifiuta
                          </button>
                        </>
                      ) : null}
                      {c.status === "active" ? (
                        <>
                          <button
                            type="button"
                            disabled={busy}
                            className="text-xs px-3 py-1 rounded border"
                            onClick={() => requestVisit(c.id)}
                          >
                            Richiedi visita
                          </button>
                          <button
                            type="button"
                            disabled={busy}
                            className="text-xs px-3 py-1 rounded border"
                            onClick={() => openChat(c.id)}
                          >
                            Chat contestuale
                          </button>
                          <button
                            type="button"
                            disabled={busy}
                            className="text-xs px-3 py-1 rounded border border-rose-300 text-rose-700"
                            onClick={() => respond(c.id, "revoke")}
                          >
                            Revoca
                          </button>
                        </>
                      ) : null}
                    </div>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </section>

        <section className="space-y-3" data-testid="visits-list">
          <h2 className="text-lg font-semibold">Visite</h2>
          {(visits || []).map((v) => (
            <div key={v.id} className="border rounded-lg p-3 space-y-2 bg-white/60">
              <p className="text-sm">
                {v.id.slice(0, 8)} · collab {v.collaboration_id?.slice(0, 8)} · {v.status}
              </p>
              <div className="flex flex-wrap gap-2">
                {v.status === "requested" || v.status === "proposed" ? (
                  <button
                    type="button"
                    className="text-xs px-2 py-1 border rounded"
                    onClick={() => patchVisit(v.id, "agreed")}
                  >
                    Concorda
                  </button>
                ) : null}
                {v.status === "agreed" ? (
                  <button
                    type="button"
                    className="text-xs px-2 py-1 border rounded"
                    onClick={() => patchVisit(v.id, "completed")}
                  >
                    Segna effettuata
                  </button>
                ) : null}
                {v.status === "completed" ? (
                  <>
                    <div className="flex items-center gap-2">
                      <label className="text-xs">Rating</label>
                      <select
                        value={rating}
                        onChange={(e) => setRating(e.target.value)}
                        className="text-xs border rounded px-1"
                      >
                        {[1, 2, 3, 4, 5].map((n) => (
                          <option key={n} value={n}>
                            {n}
                          </option>
                        ))}
                      </select>
                      <input
                        className="text-xs border rounded px-2 py-1"
                        placeholder="Mini-dossier feedback"
                        value={fbText}
                        onChange={(e) => setFbText(e.target.value)}
                      />
                      <button
                        type="button"
                        className="text-xs px-2 py-1 bg-slate-800 text-white rounded"
                        onClick={() => submitFeedback(v.id)}
                      >
                        Invia feedback
                      </button>
                    </div>
                    <button
                      type="button"
                      className="text-xs px-2 py-1 border rounded"
                      onClick={() => createDocRequest(v.collaboration_id, v.id)}
                    >
                      Richiesta documentale esplicita
                    </button>
                    <button
                      type="button"
                      className="text-xs px-2 py-1 border rounded"
                      onClick={() => openChat(v.collaboration_id, v.id)}
                    >
                      Chat su visita
                    </button>
                  </>
                ) : null}
              </div>
            </div>
          ))}
        </section>

        <section className="space-y-2" data-testid="feedback-list">
          <h2 className="text-lg font-semibold">Mini-dossier (feedback/rating)</h2>
          {(feedback || []).map((f) => (
            <div key={f.id} className="text-sm border rounded p-2">
              Rating {f.rating}/5 · visit {f.visit_id?.slice(0, 8)} · document_request=
              {String(!!f.is_document_request)} · contested={String(!!f.contested)}
            </div>
          ))}
        </section>

        <section className="space-y-2" data-testid="docreq-list">
          <h2 className="text-lg font-semibold">Richieste documentali (esplicite)</h2>
          {(docReqs || []).map((d) => (
            <div key={d.id} className="text-sm border rounded p-2 flex justify-between gap-2">
              <span>
                {d.status} · auto={String(!!d.auto_created)} · watermark=
                {String(!!d.watermark_required)}
              </span>
              {d.status === "pending" ? (
                <button
                  type="button"
                  className="text-xs px-2 py-1 border rounded"
                  onClick={() => fulfillDoc(d.id)}
                >
                  Condividi (owner)
                </button>
              ) : null}
            </div>
          ))}
        </section>

        {thread ? (
          <section className="space-y-2 border rounded-lg p-4" data-testid="collab-chat">
            <h2 className="text-lg font-semibold">
              Chat contestuale {selected ? `(collab ${selected.slice(0, 8)})` : ""}
            </h2>
            <ul className="space-y-1 max-h-48 overflow-auto text-sm">
              {messages.map((m) => (
                <li key={m.id}>
                  <span className="text-crm-muted text-xs">{m.sender_agency_id}</span> {m.body}
                </li>
              ))}
            </ul>
            <div className="flex gap-2">
              <input
                className="flex-1 border rounded px-2 py-1 text-sm"
                value={msg}
                onChange={(e) => setMsg(e.target.value)}
                placeholder="Messaggio"
              />
              <button
                type="button"
                disabled={busy}
                className="text-sm px-3 py-1 bg-slate-800 text-white rounded"
                onClick={sendMsg}
              >
                Invia
              </button>
            </div>
          </section>
        ) : null}
      </div>
    </AgencyShell>
  );
}
