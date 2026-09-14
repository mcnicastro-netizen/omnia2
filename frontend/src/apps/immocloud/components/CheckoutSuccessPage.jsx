/* Checkout success page (B2C · Cap. 21). Polls /billing/b2c/status/{session_id} */
import React, { useEffect, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { useTranslation } from "react-i18next";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

export default function CheckoutSuccessPage() {
  const { t } = useTranslation();
  const [params] = useSearchParams();
  const sid = params.get("session_id");
  const [status, setStatus] = useState(null);
  const [tries, setTries] = useState(0);

  useEffect(() => {
    if (!sid) return;
    let cancelled = false;
    async function poll() {
      const r = await fetch(`${BACKEND_URL}/api/billing/b2c/status/${sid}`, { credentials: "include" });
      const body = await r.json().catch(() => ({}));
      if (cancelled) return;
      setStatus(body);
      if (body?.status !== "paid" && tries < 10) {
        setTries(x => x + 1);
        setTimeout(poll, 1500);
      }
    }
    poll();
    return () => { cancelled = true; };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [sid]);

  return (
    <div className="min-h-screen bg-stone-50 flex items-center">
      <div className="max-w-lg mx-auto px-4 py-16 text-center">
        <div className="text-6xl mb-4">✅</div>
        <h1 className="text-2xl font-serif text-stone-900" data-testid="checkout-success-title">
          {t("checkout.success_title", "Pagamento ricevuto")}
        </h1>
        <p className="mt-3 text-stone-600">
          {status?.status === "paid"
            ? t("checkout.success_paid", "Il tuo entitlement UNI 10750 è attivo per 24 ore. Torna al valutatore per scaricare il report PDF.")
            : t("checkout.success_pending", "Stiamo confermando il pagamento con Stripe…")}
        </p>
        <div className="mt-6">
          <Link to="/it/cloud/valutatore?tier=uni" className="px-4 py-2 bg-stone-900 text-white rounded" data-testid="checkout-success-back">
            {t("checkout.back_to_valuator", "Torna al valutatore")}
          </Link>
        </div>
      </div>
    </div>
  );
}
