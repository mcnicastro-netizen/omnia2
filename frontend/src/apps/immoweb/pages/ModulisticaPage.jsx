/**
 * OMNIA — Modulistica CRM (M5.S7) + firma elettronica (M5.S8)
 * Libreria template, generazione PDF white-label, invio firma (Yousign/DocuSign/mock).
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
  const [signEmail, setSignEmail] = useState("");
  const [signFirstName, setSignFirstName] = useState("");
  const [signLastName, setSignLastName] = useState("");
  const [selectedDoc, setSelectedDoc] = useState(null);
  const [category, setCategory] = useState("all");

  const load = async () => {
    setLoading(true);
    try {
      const [t, d, e] = await Promise.all([
        api.get("/app/modulistica/templates"),
        api.get("/app/modulistica/documents", { params: { page_size: 50 } }),
        api.get("/app/modulistica/esign/status"),
      ]);
      setTemplates(t.data.items || []);
      setDocs(d.data.items || []);
      setEsign(e.data);
      if (!slug && t.data.items?.[0]) setSlug(t.data.items[0].slug);
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

  const filtered = useMemo(() => {
    if (category === "all") return templates;
    return templates.filter((t) => t.category === category);
  }, [templates, category]);

  const categories = useMemo(() => {
    const set = new Set(templates.map((t) => t.category));
    return ["all", ...Array.from(set)];
  }, [templates]);

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
      await load();
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
    if (!signEmail.trim()) {
      toast.error("Inserisci l'email del firmatario");
      return;
    }
    const first = signFirstName.trim();
    const last = signLastName.trim();
    if (!first || !last) {
      toast.error("Inserisci nome e cognome del firmatario");
      return;
    }
    setBusy(true);
    try {
      const { data } = await api.post(`/app/modulistica/documents/${id}/send-sign`, {
        signers: [
          {
            name: `${first} ${last}`,
            first_name: first,
            last_name: last,
            email: signEmail.trim(),
            role: "client",
          },
        ],
      });
      toast.success(data.esign?.message || "Richiesta firma inviata");
      if (data.esign?.sign_url) {
        toast.message("Link firma (mock/provider)", { description: data.esign.sign_url });
      }
      setSelectedDoc((prev) => (prev?.id === id ? { ...prev, ...data, status: "sent", esign: data.esign } : prev));
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
            Template italiani auto-compilati da CRM, PDF brandizzati con i colori dell&apos;agenzia,
            firma digitale via Yousign/DocuSign (mock in locale). Bozze operative — non parere legale.
          </p>
          {esign && (
            <p className="text-xs text-stone-500" data-testid="modulistica-esign-status">
              Firma: <span className="font-medium text-stone-800">{esign.provider}</span> — {esign.note}
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
                      </option>
                    ))}
                  </select>
                </label>
                {filtered.find((t) => t.slug === slug)?.when_to_use && (
                  <p className="text-xs text-stone-500">
                    {filtered.find((t) => t.slug === slug).when_to_use}
                  </p>
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
                <p className="text-xs text-stone-500">
                  Provider: <strong>{esign?.provider || "—"}</strong>. Nessuna firma qualificata proprietaria
                  (D-042): usiamo Yousign/DocuSign.
                </p>
                <label className="block text-sm space-y-1">
                  <span className="text-stone-600">Nome firmatario</span>
                  <input
                    data-testid="modulistica-signer-first"
                    className="w-full border border-stone-300 px-3 py-2 text-sm"
                    value={signFirstName}
                    onChange={(e) => setSignFirstName(e.target.value)}
                    placeholder="Marco"
                  />
                </label>
                <label className="block text-sm space-y-1">
                  <span className="text-stone-600">Cognome firmatario</span>
                  <input
                    data-testid="modulistica-signer-last"
                    className="w-full border border-stone-300 px-3 py-2 text-sm"
                    value={signLastName}
                    onChange={(e) => setSignLastName(e.target.value)}
                    placeholder="Nicastro"
                  />
                </label>
                <label className="block text-sm space-y-1">
                  <span className="text-stone-600">Email firmatario</span>
                  <input
                    data-testid="modulistica-signer-email"
                    type="email"
                    className="w-full border border-stone-300 px-3 py-2 text-sm"
                    value={signEmail}
                    onChange={(e) => setSignEmail(e.target.value)}
                  />
                </label>
                {selectedDoc ? (
                  <div className="space-y-2 text-sm">
                    <p className="text-stone-700">
                      Selezionato: <strong>{selectedDoc.title}</strong>{" "}
                      <span className="text-stone-400">({STATUS_LABEL[selectedDoc.status] || selectedDoc.status})</span>
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
                      <button
                        type="button"
                        data-testid="modulistica-send-sign"
                        disabled={busy}
                        className="bg-[#0B1E3F] text-white px-3 py-2 text-xs uppercase tracking-widest disabled:opacity-50"
                        onClick={() => sendSign(selectedDoc.id)}
                      >
                        Invia firma
                      </button>
                      {selectedDoc.status === "sent" && (
                        <button
                          type="button"
                          data-testid="modulistica-mark-signed"
                          disabled={busy}
                          className="border border-emerald-700 text-emerald-800 px-3 py-2 text-xs uppercase tracking-widest"
                          onClick={() => markSigned(selectedDoc.id)}
                        >
                          Segna firmato
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
                  {docs.map((d) => (
                    <li
                      key={d.id}
                      className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 px-4 py-3"
                      data-testid={`modulistica-doc-${d.id}`}
                    >
                      <div>
                        <button
                          type="button"
                          className="text-left text-sm font-medium text-stone-900 hover:underline"
                          onClick={() => setSelectedDoc(d)}
                        >
                          {d.title}
                        </button>
                        <p className="text-xs text-stone-500">
                          {d.slug} · {STATUS_LABEL[d.status] || d.status}
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
                  ))}
                </ul>
              )}
            </div>

            <div className="text-xs text-stone-500 space-y-1 border-t border-stone-200 pt-4">
              <p>API white-label: <code>GET /api/v1/modulistica/templates</code> · <code>POST /api/v1/modulistica/render</code> (2 crediti)</p>
              <p>Env firma: <code>ESIGN_PROVIDER=mock|yousign|docusign</code></p>
            </div>
          </>
        )}
      </section>
    </AgencyShell>
  );
}
