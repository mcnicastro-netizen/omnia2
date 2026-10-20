/**
 * OMNIA — Modulistica CRM (M5.S7) + firma elettronica (M5.S8 / YouTrust)
 * Template italiani, PDF white-label, invio firma multi-firmatario dove richiesto.
 */
import { useEffect, useMemo, useState } from "react";
import { Link, useParams, useSearchParams } from "react-router-dom";
import { toast } from "sonner";
import AgencyShell from "@/apps/immoweb/components/AgencyShell";
import { api } from "@/shared/lib/api";

const STATUS_LABEL = {
  draft: "Bozza",
  sent: "In firma",
  signed: "Firmato",
  void: "Annullato",
};

const ESIGN_LABEL = {
  required: "Firma obbligatoria",
  recommended: "Firma consigliata",
  optional: "Firma opzionale",
  none: "Solo PDF",
};

const ROLE_LABEL = {
  buyer: "Acquirente",
  seller: "Venditore",
  landlord: "Locatore",
  agency: "Agenzia / Mediatore",
  client: "Cliente",
};

function emptySigner(role) {
  return { role, first_name: "", last_name: "", email: "" };
}

function splitName(full) {
  const parts = String(full || "")
    .trim()
    .split(/\s+/)
    .filter(Boolean);
  if (!parts.length) return { first_name: "", last_name: "" };
  if (parts.length === 1) return { first_name: parts[0], last_name: parts[0] };
  return { first_name: parts[0], last_name: parts.slice(1).join(" ") };
}

/** Prefill firmatari da contesto PDF (cliente/immobile/agenzia) quando disponibile. */
function buildSignersForTemplate(tpl, ctx = {}) {
  const roles = tpl?.signers?.length ? tpl.signers : ["client"];
  return roles.map((role) => {
    const base = emptySigner(role);
    let name = "";
    let email = "";
    if (role === "buyer") {
      name = ctx.buyer_name || ctx.client_name || "";
      email = ctx.buyer_email || ctx.client_email || "";
    } else if (role === "seller") {
      name = ctx.seller_name || "";
      email = ctx.seller_email || "";
    } else if (role === "landlord") {
      name = ctx.landlord_name || ctx.seller_name || "";
      email = ctx.landlord_email || ctx.seller_email || "";
    } else if (role === "agency") {
      name = ctx.agency_name || "";
      email = ctx.agency_email || ctx.agency_pec || "";
    } else if (role === "client") {
      name = ctx.client_name || ctx.buyer_name || "";
      email = ctx.client_email || ctx.buyer_email || "";
    }
    const { first_name, last_name } = splitName(name);
    return { ...base, first_name, last_name, email };
  });
}

export default function ModulisticaPage() {
  const { lang = "it" } = useParams();
  const [searchParams] = useSearchParams();
  const preProperty = searchParams.get("property_id") || "";
  const preClient = searchParams.get("client_id") || "";

  const [templates, setTemplates] = useState([]);
  const [docs, setDocs] = useState([]);
  const [esign, setEsign] = useState(null);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [slug, setSlug] = useState("");
  const [propertyId, setPropertyId] = useState(preProperty);
  const [clientId, setClientId] = useState(preClient);
  const [signers, setSigners] = useState([emptySigner("client")]);
  const [selectedDoc, setSelectedDoc] = useState(null);
  const [category, setCategory] = useState("all");

  const selectedTpl = useMemo(
    () => templates.find((t) => t.slug === slug) || null,
    [templates, slug],
  );

  const load = async () => {
    setLoading(true);
    try {
      const [t, d, e] = await Promise.all([
        api.get("/app/modulistica/templates"),
        api.get("/app/modulistica/documents", { params: { page_size: 50 } }),
        api.get("/app/modulistica/esign/status"),
      ]);
      const items = t.data.items || [];
      setTemplates(items);
      setDocs(d.data.items || []);
      setEsign(e.data);
      if (!slug && items[0]) {
        setSlug(items[0].slug);
        setSigners(buildSignersForTemplate(items[0], {}));
      }
    } catch (err) {
      toast.error(err?.response?.data?.detail || "Impossibile caricare la modulistica");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    if (selectedTpl) {
      setSigners(buildSignersForTemplate(selectedTpl, selectedDoc?.context || {}));
    }
  }, [selectedTpl?.slug]); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    if (selectedDoc?.context && selectedTpl) {
      setSigners(buildSignersForTemplate(selectedTpl, selectedDoc.context));
    }
  }, [selectedDoc?.id]); // eslint-disable-line react-hooks/exhaustive-deps

  const filtered = useMemo(() => {
    if (category === "all") return templates;
    return templates.filter((t) => t.category === category);
  }, [templates, category]);

  const categories = useMemo(() => {
    const set = new Set(templates.map((t) => t.category));
    return ["all", ...Array.from(set)];
  }, [templates]);

  const updateSigner = (idx, field, value) => {
    setSigners((prev) =>
      prev.map((s, i) => (i === idx ? { ...s, [field]: value } : s)),
    );
  };

  const generate = async () => {
    if (!slug) return;
    setBusy(true);
    try {
      const { data } = await api.post("/app/modulistica/documents/generate", {
        slug,
        property_id: propertyId || null,
        client_id: clientId || null,
        context: {},
      });
      toast.success("PDF generato — white-label agenzia");
      setSelectedDoc(data);
      if (selectedTpl?.esign === "required" || selectedTpl?.esign === "recommended") {
        toast.message("Prossimo passo: invia in firma YouTrust", {
          description: ESIGN_LABEL[selectedTpl.esign],
        });
      }
      await load();
      setSelectedDoc(data);
    } catch (err) {
      toast.error(err?.response?.data?.detail || "Generazione fallita");
    } finally {
      setBusy(false);
    }
  };

  const download = async (id) => {
    try {
      const r = await api.get(`/app/modulistica/documents/${id}/download`, {
        responseType: "blob",
      });
      const url = URL.createObjectURL(r.data);
      const a = document.createElement("a");
      a.href = url;
      a.download = `modulistica_${id.slice(0, 8)}.pdf`;
      a.click();
      URL.revokeObjectURL(url);
    } catch {
      toast.error("Download non disponibile");
    }
  };

  const sendSign = async (id) => {
    const payload = [];
    for (const s of signers) {
      const first = (s.first_name || "").trim();
      const last = (s.last_name || "").trim();
      const email = (s.email || "").trim();
      if (!email || !first || !last) {
        toast.error(
          `Completa nome, cognome ed email per: ${ROLE_LABEL[s.role] || s.role}`,
        );
        return;
      }
      payload.push({
        name: `${first} ${last}`,
        first_name: first,
        last_name: last,
        email,
        role: s.role || "client",
      });
    }
    setBusy(true);
    try {
      const { data } = await api.post(`/app/modulistica/documents/${id}/send-sign`, {
        signers: payload,
      });
      toast.success(data.esign?.message || "Richiesta firma inviata");
      if (data.esign?.sign_url) {
        toast.message("Link firma YouTrust", { description: data.esign.sign_url });
      }
      setSelectedDoc((prev) =>
        prev?.id === id
          ? { ...prev, status: "sent", esign: data.esign }
          : prev,
      );
      await load();
    } catch (err) {
      toast.error(err?.response?.data?.detail || "Invio firma fallito");
    } finally {
      setBusy(false);
    }
  };

  const markSigned = async (id) => {
    setBusy(true);
    try {
      await api.post(`/app/modulistica/documents/${id}/mark-signed`);
      toast.success("Documento firmato");
      await load();
    } catch (err) {
      toast.error(err?.response?.data?.detail || "Operazione fallita");
    } finally {
      setBusy(false);
    }
  };

  const esignMode = selectedTpl?.esign || "optional";
  const showSignPanel = esignMode !== "none";
  const providerLabel =
    esign?.provider === "yousign"
      ? "YouTrust (Yousign)"
      : esign?.provider || "—";

  return (
    <AgencyShell current="modulistica">
      <section data-testid="modulistica-page" className="max-w-5xl space-y-8">
        <header className="space-y-2">
          <p className="text-[10px] uppercase tracking-[0.3em] text-emerald-800">OMNIA · Modulistica</p>
          <h1
            className="text-3xl md:text-4xl tracking-tight text-stone-900"
            style={{ fontFamily: "'Fraunces', Georgia, serif" }}
            data-testid="modulistica-title"
          >
            Modulistica white-label
          </h1>
          <p className="text-sm text-stone-600 max-w-2xl">
            Template italiani auto-compilati da CRM. Mandati, proposte e compliance si inviano in firma
            elettronica YouTrust (OTP email). Bozze operative — non parere legale.
          </p>
          {esign && (
            <p className="text-xs text-stone-500" data-testid="modulistica-esign-status">
              Firma: <span className="font-medium text-stone-800">{providerLabel}</span>
              {esign.ready ? " · pronto" : " · non pronto"} — {esign.note}
            </p>
          )}
        </header>

        {loading ? (
          <p className="text-sm text-stone-500">Caricamento…</p>
        ) : (
          <>
            <div className="flex flex-wrap gap-2" data-testid="modulistica-categories">
              {categories.map((c) => (
                <button
                  key={c}
                  type="button"
                  onClick={() => setCategory(c)}
                  className={`text-xs uppercase tracking-widest px-3 py-1.5 border transition ${
                    category === c
                      ? "bg-[#0B1E3F] text-stone-50 border-[#0B1E3F]"
                      : "border-stone-300 text-stone-600 hover:border-stone-500"
                  }`}
                >
                  {c === "all" ? "Tutti" : c}
                </button>
              ))}
            </div>

            <div className="grid md:grid-cols-2 gap-6">
              <div className="space-y-4 border border-stone-200 bg-white p-5" data-testid="modulistica-generate">
                <h2 className="text-sm uppercase tracking-widest text-stone-500">Genera documento</h2>
                <label className="block text-sm space-y-1">
                  <span className="text-stone-600">Template</span>
                  <select
                    data-testid="modulistica-slug"
                    className="w-full border border-stone-300 px-3 py-2 text-sm bg-white"
                    value={slug}
                    onChange={(e) => setSlug(e.target.value)}
                  >
                    {filtered.map((t) => (
                      <option key={t.slug} value={t.slug}>
                        {t.name}
                        {t.esign === "required" ? " · firma" : ""}
                      </option>
                    ))}
                  </select>
                </label>
                {selectedTpl && (
                  <div className="text-xs text-stone-500 space-y-1" data-testid="modulistica-template-meta">
                    <p>{selectedTpl.when_to_use}</p>
                    <p>
                      <span
                        className={
                          esignMode === "required"
                            ? "text-rose-700 font-medium"
                            : esignMode === "recommended"
                              ? "text-amber-800 font-medium"
                              : "text-stone-500"
                        }
                      >
                        {ESIGN_LABEL[esignMode] || esignMode}
                      </span>
                      {" · "}
                      Firmatari:{" "}
                      {(selectedTpl.signers || [])
                        .map((r) => ROLE_LABEL[r] || r)
                        .join(" + ")}
                    </p>
                  </div>
                )}
                <label className="block text-sm space-y-1">
                  <span className="text-stone-600">ID immobile (opzionale)</span>
                  <input
                    data-testid="modulistica-property-id"
                    className="w-full border border-stone-300 px-3 py-2 text-sm"
                    value={propertyId}
                    onChange={(e) => setPropertyId(e.target.value)}
                    placeholder="Codice immobile"
                  />
                </label>
                <label className="block text-sm space-y-1">
                  <span className="text-stone-600">ID cliente (opzionale)</span>
                  <input
                    data-testid="modulistica-client-id"
                    className="w-full border border-stone-300 px-3 py-2 text-sm"
                    value={clientId}
                    onChange={(e) => setClientId(e.target.value)}
                    placeholder="Codice cliente"
                  />
                </label>
                <button
                  type="button"
                  data-testid="modulistica-generate-btn"
                  disabled={busy || !slug}
                  onClick={generate}
                  className="w-full bg-[#1F6B5C] text-white text-sm uppercase tracking-widest py-3 disabled:opacity-50"
                >
                  {busy ? "Generazione…" : "Genera PDF"}
                </button>
                <p className="text-[11px] text-stone-400">
                  I campi vuoti restano come <code>[DA COMPILARE]</code>. Collega immobile/cliente per auto-fill.
                </p>
              </div>

              <div className="space-y-4 border border-stone-200 bg-white p-5" data-testid="modulistica-sign-panel">
                <h2 className="text-sm uppercase tracking-widest text-stone-500">Invia in firma</h2>
                {!showSignPanel ? (
                  <p className="text-xs text-stone-500" data-testid="modulistica-esign-none">
                    Questo template è una comunicazione PDF: non richiede firma elettronica.
                  </p>
                ) : (
                  <>
                    <p className="text-xs text-stone-500">
                      Provider: <strong>{providerLabel}</strong>. OTP via email (YouTrust).
                      Nessuna firma qualificata proprietaria (D-042).
                      {esignMode === "required" && (
                        <span className="block mt-1 text-rose-700">
                          Per mandati e proposte completa tutti i firmatari sotto.
                        </span>
                      )}
                    </p>
                    {signers.map((s, idx) => (
                      <div
                        key={`${s.role}-${idx}`}
                        className="space-y-2 border border-stone-100 p-3"
                        data-testid={`modulistica-signer-${idx}`}
                      >
                        <p className="text-[10px] uppercase tracking-widest text-stone-500">
                          {ROLE_LABEL[s.role] || s.role}
                        </p>
                        <div className="grid grid-cols-2 gap-2">
                          <label className="block text-sm space-y-1">
                            <span className="text-stone-600">Nome</span>
                            <input
                              data-testid={`modulistica-signer-first-${idx}`}
                              className="w-full border border-stone-300 px-3 py-2 text-sm"
                              value={s.first_name}
                              onChange={(e) => updateSigner(idx, "first_name", e.target.value)}
                            />
                          </label>
                          <label className="block text-sm space-y-1">
                            <span className="text-stone-600">Cognome</span>
                            <input
                              data-testid={`modulistica-signer-last-${idx}`}
                              className="w-full border border-stone-300 px-3 py-2 text-sm"
                              value={s.last_name}
                              onChange={(e) => updateSigner(idx, "last_name", e.target.value)}
                            />
                          </label>
                        </div>
                        <label className="block text-sm space-y-1">
                          <span className="text-stone-600">Email</span>
                          <input
                            data-testid={`modulistica-signer-email-${idx}`}
                            type="email"
                            className="w-full border border-stone-300 px-3 py-2 text-sm"
                            value={s.email}
                            onChange={(e) => updateSigner(idx, "email", e.target.value)}
                          />
                        </label>
                      </div>
                    ))}
                  </>
                )}
                {selectedDoc ? (
                  <div className="space-y-2 text-sm">
                    <p className="text-stone-700">
                      Selezionato: <strong>{selectedDoc.title}</strong>{" "}
                      <span className="text-stone-400">
                        ({STATUS_LABEL[selectedDoc.status] || selectedDoc.status})
                      </span>
                    </p>
                    <div className="flex flex-wrap gap-2">
                      <button
                        type="button"
                        data-testid="modulistica-download-selected"
                        className="border border-stone-300 px-3 py-2 text-xs uppercase tracking-widest"
                        onClick={() => download(selectedDoc.id)}
                      >
                        Scarica PDF
                      </button>
                      {showSignPanel && (
                        <button
                          type="button"
                          data-testid="modulistica-send-sign"
                          disabled={busy || !esign?.ready}
                          className="bg-[#0B1E3F] text-white px-3 py-2 text-xs uppercase tracking-widest disabled:opacity-50"
                          onClick={() => sendSign(selectedDoc.id)}
                        >
                          Invia firma
                        </button>
                      )}
                      {selectedDoc.status === "sent" && esign?.provider === "mock" && (
                        <button
                          type="button"
                          data-testid="modulistica-mark-signed"
                          disabled={busy}
                          className="border border-emerald-700 text-emerald-800 px-3 py-2 text-xs uppercase tracking-widest"
                          onClick={() => markSigned(selectedDoc.id)}
                        >
                          Segna firmato (mock)
                        </button>
                      )}
                    </div>
                  </div>
                ) : (
                  <p className="text-xs text-stone-400">Genera o seleziona un documento dall&apos;elenco.</p>
                )}
              </div>
            </div>

            <div className="space-y-3" data-testid="modulistica-docs-list">
              <h2 className="text-sm uppercase tracking-widest text-stone-500">Documenti recenti</h2>
              {docs.length === 0 ? (
                <p className="text-sm text-stone-500">Nessun documento ancora. Genera il primo template.</p>
              ) : (
                <ul className="divide-y divide-stone-200 border border-stone-200 bg-white">
                  {docs.map((d) => {
                    const tpl = templates.find((t) => t.slug === d.slug);
                    return (
                      <li
                        key={d.id}
                        className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 px-4 py-3"
                        data-testid={`modulistica-doc-${d.id}`}
                      >
                        <div>
                          <button
                            type="button"
                            className="text-left text-sm font-medium text-stone-900 hover:underline"
                            onClick={() => {
                              setSelectedDoc(d);
                              if (d.slug) setSlug(d.slug);
                            }}
                          >
                            {d.title}
                          </button>
                          <p className="text-xs text-stone-500">
                            {d.slug} · {STATUS_LABEL[d.status] || d.status}
                            {tpl?.esign ? ` · ${ESIGN_LABEL[tpl.esign] || tpl.esign}` : ""}
                            {d.esign?.provider ? ` · ${d.esign.provider}` : ""}
                            {d.property_id ? (
                              <>
                                {" · "}
                                <Link
                                  className="text-emerald-800 hover:underline"
                                  to={`/${lang}/app/properties/${d.property_id}/fascicolo`}
                                >
                                  Fascicolo
                                </Link>
                              </>
                            ) : null}
                          </p>
                        </div>
                        <button
                          type="button"
                          className="text-xs uppercase tracking-widest border border-stone-300 px-3 py-1.5 self-start"
                          onClick={() => download(d.id)}
                        >
                          PDF
                        </button>
                      </li>
                    );
                  })}
                </ul>
              )}
            </div>

            <div className="text-xs text-stone-500 space-y-1 border-t border-stone-200 pt-4">
              <p>
                Firma richiesta: mandato vendita/locazione, proposta acquisto. Consigliata: preliminare,
                privacy, AML. Solo PDF: lettera condòmini.
              </p>
              <p>
                Env: <code>ESIGN_PROVIDER=yousign</code> · YouTrust sandbox OTP email
              </p>
            </div>
          </>
        )}
      </section>
    </AgencyShell>
  );
}
