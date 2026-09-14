/* Checkout cancel page (B2C · Cap. 21) */
import React from "react";
import { Link } from "react-router-dom";
import { useTranslation } from "react-i18next";

export default function CheckoutCancelPage() {
  const { t } = useTranslation();
  return (
    <div className="min-h-screen bg-stone-50 flex items-center">
      <div className="max-w-lg mx-auto px-4 py-16 text-center">
        <div className="text-6xl mb-4">🚫</div>
        <h1 className="text-2xl font-serif text-stone-900" data-testid="checkout-cancel-title">
          {t("checkout.cancel_title", "Pagamento annullato")}
        </h1>
        <p className="mt-3 text-stone-600">
          {t("checkout.cancel_body", "Nessun addebito effettuato. Puoi comunque usare la stima rapida gratuita.")}
        </p>
        <div className="mt-6 flex gap-2 justify-center">
          <Link to="/it/cloud/valutatore?tier=base" className="px-4 py-2 bg-stone-900 text-white rounded" data-testid="checkout-cancel-base">
            {t("checkout.try_base", "Prova la stima gratuita")}
          </Link>
          <Link to="/it/cloud" className="px-4 py-2 border border-stone-300 rounded" data-testid="checkout-cancel-home">
            {t("common.home", "Home")}
          </Link>
        </div>
      </div>
    </div>
  );
}
