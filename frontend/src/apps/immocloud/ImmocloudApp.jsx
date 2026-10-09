import React, { useEffect, useState } from "react";
import { Route, Routes } from "react-router-dom";
import { THEME } from "./cloudTheme";
import CloudTopNav from "./components/CloudTopNav";
import FooterB2C from "./components/FooterB2C";
import CloudHomePage from "./pages/CloudHomePage";
import CloudSearchPage from "./pages/CloudSearchPage";
import CloudRegisterPage from "./pages/CloudRegisterPage";
import PropertyDetailPage from "./components/PropertyDetailPage";
import SellPage from "./components/SellPage";
import ValuatorPage from "./components/ValuatorPage";
import CheckoutSuccessPage from "./components/CheckoutSuccessPage";
import CheckoutCancelPage from "./components/CheckoutCancelPage";
import MutuiPage from "./components/MutuiPage";
import VisuraPage from "./components/VisuraPage";
import AccountDashboard from "./components/AccountDashboard";
import ErrorBoundary from "@/shared/components/ErrorBoundary";

/* M17 — ImmocloudApp è ora solo il router B2C: le pagine vivono in pages/ e components/. */
export default function ImmocloudApp() {
  const [apiDown, setApiDown] = useState(false);
  useEffect(() => {
    const onDown = () => setApiDown(true);
    const onUp = () => setApiDown(false);
    window.addEventListener("omnia:api-unreachable", onDown);
    window.addEventListener("online", onUp);
    return () => {
      window.removeEventListener("omnia:api-unreachable", onDown);
      window.removeEventListener("online", onUp);
    };
  }, []);

  return (
    <ErrorBoundary name="cloud">
      <div className={`min-h-screen ${THEME.bg} ${THEME.text}`} data-testid="immocloud-app">
        {apiDown && (
          <div
            role="alert"
            data-testid="cloud-api-unreachable"
            className="bg-amber-900 text-amber-50 text-sm text-center px-4 py-2"
          >
            Connessione al servizio non disponibile. Controlla la rete e riprova.
            <button
              type="button"
              className="ml-3 underline"
              onClick={() => { setApiDown(false); window.location.reload(); }}
            >
              Ricarica
            </button>
          </div>
        )}
        <CloudTopNav />
        <Routes>
          <Route index element={<CloudHomePage />} />
          <Route path="search" element={<CloudSearchPage />} />
          <Route path="register" element={<CloudRegisterPage />} />
          <Route path="property/:pid" element={<PropertyDetailPage />} />
          <Route path="account/sell" element={<SellPage />} />
          <Route path="account" element={<AccountDashboard />} />
          <Route path="valutatore" element={<ValuatorPage />} />
          <Route path="valuator" element={<ValuatorPage />} />
          <Route path="visura" element={<VisuraPage />} />
          <Route path="checkout/success" element={<CheckoutSuccessPage />} />
          <Route path="checkout/cancel" element={<CheckoutCancelPage />} />
          <Route path="mutui" element={<MutuiPage />} />
        </Routes>
        <FooterB2C />
      </div>
    </ErrorBoundary>
  );
}
