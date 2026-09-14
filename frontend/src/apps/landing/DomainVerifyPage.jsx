import React, { useState } from "react";
import { useTranslation } from "react-i18next";
import { Link } from "react-router-dom";
import Brand from "@/shared/components/Brand";

const BACKEND = process.env.REACT_APP_BACKEND_URL;

/**
 * M2.5.4b — Domain Ownership Checker (D-054).
 *
 * Public landing page at /:lang/verifica-dominio. Lead magnet for the
 * "Domain Sovereignty Kit" strategy (D-051). Zero authentication required.
 *
 * WHITE LABEL note: this same feature is also exposed as
 *   - `/api/v1/domain/check` (billed API, partner web agencies)
 *   - `/api/widgets/v1/domain-check.html` (embeddable iframe with data-key)
 *
 * NO PAPER note: every action leads to a digital delivery (email + PDF
 * download). No physical mail, no in-person signatures required.
 */
export default function DomainVerifyPage() {
  const { i18n } = useTranslation();
  const lang = i18n.language?.slice(0, 2) || "it";

  const [domain, setDomain] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [result, setResult] = useState(null);

  const check = async (e) => {
    e?.preventDefault();
    if (!domain.trim()) return;
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const r = await fetch(`${BACKEND}/api/domain/check`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ domain: domain.trim() }),
      });
      const data = await r.json();
      if (!r.ok) throw new Error(data?.detail || `HTTP ${r.status}`);
      setResult(data);
    } catch (err) {
      setError(err?.message || "Errore inatteso");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-stone-50 text-stone-900" data-testid="domain-verify-page">
      {/* Top bar */}
      <header className="border-b border-stone-200 bg-white/70 backdrop-blur">
        <div className="max-w-6xl mx-auto px-6 py-4 flex items-center justify-between">
          <Link to={`/${lang}`} className="text-lg" style={{ fontFamily: "'Fraunces', Georgia, serif" }}>
            <Brand />
          </Link>
          <nav className="text-xs uppercase tracking-widest text-stone-500 flex gap-5">
            <Link to={`/${lang}/agenzie`} className="hover:text-stone-900">Per Agenzie</Link>
            <Link to={`/${lang}/cloud`} className="hover:text-stone-900">ImmobilCloud</Link>
            <Link to={`/${lang}/login`} className="hover:text-stone-900">Accedi</Link>
          </nav>
        </div>
      </header>

      {/* Hero */}
      <section className="max-w-4xl mx-auto px-6 pt-16 pb-8">
        <p className="text-[10px] uppercase tracking-[0.3em] text-emerald-700 mb-3" data-testid="verify-eyebrow">
          Domain Sovereignty Kit · Gratuito
        </p>
        <h1 className="text-4xl sm:text-5xl lg:text-6xl leading-[1.05] tracking-tight" style={{ fontFamily: "'Fraunces', Georgia, serif" }}>
          Il dominio della tua agenzia<br />è veramente tuo?
        </h1>
        <p className="text-base sm:text-lg text-stone-600 mt-6 max-w-2xl leading-relaxed">
          La maggior parte delle agenzie immobiliari italiane non è proprietaria del proprio dominio web:
          è intestato al fornitore del gestionale. Se un giorno decidi di cambiare software, il dominio resta lì.
          <strong className="text-stone-900"> Scoprilo in 5 secondi, gratis.</strong>
        </p>

        {/* Check form */}
        <form onSubmit={check} className="mt-10 flex flex-col sm:flex-row gap-3 max-w-2xl">
          <input
            type="text"
            data-testid="verify-domain-input"
            value={domain}
            onChange={(e) => setDomain(e.target.value)}
            placeholder="es. agenziarossi.it"
            className="flex-1 px-5 py-4 text-lg border border-stone-300 rounded-lg bg-white focus:border-emerald-700 focus:outline-none"
            required
            autoComplete="off"
            spellCheck="false"
          />
          <button
            type="submit"
            data-testid="verify-domain-submit"
            disabled={loading || !domain.trim()}
            className="px-8 py-4 bg-emerald-700 text-white text-xs uppercase tracking-widest rounded-lg hover:bg-emerald-800 disabled:opacity-40 disabled:cursor-not-allowed"
          >
            {loading ? "…" : "Verifica ora"}
          </button>
        </form>
        <p className="text-xs text-stone-500 mt-2 max-w-2xl">
          🔒 Nessuna registrazione. Nessun dato personale richiesto per il check. Query RDAP pubblica sul registro ufficiale.
        </p>

        {error && (
          <div className="mt-6 text-sm text-red-800 bg-red-50 border border-red-300 rounded-lg p-4 max-w-2xl" data-testid="verify-error">
            {error}
          </div>
        )}
      </section>

      {result && <VerdictBlock data={result} lang={lang} />}

      {/* How it works */}
      <section className="max-w-4xl mx-auto px-6 py-16 border-t border-stone-200 mt-16">
        <h2 className="text-2xl sm:text-3xl mb-8" style={{ fontFamily: "'Fraunces', Georgia, serif" }}>
          Perché è importante saperlo
        </h2>
        <div className="grid md:grid-cols-3 gap-8">
          <Card num="01" title="Il tuo brand vale il dominio" body="Anni di annunci, SEO, biglietti da visita e vetrine puntano al tuo dominio. Se non è a tuo nome, se lo cambi lo perdi." />
          <Card num="02" title="Il lock-in è strutturale" body="Molti gestionali immobiliari registrano il dominio a proprio nome. Non è cattiva volontà: è un modello che vincola tacitamente." />
          <Card num="03" title="OMNIA non tocca il tuo dominio" body="Nel nostro onboarding NON registriamo mai un dominio a nome nostro. Domain Vault: tu resti proprietario, sempre." />
        </div>
      </section>

      {/* Footer CTA */}
      <section className="bg-stone-900 text-white">
        <div className="max-w-4xl mx-auto px-6 py-16 text-center">
          <h2 className="text-3xl sm:text-4xl" style={{ fontFamily: "'Fraunces', Georgia, serif" }}>
            Vuoi vedere OMNIA in azione?
          </h2>
          <p className="text-stone-300 mt-4 mb-8 max-w-2xl mx-auto">
            Gestionale + CRM + valutatore + portale B2C, tutto in un unico ecosistema. Nessun setup fee, nessun lock-in, nessun dominio a nome nostro.
          </p>
          <Link
            to={`/${lang}/agenzie`}
            data-testid="verify-cta-agenzie"
            className="inline-block px-8 py-4 bg-emerald-500 text-stone-900 text-xs uppercase tracking-widest rounded-lg hover:bg-emerald-400 font-medium"
          >
            Scopri OMNIA per Agenzie →
          </Link>
        </div>
      </section>

      <footer className="border-t border-stone-200 py-6 text-center text-xs text-stone-500">
        © {new Date().getFullYear()} OMNIA Real Estate Ecosystem — Il primo ecosistema immobiliare italiano che rispetta la tua sovranità digitale.
      </footer>
    </div>
  );
}

function Card({ num, title, body }) {
  return (
    <div className="border-l-2 border-emerald-600 pl-5">
      <p className="text-[10px] uppercase tracking-widest text-emerald-700 mb-2">{num}</p>
      <h3 className="text-lg mb-2" style={{ fontFamily: "'Fraunces', Georgia, serif" }}>{title}</h3>
      <p className="text-sm text-stone-600 leading-relaxed">{body}</p>
    </div>
  );
}

/* ================= Verdict block + Lead capture ================= */

function VerdictBlock({ data, lang }) {
  const v = data.verdict || {};
  const r = data.rdap || {};

  const sevStyle = {
    good:      { bg: "bg-emerald-50",  border: "border-emerald-300", text: "text-emerald-900",  badge: "bg-emerald-600" },
    warning:   { bg: "bg-amber-50",    border: "border-amber-300",   text: "text-amber-900",    badge: "bg-amber-600" },
    critical:  { bg: "bg-red-50",      border: "border-red-300",     text: "text-red-900",      badge: "bg-red-600" },
    info:      { bg: "bg-sky-50",      border: "border-sky-300",     text: "text-sky-900",      badge: "bg-sky-600" },
  }[v.severity || "info"];

  const dateFmt = (iso) => {
    if (!iso) return "—";
    try { return new Date(iso).toLocaleDateString("it-IT"); } catch { return iso; }
  };

  const showLead = v.severity === "critical" || v.severity === "warning" || v.status === "not_registered";

  return (
    <section className="max-w-4xl mx-auto px-6 pb-8">
      <div className={`border rounded-2xl p-8 ${sevStyle.bg} ${sevStyle.border}`} data-testid="verify-verdict">
        <span
          className={`inline-block px-3 py-1 rounded-full text-[10px] uppercase tracking-widest text-white font-medium mb-4 ${sevStyle.badge}`}
          data-testid="verify-verdict-status"
        >
          {(v.status || "").replace(/_/g, " ")}
        </span>
        <h2 className={`text-2xl sm:text-3xl mb-4 ${sevStyle.text}`} style={{ fontFamily: "'Fraunces', Georgia, serif" }} data-testid="verify-verdict-headline">
          {v.headline}
        </h2>
        <p className={`text-base leading-relaxed mb-6 ${sevStyle.text}`} data-testid="verify-verdict-explanation">
          {v.explanation}
        </p>

        <div className="bg-white border border-stone-200 rounded-lg p-5 grid md:grid-cols-2 gap-3 text-sm" data-testid="verify-verdict-details">
          <DetailRow label="Dominio" value={data.domain} />
          <DetailRow label="Registrante ufficiale" value={r.registrant || "Nascosto (privacy)"} strong />
          <DetailRow label="Registrar" value={r.registrar || "—"} />
          <DetailRow label="Registrato il" value={dateFmt(r.created_at)} />
          <DetailRow label="Scade il" value={dateFmt(r.expires_at)} />
          <DetailRow label="Ultima modifica" value={dateFmt(r.last_changed)} />
          {r.nameservers?.length > 0 && (
            <div className="md:col-span-2">
              <p className="text-[10px] uppercase tracking-widest text-stone-500 mb-1">Name servers</p>
              <p className="text-xs font-mono text-stone-700 break-all">{r.nameservers.join(" · ")}</p>
            </div>
          )}
        </div>
      </div>

      {showLead && <LegalKitBlock domain={data.domain} />}
      {showLead && <LeadForm checkId={data.id} lang={lang} />}
    </section>
  );
}

function LegalKitBlock({ domain }) {
  const [downloading, setDownloading] = useState(false);
  const [downloaded, setDownloaded] = useState(false);
  const [err, setErr] = useState(null);
  // Optional context — pre-fill domain from the check just done
  const [agencyName, setAgencyName] = useState("");
  const [signerName, setSignerName] = useState("");
  const [agencyPec, setAgencyPec] = useState("");
  const [consent, setConsent] = useState(false);
  const [email, setEmail] = useState("");

  const download = async () => {
    if (!consent) { setErr("Devi accettare il trattamento dati per proseguire."); return; }
    if (!email.trim()) { setErr("Email obbligatoria per ricevere il kit."); return; }
    setErr(null); setDownloading(true);
    try {
      const r = await fetch(`${BACKEND}/api/legal/kit`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          email: email.trim(),
          name: signerName.trim() || "—",
          agency: agencyName.trim() || null,
          consent: true,
          source: "landing_verifica_dominio",
          context: {
            signer_name: signerName.trim() || undefined,
            agency_name: agencyName.trim() || undefined,
            agency_pec: agencyPec.trim() || undefined,
            domain,
          },
        }),
      });
      if (!r.ok) {
        const errData = await r.json().catch(() => ({}));
        throw new Error(errData?.detail || `HTTP ${r.status}`);
      }
      // r is a ZIP blob — trigger download
      const blob = await r.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = "omnia_legal_kit.zip";
      document.body.appendChild(a);
      a.click();
      a.remove();
      URL.revokeObjectURL(url);
      setDownloaded(true);
    } catch (e) {
      setErr(e?.message || "Errore durante il download");
    } finally { setDownloading(false); }
  };

  if (downloaded) {
    return (
      <div className="mt-6 bg-emerald-50 border border-emerald-300 rounded-lg p-5 text-emerald-900" data-testid="legal-kit-success">
        <p className="font-medium mb-1">✅ Kit Legale scaricato con successo</p>
        <p className="text-sm">Trovi 4 template PDF pronti da inviare via PEC — GDPR art. 20, Titolarità dominio, Disdetta fornitore, Reclamo CNR-IIT. Nessun invio cartaceo necessario. Compila i placeholder <strong>[DA COMPILARE]</strong> con i tuoi dati e sei a posto.</p>
      </div>
    );
  }

  return (
    <div className="mt-6 bg-amber-50 border border-amber-300 rounded-lg p-6" data-testid="legal-kit-block">
      <div className="flex items-start gap-4 mb-4">
        <div className="w-10 h-10 rounded-lg bg-amber-500 text-white flex items-center justify-center text-xl shrink-0">📥</div>
        <div>
          <h3 className="text-lg font-medium mb-1" style={{ fontFamily: "'Fraunces', Georgia, serif" }}>
            Scarica subito il Legal Kit gratuito (PDF)
          </h3>
          <p className="text-sm text-amber-900 leading-relaxed">
            <strong>4 template PDF pronti</strong> per riprendere il controllo del tuo dominio e dei tuoi dati.
            100% digitale — invio via PEC, mai cartaceo. Compili i placeholder e sei a posto.
          </p>
        </div>
      </div>

      <ul className="text-xs text-amber-900 mb-5 space-y-1 pl-4">
        <li>1️⃣ Richiesta portabilità dati (GDPR art. 20)</li>
        <li>2️⃣ Richiesta titolarità dominio al registrar</li>
        <li>3️⃣ Disdetta contratto fornitore</li>
        <li>4️⃣ Reclamo / info Registro .it (CNR-IIT)</li>
      </ul>

      <div className="grid md:grid-cols-2 gap-3 mb-3">
        <input type="email" data-testid="kit-email" value={email} onChange={(e) => setEmail(e.target.value)} placeholder="Email (obbligatoria)" maxLength={200} className="px-3 py-2 border border-amber-300 rounded text-sm bg-white" />
        <input type="text" data-testid="kit-agency" value={agencyName} onChange={(e) => setAgencyName(e.target.value)} placeholder="Nome agenzia (opz.)" maxLength={200} className="px-3 py-2 border border-amber-300 rounded text-sm bg-white" />
        <input type="text" data-testid="kit-signer" value={signerName} onChange={(e) => setSignerName(e.target.value)} placeholder="Nome legale rappresentante (opz.)" maxLength={200} className="px-3 py-2 border border-amber-300 rounded text-sm bg-white" />
        <input type="email" data-testid="kit-pec" value={agencyPec} onChange={(e) => setAgencyPec(e.target.value)} placeholder="PEC agenzia (opz.)" maxLength={200} className="px-3 py-2 border border-amber-300 rounded text-sm bg-white" />
      </div>
      <label className="flex items-start gap-2 text-xs text-amber-900 mb-3">
        <input type="checkbox" data-testid="kit-consent" checked={consent} onChange={(e) => setConsent(e.target.checked)} className="mt-0.5" />
        <span>Acconsento al trattamento dei dati per ricevere il kit e comunicazioni OMNIA (revoca in qualsiasi momento via email). GDPR 2016/679.</span>
      </label>

      {err && <p className="text-sm text-red-700 mb-3" data-testid="kit-error">{err}</p>}

      <div className="flex flex-wrap gap-3 items-center">
        <button
          onClick={download}
          disabled={downloading || !email.trim() || !consent}
          data-testid="kit-download-btn"
          className="px-6 py-3 bg-amber-600 text-white text-xs uppercase tracking-widest rounded-lg hover:bg-amber-700 disabled:opacity-40 disabled:cursor-not-allowed"
        >
          {downloading ? "Genero PDF…" : "📥 Scarica il Legal Kit (ZIP)"}
        </button>
        <span className="text-xs text-amber-900">
          Nessun invio cartaceo. Delivery digitale al 100%.
        </span>
      </div>
    </div>
  );
}

function DetailRow({ label, value, strong }) {
  return (
    <div className="flex justify-between gap-3">
      <span className="text-[10px] uppercase tracking-widest text-stone-500">{label}</span>
      <span className={`text-right ${strong ? "font-medium text-stone-900" : "text-stone-700"}`}>{value}</span>
    </div>
  );
}

function LeadForm({ checkId }) {
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [agency, setAgency] = useState("");
  const [consent, setConsent] = useState(false);
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState(null);
  const [err, setErr] = useState(null);

  const submit = async (e) => {
    e.preventDefault();
    setErr(null); setMsg(null);
    if (!name.trim() || !email.trim() || !consent) {
      setErr("Nome, email e consenso obbligatori.");
      return;
    }
    setBusy(true);
    try {
      const r = await fetch(`${BACKEND}/api/domain/lead`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          check_id: checkId, name: name.trim(), email: email.trim(),
          agency: agency.trim() || null, consent: true, source: "landing",
        }),
      });
      const data = await r.json();
      if (!r.ok) throw new Error(data?.detail || `HTTP ${r.status}`);
      setMsg(data.message || "Richiesta ricevuta.");
      setName(""); setEmail(""); setAgency(""); setConsent(false);
    } catch (e) {
      setErr(e?.message || "Errore invio");
    } finally { setBusy(false); }
  };

  if (msg) {
    return (
      <div className="mt-6 bg-emerald-50 border border-emerald-300 rounded-lg p-5 text-emerald-900" data-testid="verify-lead-success">
        <p className="font-medium mb-1">✅ {msg}</p>
        <p className="text-sm">Ti scriviamo entro 24 ore con il kit legale digitale (PEC + template GDPR + istruzioni passo-passo). Tutto via email, nessun invio cartaceo.</p>
      </div>
    );
  }

  return (
    <form onSubmit={submit} className="mt-6 bg-white border border-stone-200 rounded-lg p-6" data-testid="verify-lead-form">
      <h3 className="text-lg mb-1" style={{ fontFamily: "'Fraunces', Georgia, serif" }}>Vuoi il kit legale gratuito?</h3>
      <p className="text-sm text-stone-600 mb-5">
        Ti mandiamo via email i template legali (disdetta, PEC titolarità, richiesta GDPR art. 20) — <strong>tutto digitale, zero carta</strong> — e ti richiamiamo entro 24h.
      </p>
      <div className="grid md:grid-cols-2 gap-3 mb-3">
        <input type="text" data-testid="verify-lead-name" value={name} onChange={(e) => setName(e.target.value)} placeholder="Nome e cognome" maxLength={120} required className="px-4 py-3 border border-stone-300 rounded-lg text-sm" />
        <input type="email" data-testid="verify-lead-email" value={email} onChange={(e) => setEmail(e.target.value)} placeholder="Email" maxLength={200} required className="px-4 py-3 border border-stone-300 rounded-lg text-sm" />
        <input type="text" data-testid="verify-lead-agency" value={agency} onChange={(e) => setAgency(e.target.value)} placeholder="Nome agenzia (opz.)" maxLength={200} className="px-4 py-3 border border-stone-300 rounded-lg text-sm md:col-span-2" />
      </div>
      <label className="flex items-start gap-2 text-xs text-stone-600 mb-4">
        <input type="checkbox" data-testid="verify-lead-consent" checked={consent} onChange={(e) => setConsent(e.target.checked)} className="mt-0.5" />
        <span>Acconsento al trattamento dei dati per ricevere il kit legale e comunicazioni OMNIA (revoca in qualsiasi momento via email). GDPR 2016/679.</span>
      </label>
      {err && <p className="text-sm text-red-700 mb-3" data-testid="verify-lead-error">{err}</p>}
      <button type="submit" disabled={busy} data-testid="verify-lead-submit" className="px-6 py-3 bg-stone-900 text-white text-xs uppercase tracking-widest rounded-lg hover:bg-stone-700 disabled:opacity-40">
        {busy ? "…" : "Voglio il kit legale gratuito"}
      </button>
    </form>
  );
}
