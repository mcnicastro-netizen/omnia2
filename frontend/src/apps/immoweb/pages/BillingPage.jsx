import { useCallback, useEffect, useState } from "react";
import { useLocation } from "react-router-dom";
import { api } from "@/shared/lib/api";
import { useAuth } from "@/shared/lib/auth";
import AgencyShell from "@/apps/immoweb/components/AgencyShell";
import { Button } from "@/components/ui/button";
import { toast } from "sonner";

/**
 * OMNIA — Settings ▸ Billing (M4.S3/S4) + D-085 storage meter
 *
 * D-080: demo guidata prima dell'abbonamento.
 * D-110: localStorage ≠ entitlement — "Piano attivo" solo da subscription server-side.
 * Demo confirm resta UX in-memory (sessione), non simula piano pagato.
 * D-193: Main Admin — allocate/revoke sul wallet centrale CommercialCustomer.
 */
function newIdempotencyKey(prefix) {
  if (typeof crypto !== "undefined" && crypto.randomUUID) {
    return `${prefix}-${crypto.randomUUID()}`;
  }
  return `${prefix}-${Date.now()}-${Math.random().toString(36).slice(2, 10)}`;
}

export default function BillingPage() {
  const { user } = useAuth();
  const [state, setState] = useState({ loading: true, data: null, sub: null });
  const [storage, setStorage] = useState(null);
  const [billingCycle, setBillingCycle] = useState("monthly");
  const [busy, setBusy] = useState(false);
  // D-110 — non leggere/scrivere entitlement da localStorage
  const [demoRequested, setDemoRequested] = useState(false);
  const location = useLocation();

  // D-193 wallet centrale (Main Admin only for mutate; Branch vede solo org)
  const [centralWallet, setCentralWallet] = useState(null);
  const [orgWallet, setOrgWallet] = useState(null);
  const [isMainAdmin, setIsMainAdmin] = useState(false);
  const [walletBusy, setWalletBusy] = useState(false);
  const [allocOrgId, setAllocOrgId] = useState("");
  const [allocAmount, setAllocAmount] = useState("");
  const [walletMsg, setWalletMsg] = useState(null);

  const role = user?.role || "";
  const canTryCentralWallet =
    role === "agency_admin" || role === "group_admin" || role === "super_admin";
  const canSeeOrgWallet =
    role === "agency_admin" ||
    role === "group_admin" ||
    role === "branch_admin" ||
    role === "agent" ||
    role === "super_admin";

  const refreshWalletPanels = useCallback(async () => {
    setWalletMsg(null);
    if (canTryCentralWallet) {
      try {
        const { data: ma } = await api.get("/billing/commercial/main-admin");
        // 200 from this endpoint already means Main Admin binding or Super Admin ops.
        const main =
          Boolean(ma?.is_main_admin) ||
          Boolean(ma?.is_ops_super_admin) ||
          role === "super_admin" ||
          Boolean(ma?.commercial_customer_id);
        setIsMainAdmin(main);
        if (main) {
          const { data: w } = await api.get("/billing/wallet");
          setCentralWallet(w);
          const orgs = w?.organizations || [];
          if (orgs.length) {
            setAllocOrgId((prev) => prev || orgs[0].id || "");
          }
        } else {
          setCentralWallet(null);
        }
      } catch (err) {
        // Branch / non-Main Admin: 403 atteso sul wallet centrale
        setIsMainAdmin(false);
        setCentralWallet(null);
        if (err?.response?.status && err.response.status !== 403) {
          console.error(err);
        }
      }
    }
    if (canSeeOrgWallet) {
      try {
        const { data: ow } = await api.get("/billing/wallet/organization");
        setOrgWallet(ow);
      } catch (err) {
        setOrgWallet(null);
        if (err?.response?.status && err.response.status !== 403) {
          console.error(err);
        }
      }
    }
  }, [canTryCentralWallet, canSeeOrgWallet, role]);

  useEffect(() => {
    (async () => {
      try {
        const [{ data: plans }, { data: sub }] = await Promise.all([
          api.get("/billing/plans"),
          api.get("/billing/subscription"),
        ]);
        setState({ loading: false, data: plans, sub });
      } catch (e) {
        console.error(e);
        setState({ loading: false, data: null, sub: null });
      }
      try {
        const { data: st } = await api.get("/app/storage/usage");
        setStorage(st);
      } catch (err) {
        console.error(err);
      }
    })();
  }, []);

  useEffect(() => {
    if (state.loading) return;
    refreshWalletPanels();
  }, [state.loading, refreshWalletPanels]);

  // Piano scelto dalla vetrina (/register?plan=…) — evidenzia la card Billing
  useEffect(() => {
    if (state.loading) return;
    let preferred = "";
    try {
      preferred = (sessionStorage.getItem("omnia_preferred_plan") || "").toLowerCase();
    } catch {
      preferred = "";
    }
    if (!preferred) return;
    const el = document.querySelector(`[data-testid="plan-card-${preferred}"]`);
    if (!el) return;
    el.classList.add("ring-2", "ring-[#C8A653]");
    el.scrollIntoView({ behavior: "smooth", block: "center" });
  }, [state.loading, state.data]);

  useEffect(() => {
    const params = new URLSearchParams(location.search);
    const sessionId = params.get("session_id");
    if (!sessionId) return;
    let cancel = false;
    let tries = 0;
    const poll = async () => {
      if (cancel || tries > 15) return;
      tries += 1;
      try {
        const { data } = await api.get(`/billing/status/${sessionId}`);
        if (data.payment_status === "paid") {
          toast.success("Pagamento completato ✓");
          const [{ data: sub }] = await Promise.all([
            api.get("/billing/subscription"),
          ]);
          setState((s) => ({ ...s, sub }));
          try {
            const { data: st } = await api.get("/app/storage/usage");
            setStorage(st);
          } catch (_) { /* noop */ }
        } else if (data.payment_status === "failed") {
          toast.error("Pagamento fallito — controlla la carta o contattaci.");
        } else {
          setTimeout(poll, 2000);
        }
      } catch (e) {
        if (!cancel) setTimeout(poll, 2500);
      }
    };
    poll();
    return () => { cancel = true; };
  }, [location.search]);

  const openDemo = () => {
    const email = (state.data?.demo_contact_email || "[REDACTED]").trim();
    const subject = encodeURIComponent("Richiesta demo guidata OMNIA");
    const body = encodeURIComponent(
      "Ciao Marco,\n\nvorrei prenotare una demo guidata di OMNIA per la mia agenzia.\n\nAgenzia:\nCittà:\nTelefono:\n"
    );
    window.location.href = `mailto:${email}?subject=${subject}&body=${body}`;
    setDemoRequested(true);
    toast.success("Richiesta demo aperta — l'attivazione piano resta lato server dopo provisioning.");
  };

  const checkoutSubscription = async (tier) => {
    if (!state.data?.enabled || !state.data?.self_serve_enabled) {
      toast.message(
        state.data?.enabled
          ? "Attivazione assistita: contattaci per completare l’acquisto."
          : "Checkout non disponibile — contattaci per provisioning assistito."
      );
      openDemo();
      return;
    }
    if (!demoRequested && !state.sub?.subscription) {
      const ok = window.confirm(
        "L'abbonamento si attiva dopo la demo guidata.\n\nHai già fatto la demo con OMNIA?"
      );
      if (!ok) {
        openDemo();
        return;
      }
      setDemoRequested(true);
    }
    setBusy(true);
    try {
      const { data } = await api.post("/billing/checkout", {
        plan_tier: tier,
        billing_cycle: billingCycle,
        success_url: window.location.origin,
        cancel_url: window.location.origin + window.location.pathname + "?cancel=1",
      });
      window.location.href = data.checkout_url;
    } catch (e) {
      const msg = e?.response?.data?.detail?.message || e?.response?.data?.detail || "Errore checkout";
      toast.error(typeof msg === "string" ? msg : "Errore checkout");
      setBusy(false);
    }
  };

  const h4PurchaseReady = state.data?.h4_purchase_ready === true;

  const resolveCommercialCustomerId = async () => {
    const fromSub = state.sub?.commercial_customer?.id;
    if (fromSub) return fromSub;
    try {
      const { data } = await api.get("/billing/purchase-context");
      const list = data?.commercial_customers || [];
      if (list.length === 1) return list[0].id;
      if (list.length > 1) {
        toast.message("Seleziona il CommercialCustomer (più di uno nominato).");
        return null;
      }
    } catch (err) {
      console.error(err);
    }
    toast.message("CommercialCustomer richiesto per l'acquisto (Main Admin).");
    return null;
  };

  const checkoutCredits = async (packageKey) => {
    if (!h4PurchaseReady) {
      toast.message(
        "Acquisto crediti non ancora disponibile (H4 in preparazione). Contattaci per assistenza."
      );
      return;
    }
    if (!state.data?.self_serve_enabled) {
      toast.message("Attivazione assistita: contattaci per completare l'acquisto.");
      openDemo();
      return;
    }
    const commercialCustomerId = await resolveCommercialCustomerId();
    if (!commercialCustomerId) return;
    setBusy(true);
    try {
      const { data } = await api.post("/billing/credits/purchase", {
        package_key: packageKey,
        commercial_customer_id: commercialCustomerId,
        success_url: window.location.origin,
        cancel_url: window.location.origin + window.location.pathname + "?cancel=1",
      });
      window.location.href = data.checkout_url;
    } catch (e) {
      const d = e?.response?.data?.detail;
      const code = typeof d === "object" ? d?.error || d?.code : null;
      if (code === "h4_not_ready" || e?.response?.status === 503) {
        toast.message(d?.message || "Acquisto crediti bloccato (H4 non pronto).");
      } else if (code === "sa_purchase_forbidden" || code === "not_main_admin") {
        toast.error(d?.message || "Solo il Main Admin può acquistare crediti.");
      } else {
        toast.error(typeof d === "string" ? d : d?.message || "Errore checkout crediti");
      }
      setBusy(false);
    }
  };

  const buyStorage = async () => {
    if (!h4PurchaseReady) {
      toast.message(
        "Acquisto storage non ancora disponibile (H4 in preparazione). Contattaci per assistenza."
      );
      return;
    }
    if (!state.data?.self_serve_enabled) {
      toast.message("Attivazione assistita: contattaci per completare l'acquisto.");
      openDemo();
      return;
    }
    const commercialCustomerId = await resolveCommercialCustomerId();
    if (!commercialCustomerId) return;
    setBusy(true);
    try {
      const { data } = await api.post("/billing/storage/purchase", {
        commercial_customer_id: commercialCustomerId,
        package_key: "storage_100gb",
      });
      if (data.checkout_url) {
        window.location.href = data.checkout_url;
        return;
      }
      if (data.stripe_required || data.self_serve_blocked) {
        const email = data.demo_contact_email || "[REDACTED]";
        const subject = encodeURIComponent("OMNIA — spazio archivio extra +100 GB");
        const body = encodeURIComponent(
          `Ciao,\n\nvorrei aggiungere ${data.addon?.gb || 100} GB di archivio (€${data.addon?.price_eur || 15}/mese) alla mia agenzia.\n\nAgenzia / email account:\n`
        );
        window.location.href = `mailto:${email}?subject=${subject}&body=${body}`;
        toast.message(data.message || "Contatta il supporto per aggiungere spazio.");
      }
    } catch (e) {
      const d = e?.response?.data?.detail;
      const code = typeof d === "object" ? d?.error || d?.code : null;
      if (code === "h4_not_ready" || e?.response?.status === 503) {
        toast.message(d?.message || "Acquisto storage bloccato (H4 non pronto).");
      } else if (code === "sa_purchase_forbidden" || code === "not_main_admin") {
        toast.error(d?.message || "Solo il Main Admin può acquistare storage.");
      } else {
        toast.error(typeof d === "string" ? d : d?.message || "Errore acquisto spazio");
      }
    } finally {
      setBusy(false);
    }
  };

  const openPortal = async () => {
    setBusy(true);
    try {
      const { data } = await api.post("/billing/portal");
      window.location.href = data.portal_url;
    } catch (e) {
      toast.error("Portal non disponibile");
      setBusy(false);
    }
  };

  const walletErrorMessage = (e) => {
    const d = e?.response?.data?.detail;
    if (typeof d === "string") return d;
    if (d && typeof d === "object") {
      return d.message || d.error || JSON.stringify(d);
    }
    return e?.message || "Operazione wallet non riuscita";
  };

  const allocateCredits = async () => {
    const amount = parseInt(String(allocAmount), 10);
    if (!allocOrgId || !Number.isFinite(amount) || amount <= 0) {
      toast.error("Seleziona filiale e quantità positiva.");
      return;
    }
    setWalletBusy(true);
    setWalletMsg(null);
    try {
      const key = newIdempotencyKey("alloc");
      const { data } = await api.post(
        "/billing/wallet/allocate",
        {
          organization_id: allocOrgId,
          amount,
          commercial_customer_id: centralWallet?.commercial_customer_id,
        },
        { headers: { "Idempotency-Key": key } }
      );
      const n = (data?.allocations || []).length;
      toast.success(`Allocati ${amount} crediti (${n} lotto/i).`);
      setWalletMsg({ type: "ok", text: `Allocazione completata · chiave ${key.slice(0, 18)}…` });
      setAllocAmount("");
      await refreshWalletPanels();
    } catch (e) {
      const msg = walletErrorMessage(e);
      toast.error(msg);
      setWalletMsg({ type: "err", text: msg });
    } finally {
      setWalletBusy(false);
    }
  };

  const revokeAllocation = async (allocationId) => {
    if (!allocationId) return;
    if (!window.confirm("Revocare i crediti non consumati di questa allocazione?")) return;
    setWalletBusy(true);
    setWalletMsg(null);
    try {
      const key = newIdempotencyKey("rev");
      await api.post(
        "/billing/wallet/revoke",
        {
          allocation_id: allocationId,
          commercial_customer_id: centralWallet?.commercial_customer_id,
        },
        { headers: { "Idempotency-Key": key } }
      );
      toast.success("Allocazione revocata — crediti tornati al wallet centrale.");
      setWalletMsg({ type: "ok", text: "Revoca completata." });
      await refreshWalletPanels();
    } catch (e) {
      const msg = walletErrorMessage(e);
      toast.error(msg);
      setWalletMsg({ type: "err", text: msg });
    } finally {
      setWalletBusy(false);
    }
  };

  if (state.loading) {
    return (
      <AgencyShell current="settings">
        <div className="p-6 text-stone-500" data-testid="billing-loading">Caricamento…</div>
      </AgencyShell>
    );
  }

  const { data, sub } = state;
  const activeSub = sub?.subscription;
  const wallet = sub?.wallet || { balance: 0 };
  const counters = sub?.counters || {};
  const subCounter = counters.sub || {};
  const creditsCounter = counters.credits || {};
  const demo = sub?.demo;
  const plans = data?.plans || [];
  const packages = data?.credit_packages || [];
  // D-110 + S5 — Stripe sandbox ≠ self-serve O6
  const stripeEnabled = Boolean(data?.enabled);
  const selfServeEnabled = Boolean(data?.self_serve_enabled);
  const canCheckoutDirect =
    stripeEnabled && selfServeEnabled && (Boolean(activeSub) || demoRequested || demo?.expired);

  return (
    <AgencyShell current="settings">
      <div className="p-6 md:p-10 max-w-6xl" data-testid="billing-page">
        <h1 className="font-serif text-4xl text-[#0B1E3F] mb-1">Piano & Crediti</h1>
        <p className="text-stone-500 mb-6 text-sm">
          Attivazione dopo <strong className="font-medium text-stone-600">demo guidata</strong> —
          niente prova automatica, niente sorprese.
          {data?.mode === "test" && (
            <span className="ml-2 inline-block px-2 py-0.5 text-xs bg-amber-100 text-amber-800">MODALITÀ TEST</span>
          )}
        </p>

        {/* S7 — sandbox time-boxed → Acquista */}
        {demo?.is_demo_story && (
          <div
            className={`mb-8 border p-5 flex flex-col md:flex-row md:items-center gap-4 ${
              demo.expired
                ? "border-rose-300 bg-rose-50"
                : "border-amber-300/60 bg-amber-50/80"
            }`}
            data-testid="demo-sandbox-banner"
          >
            <div className="flex-1">
              <div className="text-xs uppercase tracking-widest text-stone-500 mb-1">
                {demo.expired ? "Prova scaduta" : "Periodo di prova"}
              </div>
              <div className="font-serif text-xl text-[#0B1E3F]" data-testid="demo-sandbox-title">
                {demo.expired
                  ? "Acquista pacchetto"
                  : `${demo.days_remaining} giorno/i rimanenti`}
              </div>
              <p className="text-sm text-stone-600 mt-1" data-testid="demo-sandbox-msg">
                {demo.message}
              </p>
            </div>
            {demo.expired && (
              <Button
                className="bg-[#0B1E3F] hover:bg-[#16305a] text-white shrink-0"
                onClick={() => {
                  if (canCheckoutDirect && plans[0]) {
                    checkoutSubscription(plans[0].tier);
                  } else {
                    toast.message(
                      selfServeEnabled
                        ? "Scegli un piano sotto per acquistare."
                        : "Attivazione assistita. Contattaci per attivare il piano."
                    );
                    if (!selfServeEnabled) openDemo();
                  }
                }}
                data-testid="demo-acquista-cta"
              >
                Acquista pacchetto
              </Button>
            )}
          </div>
        )}

        {!activeSub && !demo?.is_demo_story && (
          <div className="mb-8 border border-[#0F6B5B]/30 bg-[#0F6B5B]/5 p-5 flex flex-col md:flex-row md:items-center gap-4">
            <div className="flex-1">
              <div className="text-xs uppercase tracking-widest text-[#0F6B5B] mb-1">Passo 1</div>
              <div className="font-serif text-xl text-[#0B1E3F]">Richiedi una demo guidata</div>
              <p className="text-sm text-stone-600 mt-1">
                Ti mostriamo OMNIA sulla tua agenzia. Poi, se ti convince, attivi il piano da qui.
              </p>
            </div>
            <Button
              className="bg-[#0F6B5B] hover:bg-[#0B4F42] text-white shrink-0"
              onClick={openDemo}
              data-testid="request-demo-btn"
            >
              Richiedi demo
            </Button>
          </div>
        )}

        {subCounter.renewal_due_soon || subCounter.past_due ? (
          <div
            className={`mb-6 border p-4 text-sm ${
              subCounter.past_due
                ? "border-rose-300 bg-rose-50 text-rose-900"
                : "border-amber-300 bg-amber-50 text-amber-950"
            }`}
            data-testid="billing-renewal-banner"
          >
            {subCounter.past_due
              ? "Pagamento abbonamento in ritardo — aggiorna il metodo di pagamento."
              : `Rinnovo tra ${subCounter.days_left} giorni (scade ${String(
                  subCounter.current_period_end || ""
                ).slice(0, 10)}).`}
          </div>
        ) : null}
        {creditsCounter.low ? (
          <div
            className="mb-6 border border-amber-300 bg-amber-50 text-amber-950 p-4 text-sm"
            data-testid="billing-credits-low-banner"
          >
            Crediti pacchetto bassi ({creditsCounter.balance} &lt; soglia {creditsCounter.low_threshold}).
            Ricarica sotto per non interrompere gli strumenti AI.
          </div>
        ) : null}

        <div className="grid md:grid-cols-3 gap-4 mb-10">
          <div className="border border-stone-200 bg-white p-6">
            <div className="text-xs uppercase tracking-widest text-stone-500 mb-1">Piano attuale</div>
            <div className="text-2xl font-serif text-[#0B1E3F]" data-testid="current-plan">
              {activeSub ? activeSub.tier?.toUpperCase() : "Nessuno"}
            </div>
            <div className="text-sm text-stone-500 mt-1" data-testid="current-plan-status">
              {activeSub ? `Status: ${activeSub.status}` : "Dopo la demo puoi attivare un piano"}
            </div>
            {activeSub && subCounter.current_period_end ? (
              <div className="text-sm text-[#0B1E3F] mt-2" data-testid="current-plan-period">
                Scade / rinnova: {String(subCounter.current_period_end).slice(0, 10)}
                {subCounter.days_left != null ? ` · ${subCounter.days_left} giorni` : ""}
              </div>
            ) : null}
            {activeSub && (
              <Button
                variant="outline" size="sm"
                className="mt-4"
                onClick={openPortal}
                disabled={busy}
                data-testid="open-billing-portal-btn"
              >
                Gestisci abbonamento
              </Button>
            )}
          </div>
          <div className="border border-stone-200 bg-white p-6">
            <div className="text-xs uppercase tracking-widest text-stone-500 mb-1">
              Crediti pacchetto
            </div>
            <div className="text-2xl font-serif text-[#0F6B5B]" data-testid="wallet-balance">
              {wallet.balance || 0} crediti
            </div>
            <div className="text-sm text-stone-500 mt-1">
              Staging, video, HAL Legal, ecc. (soglia alert automatico:{" "}
              {creditsCounter.low_threshold ?? "—"})
            </div>
          </div>
          <div
            className={`border bg-white p-6 ${
              storage?.full ? "border-rose-300" : storage?.warn_80 ? "border-amber-300" : "border-stone-200"
            }`}
            data-testid="storage-meter"
          >
            <div className="text-xs uppercase tracking-widest text-stone-500 mb-1">Spazio archivio</div>
            <div className="text-2xl font-serif text-[#0B1E3F]">
              {storage ? `${storage.used_gb} / ${storage.quota_gb} GB` : "—"}
            </div>
            <div className="mt-3 h-2 w-full bg-stone-100 rounded overflow-hidden">
              <div
                className={`h-full ${
                  storage?.full ? "bg-rose-600" : storage?.warn_90 ? "bg-amber-500" : storage?.warn_80 ? "bg-amber-400" : "bg-emerald-700"
                }`}
                style={{ width: `${Math.min(100, storage?.percent_used || 0)}%` }}
              />
            </div>
            <p className="text-sm text-stone-500 mt-2">
              Foto, documenti e video. Backup automatico incluso (30 giorni).
            </p>
            {storage?.full && (
              <p className="text-sm text-rose-700 mt-2" data-testid="storage-full-msg">
                Spazio esaurito: non puoi caricare nuovi file finché non liberi spazio o aggiungi GB.
              </p>
            )}
            <Button
              className="mt-4 bg-[#0B1E3F] hover:bg-stone-800 text-white"
              size="sm"
              onClick={buyStorage}
              disabled={busy || !h4PurchaseReady}
              data-testid="buy-storage-btn"
            >
              Aggiungi 100 GB (€15/mese)
            </Button>
          </div>
        </div>

        <div className="mb-4 flex items-center gap-3">
          <h2 className="font-serif text-2xl text-[#0B1E3F]">Piani abbonamento</h2>
          <div className="ml-auto flex items-center gap-2 text-sm">
            <button
              className={`px-3 py-1 border ${billingCycle === "monthly" ? "bg-[#0B1E3F] text-white" : "bg-white text-stone-600"}`}
              onClick={() => setBillingCycle("monthly")}
              data-testid="cycle-monthly-btn"
            >Mensile</button>
            <button
              className={`px-3 py-1 border ${billingCycle === "yearly" ? "bg-[#0B1E3F] text-white" : "bg-white text-stone-600"}`}
              onClick={() => setBillingCycle("yearly")}
              data-testid="cycle-yearly-btn"
            >Annuale <span className="text-[#C69F4C] text-xs ml-1">−1 mese</span></button>
          </div>
        </div>
        <div className="grid md:grid-cols-3 gap-4 mb-12">
          {plans.map((p) => (
            <div key={p.tier} className="border border-stone-200 bg-white p-5 flex flex-col" data-testid={`plan-card-${p.tier}`}>
              <div className="text-xs uppercase tracking-widest text-stone-500">{p.tier}</div>
              <div className="font-serif text-xl text-[#0B1E3F] mt-1">{p.name}</div>
              <div className="text-3xl font-serif text-[#0B1E3F] mt-3">
                €{billingCycle === "monthly" ? p.price_monthly : Math.round(p.price_yearly / 12)}
                <span className="text-sm text-stone-500">/mese</span>
              </div>
              {billingCycle === "yearly" && (
                <div className="text-xs text-stone-400 mt-1">fatturato €{p.price_yearly}/anno</div>
              )}
              <ul className="text-sm text-stone-600 mt-4 space-y-1 flex-1">
                <li>{p.max_agents === -1 ? "Agenti illimitati" : `${p.max_agents} agenti`}</li>
                <li>{p.max_properties === -1 ? "Immobili illimitati" : `${p.max_properties} immobili`}</li>
                <li>
                  {p.credits_included_monthly
                    ? `${p.credits_included_monthly.toLocaleString("it-IT")} crediti/mese inclusi`
                    : "Crediti a consumo"}
                </li>
              </ul>
              {activeSub?.tier === p.tier ? (
                <Button className="mt-5" disabled data-testid={`checkout-${p.tier}-btn`}>
                  Piano attivo
                </Button>
              ) : !stripeEnabled ? (
                <Button
                  className="mt-5 bg-[#0B1E3F] hover:bg-[#16305a] text-white"
                  onClick={openDemo}
                  data-testid={`checkout-${p.tier}-btn`}
                >
                  Richiedi attivazione
                </Button>
              ) : canCheckoutDirect ? (
                <Button
                  className="mt-5 bg-[#0F6B5B] hover:bg-[#0B4F42] text-white"
                  onClick={() => checkoutSubscription(p.tier)}
                  disabled={busy}
                  data-testid={`checkout-${p.tier}-btn`}
                >
                  {demo?.expired ? "Acquista" : "Attiva"}
                </Button>
              ) : (
                <Button
                  className="mt-5 bg-[#0B1E3F] hover:bg-[#16305a] text-white"
                  onClick={() => {
                    if (demo?.expired && !selfServeEnabled) {
                      toast.message(
                        "Attivazione assistita: contattaci dopo aver scelto il piano."
                      );
                    }
                    openDemo();
                  }}
                  data-testid={`checkout-${p.tier}-btn`}
                >
                  {demo?.expired ? "Acquista pacchetto" : "Prima la demo"}
                </Button>
              )}
            </div>
          ))}
        </div>

        <h2 className="font-serif text-2xl text-[#0B1E3F] mb-4">Ricarica crediti</h2>
        <p className="text-sm text-stone-500 mb-4">
          L&apos;acquisto accredita il wallet centrale CommercialCustomer. L&apos;assegnazione alle
          filiali è un passo successivo del Main Admin (nessuna auto-allocazione).
        </p>
        <div className="grid md:grid-cols-3 gap-4 mb-12">
          {packages.map((pkg) => (
            <div key={pkg.key} className="border border-stone-200 bg-white p-5" data-testid={`pack-card-${pkg.key}`}>
              <div className="font-serif text-2xl text-[#0B1E3F]">{pkg.credits} crediti</div>
              <div className="text-3xl font-serif text-[#C69F4C] my-2">€{pkg.price_eur}</div>
              <Button
                variant="outline"
                className="w-full mt-2"
                onClick={() => checkoutCredits(pkg.key)}
                disabled={busy || !h4PurchaseReady}
                data-testid={`buy-pack-${pkg.key}-btn`}
              >
                Acquista
              </Button>
            </div>
          ))}
        </div>

        {/* D-193 — disponibilità organizzazione (tutti i ruoli CRM con org) */}
        {orgWallet && !isMainAdmin && (
          <div
            className="mb-12 border border-stone-200 bg-white p-6"
            data-testid="org-wallet-panel"
          >
            <h2 className="font-serif text-2xl text-[#0B1E3F] mb-1">Crediti disponibili</h2>
            <p className="text-sm text-stone-500 mb-4">
              Saldo spendibile della tua organizzazione (assegnato dal Main Admin).
            </p>
            <div className="text-3xl font-serif text-[#0F6B5B]" data-testid="org-spendable">
              {orgWallet.spendable ?? 0} crediti
            </div>
          </div>
        )}

        {/* D-193 — wallet centrale + allocate/revoke (solo Main Admin / Super Admin) */}
        {isMainAdmin && centralWallet && (
          <div
            className="mb-12 border border-[#0B1E3F]/15 bg-white p-6"
            data-testid="central-wallet-panel"
          >
            <h2 className="font-serif text-2xl text-[#0B1E3F] mb-1">
              Wallet centrale CommercialCustomer
            </h2>
            <p className="text-sm text-stone-500 mb-6">
              Solo Main Admin: consulta il saldo centrale, alloca alle filiali e revoca crediti non
              consumati. Nessun trasferimento tra P.IVA diverse.
            </p>

            <div className="grid md:grid-cols-3 gap-4 mb-8">
              <div className="border border-stone-200 p-4">
                <div className="text-xs uppercase tracking-widest text-stone-500">Totale</div>
                <div className="text-2xl font-serif text-[#0B1E3F]" data-testid="cc-balance-total">
                  {centralWallet.balance_total ?? 0}
                </div>
              </div>
              <div className="border border-stone-200 p-4">
                <div className="text-xs uppercase tracking-widest text-stone-500">Non allocati</div>
                <div
                  className="text-2xl font-serif text-[#0F6B5B]"
                  data-testid="cc-balance-unallocated"
                >
                  {centralWallet.balance_unallocated ?? 0}
                </div>
              </div>
              <div className="border border-stone-200 p-4">
                <div className="text-xs uppercase tracking-widest text-stone-500">Filiali</div>
                <div className="text-2xl font-serif text-[#0B1E3F]">
                  {(centralWallet.organizations || []).length}
                </div>
              </div>
            </div>

            <h3 className="font-serif text-lg text-[#0B1E3F] mb-3">Disponibilità per filiale</h3>
            <div className="overflow-x-auto mb-8" data-testid="cc-org-balances">
              <table className="w-full text-sm text-left">
                <thead>
                  <tr className="border-b border-stone-200 text-stone-500">
                    <th className="py-2 pr-4 font-medium">Organizzazione</th>
                    <th className="py-2 font-medium">Spendibile</th>
                  </tr>
                </thead>
                <tbody>
                  {(centralWallet.organizations || []).map((o) => (
                    <tr key={o.id} className="border-b border-stone-100">
                      <td className="py-2 pr-4">
                        {o.display_name || o.name || o.slug || o.id}
                      </td>
                      <td className="py-2 font-medium text-[#0F6B5B]">{o.spendable ?? 0}</td>
                    </tr>
                  ))}
                  {!(centralWallet.organizations || []).length && (
                    <tr>
                      <td colSpan={2} className="py-3 text-stone-400">
                        Nessuna organizzazione collegata.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>

            <h3 className="font-serif text-lg text-[#0B1E3F] mb-3">Alloca crediti</h3>
            <div className="flex flex-col md:flex-row gap-3 mb-8 items-stretch md:items-end">
              <label className="flex-1 text-sm">
                <span className="text-stone-500 block mb-1">Filiale</span>
                <select
                  className="w-full border border-stone-300 bg-white px-3 py-2"
                  value={allocOrgId}
                  onChange={(e) => setAllocOrgId(e.target.value)}
                  data-testid="allocate-org-select"
                >
                  {(centralWallet.organizations || []).map((o) => (
                    <option key={o.id} value={o.id}>
                      {o.display_name || o.name || o.slug || o.id}
                    </option>
                  ))}
                </select>
              </label>
              <label className="w-full md:w-40 text-sm">
                <span className="text-stone-500 block mb-1">Quantità</span>
                <input
                  type="number"
                  min={1}
                  className="w-full border border-stone-300 bg-white px-3 py-2"
                  value={allocAmount}
                  onChange={(e) => setAllocAmount(e.target.value)}
                  data-testid="allocate-amount-input"
                />
              </label>
              <Button
                className="bg-[#0F6B5B] hover:bg-[#0B4F42] text-white"
                onClick={allocateCredits}
                disabled={walletBusy || !(centralWallet.balance_unallocated > 0)}
                data-testid="allocate-submit-btn"
              >
                Alloca
              </Button>
            </div>

            <h3 className="font-serif text-lg text-[#0B1E3F] mb-3">Allocazioni attive</h3>
            <div className="overflow-x-auto mb-4" data-testid="cc-allocations-table">
              <table className="w-full text-sm text-left">
                <thead>
                  <tr className="border-b border-stone-200 text-stone-500">
                    <th className="py-2 pr-4 font-medium">Filiale</th>
                    <th className="py-2 pr-4 font-medium">Rimanenti</th>
                    <th className="py-2 font-medium">Azione</th>
                  </tr>
                </thead>
                <tbody>
                  {(centralWallet.allocations || [])
                    .filter((a) => (a.remaining_qty || 0) > 0)
                    .map((a) => {
                      const org = (centralWallet.organizations || []).find(
                        (o) => o.id === a.organization_id
                      );
                      return (
                        <tr key={a.id} className="border-b border-stone-100">
                          <td className="py-2 pr-4">
                            {org?.display_name || org?.name || a.organization_id}
                          </td>
                          <td className="py-2 pr-4">{a.remaining_qty}</td>
                          <td className="py-2">
                            <Button
                              variant="outline"
                              size="sm"
                              disabled={walletBusy}
                              onClick={() => revokeAllocation(a.id)}
                              data-testid={`revoke-alloc-${a.id}`}
                            >
                              Revoca
                            </Button>
                          </td>
                        </tr>
                      );
                    })}
                  {!(centralWallet.allocations || []).some((a) => (a.remaining_qty || 0) > 0) && (
                    <tr>
                      <td colSpan={3} className="py-3 text-stone-400">
                        Nessuna allocazione attiva.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>

            {walletMsg && (
              <p
                className={`text-sm ${
                  walletMsg.type === "ok" ? "text-emerald-800" : "text-rose-700"
                }`}
                data-testid="wallet-op-message"
              >
                {walletMsg.text}
              </p>
            )}
          </div>
        )}

      </div>
    </AgencyShell>
  );
}
