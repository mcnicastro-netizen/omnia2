import React, { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { api } from "../../../shared/lib/api";
import AgencyShell from "../components/AgencyShell";
import Brand from "../../../shared/components/Brand";

/**
 * ApiKeysPage — M2.5.2 Track B API Gateway (D-041/D-046).
 * Manage OMNIA API keys used by external partners (widgets, custom integrations).
 */
export default function ApiKeysPage() {
  const { t } = useTranslation();
  const [keys, setKeys] = useState([]);
  const [loading, setLoading] = useState(true);
  const [issued, setIssued] = useState(null); // {key, api_key} — show-once
  const [form, setForm] = useState({ name: "", initial_credits: 100, partner_id: "", allowed_origins: "" });
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);

  const load = async () => {
    setLoading(true);
    try {
      const r = await api.get("/app/api-keys");
      setKeys(r.data?.items || []);
    } catch (e) {
      setError(e?.response?.data?.detail || "load_error");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const submit = async (e) => {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      const r = await api.post("/app/api-keys", {
        name: form.name.trim(),
        initial_credits: parseInt(form.initial_credits, 10) || 0,
        partner_id: form.partner_id.trim() || null,
        allowed_origins: form.allowed_origins
          .split(/[\n,]+/)
          .map((s) => s.trim())
          .filter(Boolean),
      });
      setIssued(r.data);
      setForm({ name: "", initial_credits: 100, partner_id: "", allowed_origins: "" });
      load();
    } catch (e) {
      setError(e?.response?.data?.detail || "create_error");
    } finally {
      setBusy(false);
    }
  };

  const revoke = async (id) => {
    if (!confirm(t("api_keys.confirm_revoke") || "Revocare questa chiave?")) return;
    try {
      await api.post(`/app/api-keys/${id}/revoke`);
      load();
    } catch (e) {
      setError(e?.response?.data?.detail || "revoke_error");
    }
  };

  const topUp = async (id) => {
    const raw = prompt(t("api_keys.topup_prompt") || "Crediti da aggiungere (positivo=carica, negativo=scala):", "100");
    if (raw === null) return;
    const delta = parseInt(raw, 10);
    if (isNaN(delta)) return;
    try {
      await api.post(`/app/api-keys/${id}/credits`, { delta, reason: "manual top-up" });
      load();
    } catch (e) {
      setError(e?.response?.data?.detail || "topup_error");
    }
  };

  const copy = async (text) => {
    try {
      await navigator.clipboard.writeText(text);
    } catch (_) {
      // clipboard not available (older browser) — silent fallback
    }
  };

  return (
    <AgencyShell current="api-keys">
      <section data-testid="api-keys-page" className="space-y-8">
        <div>
          <p className="text-[10px] uppercase tracking-[0.3em] text-stone-500 mb-2">
            <Brand>ImmoWeb · Track B / API Gateway</Brand>
          </p>
          <h1
            className="text-3xl md:text-4xl tracking-tight"
            style={{ fontFamily: "'Fraunces', Georgia, serif" }}
          >
            {t("api_keys.title") || "Chiavi API"}
          </h1>
          <p className="text-sm text-stone-600 mt-1 max-w-2xl">
            {t("api_keys.subtitle") ||
              "Emetti chiavi API per far consumare le feature OMNIA (Valutatore, Mutui, HAL Legal) da widget o gestionali esterni. 1 credito = €0,03."}
          </p>
        </div>

        {/* Show-once plaintext key box */}
        {issued && (
          <div
            data-testid="api-key-issued-box"
            className="border-2 border-emerald-500 bg-emerald-50 rounded-lg p-4"
          >
            <div className="flex items-start justify-between mb-2">
              <div>
                <p className="text-[10px] uppercase tracking-widest text-emerald-700 font-semibold">
                  {t("api_keys.issued_once") || "Chiave visibile una sola volta"}
                </p>
                <p className="text-xs text-stone-600 mt-1">
                  {t("api_keys.issued_hint") ||
                    "Copiala ora — dopo aver chiuso questo box la chiave non sarà più recuperabile."}
                </p>
              </div>
              <button
                onClick={() => setIssued(null)}
                className="text-stone-500 hover:text-stone-900 text-xl"
                aria-label="Close"
                data-testid="api-key-issued-close"
              >
                ×
              </button>
            </div>
            <div className="flex items-center gap-2 bg-white border border-emerald-300 rounded p-3 mt-2">
              <code
                data-testid="api-key-plaintext"
                className="font-mono text-sm text-stone-900 flex-1 break-all"
              >
                {issued.key}
              </code>
              <button
                onClick={() => copy(issued.key)}
                data-testid="api-key-copy"
                className="text-xs font-sans uppercase tracking-widest bg-emerald-600 text-white px-3 py-1.5 rounded hover:bg-emerald-700"
              >
                {t("common.copy") || "Copia"}
              </button>
            </div>
          </div>
        )}

        {/* Create form */}
        <form
          onSubmit={submit}
          data-testid="api-key-create-form"
          className="bg-white border border-stone-200 rounded-lg p-4 space-y-3 max-w-3xl"
        >
          <p className="text-[10px] uppercase tracking-widest text-stone-500">
            {t("api_keys.create_title") || "Emetti nuova chiave"}
          </p>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            <div className="sm:col-span-1">
              <label className="text-xs text-stone-500 block mb-1">
                {t("api_keys.name") || "Nome"} *
              </label>
              <input
                data-testid="api-key-name-input"
                type="text"
                required
                minLength={1}
                maxLength={120}
                value={form.name}
                onChange={(e) => setForm({ ...form, name: e.target.value })}
                placeholder="Widget cliente X"
                className="w-full border border-stone-300 rounded px-3 py-2 text-sm"
              />
            </div>
            <div>
              <label className="text-xs text-stone-500 block mb-1">
                {t("api_keys.initial_credits") || "Crediti iniziali"}
              </label>
              <input
                data-testid="api-key-credits-input"
                type="number"
                min={0}
                max={1000000}
                value={form.initial_credits}
                onChange={(e) => setForm({ ...form, initial_credits: e.target.value })}
                className="w-full border border-stone-300 rounded px-3 py-2 text-sm"
              />
            </div>
            <div>
              <label className="text-xs text-stone-500 block mb-1">
                {t("api_keys.partner_id") || "Partner ID"} <span className="text-stone-400">(D-046)</span>
              </label>
              <input
                data-testid="api-key-partner-input"
                type="text"
                maxLength={60}
                value={form.partner_id}
                onChange={(e) => setForm({ ...form, partner_id: e.target.value })}
                placeholder="webagency_xyz"
                className="w-full border border-stone-300 rounded px-3 py-2 text-sm"
              />
            </div>
          </div>
          <div>
            <label className="text-xs text-stone-500 block mb-1">
              {t("api_keys.origins") || "Origins consentiti"} <span className="text-stone-400">(widget security, uno per riga)</span>
            </label>
            <textarea
              data-testid="api-key-origins-input"
              rows={2}
              value={form.allowed_origins}
              onChange={(e) => setForm({ ...form, allowed_origins: e.target.value })}
              placeholder="https://agenziarossi.it&#10;https://*.agenziarossi.it"
              className="w-full border border-stone-300 rounded px-3 py-2 text-sm font-mono text-xs"
            />
            <p className="text-xs text-stone-500 mt-1">
              {t("api_keys.origins_hint") || "Vuoto = nessuna restrizione (chiave server-side). Popolato = solo widget su quei domini possono usarla."}
            </p>
          </div>
          {error && (
            <p data-testid="api-key-error" className="text-xs text-red-600">
              {error}
            </p>
          )}
          <div className="flex justify-end">
            <button
              type="submit"
              disabled={busy || !form.name.trim()}
              data-testid="api-key-submit"
              className="bg-stone-900 text-stone-50 text-xs uppercase tracking-widest px-5 py-2 rounded hover:bg-stone-700 disabled:opacity-40"
            >
              {busy ? "…" : t("api_keys.issue") || "Emetti chiave"}
            </button>
          </div>
        </form>

        {/* Keys list */}
        <div>
          <p className="text-[10px] uppercase tracking-widest text-stone-500 mb-3">
            {t("api_keys.list_title") || "Chiavi attive"}
          </p>
          <div className="border border-stone-200 rounded-lg overflow-hidden bg-white">
            <table className="w-full text-sm">
              <thead className="bg-stone-50 text-[10px] uppercase tracking-widest text-stone-500">
                <tr>
                  <th className="text-left px-4 py-3 font-medium">Nome</th>
                  <th className="text-left px-4 py-3 font-medium">Prefix</th>
                  <th className="text-left px-4 py-3 font-medium">Partner</th>
                  <th className="text-right px-4 py-3 font-medium">Saldo</th>
                  <th className="text-right px-4 py-3 font-medium">Spesi</th>
                  <th className="text-left px-4 py-3 font-medium">Stato</th>
                  <th className="text-right px-4 py-3 font-medium">Azioni</th>
                </tr>
              </thead>
              <tbody data-testid="api-keys-table-body">
                {loading ? (
                  <tr>
                    <td colSpan={7} className="px-4 py-6 text-stone-500 text-center">…</td>
                  </tr>
                ) : keys.length === 0 ? (
                  <tr>
                    <td colSpan={7} className="px-4 py-6 text-stone-500 text-center" data-testid="api-keys-empty">
                      {t("api_keys.empty") || "Nessuna chiave attiva. Emetti la prima con il form sopra."}
                    </td>
                  </tr>
                ) : (
                  keys.map((k) => (
                    <tr
                      key={k.id}
                      data-testid={`api-key-row-${k.id}`}
                      className="border-t border-stone-200 hover:bg-stone-50"
                    >
                      <td className="px-4 py-3 font-medium text-stone-900">{k.name}</td>
                      <td className="px-4 py-3 font-mono text-xs text-stone-600">{k.key_prefix}…</td>
                      <td className="px-4 py-3 text-stone-600 text-xs">{k.partner_id || "—"}</td>
                      <td className="px-4 py-3 text-right tabular-nums text-stone-900">
                        {k.credits_balance}
                      </td>
                      <td className="px-4 py-3 text-right tabular-nums text-stone-500">
                        {k.credits_spent}
                      </td>
                      <td className="px-4 py-3">
                        {k.is_active ? (
                          <span className="inline-block px-2 py-0.5 rounded text-[10px] uppercase tracking-widest bg-emerald-100 text-emerald-800">
                            active
                          </span>
                        ) : (
                          <span className="inline-block px-2 py-0.5 rounded text-[10px] uppercase tracking-widest bg-stone-200 text-stone-600">
                            revoked
                          </span>
                        )}
                      </td>
                      <td className="px-4 py-3 text-right space-x-2">
                        {k.is_active && (
                          <>
                            <button
                              onClick={() => topUp(k.id)}
                              data-testid={`api-key-topup-${k.id}`}
                              className="text-xs uppercase tracking-widest text-stone-600 hover:text-stone-900"
                            >
                              +€
                            </button>
                            <button
                              onClick={() => revoke(k.id)}
                              data-testid={`api-key-revoke-${k.id}`}
                              className="text-xs uppercase tracking-widest text-red-600 hover:text-red-800"
                            >
                              revoca
                            </button>
                          </>
                        )}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>

        <div className="bg-stone-50 border border-stone-200 rounded-lg p-4 text-xs text-stone-600 space-y-2 max-w-3xl">
          <p className="font-medium text-stone-900">
            {t("api_keys.docs_title") || "Come si usa"}
          </p>
          <p>
            Auth header: <code className="bg-white px-1.5 py-0.5 rounded font-mono">Authorization: Bearer omk_live_...</code>
          </p>
          <p>
            Endpoint API v1: <code>/api/v1/valuator</code> (5cr) · <code>/api/v1/mortgages/compare</code> (1) · <code>/api/v1/legal/ask</code> (3) · <code>/api/v1/widgets/lead</code> (0) · <code>/api/v1/feed/properties</code> (0)
          </p>
          <p>
            Widget embed (Track B, M2.5.3):
          </p>
          <pre className="bg-white border border-stone-200 rounded p-3 overflow-x-auto text-[11px] leading-snug">{`<script src="${window.location.origin}/api/widgets/v1/loader.js"
  data-key="omk_live_..."
  data-widget="valuator"
  data-primary="#0b1e3f"
  data-lang="it"></script>`}</pre>
          <p>
            Anteprima widget: <a href="/it/widgets" className="underline">/it/widgets</a> · Health API: <a href="/api/v1/health" target="_blank" rel="noreferrer" className="underline">/api/v1/health</a>
          </p>
        </div>
      </section>
    </AgencyShell>
  );
}
