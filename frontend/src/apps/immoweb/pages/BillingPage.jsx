import { useEffect, useState } from "react";
import { useLocation } from "react-router-dom";
import { api } from "@/shared/lib/api";
import AgencyShell from "@/apps/immoweb/components/AgencyShell";
import { Button } from "@/components/ui/button";
import { toast } from "sonner";

/**
 * OMNIA — Settings ▸ Billing (M4.S3/S4)
 *
 * Mostra piano attuale + saldo crediti + selettore piano/pacchetto.
 * Se STRIPE_ENABLED=true crea Checkout Session e reindirizza.
 */
export default function BillingPage() {
  const [state, setState] = useState({ loading: true, data: null, sub: null });
  const [billingCycle, setBillingCycle] = useState("monthly");
  const [busy, setBusy] = useState(false);
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
    })();
  }, []);

  // On return from Stripe with session_id — poll status
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
        } else if (data.payment_status === "failed") {
          toast.error("Pagamento fallito");
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

  const checkoutSubscription = async (tier) => {
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

  return (
    <AgencyShell current="settings">
      <div className="p-6 md:p-10 max-w-6xl" data-testid="billing-page">
        <h1 className="font-serif text-4xl text-[#0B1E3F] mb-1">Piano & Crediti</h1>
        <p className="text-stone-500 mb-8 text-sm">
          Gestisci l'abbonamento della tua agenzia e ricarica il portafoglio crediti per servizi a consumo.
          {data?.mode === "test" && (
            <span className="ml-2 inline-block px-2 py-0.5 text-xs bg-amber-100 text-amber-800">MODALITÀ TEST</span>
          )}
        </p>

        {/* Current state */}
        <div className="grid md:grid-cols-2 gap-4 mb-10">
          <div className="border border-stone-200 bg-white p-6">
            <div className="text-xs uppercase tracking-widest text-stone-500 mb-1">Piano attuale</div>
            <div className="text-2xl font-serif text-[#0B1E3F]" data-testid="current-plan">
              {activeSub ? activeSub.tier?.toUpperCase() : "Nessuno"}
            </div>
            <div className="text-sm text-stone-500 mt-1">
              {activeSub ? `Status: ${activeSub.status}` : "Attiva un piano per iniziare"}
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
              Consumati per valutatore, HAL, ricerca APE, video, ecc.
            </div>
          </div>
        </div>

        {/* Plans */}
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
            >Annuale <span className="text-[#C69F4C] text-xs ml-1">−2 mesi</span></button>
          </div>
        </div>
        <div className="grid md:grid-cols-4 gap-4 mb-12">
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
                <li>{p.trial_days} giorni prova gratuita</li>
              </ul>
              <Button
                className="mt-5 bg-[#0F6B5B] hover:bg-[#0B4F42] text-white"
                onClick={() => checkoutSubscription(p.tier)}
                disabled={busy || activeSub?.tier === p.tier}
                data-testid={`checkout-${p.tier}-btn`}
              >
                {activeSub?.tier === p.tier ? "Piano attivo" : "Attiva"}
              </Button>
            </div>
          ))}
        </div>

        {/* Credit packages */}
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
