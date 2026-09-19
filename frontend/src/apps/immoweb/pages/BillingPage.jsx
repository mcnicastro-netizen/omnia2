import { useEffect, useState } from "react";
import { useLocation } from "react-router-dom";
import { api } from "@/shared/lib/api";
import AgencyShell from "@/apps/immoweb/components/AgencyShell";
import { Button } from "@/components/ui/button";
import { toast } from "sonner";

/**
 * OMNIA — Settings ▸ Billing (M4.S3/S4) + D-085 storage meter
 *
 * D-080: demo guidata prima dell'abbonamento.
 * CTA primaria = Richiedi demo; checkout solo dopo conferma demo (o piano già attivo).
 */
export default function BillingPage() {
  const [state, setState] = useState({ loading: true, data: null, sub: null });
  const [storage, setStorage] = useState(null);
  const [billingCycle, setBillingCycle] = useState("monthly");
  const [busy, setBusy] = useState(false);
  const [demoDone, setDemoDone] = useState(() => {
    try {
      return localStorage.getItem("omnia_demo_done") === "1";
    } catch {
      return false;
    }
  });
  const location = useLocation();

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
    const email = (state.data?.demo_contact_email || "mcnicastro@gmail.com").trim();
    const subject = encodeURIComponent("Richiesta demo guidata OMNIA");
    const body = encodeURIComponent(
      "Ciao Marco,\n\nvorrei prenotare una demo guidata di OMNIA per la mia agenzia.\n\nAgenzia:\nCittà:\nTelefono:\n"
    );
    window.location.href = `mailto:${email}?subject=${subject}&body=${body}`;
    try {
      localStorage.setItem("omnia_demo_done", "1");
    } catch { /* noop */ }
    setDemoDone(true);
    toast.success("Perfetto — dopo la demo potrai attivare il piano qui.");
  };

  const checkoutSubscription = async (tier) => {
    if (!demoDone && !state.sub?.subscription) {
      const ok = window.confirm(
        "L'abbonamento si attiva dopo la demo guidata.\n\nHai già fatto la demo con OMNIA?"
      );
      if (!ok) {
        openDemo();
        return;
      }
      try {
        localStorage.setItem("omnia_demo_done", "1");
      } catch { /* noop */ }
      setDemoDone(true);
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

  const checkoutCredits = async (packageKey) => {
    setBusy(true);
    try {
      const { data } = await api.post("/billing/credits/purchase", {
        package_key: packageKey,
        success_url: window.location.origin,
        cancel_url: window.location.origin + window.location.pathname + "?cancel=1",
      });
      window.location.href = data.checkout_url;
    } catch (e) {
      toast.error("Errore checkout crediti");
      setBusy(false);
    }
  };

  const buyStorage = async () => {
    setBusy(true);
    try {
      const { data } = await api.post("/billing/storage/purchase");
      if (data.checkout_url) {
        window.location.href = data.checkout_url;
        return;
      }
      if (data.stripe_required) {
        const email = data.demo_contact_email || "mcnicastro@gmail.com";
        const subject = encodeURIComponent("OMNIA — spazio archivio extra +100 GB");
        const body = encodeURIComponent(
          `Ciao,\n\nvorrei aggiungere ${data.addon?.gb || 100} GB di archivio (€${data.addon?.price_eur || 15}/mese) alla mia agenzia.\n\nAgenzia / email account:\n`
        );
        window.location.href = `mailto:${email}?subject=${subject}&body=${body}`;
        toast.message(data.message || "Contatta il supporto per aggiungere spazio.");
      }
    } catch (e) {
      const d = e?.response?.data?.detail;
      toast.error(typeof d === "string" ? d : d?.message || "Errore acquisto spazio");
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
  const plans = data?.plans || [];
  const packages = data?.credit_packages || [];
  const canCheckoutDirect = Boolean(activeSub) || demoDone;

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

        {!activeSub && (
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

        <div className="grid md:grid-cols-3 gap-4 mb-10">
          <div className="border border-stone-200 bg-white p-6">
            <div className="text-xs uppercase tracking-widest text-stone-500 mb-1">Piano attuale</div>
            <div className="text-2xl font-serif text-[#0B1E3F]" data-testid="current-plan">
              {activeSub ? activeSub.tier?.toUpperCase() : "Nessuno"}
            </div>
            <div className="text-sm text-stone-500 mt-1">
              {activeSub ? `Status: ${activeSub.status}` : "Dopo la demo puoi attivare un piano"}
            </div>
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
            <div className="text-xs uppercase tracking-widest text-stone-500 mb-1">Saldo crediti</div>
            <div className="text-2xl font-serif text-[#0F6B5B]" data-testid="wallet-balance">
              {wallet.balance || 0} crediti
            </div>
            <div className="text-sm text-stone-500 mt-1">
              Consumati per valutatore, staging, video, ecc.
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
              disabled={busy}
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
              ) : canCheckoutDirect ? (
                <Button
                  className="mt-5 bg-[#0F6B5B] hover:bg-[#0B4F42] text-white"
                  onClick={() => checkoutSubscription(p.tier)}
                  disabled={busy}
                  data-testid={`checkout-${p.tier}-btn`}
                >
                  Attiva
                </Button>
              ) : (
                <Button
                  className="mt-5 bg-[#0B1E3F] hover:bg-[#16305a] text-white"
                  onClick={openDemo}
                  data-testid={`checkout-${p.tier}-btn`}
                >
                  Prima la demo
                </Button>
              )}
            </div>
          ))}
        </div>

        <h2 className="font-serif text-2xl text-[#0B1E3F] mb-4">Ricarica crediti</h2>
        <div className="grid md:grid-cols-3 gap-4">
          {packages.map((pkg) => (
            <div key={pkg.key} className="border border-stone-200 bg-white p-5" data-testid={`pack-card-${pkg.key}`}>
              <div className="font-serif text-2xl text-[#0B1E3F]">{pkg.credits} crediti</div>
              <div className="text-3xl font-serif text-[#C69F4C] my-2">€{pkg.price_eur}</div>
              <Button
                variant="outline"
                className="w-full mt-2"
                onClick={() => checkoutCredits(pkg.key)}
                disabled={busy}
                data-testid={`buy-pack-${pkg.key}-btn`}
              >
                Acquista
              </Button>
            </div>
          ))}
        </div>

      </div>
    </AgencyShell>
  );
}
