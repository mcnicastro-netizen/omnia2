import React from "react";
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
import AccountDashboard from "./components/AccountDashboard";

/* M17 — ImmocloudApp è ora solo il router B2C: le pagine vivono in pages/ e components/. */
export default function ImmocloudApp() {
  return (
    <div className={`min-h-screen ${THEME.bg} ${THEME.text}`} data-testid="immocloud-app">
      <CloudTopNav />
      <Routes>
        <Route index element={<CloudHomePage />} />
        <Route path="search" element={<CloudSearchPage />} />
        <Route path="register" element={<CloudRegisterPage />} />
        <Route path="property/:pid" element={<PropertyDetailPage />} />
        <Route path="account/sell" element={<SellPage />} />
        <Route path="account" element={<AccountDashboard />} />
        <Route path="valutatore" element={<ValuatorPage />} />
        <Route path="checkout/success" element={<CheckoutSuccessPage />} />
        <Route path="checkout/cancel" element={<CheckoutCancelPage />} />
        <Route path="mutui" element={<MutuiPage />} />
      </Routes>
      <FooterB2C />
    </div>
  );
}
