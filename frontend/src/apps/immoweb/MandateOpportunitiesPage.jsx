import React, { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { Link, useNavigate } from "react-router-dom";
import { toast } from "sonner";
import AgencyShell from "./components/AgencyShell";
import { api } from "../../shared/lib/api";

const STATUSES = [
  { value: "", label: "Aperte" },
  { value: "new", label: "Nuove" },
  { value: "contacted", label: "Contattate" },
  { value: "appointment", label: "Appuntamento" },
  { value: "mandate_won", label: "Mandato acquisito" },
  { value: "lost", label: "Persa" },
  { value: "dismissed", label: "Scartata" },
];

const DISMISS_REASONS = [
  { value: "no_response", label: "Nessuna risposta" },
  { value: "already_mandated", label: "Già con altro mandato" },
  { value: "price_unrealistic", label: "Prezzo irrealistico" },
  { value: "out_of_area", label: "Fuori zona" },
  { value: "low_demand_quality", label: "Domanda debole / non qualificata" },
  { value: "duplicate", label: "Duplicato" },
  { value: "other", label: "Altro" },
];

const NEXT = {
  new: ["contacted", "dismissed"],
  contacted: ["appointment", "lost", "dismissed"],
  appointment: ["mandate_won", "lost"],
};

function formatPrice(v) {
  if (v == null) return "—";
  return new Intl.NumberFormat("it-IT", {
    style: "currency",
    currency: "EUR",
    maximumFractionDigits: 0,
  }).format(v);
}

function scoreTone(score) {
  if (score >= 85) return "text-rose-700 bg-rose-50 border-rose-200";
  if (score >= 65) return "text-orange-700 bg-orange-50 border-orange-200";
  if (score >= 50) return "text-amber-800 bg-amber-50 border-amber-200";
  return "text-stone-600 bg-stone-100 border-stone-200";
}

function actionLabel(st) {
  if (st === "contacted") return "Contatta";
  if (st === "appointment") return "Appuntamento";
  if (st === "mandate_won") return "Mandato acquisito";
  if (st === "lost") return "Persa";
  if (st === "dismissed") return "Scarta";
  return st;
}

export default function MandateOpportunitiesPage() {
  const { t, i18n } = useTranslation();
  const lang = (i18n.language || "it").slice(0, 2);
  const navigate = useNavigate();
  const [status, setStatus] = useState("");
  const [items, setItems] = useState([]);
  const [proof, setProof] = useState(null);
  const [loading, setLoading] = useState(true);
  const [busyId, setBusyId] = useState(null);
  const [dismissFor, setDismissFor] = useState(null);
  const [dismissReason, setDismissReason] = useState("no_response");

  const load = async (st = status) => {
    setLoading(true);
    try {
      const q = st ? `?status=${st}&min_score=40` : "?min_score=40";
      const [{ data: list }, { data: p }] = await Promise.all([
        api.get(`/app/mandate-opportunities${q}`),
        api.get("/app/mandate-opportunities/proof"),
      ]);
      setItems(list.items || []);
      setProof(p);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load("");
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const advance = async (id, nextStatus) => {
    if (nextStatus === "dismissed") {
      setDismissFor(id);
      setDismissReason("no_response");
      return;
    }
    setBusyId(id);
    try {
      await api.patch(`/app/mandate-opportunities/${id}`, { status: nextStatus });
      toast.success(
        nextStatus === "contacted"
          ? "Segnato come contattato — chiudi il cerchio con telefono/WA"
          : "Stato aggiornato",
      );
      await load(status);
    } catch (err) {
      toast.error(err?.response?.data?.detail || "Aggiornamento fallito");
    } finally {
      setBusyId(null);
    }
  };

  const confirmDismiss = async () => {
    if (!dismissFor) return;
    setBusyId(dismissFor);
    try {
      await api.patch(`/app/mandate-opportunities/${dismissFor}`, {
        status: "dismissed",
        dismiss_reason: dismissReason,
      });
      toast.message("Opportunità scartata");
      setDismissFor(null);
      await load(status);
    } catch (err) {
      toast.error(err?.response?.data?.detail || "Scarto fallito");
    } finally {
      setBusyId(null);
    }
  };

  const createMandate = async (id) => {
    setBusyId(id);
    try {
      const { data } = await api.post(`/app/mandate-opportunities/${id}/create-mandate`);
      toast.success("Bozza immobile + venditore create");
      const propId = data.property_id;
      if (propId) {
        navigate(`/${lang}/app/properties/${propId}`);
        return;
      }
      await load(status);
    } catch (err) {
      toast.error(err?.response?.data?.detail || "Creazione bozza fallita");
    } finally {
      setBusyId(null);
    }
  };

  const funnel = proof?.pillars?.mandates?.funnel || {};
  const portal = proof?.pillars?.portal || {};

  return (
    <AgencyShell current="mandates">
      <section data-testid="mandate-opportunities-page" className="space-y-6">
        <div className="flex flex-wrap items-end justify-between gap-4">
          <div>
            <h1
              className="text-3xl md:text-4xl tracking-tight"
              style={{ fontFamily: "'Fraunces', Georgia, serif" }}
            >
              {t("mandates.title") || "Opportunità mandati"}
            </h1>
            <p className="text-stone-600 mt-1 max-w-2xl">
              {t("mandates.subtitle") ||
                "Annunci privati sul portale con domanda nel tuo portafoglio: contatta, scarta con motivo, o crea la bozza incarico."}
            </p>
          </div>
          <select
            data-testid="mandate-status-filter"
            value={status}
            onChange={(e) => {
              const v = e.target.value;
              setStatus(v);
              load(v);
            }}
            className="px-3 py-2 border border-stone-300 rounded-md text-sm"
          >
            {STATUSES.map((s) => (
              <option key={s.value || "open"} value={s.value}>
                {s.label}
              </option>
            ))}
          </select>
        </div>

        {proof && (
          <div
            data-testid="mandate-proof-strip"
            className="grid grid-cols-2 md:grid-cols-4 gap-3"
          >
            {[
              ["Nuove", funnel.new || 0],
              ["Contattate", funnel.contacted || 0],
              ["Appuntamenti", funnel.appointment || 0],
              ["Mandati", funnel.mandate_won || 0],
            ].map(([label, value]) => (
              <div
                key={label}
                className="bg-white border border-stone-200 rounded-lg px-4 py-3"
              >
                <p className="text-[10px] uppercase tracking-widest text-stone-500">
                  {label}
                </p>
                <p
                  className="text-2xl tabular-nums text-stone-900 mt-1"
                  style={{ fontFamily: "'Fraunces', Georgia, serif" }}
                >
                  {value}
                </p>
              </div>
            ))}
          </div>
        )}

        {proof && (
          <p className="text-xs text-stone-500" data-testid="mandate-portal-proof">
            Portale · contatti ImmobilCloud 7gg: {portal.leads_immobilcloud_7d ?? 0}
            {" · "}
            richieste: {portal.requests_immobilcloud_7d ?? 0}
            {" · "}
            Academy: {proof.pillars?.academy?.status === "not_implemented"
              ? "non ancora dimostrabile"
              : "ok"}
          </p>
        )}

        {dismissFor && (
          <div
            data-testid="mandate-dismiss-panel"
            className="bg-white border border-stone-300 rounded-lg p-4 space-y-3 max-w-lg"
          >
            <p className="text-sm font-medium text-stone-800">Motivo scarto</p>
            <select
              data-testid="mandate-dismiss-reason"
              className="w-full border border-stone-300 px-3 py-2 text-sm"
              value={dismissReason}
              onChange={(e) => setDismissReason(e.target.value)}
            >
              {DISMISS_REASONS.map((r) => (
                <option key={r.value} value={r.value}>
                  {r.label}
                </option>
              ))}
            </select>
            <div className="flex gap-2">
              <button
                type="button"
                data-testid="mandate-dismiss-confirm"
                className="bg-stone-900 text-white text-xs uppercase tracking-widest px-3 py-2"
                onClick={confirmDismiss}
                disabled={busyId === dismissFor}
              >
                Conferma scarto
              </button>
              <button
                type="button"
                className="border border-stone-300 text-xs uppercase tracking-widest px-3 py-2"
                onClick={() => setDismissFor(null)}
              >
                Annulla
              </button>
            </div>
          </div>
        )}

        {loading ? (
          <p className="text-stone-500 text-sm">{t("common.loading") || "Caricamento…"}</p>
        ) : items.length === 0 ? (
          <div
            data-testid="mandate-empty"
            className="bg-white border border-stone-200 rounded-lg p-12 text-center"
          >
            <p
              className="text-2xl mb-2"
              style={{ fontFamily: "'Fraunces', Georgia, serif" }}
            >
              {t("mandates.empty_title") || "Nessuna opportunità aperta"}
            </p>
            <p className="text-stone-500 max-w-md mx-auto">
              {t("mandates.empty_subtitle") ||
                "Quando un annuncio privato sul portale matcha una tua richiesta completa (città + prezzo + mq), compare qui."}
            </p>
          </div>
        ) : (
          <ul className="space-y-3" data-testid="mandate-list">
            {items.map((item) => {
              const listing = item.listing || {};
              const contact = listing.contact_public || {};
              const tone = scoreTone(item.demand_score || 0);
              const next = NEXT[item.status] || [];
              const phone = contact.phone || contact.whatsapp;
              return (
                <li
                  key={item.id}
                  data-testid={`mandate-row-${item.id}`}
                  className="bg-white border border-stone-200 rounded-lg p-4 md:p-5"
                >
                  <div className="flex flex-wrap gap-4 justify-between">
                    <div className="min-w-0 flex-1">
                      <div className="flex flex-wrap items-center gap-2 mb-1">
                        <span
                          className={`text-[10px] uppercase tracking-widest px-2 py-0.5 border rounded ${tone}`}
                        >
                          Domanda {item.demand_score}/100
                        </span>
                        <span className="text-[10px] uppercase tracking-widest text-stone-500">
                          {item.status}
                        </span>
                        {item.dismiss_reason && (
                          <span className="text-[10px] text-stone-400">
                            scarto: {item.dismiss_reason}
                          </span>
                        )}
                      </div>
                      <h2
                        className="text-xl text-stone-900 truncate"
                        style={{ fontFamily: "'Fraunces', Georgia, serif" }}
                      >
                        {listing.title || "Annuncio privato"}
                      </h2>
                      <p className="text-sm text-stone-600 mt-0.5">
                        {[listing.city, listing.zone].filter(Boolean).join(" · ")}
                        {" · "}
                        {formatPrice(listing.price)}
                        {listing.surface_sqm ? ` · ${listing.surface_sqm} m²` : ""}
                      </p>
                      {(contact.phone || contact.whatsapp || contact.display_name) && (
                        <p className="text-sm text-stone-700 mt-2">
                          Contatto pubblico:{" "}
                          {contact.display_name || "—"}
                          {contact.phone ? ` · ${contact.phone}` : ""}
                          {contact.whatsapp ? ` · WA ${contact.whatsapp}` : ""}
                        </p>
                      )}
                      {item.best_request_id && (
                        <Link
                          to={`/${lang}/app/requests/${item.best_request_id}`}
                          className="inline-block mt-2 text-xs uppercase tracking-widest text-stone-500 hover:text-stone-900"
                        >
                          Richiesta che genera la domanda →
                        </Link>
                      )}
                    </div>
                    <div className="flex flex-col gap-2 items-stretch min-w-[11rem]">
                      {listing.cloud_path && (
                        <a
                          href={`/${lang}${listing.cloud_path}`}
                          target="_blank"
                          rel="noreferrer"
                          className="text-center text-xs uppercase tracking-widest px-3 py-2 border border-stone-300 rounded-md hover:border-stone-500"
                        >
                          Vedi su portale
                        </a>
                      )}
                      {phone && item.status === "new" && (
                        <a
                          href={
                            contact.whatsapp
                              ? `https://wa.me/${String(contact.whatsapp).replace(/\D/g, "")}`
                              : `tel:${phone}`
                          }
                          target="_blank"
                          rel="noreferrer"
                          data-testid="mandate-contact-link"
                          className="text-center text-xs uppercase tracking-widest px-3 py-2 border border-emerald-700 text-emerald-800 rounded-md"
                          onClick={() => advance(item.id, "contacted")}
                        >
                          Chiama / WhatsApp
                        </a>
                      )}
                      {["new", "contacted", "appointment"].includes(item.status) && (
                        <button
                          type="button"
                          disabled={busyId === item.id}
                          data-testid="mandate-create-draft"
                          onClick={() => createMandate(item.id)}
                          className="text-xs uppercase tracking-widest px-3 py-2 bg-[#1F6B5C] text-white rounded-md hover:opacity-90 disabled:opacity-50"
                        >
                          Crea bozza incarico
                        </button>
                      )}
                      {next.map((st) => (
                        <button
                          key={st}
                          type="button"
                          disabled={busyId === item.id}
                          data-testid={`mandate-advance-${st}`}
                          onClick={() => advance(item.id, st)}
                          className={
                            st === "dismissed"
                              ? "text-xs uppercase tracking-widest px-3 py-2 border border-stone-300 text-stone-600 rounded-md disabled:opacity-50"
                              : "text-xs uppercase tracking-widest px-3 py-2 bg-stone-900 text-white rounded-md hover:bg-stone-700 disabled:opacity-50"
                          }
                        >
                          {actionLabel(st)}
                        </button>
                      ))}
                    </div>
                  </div>
                </li>
              );
            })}
          </ul>
        )}
      </section>
    </AgencyShell>
  );
}
