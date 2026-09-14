/* OMNIA — Moderation Page (M3.S5 v2)
 *
 * Admin queue for B2C private property listings. Lists pending ads, shows
 * details + photos, and lets the admin approve or reject (with notes).
 */
import React, { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { api } from "../../shared/lib/api";
import { formatApiErrorDetail } from "../../shared/lib/auth";
import AgencyShell from "./components/AgencyShell";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

export default function ModerationPage() {
  const { t } = useTranslation();
  const [tab, setTab] = useState("pending");
  const [data, setData] = useState({ items: [], total: 0 });
  const [loading, setLoading] = useState(false);
  const [selected, setSelected] = useState(null);
  const [rejectNotes, setRejectNotes] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  const load = (status) => {
    setLoading(true);
    api.get(`/app/moderation/queue?status=${status}`)
      .then((r) => setData(r.data))
      .catch((e) => setError(formatApiErrorDetail(e?.response?.data?.detail)))
      .finally(() => setLoading(false));
  };

  useEffect(() => { load(tab); }, [tab]);

  const approve = async (pid) => {
    setBusy(true); setError("");
    try {
      await api.post(`/app/moderation/${pid}/approve`);
      setSelected(null);
      load(tab);
    } catch (e) {
      setError(formatApiErrorDetail(e?.response?.data?.detail));
    } finally { setBusy(false); }
  };

  const reject = async (pid) => {
    if (!rejectNotes || rejectNotes.length < 3) {
      setError(t("moderation.err_notes_required"));
      return;
    }
    setBusy(true); setError("");
    try {
      await api.post(`/app/moderation/${pid}/reject`, { notes: rejectNotes });
      setSelected(null);
      setRejectNotes("");
      load(tab);
    } catch (e) {
      setError(formatApiErrorDetail(e?.response?.data?.detail));
    } finally { setBusy(false); }
  };

  return (
    <AgencyShell>
      <div data-testid="moderation-page" className="max-w-6xl mx-auto p-6">
        <header className="mb-6">
          <h1 className="text-3xl font-light tracking-tight" style={{ fontFamily: "'Fraunces', Georgia, serif" }}>
            {t("moderation.title")}
          </h1>
          <p className="text-stone-500 text-sm mt-1">{t("moderation.subtitle")}</p>
        </header>

        {/* Tabs */}
        <div className="flex gap-2 mb-6 border-b border-stone-200">
          {["pending", "approved", "rejected"].map((s) => (
            <button
              key={s}
              data-testid={`moderation-tab-${s}`}
              onClick={() => setTab(s)}
              className={`px-4 py-2 text-xs uppercase tracking-widest transition border-b-2 ${
                tab === s ? "border-[#0B1E3F] text-[#0B1E3F] font-medium" : "border-transparent text-stone-500 hover:text-stone-800"
              }`}>
              {t(`moderation.tab_${s}`)}
            </button>
          ))}
        </div>

        {error && (
          <div data-testid="moderation-error" className="mb-4 text-xs text-rose-700 bg-rose-50 border border-rose-200 rounded px-3 py-2">
            {error}
          </div>
        )}

        {loading ? (
          <p className="text-stone-500 text-sm">{t("common.loading")}</p>
        ) : data.items.length === 0 ? (
          <p data-testid="moderation-empty" className="text-stone-500 text-sm py-10">
            {t("moderation.empty")}
          </p>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {data.items.map((p) => (
              <article
                key={p.id}
                data-testid={`moderation-card-${p.id}`}
                className="bg-white border border-stone-200 rounded-lg p-5"
              >
                <div className="flex items-start gap-4">
                  {p.photos && p.photos.length > 0 ? (
                    <div className="w-20 h-20 bg-stone-100 rounded overflow-hidden shrink-0">
                      <img src={`${BACKEND_URL}/api/public/property/${p.id}/photo/0`} alt="" className="w-full h-full object-cover" />
                    </div>
                  ) : (
                    <div className="w-20 h-20 bg-stone-100 rounded flex items-center justify-center text-stone-400 text-xs shrink-0">
                      {t("moderation.no_photo")}
                    </div>
                  )}
                  <div className="min-w-0 flex-1">
                    <h2 className="text-base font-medium text-stone-900 truncate">{p.title}</h2>
                    <p className="text-xs text-stone-600 mt-0.5">
                      {p.city}{p.property_type ? ` · ${p.property_type}` : ""}
                      {p.operation === "rent" && p.rent_monthly ? ` · € ${p.rent_monthly.toLocaleString("it-IT")}/mese` :
                       p.price ? ` · € ${p.price.toLocaleString("it-IT")}` : ""}
                    </p>
                    <p className="text-xs text-stone-500 mt-1">
                      {p.surface_sqm ? `${p.surface_sqm} m² · ` : ""}
                      {p.rooms ? `${p.rooms} loc. · ` : ""}
                      {p.bedrooms ? `${p.bedrooms} cam. · ` : ""}
                      {p.bathrooms ? `${p.bathrooms} bagni` : ""}
                    </p>
                    {p.description && (
                      <p className="text-xs text-stone-600 mt-2 line-clamp-2">{p.description}</p>
                    )}
                    {p.owner && (
                      <p className="text-[11px] text-stone-500 mt-2">
                        👤 {p.owner.name} · 📧 {p.owner.email}{p.owner.phone ? ` · 📞 ${p.owner.phone}` : ""}
                      </p>
                    )}
                    <StatusBadge status={p.moderation_status} notes={p.moderation_notes} />
                  </div>
                </div>

                {tab === "pending" && (
                  <div className="flex gap-2 mt-4 pt-4 border-t border-stone-100">
                    <button
                      data-testid={`approve-${p.id}`}
                      onClick={() => approve(p.id)}
                      disabled={busy}
                      className="flex-1 px-4 py-2 bg-emerald-600 text-white text-xs uppercase tracking-widest rounded hover:bg-emerald-700 disabled:opacity-50"
                    >
                      ✓ {t("moderation.approve")}
                    </button>
                    <button
                      data-testid={`reject-open-${p.id}`}
                      onClick={() => { setSelected(p.id); setRejectNotes(""); }}
                      disabled={busy}
                      className="flex-1 px-4 py-2 bg-rose-600 text-white text-xs uppercase tracking-widest rounded hover:bg-rose-700 disabled:opacity-50"
                    >
                      ✗ {t("moderation.reject")}
                    </button>
                  </div>
                )}

                {selected === p.id && (
                  <div className="mt-4 pt-4 border-t border-stone-100 space-y-2">
                    <label className="text-xs uppercase tracking-widest text-stone-500">
                      {t("moderation.reject_notes_label")}
                    </label>
                    <textarea
                      data-testid={`reject-notes-${p.id}`}
                      value={rejectNotes}
                      onChange={(e) => setRejectNotes(e.target.value)}
                      placeholder={t("moderation.reject_notes_placeholder")}
                      rows={3}
                      className="w-full px-3 py-2 border border-stone-300 rounded text-sm focus:outline-none focus:border-rose-600"
                    />
                    <div className="flex gap-2">
                      <button
                        data-testid={`reject-confirm-${p.id}`}
                        onClick={() => reject(p.id)}
                        disabled={busy}
                        className="px-4 py-2 bg-rose-600 text-white text-xs uppercase tracking-widest rounded hover:bg-rose-700 disabled:opacity-50"
                      >
                        {t("moderation.reject_confirm")}
                      </button>
                      <button
                        onClick={() => setSelected(null)}
                        className="px-4 py-2 border border-stone-300 text-xs uppercase tracking-widest rounded hover:bg-stone-50"
                      >
                        {t("common.cancel")}
                      </button>
                    </div>
                  </div>
                )}
              </article>
            ))}
          </div>
        )}
      </div>
    </AgencyShell>
  );
}

function StatusBadge({ status, notes }) {
  const { t } = useTranslation();
  const config = {
    pending: { cls: "bg-amber-100 text-amber-800 border-amber-200", label: t("moderation.status_pending") },
    approved: { cls: "bg-emerald-100 text-emerald-800 border-emerald-200", label: t("moderation.status_approved") },
    rejected: { cls: "bg-rose-100 text-rose-800 border-rose-200", label: t("moderation.status_rejected") },
  }[status] || { cls: "bg-stone-100 text-stone-800 border-stone-200", label: status };
  return (
    <div className="mt-2 flex items-center gap-2 flex-wrap">
      <span className={`inline-block text-[10px] uppercase tracking-widest px-2 py-1 rounded border ${config.cls}`}>
        {config.label}
      </span>
      {status === "rejected" && notes && (
        <span className="text-[11px] text-rose-700 italic">&ldquo;{notes}&rdquo;</span>
      )}
    </div>
  );
}
