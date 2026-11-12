import React, { useCallback, useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { useTranslation } from "react-i18next";
import AgencyShell from "../components/AgencyShell";
import MlsEmbedKit from "../components/MlsEmbedKit";
import { api } from "../../../shared/lib/api";

const STEP_META = [
  {
    id: "site",
    title: "Sito e identità",
    hint: "Sito già tuo → resta dov’è; se vuoi la rete in home, sostituisci solo il box MLS. Restyling → template OMNIA.",
  },
  {
    id: "import_properties",
    title: "Portafoglio immobili",
    hint: "Hai un gestionale? Importa CSV/XML. Solo sito? Carica schede a mano con guida foto e testi.",
  },
  {
    id: "mls",
    title: "Rete MLS",
    hint: "Adesione + immobili e richieste (richieste ON di default, solo agenzie).",
  },
  {
    id: "documents",
    title: "Modulistica e paperless",
    hint: "Personalizza documenti. Firma elettronica: predisposizione (credenziali in produzione).",
    href: "modulistica",
  },
  {
    id: "publishing",
    title: "Pubblicazione",
    hint: "Portale OMNIA e altri portali pubblicitari.",
    href: "publishing",
  },
  {
    id: "import_crm",
    title: "Clienti e richieste",
    hint: "Import anagrafiche/richieste; condivisione rete già impostata allo step MLS.",
    href: "clients/import",
  },
  {
    id: "team",
    title: "Squadra",
    hint: "Invita colleghi entro i posti del piano. Opzionale.",
    href: "members",
    optional: true,
  },
];

export default function AvvioSetupPage() {
  const { t } = useTranslation();
  const { lang } = useParams();
  const l = (lang || "it").slice(0, 2);
  const [data, setData] = useState(null);
  const [err, setErr] = useState("");
  const [busy, setBusy] = useState(false);
  const [mlsPublic, setMlsPublic] = useState(false);
  const [shareListings, setShareListings] = useState(true);
  const [shareRequests, setShareRequests] = useState(true);
  const [joinMls, setJoinMls] = useState(true);
  const [paperless, setPaperless] = useState(true);

  const load = useCallback(async () => {
    setErr("");
    try {
      const r = await api.get("/app/setup-journey");
      setData(r.data);
      const mls = r.data?.journey?.steps?.mls;
      if (mls) {
        setShareListings(mls.share_listings !== false);
        setShareRequests(mls.share_requests !== false);
      }
      const site = r.data?.journey?.steps?.site;
      if (site?.mls_on_public_site != null) setMlsPublic(!!site.mls_on_public_site);
    } catch (e) {
      setErr(e?.response?.data?.detail?.hint || e?.response?.data?.detail || "Impossibile caricare Avvio");
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const journey = data?.journey;
  const steps = journey?.steps || {};
  const progress = data?.progress || { done: 0, total: 6 };
  const completed = journey?.status === "completed";
  const next = data?.next_step;
  const ctx = data?.context || {};
  const team = ctx.team || {};

  const run = async (fn) => {
    setBusy(true);
    setErr("");
    try {
      await fn();
      await load();
    } catch (e) {
      const d = e?.response?.data?.detail;
      setErr(
        (typeof d === "object" && (d.hint || d.error)) ||
          (typeof d === "string" ? d : null) ||
          e.message ||
          "Errore"
      );
    } finally {
      setBusy(false);
    }
  };

  const completeSite = (choice, mlsOnPublic) =>
    run(() =>
      api.post("/app/setup-journey/site", {
        choice,
        mls_on_public_site: typeof mlsOnPublic === "boolean" ? mlsOnPublic : mlsPublic,
      })
    );

  const completeMls = () =>
    run(() =>
      api.post("/app/setup-journey/mls", {
        join: joinMls,
        share_listings: shareListings,
        share_requests: shareRequests,
        accept_terms: true,
      })
    );

  const completeDocuments = () =>
    run(() =>
      api.post("/app/setup-journey/documents", {
        paperless_intent: paperless,
        mark_done: true,
      })
    );

  const markStep = (id) =>
    run(() => api.post(`/app/setup-journey/step/${id}`, { mark_done: true }));

  const finish = () =>
    run(() => api.post("/app/setup-journey/complete", { skip_optional: true }));

  return (
    <AgencyShell current="avvio">
      <section data-testid="avvio-setup-page" className="max-w-3xl space-y-8">
        <header>
          <p className="text-[10px] uppercase tracking-[0.3em] text-stone-500 mb-2 font-sans">
            {t("avvio.eyebrow", "Avvio agenzia")}
          </p>
          <h1
            className="text-3xl md:text-4xl tracking-tight text-stone-900"
            style={{ fontFamily: "'Fraunces', Georgia, serif" }}
          >
            {t("avvio.title", "Mettiamo in ordine la tua agenzia")}
          </h1>
          <p className="mt-2 text-sm font-sans text-stone-600 max-w-2xl">
            {t(
              "avvio.subtitle",
              "Un passo alla volta. Gli strumenti restano in menu; la barra in alto ti riporta qui finché non chiudi Avvio."
            )}
          </p>
          <div className="mt-4 flex flex-wrap items-center gap-3">
            <p className="text-xs font-sans uppercase tracking-widest text-stone-500" data-testid="avvio-progress">
              {progress.done}/{progress.total} obbligatori
              {completed
                ? " · completato"
                : next && next !== "done"
                  ? ` · prossimo: ${STEP_META.find((s) => s.id === next)?.title || next}`
                  : ""}
            </p>
            {typeof ctx.credits_balance === "number" ? (
              <Link
                to={`/${l}/app/settings/billing`}
                data-testid="avvio-credits-chip"
                className="inline-flex items-center gap-2 px-3 py-1.5 border border-stone-900 bg-white text-stone-900"
              >
                <span className="text-[10px] uppercase tracking-widest text-stone-500">Crediti</span>
                <span className="text-base font-semibold tabular-nums" style={{ fontFamily: "'Fraunces', Georgia, serif" }}>
                  {Math.trunc(Number(ctx.credits_balance))
                    .toString()
                    .replace(/\B(?=(\d{3})+(?!\d))/g, ".")}
                </span>
              </Link>
            ) : null}
          </div>
        </header>

        {err && (
          <p data-testid="avvio-error" className="text-sm text-red-800 bg-red-50 border border-red-200 px-3 py-2">
            {typeof err === "string" ? err : JSON.stringify(err)}
          </p>
        )}

        {completed ? (
          <div className="border border-emerald-200 bg-emerald-50 px-5 py-4 space-y-3" data-testid="avvio-done">
            <p className="font-sans text-sm text-emerald-900">
              Avvio completato. Puoi lavorare dal gestionale; il menu resta completo (strumenti inclusi).
            </p>
            <Link
              to={`/${l}/app/dashboard`}
              className="inline-flex px-4 py-2 text-xs uppercase tracking-widest bg-stone-900 text-white"
            >
              Vai a Oggi →
            </Link>
          </div>
        ) : null}

        <ol className="space-y-4">
          {STEP_META.map((meta, idx) => {
            const st = steps[meta.id] || {};
            const isDone = !!st.done;
            const isCurrent = !completed && next === meta.id;
            return (
              <li
                key={meta.id}
                data-testid={`avvio-step-${meta.id}`}
                className={`border px-4 py-4 ${
                  isCurrent ? "border-stone-900 bg-white" : "border-stone-200 bg-stone-50/80"
                }`}
              >
                <div className="flex flex-wrap items-baseline justify-between gap-2">
                  <h2 className="text-lg text-stone-900" style={{ fontFamily: "'Fraunces', Georgia, serif" }}>
                    <span className="text-stone-400 mr-2">{idx + 1}.</span>
                    {meta.title}
                    {meta.optional ? (
                      <span className="ml-2 text-[10px] uppercase tracking-widest text-stone-400">opzionale</span>
                    ) : null}
                  </h2>
                  <span className="text-[10px] uppercase tracking-widest font-sans text-stone-500">
                    {isDone ? "fatto" : isCurrent ? "in corso" : "da fare"}
                  </span>
                </div>
                {isCurrent || isDone ? (
                  <p className="mt-1 text-sm font-sans text-stone-600">{meta.hint}</p>
                ) : (
                  <p className="mt-1 text-xs font-sans text-stone-400">Dopo il passo in corso.</p>
                )}

                {/* —— STEP 1: sito già mio OPPURE restyling —— */}
                {meta.id === "site" && isCurrent && (
                  <div className="mt-4 space-y-3" data-testid="avvio-site-form">
                    {ctx.declared_url ? (
                      <p className="text-xs text-stone-500 truncate" data-testid="avvio-declared-url">
                        URL in registrazione: {ctx.declared_url}
                      </p>
                    ) : null}
                    <div className="grid sm:grid-cols-2 gap-3">
                      <div className="border border-stone-900 bg-white px-3 py-3 space-y-2">
                        <p className="text-sm font-sans font-medium text-stone-900">Il sito è già mio</p>
                        <p className="text-xs text-stone-500">
                          Resta dove sta: niente clone, niente template. Se aderisci alla rete,
                          sostituisci solo il riquadro MLS in home. Il resto del sito non si tocca.
                        </p>
                        <button
                          type="button"
                          disabled={busy}
                          onClick={() => completeSite("external", true)}
                          data-testid="avvio-site-external-embed"
                          className="w-full px-3 py-2 text-[11px] uppercase tracking-widest bg-stone-900 text-white disabled:opacity-40"
                        >
                          Tengo il sito, sostituisco solo il box MLS
                        </button>
                        <button
                          type="button"
                          disabled={busy}
                          onClick={() => completeSite("external", false)}
                          data-testid="avvio-site-external"
                          className="w-full px-3 py-2 text-[11px] uppercase tracking-widest border border-stone-400 disabled:opacity-40"
                        >
                          Tengo il sito, rete solo in gestionale
                        </button>
                      </div>
                      <div className="border border-stone-200 px-3 py-3 space-y-2">
                        <p className="text-sm font-sans font-medium text-stone-900">Restyling / sito OMNIA</p>
                        <p className="text-xs text-stone-500">
                          Apri Il mio sito: compaiono i template, ne scegli uno e ritocchi logo/slogan.
                        </p>
                        <label className="flex items-start gap-2 text-xs font-sans text-stone-700">
                          <input
                            type="checkbox"
                            checked={mlsPublic}
                            onChange={(e) => setMlsPublic(e.target.checked)}
                            className="mt-0.5"
                            data-testid="avvio-mls-public"
                          />
                          <span>Voglio anche la rete MLS sul sito pubblico</span>
                        </label>
                        <div className="flex flex-wrap gap-2">
                          <Link
                            to={`/${l}/app/website?restyle=1`}
                            data-testid="avvio-open-restyle"
                            className="px-3 py-2 text-[11px] uppercase tracking-widest border border-stone-900"
                          >
                            Mostra i template →
                          </Link>
                          <button
                            type="button"
                            disabled={busy}
                            onClick={() => completeSite("omnia_theme")}
                            data-testid="avvio-site-omnia"
                            className="px-3 py-2 text-[11px] uppercase tracking-widest border border-stone-300 disabled:opacity-50"
                          >
                            Segna fatto (dopo aver scelto)
                          </button>
                        </div>
                      </div>
                    </div>
                  </div>
                )}

                {/* —— STEP 2: gestionale OPPURE solo sito —— */}
                {meta.id === "import_properties" && isCurrent && (
                  <div className="mt-4 space-y-3" data-testid="avvio-portfolio-form">
                    <div className="grid sm:grid-cols-2 gap-3">
                      <div className="border border-stone-200 px-3 py-3 space-y-2">
                        <p className="text-sm font-sans font-medium text-stone-900">Ho già un gestionale</p>
                        <p className="text-xs text-stone-500">
                          Importa CSV/XML dal software precedente (hub Importa).
                        </p>
                        <Link
                          to={`/${l}/app/import`}
                          data-testid="avvio-open-import"
                          className="inline-flex px-3 py-2 text-[11px] uppercase tracking-widest border border-stone-400"
                        >
                          Apri Importa →
                        </Link>
                      </div>
                      <div className="border border-stone-200 px-3 py-3 space-y-2">
                        <p className="text-sm font-sans font-medium text-stone-900">Ho solo il sito</p>
                        <p className="text-xs text-stone-500">
                          Crea le schede a mano: foto (copertina + interni), titolo, prezzo, descrizione, zona.
                          Ti guidiamo nel form immobile.
                        </p>
                        <Link
                          to={`/${l}/app/properties/new?guide=site`}
                          data-testid="avvio-open-manual-property"
                          className="inline-flex px-3 py-2 text-[11px] uppercase tracking-widest bg-stone-900 text-white"
                        >
                          Nuovo immobile (guida) →
                        </Link>
                      </div>
                    </div>
                    <button
                      type="button"
                      disabled={busy}
                      onClick={() => markStep("import_properties")}
                      data-testid="avvio-done-import_properties"
                      className="px-3 py-2 text-[11px] uppercase tracking-widest border border-stone-400"
                    >
                      Segna fatto (anche se carichi dopo)
                    </button>
                  </div>
                )}

                {meta.id === "mls" && isCurrent && (
                  <div className="mt-4 space-y-3" data-testid="avvio-mls-form">
                    <label className="flex gap-2 text-sm font-sans">
                      <input type="checkbox" checked={joinMls} onChange={(e) => setJoinMls(e.target.checked)} />
                      Aderisco alla rete MLS OMNIA
                    </label>
                    <label className="flex gap-2 text-sm font-sans">
                      <input
                        type="checkbox"
                        checked={shareListings}
                        onChange={(e) => setShareListings(e.target.checked)}
                      />
                      Condividi immobili in rete
                    </label>
                    <label className="flex gap-2 text-sm font-sans">
                      <input
                        type="checkbox"
                        checked={shareRequests}
                        onChange={(e) => setShareRequests(e.target.checked)}
                        data-testid="avvio-share-requests"
                      />
                      Condividi richieste in rete (solo agenti/agenzie — default sì)
                    </label>
                    <button
                      type="button"
                      disabled={busy}
                      onClick={completeMls}
                      data-testid="avvio-mls-save"
                      className="px-3 py-2 text-[11px] uppercase tracking-widest bg-stone-900 text-white disabled:opacity-50"
                    >
                      Conferma MLS
                    </button>
                    {ctx.embed ? <MlsEmbedKit kit={ctx.embed} compact /> : null}
                  </div>
                )}

                {meta.id === "documents" && isCurrent && (
                  <div className="mt-4 space-y-3" data-testid="avvio-docs-form">
                    <label className="flex gap-2 text-sm font-sans">
                      <input
                        type="checkbox"
                        checked={paperless}
                        onChange={(e) => setPaperless(e.target.checked)}
                      />
                      Predisponi percorso paperless (firma elettronica: credenziali in produzione)
                    </label>
                    <div className="flex flex-wrap gap-2">
                      <Link
                        to={`/${l}/app/modulistica`}
                        className="px-3 py-2 text-[11px] uppercase tracking-widest border border-stone-400"
                      >
                        Apri Modulistica
                      </Link>
                      <button
                        type="button"
                        disabled={busy}
                        onClick={completeDocuments}
                        data-testid="avvio-docs-done"
                        className="px-3 py-2 text-[11px] uppercase tracking-widest bg-stone-900 text-white"
                      >
                        Segna fatto
                      </button>
                    </div>
                  </div>
                )}

                {meta.id === "team" && (isCurrent || isDone) && (
                  <div className="mt-4 space-y-3" data-testid="avvio-team-seats">
                    <p className="text-sm font-sans text-stone-700">
                      Piano <strong>{team.tier || ctx.plan_name || "—"}</strong>
                      {" · "}
                      posti{" "}
                      <strong data-testid="avvio-seats">
                        {team.members ?? "—"}
                        {team.max_agents < 0 || team.max_agents == null
                          ? " / illimitati"
                          : ` / ${team.max_agents}`}
                      </strong>
                      {team.pending_invites ? ` · ${team.pending_invites} invite in attesa` : ""}
                      {team.seats_left != null ? ` · liberi ${team.seats_left}` : ""}
                    </p>
                    <p className="text-xs text-stone-500 font-sans">
                      Li attivi tu: Collaboratori → «Invita» con email. Il collega apre il link, accetta e entra.
                      Il tetto è del piano (Starter 3 · Pro 10 · Agency illimitati).
                    </p>
                    {isCurrent ? (
                      <div className="flex flex-wrap gap-2">
                        <Link
                          to={`/${l}/app/members`}
                          data-testid="avvio-open-team"
                          className="px-3 py-2 text-[11px] uppercase tracking-widest border border-stone-400"
                        >
                          Apri Membri / Invita →
                        </Link>
                        <button
                          type="button"
                          disabled={busy}
                          onClick={() => markStep("team")}
                          data-testid="avvio-done-team"
                          className="px-3 py-2 text-[11px] uppercase tracking-widest bg-stone-900 text-white"
                        >
                          Segna fatto / salta
                        </button>
                      </div>
                    ) : null}
                  </div>
                )}

                {["publishing", "import_crm"].includes(meta.id) && isCurrent && (
                  <div className="mt-4 flex flex-wrap gap-2">
                    {meta.href ? (
                      <Link
                        to={`/${l}/app/${meta.href}`}
                        className="px-3 py-2 text-[11px] uppercase tracking-widest border border-stone-400"
                        data-testid={`avvio-open-${meta.id}`}
                      >
                        Apri →
                      </Link>
                    ) : null}
                    <button
                      type="button"
                      disabled={busy}
                      onClick={() => markStep(meta.id)}
                      data-testid={`avvio-done-${meta.id}`}
                      className="px-3 py-2 text-[11px] uppercase tracking-widest bg-stone-900 text-white"
                    >
                      Segna fatto
                    </button>
                  </div>
                )}

                {isDone && st.choice ? (
                  <p className="mt-2 text-xs font-sans text-stone-500">
                    Scelta sito: {st.choice}
                    {st.mls_via_embed || st.mls_on_public_site
                      ? " · box MLS da incollare sul sito"
                      : ""}
                  </p>
                ) : null}
                {meta.id === "site" && isDone && ctx.embed ? (
                  <div className="mt-3">
                    <MlsEmbedKit kit={ctx.embed} compact />
                  </div>
                ) : null}
                {meta.id === "mls" && isDone && ctx.embed ? (
                  <div className="mt-3">
                    <MlsEmbedKit kit={ctx.embed} compact />
                  </div>
                ) : null}
              </li>
            );
          })}
        </ol>

        {!completed && progress.done >= progress.total ? (
          <button
            type="button"
            disabled={busy}
            onClick={finish}
            data-testid="avvio-complete"
            className="px-5 py-3 text-xs uppercase tracking-widest bg-[#0B1E3F] text-white"
          >
            Chiudi Avvio e apri gestionale
          </button>
        ) : null}
      </section>
    </AgencyShell>
  );
}
