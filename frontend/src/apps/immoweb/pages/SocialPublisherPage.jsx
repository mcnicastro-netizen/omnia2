import React, { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { api } from "../../../shared/lib/api";
import AgencyShell from "../components/AgencyShell";
import Brand from "../../../shared/components/Brand";

/**
 * M2.6c — Social Publisher (Sprint 1 · Item #2).
 *
 * Configurazione self-service di canali social (Facebook Page, Instagram
 * Business, Telegram Channel) per pubblicare on-demand un immobile. Le
 * credenziali vengono cifrate lato backend (AES-256-GCM) e non tornano mai
 * in chiaro alla UI.
 */
const CHANNEL_META = {
  facebook_page: {
    label: "Facebook Page",
    hint: "Serve un Page Access Token con permesso pages_manage_posts (durata lunga, ideale non-scadente).",
    color: "#1877F2",
  },
  instagram_business: {
    label: "Instagram Business",
    hint: "Account IG Business collegato a una Pagina Facebook. La foto deve essere HTTPS pubblica.",
    color: "#E4405F",
  },
  telegram: {
    label: "Telegram Channel",
    hint: "Ottieni il bot token da @BotFather. Il bot deve essere admin del canale target.",
    color: "#26A5E4",
  },
};

export default function SocialPublisherPage() {
  const { i18n } = useTranslation();
  const lang = (i18n.language || "it").slice(0, 2);
  const nav = useNavigate();

  const [catalog, setCatalog] = useState([]);
  const [channels, setChannels] = useState([]);
  const [posts, setPosts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [modal, setModal] = useState(null); // { channel, creds }
  const [busy, setBusy] = useState(false);
  const [validating, setValidating] = useState(null);
  const [validationResult, setValidationResult] = useState(null);

  const load = async () => {
    setLoading(true);
    setError(null);
    try {
      const [c1, c2, c3] = await Promise.all([
        api.get("/app/publishing/social/catalog"),
        api.get("/app/publishing/social/channels"),
        api.get("/app/publishing/social/posts?limit=20"),
      ]);
      setCatalog(c1.data.items || []);
      setChannels(c2.data.items || []);
      setPosts(c3.data.items || []);
    } catch (e) {
      setError(e?.response?.data?.detail || "load_error");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const configuredTypes = new Set(channels.map((c) => c.channel));
  const availableChannels = catalog.filter((c) => !configuredTypes.has(c.channel));

  const openConfigure = (channel) => {
    const creds = {};
    (channel.credential_fields || []).forEach((f) => {
      creds[f.name] = "";
    });
    setModal({ channel, creds });
    setError(null);
    setValidationResult(null);
  };

  const submitConfigure = async () => {
    if (!modal) return;
    setBusy(true);
    setError(null);
    try {
      await api.post("/app/publishing/social/channels", {
        channel: modal.channel.channel,
        credentials: modal.creds,
      });
      setModal(null);
      await load();
    } catch (e) {
      const detail = e?.response?.data?.detail || "activate_error";
      setError(typeof detail === "string" ? detail : JSON.stringify(detail));
    } finally {
      setBusy(false);
    }
  };

  const disconnect = async (id) => {
    if (!confirm("Disconnettere questo canale? Le credenziali verranno rimosse.")) return;
    try {
      await api.delete(`/app/publishing/social/channels/${id}`);
      await load();
    } catch (e) {
      setError(e?.response?.data?.detail || "delete_error");
    }
  };

  const validate = async (channel) => {
    setValidating(channel.id);
    setValidationResult(null);
    try {
      const r = await api.post(`/app/publishing/social/channels/${channel.id}/validate`);
      setValidationResult({ ok: true, ...r.data, channelType: channel.channel });
    } catch (e) {
      setValidationResult({
        ok: false,
        error: e?.response?.data?.detail || "validation_failed",
        channelType: channel.channel,
      });
    } finally {
      setValidating(null);
      await load();
    }
  };

  return (
    <AgencyShell current="publishing">
      <section data-testid="social-publisher-page" className="space-y-8">
        <div>
          <p className="text-[10px] uppercase tracking-[0.3em] text-stone-500 mb-2">
            <Brand>ImmoWeb · Social Publisher</Brand>
          </p>
          <div className="flex flex-wrap items-start justify-between gap-4">
            <h1
              className="text-3xl md:text-4xl tracking-tight"
              style={{ fontFamily: "'Fraunces', Georgia, serif" }}
            >
              Canali social
            </h1>
            <Link
              to={`/${lang}/app/publishing`}
              data-testid="back-to-publishing"
              className="px-4 py-2 text-xs uppercase tracking-widest border border-stone-300 text-stone-700 hover:bg-stone-100 transition"
            >
              ← Torna ai portali
            </Link>
          </div>
          <p className="text-sm text-stone-600 mt-2 max-w-2xl">
            Configura le tue Pagine Facebook, account Instagram Business e canali Telegram per
            pubblicare on-demand un annuncio con foto e caption. Le credenziali sono cifrate
            AES-256-GCM e non lasciano il tuo tenant.
          </p>
        </div>

        {error && (
          <div
            data-testid="social-error"
            className="text-sm text-red-700 bg-red-50 border border-red-300 rounded p-3"
          >
            {String(error)}
          </div>
        )}

        {validationResult && (
          <div
            data-testid="social-validation-result"
            className={`text-sm border rounded p-3 flex items-start gap-3 ${
              validationResult.ok
                ? "text-emerald-800 bg-emerald-50 border-emerald-200"
                : "text-red-800 bg-red-50 border-red-200"
            }`}
          >
            <div className="flex-1">
              <strong>Validazione {CHANNEL_META[validationResult.channelType]?.label}</strong>
              {validationResult.ok ? (
                <div className="text-xs mt-1">
                  {validationResult.name && <>Nome: <strong>{validationResult.name}</strong> · </>}
                  {validationResult.username && <>Handle: <strong>@{validationResult.username}</strong> · </>}
                  {validationResult.bot_username && <>Bot: <strong>@{validationResult.bot_username}</strong> · </>}
                  ID: <code className="text-[11px]">{validationResult.id || validationResult.chat_id}</code>
                </div>
              ) : (
                <div className="text-xs mt-1">{String(validationResult.error)}</div>
              )}
            </div>
            <button
              onClick={() => setValidationResult(null)}
              className="text-xs text-stone-500 hover:text-stone-800"
            >
              ✕
            </button>
          </div>
        )}

        {/* Configured channels */}
        <div>
          <h2 className="text-lg mb-3" style={{ fontFamily: "'Fraunces', Georgia, serif" }}>
            Canali configurati
          </h2>
          <div className="bg-white border border-stone-200 rounded-lg overflow-hidden">
            {loading ? (
              <div className="px-4 py-6 text-stone-500 text-center text-sm">…</div>
            ) : channels.length === 0 ? (
              <div
                className="px-4 py-6 text-stone-500 text-center text-sm"
                data-testid="social-empty-channels"
              >
                Nessun canale ancora configurato. Attivane uno dalla sezione qui sotto.
              </div>
            ) : (
              <table className="w-full text-sm">
                <thead className="bg-stone-50 text-[10px] uppercase tracking-widest text-stone-500">
                  <tr>
                    <th className="text-left px-4 py-3">Canale</th>
                    <th className="text-left px-4 py-3">Stato</th>
                    <th className="text-left px-4 py-3">Ultimo utilizzo</th>
                    <th className="text-left px-4 py-3">Post ok / errori</th>
                    <th className="text-right px-4 py-3">Azioni</th>
                  </tr>
                </thead>
                <tbody data-testid="social-channels-table">
                  {channels.map((c) => {
                    const meta = CHANNEL_META[c.channel] || { label: c.channel, color: "#666" };
                    const last = c.last_used_at
                      ? new Date(c.last_used_at).toLocaleString("it-IT")
                      : "mai";
                    return (
                      <tr
                        key={c.id}
                        data-testid={`social-channel-row-${c.channel}`}
                        className="border-t border-stone-200 hover:bg-stone-50"
                      >
                        <td className="px-4 py-3">
                          <div className="flex items-center gap-2">
                            <span
                              className="inline-block w-2 h-2 rounded-full"
                              style={{ backgroundColor: meta.color }}
                            />
                            <div>
                              <div className="font-medium">{meta.label}</div>
                              {c.display_name && (
                                <div className="text-[10px] text-stone-500 mt-0.5">{c.display_name}</div>
                              )}
                            </div>
                          </div>
                        </td>
                        <td className="px-4 py-3">
                          <StatusBadge status={c.status} />
                          {c.last_error && (
                            <div
                              className="text-[10px] text-red-600 mt-1 max-w-[200px] truncate"
                              title={c.last_error}
                            >
                              ⚠ {c.last_error}
                            </div>
                          )}
                        </td>
                        <td className="px-4 py-3 text-stone-600 text-xs">{last}</td>
                        <td className="px-4 py-3 text-stone-600 text-xs">
                          <span className="text-emerald-700">{c.posts_ok || 0}</span>
                          {" / "}
                          <span className="text-red-600">{c.posts_failed || 0}</span>
                        </td>
                        <td className="px-4 py-3 text-right">
                          <div className="flex justify-end gap-2 items-center">
                            <button
                              onClick={() => validate(c)}
                              disabled={validating === c.id}
                              data-testid={`social-validate-${c.channel}`}
                              className="text-[10px] uppercase tracking-widest bg-stone-800 text-white px-2 py-1 rounded hover:bg-stone-900 disabled:opacity-40"
                            >
                              {validating === c.id ? "…" : "Testa"}
                            </button>
                            <button
                              onClick={() => disconnect(c.id)}
                              data-testid={`social-disconnect-${c.channel}`}
                              className="text-[10px] uppercase tracking-widest text-red-600 hover:text-red-800"
                            >
                              Disconnetti
                            </button>
                          </div>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            )}
          </div>
        </div>

        {/* Available channels to add */}
        {availableChannels.length > 0 && (
          <div>
            <h2 className="text-lg mb-3" style={{ fontFamily: "'Fraunces', Georgia, serif" }}>
              Aggiungi un canale
            </h2>
            <div className="grid md:grid-cols-3 gap-3">
              {availableChannels.map((ch) => {
                const meta = CHANNEL_META[ch.channel] || {};
                return (
                  <div
                    key={ch.channel}
                    data-testid={`social-catalog-${ch.channel}`}
                    className="bg-white border border-stone-200 rounded-lg p-4 flex flex-col"
                  >
                    <div className="flex items-center gap-2 mb-2">
                      <span
                        className="inline-block w-2 h-2 rounded-full"
                        style={{ backgroundColor: meta.color }}
                      />
                      <h3 className="font-medium">{meta.label || ch.name}</h3>
                    </div>
                    <p className="text-xs text-stone-500 flex-1 mb-3">{meta.hint || ch.notes}</p>
                    <button
                      onClick={() => openConfigure(ch)}
                      data-testid={`social-add-${ch.channel}`}
                      className="text-xs uppercase tracking-widest bg-emerald-700 text-white px-3 py-1.5 rounded hover:bg-emerald-800 self-start"
                    >
                      Configura
                    </button>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* Recent posts history */}
        <div>
          <h2 className="text-lg mb-3" style={{ fontFamily: "'Fraunces', Georgia, serif" }}>
            Storico pubblicazioni
          </h2>
          <div className="bg-white border border-stone-200 rounded-lg overflow-hidden">
            {loading ? (
              <div className="px-4 py-6 text-stone-500 text-center text-sm">…</div>
            ) : posts.length === 0 ? (
              <div className="px-4 py-6 text-stone-500 text-center text-sm" data-testid="social-empty-posts">
                Nessuna pubblicazione ancora. Attiva un canale e pubblica un immobile dalla sua scheda.
              </div>
            ) : (
              <table className="w-full text-sm">
                <thead className="bg-stone-50 text-[10px] uppercase tracking-widest text-stone-500">
                  <tr>
                    <th className="text-left px-4 py-3">Quando</th>
                    <th className="text-left px-4 py-3">Canale</th>
                    <th className="text-left px-4 py-3">Immobile</th>
                    <th className="text-left px-4 py-3">Stato</th>
                    <th className="text-left px-4 py-3">External ID / Errore</th>
                  </tr>
                </thead>
                <tbody data-testid="social-posts-table">
                  {posts.map((p) => (
                    <tr key={p.id} className="border-t border-stone-200 hover:bg-stone-50">
                      <td className="px-4 py-3 text-stone-600 text-xs whitespace-nowrap">
                        {new Date(p.created_at).toLocaleString("it-IT")}
                      </td>
                      <td className="px-4 py-3 text-xs">
                        {CHANNEL_META[p.channel]?.label || p.channel}
                      </td>
                      <td className="px-4 py-3 text-xs">
                        {p.property_id ? (
                          <Link
                            to={`/${lang}/app/properties/${p.property_id}`}
                            className="text-emerald-700 hover:underline"
                          >
                            {p.property_id.slice(0, 8)}…
                          </Link>
                        ) : (
                          <span className="text-stone-400">manuale</span>
                        )}
                      </td>
                      <td className="px-4 py-3">
                        <StatusBadge status={p.status === "success" ? "active" : "error"} />
                      </td>
                      <td className="px-4 py-3 text-[11px] font-mono text-stone-600 max-w-[280px] truncate">
                        {p.external_id || p.error || "—"}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </div>

        {/* Configuration modal */}
        {modal && (
          <div
            data-testid="social-configure-modal"
            className="fixed inset-0 bg-black/40 flex items-center justify-center z-50 p-4"
            onClick={() => setModal(null)}
          >
            <div
              className="bg-white rounded-lg max-w-md w-full p-6"
              onClick={(e) => e.stopPropagation()}
            >
              <h3 className="text-lg mb-1" style={{ fontFamily: "'Fraunces', Georgia, serif" }}>
                Configura {CHANNEL_META[modal.channel.channel]?.label}
              </h3>
              <p className="text-xs text-stone-500 mb-4">
                {CHANNEL_META[modal.channel.channel]?.hint || modal.channel.notes}
              </p>
              <div className="space-y-3 mb-4">
                {(modal.channel.credential_fields || []).map((f) => (
                  <div key={f.name}>
                    <label className="text-xs text-stone-500 block mb-1">{f.label}</label>
                    <input
                      type="text"
                      data-testid={`social-cred-${f.name}`}
                      value={modal.creds[f.name] || ""}
                      onChange={(e) =>
                        setModal({
                          ...modal,
                          creds: { ...modal.creds, [f.name]: e.target.value },
                        })
                      }
                      className="w-full border border-stone-300 rounded px-3 py-2 text-sm font-mono"
                      autoComplete="off"
                    />
                  </div>
                ))}
              </div>
              <div className="flex justify-end gap-2">
                <button
                  onClick={() => setModal(null)}
                  className="text-xs uppercase tracking-widest text-stone-500 hover:text-stone-800 px-3 py-2"
                >
                  Annulla
                </button>
                <button
                  onClick={submitConfigure}
                  disabled={busy}
                  data-testid="social-modal-confirm"
                  className="text-xs uppercase tracking-widest bg-emerald-700 text-white px-4 py-2 rounded hover:bg-emerald-800 disabled:opacity-40"
                >
                  {busy ? "…" : "Salva canale"}
                </button>
              </div>
            </div>
          </div>
        )}
      </section>
    </AgencyShell>
  );
}

function StatusBadge({ status }) {
  const styles = {
    active: "bg-emerald-100 text-emerald-800",
    pending: "bg-amber-100 text-amber-800",
    error: "bg-red-100 text-red-800",
    disabled: "bg-stone-200 text-stone-600",
  };
  return (
    <span
      className={`inline-block px-2 py-0.5 rounded text-[10px] uppercase tracking-widest ${
        styles[status] || styles.disabled
      }`}
    >
      {status}
    </span>
  );
}
