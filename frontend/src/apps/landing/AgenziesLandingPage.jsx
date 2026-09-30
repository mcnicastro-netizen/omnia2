import React, { useEffect, useState } from "react";
import axios from "axios";
import { useTranslation } from "react-i18next";
import { Link } from "react-router-dom";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api/founders`;

const HERO_IMG =
  "https://images.unsplash.com/photo-1551836022-deb4988cc6c0?w=1600&q=80&auto=format&fit=crop";

// D-109 — prezzi da GET /billing/plans (SoT); niente listino morto in FE
const BILLING_API = `${BACKEND_URL}/api/billing/plans`;

const PLAN_FEATURES = {
  starter: [
    "HAL Chatbot AI + Lead Scoring",
    "HAL Legal anti-hallucination",
    "Valutatore Pro UNI 10750",
    "Multiposting incluso",
    "Supporto email",
  ],
  pro: [
    "Tutto di Starter +",
    "HAL Improve copywriter inline",
    "White-label con tuo dominio",
    "Multiposting avanzato",
    "Supporto prioritario",
  ],
  agency: [
    "Tutto di Pro +",
    "White-label + custom",
    "Multiposting tutti i portali",
    "Limiti immobili/agenti illimitati",
    "Supporto dedicato",
  ],
};

const WOW_MOMENTS = [
  {
    icon: "🎯",
    title: "AI Lead Scoring",
    text:
      "Ogni lead che entra nel CRM viene analizzato dall'AI e ricevi un punteggio 0–100 di probabilità di chiusura. Niente più tempo perso su contatti freddi.",
  },
  {
    icon: "⚖️",
    title: "HAL Legal",
    text:
      "Chatbot specializzato in diritto immobiliare italiano. Cita Normattiva, Cassazione, Agenzia Entrate. Zero allucinazioni grazie al validator anti-hallucination.",
  },
  {
    icon: "📐",
    title: "Valutatore Pro UNI 10750",
    text:
      "Stima bank-grade per tutto il territorio nazionale. Coefficienti di merito + UNI 10750 + dati ISTAT province. Bastano 3 click.",
  },
];

export default function AgenziesLandingPage() {
  const { t, i18n } = useTranslation();
  const lang = (i18n.language || "it").slice(0, 2);

  const [spots, setSpots] = useState({ remaining: 50, total: 50, registered: 0 });
  const [plans, setPlans] = useState([]);
  const [plansError, setPlansError] = useState(null);
  const [formData, setFormData] = useState({
    email: "",
    name: "",
    agency: "",
    city: "",
    address: "",
    street_number: "",
    has_website: "",
    website_url: "",
    tier_interest: "",
    notes: "",
  });
  const [submitting, setSubmitting] = useState(false);
  const [result, setResult] = useState(null);
  const [errorMsg, setErrorMsg] = useState(null);

  useEffect(() => {
    axios
      .get(`${API}/spots`)
      .then((r) => setSpots(r.data))
      .catch(() => {});
    axios
      .get(BILLING_API)
      .then((r) => {
        const list = (r.data?.plans || []).map((p) => ({
          id: p.tier,
          name: p.name,
          foundersPrice: p.price_monthly,
          // D-079 — annuale = 11× mensile (−1 mese)
          yearlyPrice: p.price_yearly ?? Math.round(p.price_monthly * 11),
          standardPrice: null,
          users: p.max_agents === -1 ? "illimitati" : p.max_agents,
          credits: p.credits_included_monthly,
          listings: p.max_properties === -1 ? "illimitati" : p.max_properties,
          highlight: p.tier === "pro",
          features: PLAN_FEATURES[p.tier] || [],
        }));
        setPlans(list);
        setPlansError(null);
      })
      .catch(() => {
        setPlans([]);
        setPlansError("Prezzi temporaneamente non disponibili");
      });
  }, []);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((f) => ({ ...f, [name]: value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    setErrorMsg(null);
    try {
      if (!formData.has_website) {
        setErrorMsg("Indica se hai già un sito web.");
        setSubmitting(false);
        return;
      }
      if (formData.has_website === "yes" && !(formData.website_url || "").trim()) {
        setErrorMsg("Inserisci l'URL del sito web per personalizzare la demo.");
        setSubmitting(false);
        return;
      }
      const payload = {
        ...formData,
        agents_count: 1,
        has_website: formData.has_website,
        website_url: formData.has_website === "yes" ? (formData.website_url || "").trim() : null,
        tier_interest: formData.tier_interest || null,
        notes: formData.notes || null,
      };
      const r = await axios.post(`${API}/register`, payload);
      setResult(r.data);
      setSpots((s) => ({ ...s, remaining: r.data.remaining, registered: r.data.position }));
    } catch (err) {
      const detail = err?.response?.data?.detail || "Errore di rete. Riprova.";
      setErrorMsg(detail);
    } finally {
      setSubmitting(false);
    }
  };

  const isFull = spots.remaining <= 0;

  return (
    <div className="min-h-screen bg-[#fbf9f5] text-stone-900" data-testid="agenzie-landing">
      {/* Top nav — Chi siamo / Prodotti / Prezzi */}
      <header className="absolute top-0 left-0 right-0 z-10 px-6 sm:px-12 py-5">
        <div className="flex flex-wrap items-center justify-between gap-4 max-w-screen-2xl mx-auto">
          <Link
            to={`/${lang}`}
            className="text-xl md:text-2xl tracking-tight font-medium text-white"
            style={{ fontFamily: "'Fraunces', Georgia, serif" }}
            data-testid="agenzie-logo"
          >
            OMNIA<sup className="text-[10px] text-white/60 ml-0.5">™</sup>
          </Link>
          <nav
            className="flex flex-wrap items-center gap-4 sm:gap-6 text-[11px] uppercase tracking-widest text-white/80"
            data-testid="agenzie-top-nav"
            aria-label="Sezioni landing"
          >
            <a href="#chi-siamo" className="hover:text-white transition">Chi siamo</a>
            <a href="#prodotti" className="hover:text-white transition">Prodotti</a>
            <a href="#prezzi" className="hover:text-white transition">Prezzi</a>
            <a
              href="#founders-form"
              className="text-white border border-white/40 px-4 py-2 hover:bg-white hover:text-stone-900 transition"
              data-testid="agenzie-cta-top"
            >
              Richiedi demo
            </a>
          </nav>
        </div>
      </header>

      {/* Hero */}
      <section className="relative min-h-[600px] flex items-center justify-center text-center px-6"
        style={{
          backgroundImage: `linear-gradient(rgba(11, 30, 63, 0.7), rgba(11, 30, 63, 0.85)), url(${HERO_IMG})`,
          backgroundSize: "cover",
          backgroundPosition: "center",
        }}
      >
        <div className="max-w-4xl mx-auto py-32">
          <p className="text-xs sm:text-sm uppercase tracking-[0.3em] text-[#C19A6B] mb-6"
            data-testid="agenzie-hero-overline">
            Founders 50 — Programma esclusivo
          </p>
          <h1 className="text-4xl sm:text-5xl lg:text-6xl text-white leading-tight font-light"
            style={{ fontFamily: "'Fraunces', Georgia, serif" }}
            data-testid="agenzie-hero-title">
            50 strumenti AI per la tua agenzia.<br/>
            <span className="text-[#C19A6B]">6 mesi di vantaggio</span> per i primi 50.
          </h1>
          <p className="text-base sm:text-lg text-white/80 mt-8 max-w-2xl mx-auto leading-relaxed"
            data-testid="agenzie-hero-sub">
            ImmobilCloud (portale B2C) · ImmoWeb (gestionale AI) · Omnia Academy.
            Priorità di oggi, match spiegati, HAL che propone e tu confermi.
            Un ecosistema — nord: sistema operativo dell&apos;agenzia. White-label. Prezzo bloccato 24 mesi.
          </p>

          {/* Spots counter */}
          <div className="inline-block mt-12 px-8 py-4 border border-[#C19A6B]/40 backdrop-blur-sm"
            data-testid="agenzie-spots-counter">
            <p className="text-[10px] uppercase tracking-widest text-white/60 mb-1">Posti rimanenti</p>
            <p className="text-4xl text-[#C19A6B] font-light"
              style={{ fontFamily: "'Fraunces', Georgia, serif" }}>
              {spots.remaining} <span className="text-white/40 text-xl">/ {spots.total}</span>
            </p>
          </div>

          <div className="mt-10">
            <a href="#founders-form"
              className="inline-block bg-[#C19A6B] text-white px-10 py-4 text-sm uppercase tracking-widest hover:bg-[#a8845a] transition"
              data-testid="agenzie-hero-cta">
              Prenota il tuo posto →
            </a>
          </div>
        </div>
      </section>

      {/* Chi siamo */}
      <section id="chi-siamo" className="px-6 sm:px-12 py-20 max-w-3xl mx-auto text-center" data-testid="agenzie-chi-siamo">
        <p className="text-xs uppercase tracking-[0.3em] text-stone-500 mb-3">Chi siamo</p>
        <h2 className="text-3xl sm:text-4xl text-stone-900 mb-6 font-light"
          style={{ fontFamily: "'Fraunces', Georgia, serif" }}>
          OMNIA — sistema operativo dell&apos;agenzia
        </h2>
        <p className="text-stone-600 text-sm sm:text-base leading-relaxed">
          Uniamo gestionale AI, portale B2C e Academy in un unico ecosistema white-label.
          HAL ti assiste nel quotidiano; tu resti al comando. Nati per agenzie italiane che
          vogliono lavorare meglio — non per accumulare software inutili.
        </p>
      </section>

      {/* Prodotti */}
      <section id="prodotti" className="px-6 sm:px-12 py-24 max-w-6xl mx-auto">
        <p className="text-xs uppercase tracking-[0.3em] text-stone-500 mb-3 text-center">Prodotti</p>
        <h2 className="text-3xl sm:text-4xl text-stone-900 text-center mb-16 font-light"
          style={{ fontFamily: "'Fraunces', Georgia, serif" }}>
          3 strumenti AI che cambiano la giornata di un agente
        </h2>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-8" data-testid="agenzie-wow-grid">
          {WOW_MOMENTS.map((w, i) => (
            <div key={i} className="bg-white p-8 border border-stone-200 hover:border-[#C19A6B] transition"
              data-testid={`agenzie-wow-${i + 1}`}>
              <div className="text-4xl mb-4">{w.icon}</div>
              <h3 className="text-xl text-stone-900 mb-3 font-medium"
                style={{ fontFamily: "'Fraunces', Georgia, serif" }}>{w.title}</h3>
              <p className="text-sm text-stone-600 leading-relaxed">{w.text}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Pricing */}
      <section id="prezzi" className="bg-stone-50 px-6 sm:px-12 py-24 border-y border-stone-200">
        <div className="max-w-6xl mx-auto">
          <p className="text-xs uppercase tracking-[0.3em] text-stone-500 mb-3 text-center">Listino corrente</p>
          <h2 className="text-3xl sm:text-4xl text-stone-900 text-center mb-4 font-light"
            style={{ fontFamily: "'Fraunces', Georgia, serif" }}>
            Piani agenzia
          </h2>
          <p className="text-center text-stone-600 mb-16 text-sm">
            Mensile o annuale (11 mesi — 1 mese incluso) · attivazione assistita fino a gate O6
          </p>

          {plansError ? (
            <p className="text-center text-sm text-stone-500 mb-8" data-testid="agenzie-pricing-unavailable">{plansError}</p>
          ) : null}

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {plans.map((p) => (
              <div key={p.id}
                className={`bg-white p-8 border ${p.highlight ? "border-[#C19A6B] shadow-lg relative" : "border-stone-200"}`}
                data-testid={`agenzie-tier-${p.id}`}>
                {p.highlight && (
                  <div className="absolute -top-3 left-1/2 -translate-x-1/2 bg-[#C19A6B] text-white text-[10px] uppercase tracking-widest px-3 py-1">
                    Più scelto
                  </div>
                )}
                <h3 className="text-2xl text-stone-900 font-medium mb-2"
                  style={{ fontFamily: "'Fraunces', Georgia, serif" }}>{p.name}</h3>
                <div className="mt-4 mb-6">
                  <p className="text-4xl text-stone-900 font-light"
                    style={{ fontFamily: "'Fraunces', Georgia, serif" }}>
                    €{p.foundersPrice}<span className="text-sm text-stone-500 ml-1">/mese</span>
                  </p>
                  <p className="text-sm text-stone-600 mt-2" data-testid={`agenzie-tier-yearly-${p.id}`}>
                    oppure <strong>€{p.yearlyPrice}</strong>/anno
                    <span className="text-stone-500"> (equivalente 11 mesi)</span>
                  </p>
                  {p.standardPrice ? (
                    <p className="text-xs text-stone-400 line-through mt-1">€{p.standardPrice}/mese standard</p>
                  ) : null}
                </div>
                <ul className="text-sm space-y-2 mb-6 text-stone-700">
                  <li><strong>{p.users}</strong> agenti</li>
                  <li><strong>{p.credits}</strong> crediti/mese</li>
                  <li><strong>{p.listings}</strong> immobili</li>
                </ul>
                <ul className="text-xs space-y-2 text-stone-600 border-t border-stone-200 pt-4">
                  {p.features.map((f, i) => (
                    <li key={i}>✓ {f}</li>
                  ))}
                </ul>
              </div>
            ))}
          </div>

          <p className="text-center text-xs text-stone-500 mt-10">
            Fonte prezzi: GET /api/billing/plans · crediti e top-up come da catalogo
          </p>
        </div>
      </section>

      {/* Form */}
      <section id="founders-form" className="px-6 sm:px-12 py-24 bg-[#0B1E3F] text-white">
        <div className="max-w-2xl mx-auto">
          <p className="text-xs uppercase tracking-[0.3em] text-[#C19A6B] mb-3 text-center">Aderisci ora</p>
          <h2 className="text-3xl sm:text-4xl text-white text-center mb-4 font-light"
            style={{ fontFamily: "'Fraunces', Georgia, serif" }}>
            Prenota il tuo posto
          </h2>
          <p className="text-center text-white/70 mb-12 text-sm">
            {spots.remaining > 0
              ? `Solo ${spots.remaining}/${spots.total} posti disponibili — Ti contattiamo entro 24h per demo personalizzata.`
              : "Programma Founders 50 al completo. Iscriviti alla lista d'attesa."}
          </p>

          {result ? (
            <div className="bg-[#C19A6B]/10 border border-[#C19A6B] p-8 text-center" data-testid="agenzie-form-success">
              <p className="text-2xl text-[#C19A6B] mb-4"
                style={{ fontFamily: "'Fraunces', Georgia, serif" }}>
                Benvenuto, Founder #{result.position}
              </p>
              <p className="text-white/80 text-sm">{result.message}</p>
              {result.email_status === "sent" ? (
                <p className="text-white/60 text-xs mt-6">Controlla la tua casella email (anche spam).</p>
              ) : result.email_status === "mock" ? (
                <p className="text-amber-200/90 text-xs mt-6" data-testid="agenzie-email-mock">
                  Ambiente di prova: email non inviata (serve RESEND_API_KEY). La richiesta è comunque registrata.
                </p>
              ) : (
                <p className="text-amber-200/90 text-xs mt-6">Email di conferma non partita — ti contattiamo comunque.</p>
              )}
            </div>
          ) : (
            <form onSubmit={handleSubmit} className="space-y-4" data-testid="agenzie-form">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <input name="name" required value={formData.name} onChange={handleChange}
                  placeholder="Nome e cognome *"
                  data-testid="founders-input-name"
                  className="bg-white/10 border border-white/20 px-4 py-3 text-white placeholder:text-white/40 focus:outline-none focus:border-[#C19A6B]" />
                <input name="email" type="email" required value={formData.email} onChange={handleChange}
                  placeholder="Email *"
                  data-testid="founders-input-email"
                  className="bg-white/10 border border-white/20 px-4 py-3 text-white placeholder:text-white/40 focus:outline-none focus:border-[#C19A6B]" />
              </div>
              <input name="agency" required value={formData.agency} onChange={handleChange}
                placeholder="Nome agenzia *"
                data-testid="founders-input-agency"
                className="w-full bg-white/10 border border-white/20 px-4 py-3 text-white placeholder:text-white/40 focus:outline-none focus:border-[#C19A6B]" />
              <input name="city" required value={formData.city} onChange={handleChange}
                placeholder="Città *"
                data-testid="founders-input-city"
                className="w-full bg-white/10 border border-white/20 px-4 py-3 text-white placeholder:text-white/40 focus:outline-none focus:border-[#C19A6B]" />
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <input name="address" required value={formData.address} onChange={handleChange}
                  placeholder="Indirizzo (via) *"
                  data-testid="founders-input-address"
                  className="md:col-span-2 bg-white/10 border border-white/20 px-4 py-3 text-white placeholder:text-white/40 focus:outline-none focus:border-[#C19A6B]" />
                <input name="street_number" required value={formData.street_number} onChange={handleChange}
                  placeholder="Civico *"
                  data-testid="founders-input-street-number"
                  className="bg-white/10 border border-white/20 px-4 py-3 text-white placeholder:text-white/40 focus:outline-none focus:border-[#C19A6B]" />
              </div>
              <select name="has_website" required value={formData.has_website} onChange={handleChange}
                data-testid="founders-input-has-website"
                className="w-full bg-white/10 border border-white/20 px-4 py-3 text-white focus:outline-none focus:border-[#C19A6B]">
                <option value="" className="text-stone-900">Hai già un sito web? *</option>
                <option value="yes" className="text-stone-900">Sì — voglio una demo col mio look</option>
                <option value="no" className="text-stone-900">No — parto da zero con OMNIA</option>
              </select>
              {formData.has_website === "yes" ? (
                <input
                  name="website_url"
                  type="url"
                  required
                  value={formData.website_url}
                  onChange={handleChange}
                  placeholder="URL del sito (es. https://www.tuaagenzia.it) *"
                  data-testid="founders-input-website-url"
                  className="w-full bg-white/10 border border-white/20 px-4 py-3 text-white placeholder:text-white/40 focus:outline-none focus:border-[#C19A6B]"
                />
              ) : null}
              <select name="tier_interest" value={formData.tier_interest} onChange={handleChange}
                data-testid="founders-input-package"
                className="w-full bg-white/10 border border-white/20 px-4 py-3 text-white focus:outline-none focus:border-[#C19A6B]">
                <option value="" className="text-stone-900">Quale pacchetto ti interessa? (opzionale)</option>
                {(plans.length ? plans : [
                  { id: "starter", name: "Starter", foundersPrice: 49 },
                  { id: "pro", name: "Pro", foundersPrice: 99, highlight: true },
                  { id: "agency", name: "Agency", foundersPrice: 299 },
                ]).map((p) => (
                  <option key={p.id} value={p.id} className="text-stone-900">
                    {p.name} — €{p.foundersPrice}/mese{p.highlight ? " (più scelto)" : ""}
                  </option>
                ))}
              </select>
              <textarea name="notes" value={formData.notes} onChange={handleChange}
                placeholder="Note (opzionale)" rows="3"
                data-testid="founders-input-notes"
                className="w-full bg-white/10 border border-white/20 px-4 py-3 text-white placeholder:text-white/40 focus:outline-none focus:border-[#C19A6B]" />

              {errorMsg && (
                <p className="text-red-400 text-sm border border-red-400/30 px-4 py-3" data-testid="agenzie-form-error">
                  {errorMsg}
                </p>
              )}

              <button type="submit" disabled={submitting || isFull}
                data-testid="agenzie-form-submit"
                className="w-full bg-[#C19A6B] text-white py-4 text-sm uppercase tracking-widest hover:bg-[#a8845a] transition disabled:opacity-50 disabled:cursor-not-allowed">
                {submitting ? "Invio in corso..." : isFull ? "Programma completo" : "Richiedi demo"}
              </button>

              <p className="text-xs text-white/40 text-center mt-4">
                Inviando questo modulo accetti di essere contattato da OMNIA per la demo personalizzata.
                I tuoi dati restano riservati (GDPR).
              </p>
            </form>
          )}
        </div>
      </section>

      {/* Footer minimal */}
      <footer className="bg-[#080d1c] text-white/60 px-6 sm:px-12 py-12 text-center text-xs">
        <p style={{ fontFamily: "'Fraunces', Georgia, serif" }} className="text-lg text-white mb-2">OMNIA</p>
        <p className="uppercase tracking-widest">Real Estate Ecosystem</p>
        <div className="mt-6 flex flex-wrap justify-center gap-5 text-white/70">
          <Link
            to={`/${lang}/domain-sovereignty-policy`}
            className="uppercase tracking-widest hover:text-white underline decoration-white/20 hover:decoration-white transition"
            data-testid="agenzie-footer-domain-sovereignty-link"
          >
            🛡️ {t("domain_vault.policy_link")}
          </Link>
          <Link
            to={`/${lang}/verifica-dominio`}
            className="uppercase tracking-widest hover:text-white underline decoration-white/20 hover:decoration-white transition"
          >
            {t("domain_vault.existing_domain_verify_cta")}
          </Link>
        </div>
        <p className="mt-6 text-white/40">
          © 2026 OMNIA — Founders 50 program · Riservato a operatori del settore immobiliare
        </p>
      </footer>
    </div>
  );
}
