import React, { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { api } from "../../../../shared/lib/api";

/**
 * Scheda cliente Ops — flusso lineare:
 * 1) Controlla documenti → Segna verificato
 * 2) Controlla pagamento
 * 3) Attiva (email password)
 */
export default function BridgeTenantDetailPage() {
  const { lang: langParam, agencyId } = useParams();
  const lang = langParam || "it";
  const base = `/${lang}/app/ops`;
  const [data, setData] = useState(null);
  const [err, setErr] = useState(null);
  const [busy, setBusy] = useState(true);
  const [actionMsg, setActionMsg] = useState(null);
  const [kycBusy, setKycBusy] = useState(false);
  const [attivaBusy, setAttivaBusy] = useState(false);
  const [showDanger, setShowDanger] = useState(false);
  const [issuedKey, setIssuedKey] = useState(null);
  const [keyCopied, setKeyCopied] = useState(false);

  const load = async () => {
    setBusy(true);
    setErr(null);
    try {
      const r = await api.get(`/app/ops/bridge/tenants/${agencyId}`);
      setData(r.data);
    } catch {
      setErr("Agenzia non trovata.");
      setData(null);
    } finally {
      setBusy(false);
    }
  };

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [agencyId]);

  const attiva = async ({ bypassPay = false, bypassKyc = false } = {}) => {
    const a0 = data?.agency || {};
    const tier = a0.preferred_plan_tier || data?.payment?.plan_tier || "pro";
    const payOk = Boolean(data?.payment?.ok);
    const kycOk = (a0.kyc?.status || "").toLowerCase() === "verified";

    if (!bypassKyc && !kycOk) {
      setActionMsg("Prima segna i documenti come verificati (passo 1).");
      return;
    }
    if (!bypassPay && !payOk) {
      if (
        !window.confirm(
          "Pagamento non trovato. Attivare comunque? (solo emergenza Ops)"
        )
      ) {
        return;
      }
      bypassPay = true;
    }

    if (
      !window.confirm(
        `Attivare «${a0.display_name}» sul piano ${String(tier).toUpperCase()}?\n` +
          "Il titolare entra con la password scelta in registrazione."
      )
    ) {
      return;
    }

    setAttivaBusy(true);
    setActionMsg(null);
    setIssuedKey(null);
    try {
      const r = await api.post("/app/ops/activate-agency", {
        agency_id: agencyId,
        grant_plan: true,
        tier,
        credits: 2000,
        send_email: true,
        wipe_crm: true,
        note: "cabina_scheda",
        require_kyc_verified: !bypassKyc,
        require_payment: !bypassPay,
        // D-161: password = register; niente API=password
        issue_login_credential: false,
      });
      const once = r?.data?.credential_key;
      if (once) setIssuedKey(once);
      const mail = r?.data?.email;
      const mailOk = mail?.ok === true || mail?.status === "sent" || mail?.status === "mock";
      if (once) {
        setActionMsg("Attivata. Copia la chiave qui sotto (anche via email al titolare).");
      } else if (mailOk) {
        setActionMsg(
          `Attivata. Email di conferma inviata a ${mail?.to || "titolare"} — entra con la password di registrazione.`
        );
      } else {
        setActionMsg(
          `Attivata, ma email non partita (${mail?.status || mail?.error || "sconosciuto"}). Controlla Resend / email titolare.`
        );
      }
      await load();
    } catch (e) {
      const d = e?.response?.data?.detail;
      if (d?.error === "payment_required") {
        setActionMsg(
          "Pagamento ancora assente. Il cliente deve completare Stripe, oppure conferma il bypass."
        );
      } else if (d?.error === "kyc_not_verified") {
        setActionMsg("Documenti non ancora verificati. Usa «Segna verificato».");
      } else {
        setActionMsg(
          (typeof d === "object" && (d.hint || d.error)) || d || "Attivazione fallita"
        );
      }
    } finally {
      setAttivaBusy(false);
    }
  };

  const setKycStatus = async (status) => {
    const notes =
      status === "rejected"
        ? window.prompt("Motivo rifiuto (visibile in nota Ops):") || ""
        : "";
    setKycBusy(true);
    setActionMsg(null);
    try {
      await api.patch(`/app/ops/bridge/tenants/${agencyId}/kyc`, { status, notes });
      setActionMsg(status === "verified" ? "Documenti verificati." : `KYC → ${status}`);
      await load();
    } catch (e) {
      setActionMsg(e?.response?.data?.detail || "Aggiornamento KYC fallito");
    } finally {
      setKycBusy(false);
    }
  };

  const downloadKyc = async (docId, name) => {
    try {
      const r = await api.get(
        `/app/ops/bridge/tenants/${agencyId}/kyc/documents/${docId}/download`,
        { responseType: "blob" }
      );
      const url = window.URL.createObjectURL(new Blob([r.data]));
      const link = document.createElement("a");
      link.href = url;
      link.setAttribute("download", name || "documento");
      document.body.appendChild(link);
      link.click();
      link.parentNode.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch {
      setActionMsg("Download fallito");
    }
  };

  const openAsCrm = async () => {
    if (!window.confirm("Aprire il gestionale di questa agenzia?")) return;
    setActionMsg(null);
    try {
      await api.post("/app/ops/bridge/impersonate", { agency_id: agencyId });
      window.location.href = `/${lang}/app/dashboard`;
    } catch (e) {
      setActionMsg(e?.response?.data?.detail || "Apertura CRM non riuscita");
    }
  };

  const offboard = async () => {
    const conf = window.prompt(
      "Chiudere agenzia? Digita CHIUDI_AGENZIA per confermare."
    );
    if (conf !== "CHIUDI_AGENZIA") return;
    const eraseMembers = window.confirm(
      "Anonimizzare anche i membri? OK = sì · Annulla = solo chiusura tenant."
    );
    setActionMsg(null);
    try {
      const r = await api.post(`/app/ops/bridge/tenants/${agencyId}/offboard`, {
        confirm: "CHIUDI_AGENZIA",
        erase_members: eraseMembers,
      });
      setActionMsg(
        `Chiusa. Membri anonimizzati: ${(r.data?.members_erased || []).length}`
      );
      window.location.href = `${base}/clienti`;
    } catch (e) {
      setActionMsg(e?.response?.data?.detail?.error || "Chiusura fallita");
    }
  };

  if (busy && !data) {
    return <p className="text-sm text-stone-500">Caricamento…</p>;
  }
  if (err || !data) {
    return (
      <div>
        <p className="text-sm text-red-700">{err || "Errore"}</p>
        <Link to={`${base}/clienti`} className="text-xs uppercase tracking-widest mt-4 inline-block">
          ← Clienti
        </Link>
      </div>
    );
  }

  const a = data.agency || {};
  const owner = data.owner || {};
  const pay = data.payment || {};
  const pending = (a.activation_status || "active") === "pending";
  const kycStatus = (a.kyc?.status || "incomplete").toLowerCase();
  const kycVerified = kycStatus === "verified";
  const hasVisura = Boolean(a.kyc?.checklist?.visura_camerale);
  const hasId = Boolean(a.kyc?.checklist?.id_titolare);
  const docsReady = hasVisura && hasId;
  const payOk = Boolean(pay.ok);
  const canActivate = pending && kycVerified && payOk;
  const docs = a.kyc?.documents || [];

  return (
    <div data-testid="bridge-tenant-detail" className="space-y-8 max-w-3xl">
      <div>
        <Link
          to={`${base}/clienti`}
          className="text-[10px] uppercase tracking-widest text-stone-500 hover:text-stone-800"
        >
          ← Clienti
        </Link>
        <h1
          className="mt-3 text-3xl text-[#0B1E3F] tracking-tight"
          style={{ fontFamily: "'Fraunces', Georgia, serif" }}
        >
          {a.display_name}
        </h1>
        <p className="text-sm text-stone-600 mt-1">
          {owner.name || "—"} · {owner.email || "—"}
        </p>
        <p className="text-xs text-stone-500 mt-1">
          {a.slug} · piano {(a.preferred_plan_tier || pay.plan_tier || "—").toString().toUpperCase()} ·{" "}
          {pending ? "in attesa" : a.activation_status || "active"}
        </p>
      </div>

      {actionMsg ? (
        <p
          data-testid="bridge-action-msg"
          className="text-sm text-[#0B1E3F] bg-[#0B1E3F]/5 border border-[#0B1E3F]/20 px-3 py-2 rounded"
        >
          {actionMsg}
        </p>
      ) : null}

      {issuedKey ? (
        <div
          data-testid="bridge-credential-once"
          className="bg-amber-50 border border-amber-200 rounded-lg px-4 py-3 space-y-2"
        >
          <p className="text-xs uppercase tracking-widest text-amber-900">
            Chiave di accesso — copiala ora (una sola volta)
          </p>
          <p className="font-mono text-sm break-all bg-white border border-amber-100 rounded px-3 py-2">
            {issuedKey}
          </p>
          <div className="flex flex-wrap gap-2">
            <button
              type="button"
              data-testid="bridge-credential-copy"
              className="text-xs uppercase tracking-widest px-3 py-2 rounded bg-[#0B1E3F] text-white"
              onClick={async () => {
                try {
                  await navigator.clipboard.writeText(issuedKey);
                  setKeyCopied(true);
                  setTimeout(() => setKeyCopied(false), 2000);
                } catch {
                  setActionMsg("Copia manuale: seleziona il testo sopra.");
                }
              }}
            >
              {keyCopied ? "Copiata ✓" : "Copia chiave"}
            </button>
            <button
              type="button"
              className="text-xs uppercase tracking-widest px-3 py-2 rounded border border-stone-300 bg-white"
              onClick={() => setIssuedKey(null)}
            >
              Nascondi
            </button>
          </div>
          <p className="text-xs text-stone-600">
            Il cliente la riceve anche via email. Al primo ingresso gli chiediamo di
            sostituirla con una password personale.
          </p>
        </div>
      ) : null}

      {/* ——— Checklist attivazione ——— */}
      <section
        data-testid="bridge-activation-checklist"
        className="bg-white border border-stone-200 rounded-lg divide-y divide-stone-100"
      >
        <div className="px-4 py-3">
          <h2 className="text-xs uppercase tracking-widest text-stone-500">
            Attivazione — 3 passi
          </h2>
          <p className="text-sm text-stone-600 mt-1">
            Controlla documenti, verifica pagamento, poi attiva. Una email parte al cliente.
          </p>
        </div>

        {/* Step 1 */}
        <div className="px-4 py-4 space-y-3" data-testid="bridge-step-docs">
          <div className="flex items-start justify-between gap-3">
            <div>
              <p className="text-sm font-medium text-[#0B1E3F]">
                1 · Documenti{" "}
                <StatusPill
                  ok={kycVerified}
                  warn={docsReady && !kycVerified}
                  label={
                    kycVerified
                      ? "verificati"
                      : docsReady
                        ? "da verificare"
                        : "incompleti"
                  }
                />
              </p>
              <p className="text-xs text-stone-500 mt-1">
                Visura {hasVisura ? "✓" : "✗"} · CI {hasId ? "✓" : "✗"} · PEC{" "}
                {a.contact?.pec ? "✓" : "—"} · P.IVA {a.fiscal?.vat_number ? "✓" : "—"}
              </p>
            </div>
          </div>

          <ul className="space-y-2">
            {docs.length === 0 ? (
              <li className="text-sm text-amber-800 bg-amber-50 border border-amber-200 rounded px-3 py-2">
                Il cliente non ha ancora caricato documenti.
              </li>
            ) : (
              docs.map((d) => (
                <li
                  key={d.id}
                  className="flex items-center justify-between gap-3 text-sm border border-stone-100 rounded px-3 py-2 bg-stone-50"
                >
                  <span>
                    <span className="text-[10px] uppercase tracking-widest text-stone-500 mr-2">
                      {d.doc_type === "visura_camerale"
                        ? "Visura"
                        : d.doc_type === "documento_identita"
                          ? "CI"
                          : d.doc_type}
                    </span>
                    {d.filename}
                  </span>
                  <button
                    type="button"
                    className="text-[10px] uppercase tracking-widest text-[#0B1E3F] underline shrink-0"
                    onClick={() => downloadKyc(d.id, d.filename)}
                  >
                    Scarica
                  </button>
                </li>
              ))
            )}
          </ul>

          {a.fiscal?.vat_number ? (
            <p className="text-xs text-stone-500">
              Controllo crociato:{" "}
              <a
                className="underline text-[#0B1E3F]"
                href={`https://www.registroimprese.it/ricerca-libera?q=${encodeURIComponent(
                  a.fiscal.vat_number
                )}`}
                target="_blank"
                rel="noopener noreferrer"
              >
                Registro Imprese · {a.fiscal.vat_number}
              </a>
            </p>
          ) : null}

          {pending && !kycVerified ? (
            <div className="flex flex-wrap gap-2 pt-1">
              <button
                type="button"
                disabled={kycBusy || !docsReady}
                className="text-xs uppercase tracking-widest px-4 py-2.5 rounded bg-emerald-800 text-white disabled:opacity-40"
                data-testid="bridge-kyc-verify"
                onClick={() => setKycStatus("verified")}
              >
                Segna verificato
              </button>
              <button
                type="button"
                disabled={kycBusy}
                className="text-xs uppercase tracking-widest px-4 py-2.5 rounded border border-rose-300 text-rose-800"
                onClick={() => setKycStatus("rejected")}
              >
                Rifiuta documenti
              </button>
            </div>
          ) : null}
          {a.kyc?.notes ? (
            <p className="text-xs text-stone-500">Nota: {a.kyc.notes}</p>
          ) : null}
        </div>

        {/* Step 2 */}
        <div className="px-4 py-4 space-y-2" data-testid="bridge-step-pay">
          <p className="text-sm font-medium text-[#0B1E3F]">
            2 · Pagamento{" "}
            <StatusPill
              ok={payOk}
              label={payOk ? "ok" : "manca"}
            />
          </p>
          <p className="text-sm text-stone-600" data-testid="bridge-pay-detail">
            {payOk
              ? `Abbonamento ricevuto${
                  pay.subscription_status ? ` (${pay.subscription_status})` : ""
                }${pay.last_paid_at ? ` · pagato ${String(pay.last_paid_at).slice(0, 10)}` : ""}.`
              : "Nessun pagamento Stripe trovato. Il cliente paga da sala d’attesa (carta test 4242…)."}
          </p>
          {payOk ? (
            <p className="text-sm text-stone-700" data-testid="bridge-pay-period">
              {pay.current_period_end
                ? `Scade / rinnova: ${String(pay.current_period_end).slice(0, 10)}${
                    pay.days_left != null ? ` · ${pay.days_left} giorni` : ""
                  }${pay.renewal_due_soon ? " · in scadenza" : ""}${
                    pay.past_due ? " · PAST DUE" : ""
                  }`
                : "Periodo Stripe non ancora sincronizzato."}
            </p>
          ) : null}
          <p className="text-sm text-stone-700" data-testid="bridge-package-credits">
            Crediti pacchetto:{" "}
            <strong>{data.credits?.balance ?? 0}</strong>
            {data.credits?.low ? (
              <span className="text-amber-800"> · bassi (&lt;{data.credits?.low_threshold})</span>
            ) : null}
            <span className="text-xs text-stone-500"> · non confondere con crediti Kling/video</span>
          </p>
          {!payOk && pending ? (
            <p className="text-xs text-amber-800 bg-amber-50 border border-amber-200 rounded px-3 py-2">
              Finché non paga, Attiva chiederà conferma di bypass emergenza.
            </p>
          ) : null}
        </div>

        {/* Step 3 */}
        <div className="px-4 py-4 space-y-3" data-testid="bridge-step-activate">
          <p className="text-sm font-medium text-[#0B1E3F]">
            3 · Attiva gestionale{" "}
            <StatusPill
              ok={!pending}
              warn={pending && canActivate}
              label={pending ? (canActivate ? "pronta" : "bloccata") : "già attiva"}
            />
          </p>
          {pending ? (
            <>
              {!canActivate ? (
                <ul className="text-sm text-stone-600 list-disc pl-5 space-y-1">
                  {!kycVerified ? <li>Manca verifica documenti (passo 1)</li> : null}
                  {!payOk ? <li>Manca pagamento (passo 2)</li> : null}
                </ul>
              ) : (
                <p className="text-sm text-stone-600">
                  Tutto ok. Attiva sblocca il CRM; il titolare usa la password di
                  registrazione.
                </p>
              )}
              <button
                type="button"
                data-testid="bridge-attiva"
                disabled={attivaBusy || !kycVerified}
                onClick={() => attiva()}
                className="text-xs uppercase tracking-widest px-5 py-3 rounded bg-[#0B1E3F] text-white disabled:opacity-40"
              >
                {attivaBusy
                  ? "Attivazione…"
                  : canActivate
                    ? "Attiva gestionale"
                    : kycVerified
                      ? "Attiva (pagamento mancante → conferma)"
                      : "Attiva (prima verifica documenti)"}
              </button>
              {pending && kycVerified && !payOk ? (
                <button
                  type="button"
                  data-testid="bridge-attiva-bypass-pay"
                  disabled={attivaBusy}
                  onClick={() => attiva({ bypassPay: true })}
                  className="block mt-2 text-[10px] uppercase tracking-widest underline text-stone-500"
                >
                  Forza attivazione senza pagamento
                </button>
              ) : null}
            </>
          ) : (
            <div className="flex flex-wrap gap-2">
              <button
                type="button"
                data-testid="bridge-impersonate"
                onClick={openAsCrm}
                className="text-xs uppercase tracking-widest px-4 py-2.5 rounded bg-[#0B1E3F] text-white"
              >
                Apri gestionale
              </button>
              <Link
                to={`${base}/api?q=${encodeURIComponent(a.slug || a.id)}`}
                className="text-xs uppercase tracking-widest px-4 py-2.5 rounded border border-stone-300 bg-white"
              >
                API keys
              </Link>
            </div>
          )}
        </div>
      </section>

      {/* Anagrafica compatta */}
      <section className="grid sm:grid-cols-2 gap-3 text-sm">
        <Card title="Titolare">
          <Row k="Nome" v={owner.name || "—"} />
          <Row k="Email" v={owner.email || "—"} />
          <Row k="Tel" v={owner.phone || a.contact?.phone || "—"} />
        </Card>
        <Card title="Agenzia">
          <Row k="Sito" v={a.contact?.website || "—"} />
          <Row k="Città" v={[a.address?.city, a.address?.province].filter(Boolean).join(" ") || "—"} />
          <Row k="P.IVA" v={a.fiscal?.vat_number || "—"} />
        </Card>
      </section>

      {/* Azioni secondarie */}
      {pending ? (
        <div className="flex flex-wrap gap-2">
          <button
            type="button"
            data-testid="bridge-impersonate"
            onClick={openAsCrm}
            className="text-xs uppercase tracking-widest px-3 py-2 rounded border border-stone-300 bg-white"
          >
            Anteprima CRM
          </button>
          <Link
            to={`${base}/api?q=${encodeURIComponent(a.slug || a.id)}`}
            className="text-xs uppercase tracking-widest px-3 py-2 rounded border border-stone-300 bg-white"
          >
            API
          </Link>
        </div>
      ) : null}

      <div>
        <button
          type="button"
          className="text-[10px] uppercase tracking-widest text-stone-400 underline"
          onClick={() => setShowDanger((v) => !v)}
        >
          {showDanger ? "Nascondi azioni pericolose" : "Azioni pericolose"}
        </button>
        {showDanger ? (
          <div className="mt-3 space-y-3 max-w-xl">
            <p className="text-sm text-stone-600">
              Solo per richieste GDPR o chiusura contratto. Non servono per
              attivare un cliente.
            </p>
            {owner?.id ? (
              <div className="border border-rose-200 rounded-lg px-3 py-3 bg-white space-y-2">
                <button
                  type="button"
                  data-testid="bridge-erase-owner"
                  onClick={async () => {
                    const conf = window.prompt(
                      `Anonimizzare titolare ${owner.email}? Digita CANCELLA_UTENTE`
                    );
                    if (conf !== "CANCELLA_UTENTE") return;
                    try {
                      await api.post(`/app/ops/bridge/users/${owner.id}/erase`, {
                        confirm: "CANCELLA_UTENTE",
                      });
                      setActionMsg("Titolare anonimizzato.");
                      await load();
                    } catch (e) {
                      setActionMsg(e?.response?.data?.detail || "Erase fallito");
                    }
                  }}
                  className="text-xs uppercase tracking-widest px-3 py-2 rounded border border-rose-300 text-rose-800 bg-white"
                >
                  Cancella dati del titolare
                </button>
                <p className="text-xs text-stone-500">
                  In pratica: rende anonima la persona (nome/email) su richiesta
                  privacy. L’agenzia resta, ma il titolare non è più
                  identificabile.
                </p>
              </div>
            ) : null}
            <div className="border border-rose-300 rounded-lg px-3 py-3 bg-rose-50 space-y-2">
              <button
                type="button"
                data-testid="bridge-offboard"
                onClick={offboard}
                className="text-xs uppercase tracking-widest px-3 py-2 rounded border border-rose-400 text-rose-900 bg-white"
              >
                Chiudi agenzia
              </button>
              <p className="text-xs text-stone-600">
                In pratica: spegne il cliente. Cancella immobili/clienti del CRM
                e chiude l’account agenzia. Puoi scegliere se anonimizzare anche
                i collaboratori.
              </p>
            </div>
          </div>
        ) : null}
      </div>

      {/* Dati operativi in fondo, non nel flusso */}
      <details className="border border-stone-200 rounded-lg bg-white">
        <summary className="px-4 py-3 text-xs uppercase tracking-widest text-stone-500 cursor-pointer">
          Dettaglio CRM · membri {data.counts?.members ?? 0} · clienti{" "}
          {data.counts?.clients ?? 0} · immobili {data.counts?.properties ?? 0}
        </summary>
        <div className="px-4 pb-4 space-y-6">
          <SimpleTable
            cols={["Nome", "Email", "Ruolo"]}
            rows={(data.members || []).map((m) => [m.name || "—", m.email, m.role])}
          />
          <SimpleTable
            cols={["Codice", "Nome", "Email"]}
            rows={(data.clients || []).map((c) => [
              c.client_code || "—",
              `${c.name || ""} ${c.surname || ""}`.trim() || "—",
              c.email || "—",
            ])}
          />
          <SimpleTable
            cols={["Rif", "Titolo", "Città"]}
            rows={(data.properties || []).map((p) => [
              p.reference_code || p.id?.slice(0, 8),
              p.title || "—",
              p.city || "—",
            ])}
          />
        </div>
      </details>
    </div>
  );
}

function StatusPill({ ok, warn, label }) {
  const cls = ok
    ? "bg-emerald-100 text-emerald-900 border-emerald-200"
    : warn
      ? "bg-amber-100 text-amber-900 border-amber-200"
      : "bg-stone-100 text-stone-600 border-stone-200";
  return (
    <span
      className={`ml-2 inline-block text-[10px] uppercase tracking-widest px-2 py-0.5 border rounded ${cls}`}
    >
      {label}
    </span>
  );
}

function Card({ title, children }) {
  return (
    <div className="bg-white border border-stone-200 rounded-lg px-4 py-3 space-y-1.5">
      <h3 className="text-[10px] uppercase tracking-widest text-stone-500">{title}</h3>
      {children}
    </div>
  );
}

function Row({ k, v }) {
  return (
    <div className="flex justify-between gap-3 text-sm">
      <span className="text-stone-500">{k}</span>
      <span className="text-stone-900 text-right break-all">{v}</span>
    </div>
  );
}

function SimpleTable({ cols, rows }) {
  if (!rows.length) {
    return <p className="text-sm text-stone-400">Vuoto</p>;
  }
  return (
    <div className="overflow-x-auto border border-stone-100 rounded">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-stone-100 text-left text-[10px] uppercase tracking-widest text-stone-500">
            {cols.map((c) => (
              <th key={c} className="px-2 py-1.5 font-medium">
                {c}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((r, i) => (
            <tr key={i} className="border-b border-stone-50 last:border-0">
              {r.map((cell, j) => (
                <td key={j} className="px-2 py-1.5 text-stone-800">
                  {cell}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
