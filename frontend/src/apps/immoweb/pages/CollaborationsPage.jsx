import React, { useCallback, useEffect, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { useTranslation } from "react-i18next";
import AgencyShell from "../components/AgencyShell";
import VisitSlotsPicker from "../components/VisitSlotsPicker";
import { defaultProposedSlots, normalizeProposedSlots } from "../components/visitSlots";
import { api } from "../../../shared/lib/api";

function formatSlot(slot) {
  if (!slot) return "—";
  const d = new Date(slot);
  if (Number.isNaN(d.getTime())) return slot;
  return d.toLocaleString("it-IT", {
    dateStyle: "medium",
    timeStyle: "short",
  });
}

/**
 * Collaborazioni MLS operative (CMJ-02/03/04/05).
 */
export default function CollaborationsPage() {
  const { i18n } = useTranslation();
  const lang = (i18n.language || "it").slice(0, 2);
  const [searchParams] = useSearchParams();
  const highlightCollab = searchParams.get("collaboration_id");
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
  const [visitFormCollabId, setVisitFormCollabId] = useState(null);
  const [proposedSlots, setProposedSlots] = useState(() => defaultProposedSlots());
  const [agreeSlotByVisit, setAgreeSlotByVisit] = useState({});

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

  const openVisitForm = (collaborationId) => {
    setVisitFormCollabId(collaborationId);
    setProposedSlots(defaultProposedSlots());
    setErr("");
  };

  const requestVisit = async (collaborationId) => {
    const check = normalizeProposedSlots(proposedSlots);
    if (!check.ok) {
      setErr(check.error);
      return;
    }
    setBusy(true);
    setErr("");
    try {
      await api.post("/app/visits", {
        collaboration_id: collaborationId,
        proposed_slots: check.slots,
      });
      setVisitFormCollabId(null);
      setProposedSlots(defaultProposedSlots());
      await load();
    } catch (e) {
      const detail = e?.response?.data?.detail;
      setErr(
        typeof detail === "object" && detail?.message
          ? detail.message
          : detail || "Richiesta visita fallita"
      );
    } finally {
      setBusy(false);
    }
  };

  const patchVisit = async (visitId, status, agreedSlot) => {
    setBusy(true);
    setErr("");
    try {
      const body = { status };
      if (status === "agreed") {
        const slot = agreedSlot || agreeSlotByVisit[visitId];
        if (!slot) {
          setErr("Seleziona uno degli orari proposti");
          setBusy(false);
          return;
        }
        body.agreed_slot = slot;
      }
      await api.patch(`/app/visits/${visitId}`, body);
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

  const dealHref = (v) => {
    const q = new URLSearchParams();
    if (v.property_id) q.set("property_id", v.property_id);
    if (v.collaboration_id) q.set("collaboration_id", v.collaboration_id);
    if (v.id) q.set("visit_id", v.id);
    if (v.property_label) q.set("property_label", v.property_label);
    return `/${lang}/app/deals?${q.toString()}`;
  };

  return (
    <AgencyShell current="collaborations">
      <div className="crm-desk max-w-6xl mx-auto space-y-6" data-testid="collaborations-page">
        <header className="space-y-2">
          <p className="crm-eyebrow">MLS operativo</p>
          <h1 className="crm-title text-3xl md:text-4xl">Collaborazioni</h1>
          <p className="text-crm-muted max-w-2xl text-sm">
            Accettazione, visite con almeno tre orari, mini-dossier, Deal e chat contestuale.
          </p>
          <p className="text-xs">
            <Link className="underline" to={`/${lang}/app/mls`}>
              MLS
            </Link>
            {" · "}
            <Link className="underline" to={`/${lang}/app/deals`}>
              Deal
            </Link>
          </p>
        </header>

        {err ? (
          <div
            className="rounded-md border border-rose-200 bg-rose-50 px-4 py-3 text-rose-800 text-sm"
            data-testid="collab-error"
          >
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
                  className={`border border-crm-border rounded-lg p-4 space-y-2 bg-white/60 ${
                    highlightCollab === c.id ? "ring-2 ring-slate-700" : ""
                  }`}
                  data-testid={`collab-item-${c.id}`}
                >
                  <div className="flex flex-wrap gap-2 justify-between items-start">
                    <div>
                      <p className="text-sm font-medium" data-testid={`collab-label-${c.id}`}>
                        {c.property_label || "Immobile"}
                      </p>
                      {c.property_address ? (
                        <p className="text-xs text-crm-muted">{c.property_address}</p>
                      ) : null}
                      <p className="text-xs text-crm-muted">
                        Partner: {c.counterpart_agency_label || "—"} · Stato: {c.status}
                        {c.viewer_role ? ` · tu: ${c.viewer_role}` : ""}
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
                            data-testid={`collab-accept-${c.id}`}
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
                            onClick={() => openVisitForm(c.id)}
                            data-testid={`collab-request-visit-${c.id}`}
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
                          <Link
                            className="text-xs px-3 py-1 rounded border inline-flex items-center"
                            to={`/${lang}/app/deals?collaboration_id=${encodeURIComponent(c.id)}&property_id=${encodeURIComponent(c.property_id || "")}&property_label=${encodeURIComponent(c.property_label || "")}`}
                          >
                            Apri Deal
                          </Link>
                          <button
                            type="button"
                            disabled={busy}
                            className="text-xs px-3 py-1 rounded border border-rose-300 text-rose-700"
                            onClick={() => respond(c.id, "revoke")}
                            data-testid={`collab-revoke-${c.id}`}
                          >
                            Revoca
                          </button>
                        </>
                      ) : null}
                      {c.status === "revoked" ? (
                        <span className="text-xs text-rose-700">Accessi documenti/chat revocati</span>
                      ) : null}
                    </div>
                  </div>
                  {visitFormCollabId === c.id ? (
                    <div
                      className="mt-2 border rounded-md p-3 bg-slate-50 space-y-3"
                      data-testid={`visit-form-${c.id}`}
                    >
                      <p className="text-sm font-medium">Proponi almeno tre orari</p>
                      <VisitSlotsPicker
                        slots={proposedSlots}
                        onChange={setProposedSlots}
                        disabled={busy}
                        testId={`visit-slots-${c.id}`}
                      />
                      <ul className="text-xs text-crm-muted space-y-1" data-testid={`visit-slots-preview-${c.id}`}>
                        {proposedSlots.filter(Boolean).map((s, i) => (
                          <li key={i}>{formatSlot(s)}</li>
                        ))}
                      </ul>
                      <div className="flex gap-2">
                        <button
                          type="button"
                          disabled={busy}
                          className="text-xs px-3 py-1 rounded bg-slate-800 text-white"
                          onClick={() => requestVisit(c.id)}
                          data-testid={`visit-submit-${c.id}`}
                        >
                          Invia richiesta
                        </button>
                        <button
                          type="button"
                          disabled={busy}
                          className="text-xs px-3 py-1 rounded border"
                          onClick={() => setVisitFormCollabId(null)}
                        >
                          Annulla
                        </button>
                      </div>
                    </div>
                  ) : null}
                </li>
              ))}
            </ul>
          )}
        </section>

        <section className="space-y-3" data-testid="visits-list">
          <h2 className="text-lg font-semibold">Visite</h2>
          {(visits || []).length === 0 ? (
            <p className="text-sm text-crm-muted">Nessuna visita.</p>
          ) : null}
          {(visits || []).map((v) => (
            <div
              key={v.id}
              className="border rounded-lg p-3 space-y-2 bg-white/60"
              data-testid={`visit-item-${v.id}`}
            >
              <p className="text-sm font-medium">{v.property_label || "Immobile"}</p>
              <p className="text-xs text-crm-muted">
                Stato visita: {v.status}
                {v.agreed_slot ? ` · confermata: ${formatSlot(v.agreed_slot)}` : ""}
                {v.next_action ? ` · prossima: ${v.next_action}` : ""}
              </p>
              {(v.proposed_slots || []).length ? (
                <ul className="text-xs space-y-1" data-testid={`visit-proposed-${v.id}`}>
                  {(v.proposed_slots || []).map((s) => (
                    <li key={s}>{formatSlot(s)}</li>
                  ))}
                </ul>
              ) : null}
              <div className="flex flex-wrap gap-2 items-center">
                {v.status === "requested" || v.status === "proposed" ? (
                  <>
                    <select
                      className="text-xs border rounded px-2 py-1"
                      value={agreeSlotByVisit[v.id] || ""}
                      onChange={(e) =>
                        setAgreeSlotByVisit((m) => ({ ...m, [v.id]: e.target.value }))
                      }
                      data-testid={`visit-agree-select-${v.id}`}
                    >
                      <option value="">Seleziona orario…</option>
                      {(v.proposed_slots || []).map((s) => (
                        <option key={s} value={s}>
                          {formatSlot(s)}
                        </option>
                      ))}
                    </select>
                    <button
                      type="button"
                      className="text-xs px-2 py-1 border rounded"
                      disabled={busy || !(agreeSlotByVisit[v.id] || (v.proposed_slots || [])[0])}
                      onClick={() =>
                        patchVisit(
                          v.id,
                          "agreed",
                          agreeSlotByVisit[v.id] || (v.proposed_slots || [])[0]
                        )
                      }
                      data-testid={`visit-confirm-${v.id}`}
                    >
                      Concorda
                    </button>
                  </>
                ) : null}
                {v.status === "agreed" ? (
                  <button
                    type="button"
                    className="text-xs px-2 py-1 border rounded"
                    disabled={busy}
                    onClick={() => patchVisit(v.id, "completed")}
                    data-testid={`visit-complete-${v.id}`}
                  >
                    Segna effettuata
                  </button>
                ) : null}
                {v.status === "completed" ? (
                  <>
                    <div className="flex items-center gap-2 flex-wrap">
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
                        data-testid={`visit-feedback-text-${v.id}`}
                      />
                      <button
                        type="button"
                        className="text-xs px-2 py-1 bg-slate-800 text-white rounded"
                        onClick={() => submitFeedback(v.id)}
                      >
                        Invia feedback
                      </button>
                    </div>
                    <Link
                      className="text-xs px-2 py-1 border rounded inline-flex items-center bg-emerald-50"
                      to={dealHref(v)}
                      data-testid={`visit-open-deal-${v.id}`}
                    >
                      Apri Deal da visita
                    </Link>
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
                      data-testid={`visit-open-chat-${v.id}`}
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
              Rating {f.rating}/5 · feedback {f.feedback_text ? "sì" : "—"} · document_request=
              {String(!!f.is_document_request)}
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
              {d.status === "fulfilled" ? (
                <button
                  type="button"
                  className="text-xs px-2 py-1 border rounded"
                  disabled={busy}
                  onClick={async () => {
                    try {
                      const r = await api.get(`/app/document-requests/${d.id}/download`, {
                        responseType: "blob",
                      });
                      const url = URL.createObjectURL(r.data);
                      const a = document.createElement("a");
                      a.href = url;
                      a.download = `omnia-wm-${d.id}.jpg`;
                      a.click();
                      URL.revokeObjectURL(url);
                    } catch (e) {
                      setErr(e?.response?.data?.detail || "Download watermark fallito");
                    }
                  }}
                >
                  Scarica watermarkato
                </button>
              ) : null}
              {d.status === "revoked" ? (
                <span className="text-xs text-rose-700">revocata</span>
              ) : null}
            </div>
          ))}
        </section>

        {thread ? (
          <section className="space-y-2 border rounded-lg p-4" data-testid="collab-chat">
            <h2 className="text-lg font-semibold">Chat contestuale</h2>
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
                data-testid="collab-chat-input"
              />
              <button
                type="button"
                disabled={busy}
                className="text-sm px-3 py-1 bg-slate-800 text-white rounded"
                onClick={sendMsg}
                data-testid="collab-chat-send"
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
