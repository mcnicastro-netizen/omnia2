import React, { useEffect, useState } from "react";
import axios from "axios";
import { useTranslation } from "react-i18next";
import { Link } from "react-router-dom";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api/founders`;

const HERO_IMG =
  "https://images.unsplash.com/photo-1551836022-deb4988cc6c0?w=1600&q=80&auto=format&fit=crop";

const PRICING = [
  {
    id: "starter",
    name: "Starter",
    foundersPrice: 39,
    standardPrice: 59,
    users: 3,
    credits: 20,
    listings: 15,
    features: [
      "HAL Chatbot AI + Lead Scoring",
      "HAL Legal anti-hallucination",
      "Valutatore Pro UNI 10750",
      "Multiposting 3 portali",
      "Supporto email 48h",
    ],
  },
  {
    id: "pro",
    name: "Pro",
    foundersPrice: 99,
    standardPrice: 179,
    users: "4–20",
    credits: 200,
    listings: 50,
    highlight: true,
    features: [
      "Tutto di Starter +",
      "HAL Improve copywriter inline",
      "White-label con tuo dominio",
      "Multiposting 8 portali",
      "Supporto email 24h + chat",
    ],
  },
  {
    id: "agency",
    name: "Agency",
    foundersPrice: 249,
    standardPrice: 349,
    users: "21+",
    credits: 600,
    listings: 70,
    features: [
      "Tutto di Pro +",
      "White-label + SSO custom",
      "Multiposting tutti i portali + custom",
      "Boost portale illimitati (fair-use)",
      "Supporto dedicato SLA 4h",
    ],
  },
];

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
  const [formData, setFormData] = useState({
    email: "",
    name: "",
    agency: "",
    city: "",
    agents_count: 3,
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
      const payload = {
        ...formData,
        agents_count: parseInt(formData.agents_count, 10) || 1,
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
      {/* Top minimal nav */}
      <header className="absolute top-0 left-0 right-0 z-10 px-6 sm:px-12 py-6">
        <div className="flex items-center justify-between max-w-screen-2xl mx-auto">
          <Link
            to={`/${lang}`}
            className="text-xl md:text-2xl tracking-tight font-medium text-white"
            style={{ fontFamily: "'Fraunces', Georgia, serif" }}
            data-testid="agenzie-logo"
          >
            OMNIA<sup className="text-[10px] text-white/60 ml-0.5">™</sup>
          </Link>
          <a
            href="#founders-form"
            className="text-xs uppercase tracking-widest text-white border border-white/40 px-5 py-2 hover:bg-white hover:text-stone-900 transition"
            data-testid="agenzie-cta-top"
          >
            Aderisci ora →
          </a>
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
            ImmobilCloud (portale B2C) · ImmoWeb (CRM AI) · Omnia Academy.
            Un solo ecosistema. White-label. Prezzo bloccato 24 mesi.
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
              Voglio il mio posto →
            </a>
          </div>
        </div>
      </section>

      {/* 3 wow moments */}
      <section className="px-6 sm:px-12 py-24 max-w-6xl mx-auto">
        <p className="text-xs uppercase tracking-[0.3em] text-stone-500 mb-3 text-center">Cosa otteniamo</p>
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
      <section className="bg-stone-50 px-6 sm:px-12 py-24 border-y border-stone-200">
        <div className="max-w-6xl mx-auto">
          <p className="text-xs uppercase tracking-[0.3em] text-stone-500 mb-3 text-center">Founders 50 Pricing</p>
          <h2 className="text-3xl sm:text-4xl text-stone-900 text-center mb-4 font-light"
            style={{ fontFamily: "'Fraunces', Georgia, serif" }}>
            Prezzo bloccato 24 mesi
          </h2>
          <p className="text-center text-stone-600 mb-16 text-sm">
            Dopo 24 mesi: prezzo standard <span className="line-through">€59 / €179 / €349</span> →{" "}
            <strong className="text-[#C19A6B]">sconto 50% a vita</strong>
          </p>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {PRICING.map((p) => (
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
                  <p className="text-xs text-stone-400 line-through mt-1">€{p.standardPrice}/mese standard</p>
                </div>
                <ul className="text-sm space-y-2 mb-6 text-stone-700">
                  <li>👥 <strong>{p.users}</strong> utenti</li>
                  <li>💳 <strong>{p.credits}</strong> crediti/mese</li>
                  <li>📋 <strong>{p.listings}</strong> annunci portale</li>
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
            Sistema crediti €0,30/cad · Pacchetti top-up · Boost portale -30% vs Idealista
          </p>
        </div>
      </section>

      {/* Form */}
      <section id="founders-form" className="px-6 sm:px-12 py-24 bg-[#0B1E3F] text-white">
        <div className="max-w-2xl mx-auto">
          <p className="text-xs uppercase tracking-[0.3em] text-[#C19A6B] mb-3 text-center">Aderisci ora</p>
          <h2 className="text-3xl sm:text-4xl text-white text-center mb-4 font-light"
            style={{ fontFamily: "'Fraunces', Georgia, serif" }}>
            Blocca il tuo posto
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
              <p className="text-white/60 text-xs mt-6">Controlla la tua casella email (anche spam).</p>
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
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <input name="city" required value={formData.city} onChange={handleChange}
                  placeholder="Città *"
                  data-testid="founders-input-city"
                  className="bg-white/10 border border-white/20 px-4 py-3 text-white placeholder:text-white/40 focus:outline-none focus:border-[#C19A6B]" />
                <input name="agents_count" type="number" min="1" max="500" required
                  value={formData.agents_count} onChange={handleChange}
                  placeholder="Numero agenti *"
                  data-testid="founders-input-agents"
                  className="bg-white/10 border border-white/20 px-4 py-3 text-white placeholder:text-white/40 focus:outline-none focus:border-[#C19A6B]" />
              </div>
              <select name="tier_interest" value={formData.tier_interest} onChange={handleChange}
                data-testid="founders-input-tier"
                className="w-full bg-white/10 border border-white/20 px-4 py-3 text-white focus:outline-none focus:border-[#C19A6B]">
                <option value="" className="text-stone-900">Quale tier ti interessa? (opzionale)</option>
                <option value="starter" className="text-stone-900">Starter — €39/mese</option>
                <option value="pro" className="text-stone-900">Pro — €99/mese (più scelto)</option>
                <option value="agency" className="text-stone-900">Agency — €249/mese</option>
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
                {submitting ? "Invio in corso..." : isFull ? "Programma completo" : `Blocca il mio posto #${spots.registered + 1}`}
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
