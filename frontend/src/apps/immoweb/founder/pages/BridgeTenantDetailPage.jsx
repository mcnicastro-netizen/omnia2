import React, { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { api } from "../../../../shared/lib/api";

export default function BridgeTenantDetailPage() {
  const { lang: langParam, agencyId } = useParams();
  const lang = langParam || "it";
  const base = `/${lang}/app/ops`;
  const [data, setData] = useState(null);
  const [err, setErr] = useState(null);
  const [busy, setBusy] = useState(true);
  const [actionMsg, setActionMsg] = useState(null);
  const [kycBusy, setKycBusy] = useState(false);

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

  const attiva = async () => {
    const a0 = data?.agency || {};
    const kycSt = (a0.kyc?.status || "incomplete").toLowerCase();
    const tier = a0.preferred_plan_tier || "pro";
    if (kycSt !== "verified") {
      const force = window.confirm(
        `Dossier KYC non verificato (stato: ${kycSt}).\n` +
          "Per GDPR/identificazione clientela conviene verificare prima.\n\n" +
          "OK = attiva comunque (bypass), Annulla = resta qui."
      );
      if (!force) return;
    } else if (
      !window.confirm(
        `Attivare questa agenzia (wipe CRM + piano ${String(tier).toUpperCase()} + email)?`
      )
    ) {
      return;
    }
    setActionMsg(null);
    try {
      await api.post("/app/ops/activate-agency", {
        agency_id: agencyId,
        grant_plan: true,
        tier,
        credits: 2000,
        send_email: true,
        wipe_crm: true,
        note: "cabina_scheda",
        require_kyc_verified: kycSt === "verified",
      });
      setActionMsg(`Attivata · piano ${String(tier).toUpperCase()}.`);
      await load();
    } catch (e) {
      const d = e?.response?.data?.detail;
      setActionMsg(
        (typeof d === "object" && (d.error || d.hint)) || d || "Attivazione fallita"
      );
    }
  };

  const setKycStatus = async (status) => {
    const notes =
      status === "rejected"
        ? window.prompt("Motivo rifiuto (nota Ops):") || ""
        : window.prompt("Nota Ops (facoltativa):") || "";
    setKycBusy(true);
    setActionMsg(null);
    try {
      await api.patch(`/app/ops/bridge/tenants/${agencyId}/kyc`, { status, notes });
      setActionMsg(`KYC → ${status}`);
      await load();
    } catch (e) {
      setActionMsg(e?.response?.data?.detail || "Aggiornamento KYC fallito");
    } finally {
      setKycBusy(false);
    }
  };

  const uploadKyc = async (docType, file) => {
    if (!file) return;
    setKycBusy(true);
    setActionMsg(null);
    try {
      const fd = new FormData();
      fd.append("file", file, file.name);
      fd.append("doc_type", docType);
      await api.post(`/app/ops/bridge/tenants/${agencyId}/kyc/documents`, fd, {
        timeout: 60000,
      });
      setActionMsg(`Caricato: ${docType}`);
      await load();
    } catch (e) {
      setActionMsg(e?.response?.data?.detail || "Upload KYC fallito");
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
    if (
      !window.confirm(
        "Aprire il gestionale di questa agenzia?\nEntri in modalità vista esplicita; poi «Torna alla cabina»."
      )
    ) {
      return;
    }
    setActionMsg(null);
    try {
      await api.post("/app/ops/bridge/impersonate", { agency_id: agencyId });
      window.location.href = `/${lang}/app/dashboard`;
    } catch (e) {
      setActionMsg(e?.response?.data?.detail || "Impersonation non riuscita");
    }
  };

  const offboard = async () => {
    const conf = window.prompt(
      'Chiudere agenzia (wipe + purge)? Digita CHIUDI_AGENZIA per confermare.'
    );
    if (conf !== "CHIUDI_AGENZIA") return;
    const eraseMembers = window.confirm(
      "Cancellare anche gli account membri (GDPR erase)? OK = sì, Annulla = solo chiusura tenant."
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
      setActionMsg(e?.response?.data?.detail?.error || "Offboard fallito");
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

  return (
    <div data-testid="bridge-tenant-detail" className="space-y-8">
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
          {a.slug} · {a.activation_status || "active"} · piano{" "}
          {a.preferred_plan_tier || a.plan || a.billing_assisted_tier || "—"}
          {a.kyc?.status ? ` · KYC ${a.kyc.status}` : ""}
        </p>
      </div>

      <div className="flex flex-wrap gap-2">
        {(a.activation_status || "active") === "pending" ? (
          <button
            type="button"
            onClick={attiva}
            className="text-xs uppercase tracking-widest px-4 py-2 rounded bg-[#0B1E3F] text-white"
          >
            Attiva
          </button>
        ) : null}
        <button
          type="button"
          data-testid="bridge-impersonate"
          onClick={openAsCrm}
          className="text-xs uppercase tracking-widest px-4 py-2 rounded bg-[#0B1E3F] text-white"
        >
          Apri come CRM
        </button>
        <Link
          to={`${base}/api?q=${encodeURIComponent(a.slug || a.id)}`}
          className="text-xs uppercase tracking-widest px-4 py-2 rounded border border-stone-300 bg-white"
        >
          API di questa agenzia
        </Link>
        {owner?.id ? (
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
            className="text-xs uppercase tracking-widest px-4 py-2 rounded border border-rose-300 text-rose-800 bg-white"
          >
            GDPR titolare
          </button>
        ) : null}
        <button
          type="button"
          data-testid="bridge-offboard"
          onClick={offboard}
          className="text-xs uppercase tracking-widest px-4 py-2 rounded border border-rose-400 text-rose-900 bg-rose-50"
        >
          Chiudi agenzia
        </button>
      </div>
      {actionMsg ? <p className="text-sm text-[#0B1E3F]">{actionMsg}</p> : null}

      <section className="grid md:grid-cols-2 gap-4">
        <Card title="Titolare">
          <Row k="Nome" v={owner.name || "—"} />
          <Row k="Email" v={owner.email || "—"} />
          <Row k="Telefono" v={owner.phone || a.contact?.phone || "—"} />
          <Row k="PEC" v={a.contact?.pec || "—"} />
        </Card>
        <Card title="Contatti agenzia">
          <Row k="Email pubblica" v={a.contact?.email || "—"} />
          <Row k="Sito" v={a.contact?.website || "—"} />
          <Row k="Città" v={[a.address?.city, a.address?.province].filter(Boolean).join(" ") || "—"} />
          <Row k="P.IVA" v={a.fiscal?.vat_number || "—"} />
          <Row k="CF" v={a.fiscal?.fiscal_code || "—"} />
          <Row k="REA" v={a.fiscal?.rea || "—"} />
        </Card>
      </section>

      <section
        data-testid="bridge-kyc"
        className="bg-white border border-stone-200 rounded-lg px-4 py-4 space-y-4"
      >
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <h2 className="text-xs uppercase tracking-widest text-stone-500">
              Identificazione clientela (GDPR)
            </h2>
            <p className="text-sm text-stone-600 mt-1 max-w-2xl">
              Dossier Ops: visura camerale + documento titolare + PEC/P.IVA. Verifica prima di
              Attiva. Ricerca imprese esterna utile come controllo crociato.
            </p>
          </div>
          <span className="text-[10px] uppercase tracking-widest px-2 py-1 border border-stone-300">
            {(a.kyc?.status || "incomplete").toUpperCase()}
          </span>
        </div>
        <div className="grid sm:grid-cols-2 gap-2 text-sm">
          <Row
            k="Visura camerale"
            v={a.kyc?.checklist?.visura_camerale ? "presente" : "manca"}
          />
          <Row
            k="Documento titolare"
            v={a.kyc?.checklist?.id_titolare ? "presente" : "manca"}
          />
          <Row k="PEC" v={a.kyc?.checklist?.pec || a.contact?.pec ? "ok" : "manca"} />
          <Row k="P.IVA" v={a.kyc?.checklist?.piva_ok || a.fiscal?.vat_number ? "ok" : "manca"} />
        </div>
        {a.fiscal?.vat_number ? (
          <p className="text-xs text-stone-500">
            Ricerca imprese:{" "}
            <a
              className="underline text-[#0B1E3F]"
              href={`https://www.registroimprese.it/ricerca-libera?q=${encodeURIComponent(
                a.fiscal.vat_number
              )}`}
              target="_blank"
              rel="noopener noreferrer"
              data-testid="bridge-kyc-registry-link"
            >
              Registro Imprese · P.IVA {a.fiscal.vat_number}
            </a>
          </p>
        ) : null}
        <ul className="divide-y divide-stone-100 border border-stone-100 rounded">
          {(a.kyc?.documents || []).map((d) => (
            <li key={d.id} className="px-3 py-2 flex justify-between gap-3 text-sm">
              <span>
                <span className="text-[10px] uppercase tracking-widest text-stone-500 mr-2">
                  {d.doc_type}
                </span>
                {d.filename}
              </span>
              <button
                type="button"
                className="text-[10px] uppercase tracking-widest text-[#0B1E3F] underline"
                onClick={() => downloadKyc(d.id, d.filename)}
              >
                Scarica
              </button>
            </li>
          ))}
          {(a.kyc?.documents || []).length === 0 ? (
            <li className="px-3 py-2 text-sm text-stone-500">Nessun PDF ancora.</li>
          ) : null}
        </ul>
        <div className="flex flex-wrap gap-3 items-center">
          <label className="text-xs uppercase tracking-widest text-stone-600">
            Carica visura
            <input
              type="file"
              accept="application/pdf,image/*"
              className="block mt-1 text-xs"
              disabled={kycBusy}
              data-testid="bridge-kyc-upload-visura"
              onChange={(e) => {
                uploadKyc("visura_camerale", e.target.files?.[0]);
                e.target.value = "";
              }}
            />
          </label>
          <label className="text-xs uppercase tracking-widest text-stone-600">
            Carica CI titolare
            <input
              type="file"
              accept="application/pdf,image/*"
              className="block mt-1 text-xs"
              disabled={kycBusy}
              data-testid="bridge-kyc-upload-id"
              onChange={(e) => {
                uploadKyc("documento_identita", e.target.files?.[0]);
                e.target.value = "";
              }}
            />
          </label>
          <button
            type="button"
            disabled={kycBusy}
            className="text-xs uppercase tracking-widest px-3 py-2 rounded bg-emerald-800 text-white"
            data-testid="bridge-kyc-verify"
            onClick={() => setKycStatus("verified")}
          >
            Segna verificato
          </button>
          <button
            type="button"
            disabled={kycBusy}
            className="text-xs uppercase tracking-widest px-3 py-2 rounded border border-rose-300 text-rose-800"
            onClick={() => setKycStatus("rejected")}
          >
            Rifiuta
          </button>
        </div>
        {a.kyc?.notes ? (
          <p className="text-xs text-stone-500">Nota: {a.kyc.notes}</p>
        ) : null}
      </section>

      <section>
        <h2 className="text-xs uppercase tracking-widest text-stone-500 mb-3">
          Membri ({data.counts?.members ?? 0})
        </h2>
        <SimpleTable
          cols={["Nome", "Email", "Ruolo"]}
          rows={(data.members || []).map((m) => [m.name || "—", m.email, m.role])}
        />
      </section>

      <section>
        <h2 className="text-xs uppercase tracking-widest text-stone-500 mb-3">
          Clienti CRM ({data.counts?.clients ?? 0})
        </h2>
        <SimpleTable
          cols={["Codice", "Nome", "Email", "Tipo", "Stato"]}
          rows={(data.clients || []).map((c) => [
            c.client_code || "—",
            `${c.name || ""} ${c.surname || ""}`.trim() || "—",
            c.email || "—",
            c.client_type,
            c.status,
          ])}
        />
      </section>

      <section>
        <h2 className="text-xs uppercase tracking-widest text-stone-500 mb-3">
          Immobili ({data.counts?.properties ?? 0})
        </h2>
        <SimpleTable
          cols={["Rif", "Titolo", "Città", "Stato"]}
          rows={(data.properties || []).map((p) => [
            p.reference_code || p.id?.slice(0, 8),
            p.title || "—",
            p.city || "—",
            p.status,
          ])}
        />
      </section>

      <section>
        <h2 className="text-xs uppercase tracking-widest text-stone-500 mb-3">
          API keys ({data.counts?.api_keys ?? 0})
        </h2>
        <SimpleTable
          cols={["Nome", "Prefisso", "Attiva", "Crediti"]}
          rows={(data.api_keys || []).map((k) => [
            k.name,
            k.key_prefix,
            k.is_active ? "sì" : "no",
            k.credits_balance ?? "—",
          ])}
        />
      </section>
    </div>
  );
}

function Card({ title, children }) {
  return (
    <div className="bg-white border border-stone-200 rounded-lg px-4 py-4 space-y-2">
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
    return (
      <p className="text-sm text-stone-500 border border-dashed border-stone-300 rounded-lg px-3 py-6 text-center">
        Vuoto
      </p>
    );
  }
  return (
    <div className="overflow-x-auto border border-stone-200 rounded-lg bg-white">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-stone-200 text-left text-[10px] uppercase tracking-widest text-stone-500">
            {cols.map((c) => (
              <th key={c} className="px-3 py-2 font-medium">
                {c}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((r, i) => (
            <tr key={i} className="border-b border-stone-100 last:border-0">
              {r.map((cell, j) => (
                <td key={j} className="px-3 py-2 text-stone-800">
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
