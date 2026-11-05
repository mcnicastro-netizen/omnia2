import React, { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { useTranslation } from "react-i18next";
import CloudPageHero from "../components/CloudPageHero";
import PwaQrCode from "../components/PwaQrCode";
import usePwaInstall from "../../../shared/hooks/usePwaInstall";
import { pwaInstallUrl } from "../../../shared/lib/pwa";

/**
 * Flusso stile Idealista: da desktop inquadra il QR → sul telefonino
 * un tocco apre il dialog nativo «Installa» (Android/Chrome) e crea l’icona.
 * iOS: guida Condividi → Aggiungi a Home (limite Apple).
 */
export default function CloudInstallAppPage() {
  const { t, i18n } = useTranslation();
  const lang = (i18n.language || "it").slice(0, 2);
  const { installed, canPrompt, iosHint, isMobile, promptInstall } = usePwaInstall();
  const [status, setStatus] = useState("");
  const installUrl = useMemo(() => pwaInstallUrl(lang), [lang]);

  useEffect(() => {
    document.title = t("cloud.pwa.page_title", "Scarica app ImmobilCloud");
  }, [t]);

  /* Su mobile, se il browser è pronto, prova subito il dialog nativo (gesto = primo tap sul CTA sotto). */
  const onInstall = async () => {
    setStatus("");
    if (installed) {
      setStatus(t("cloud.pwa.already", "Già installata: aprila dall’icona sul telefonino."));
      return;
    }
    const res = await promptInstall();
    if (res.ok) {
      setStatus(t("cloud.pwa.done", "Perfetto — ImmobilCloud è tra le tue app."));
      return;
    }
    if (iosHint || res.reason === "ios") {
      setStatus(
        t(
          "cloud.pwa.ios_hint",
          "Su iPhone: tocca Condividi (□↑) in basso → Aggiungi a Home."
        )
      );
      return;
    }
    setStatus(
      t(
        "cloud.pwa.browser_hint",
        "Apri questa pagina in Chrome sul telefonino, poi tocca Installa."
      )
    );
  };

  return (
    <div data-testid="cloud-install-app-page">
      <CloudPageHero
        eyebrow={t("cloud.pwa.eyebrow", "Telefonino")}
        title={t("cloud.pwa.page_heading", "ImmobilCloud sul telefonino")}
        subtitle={t(
          "cloud.pwa.page_sub",
          "Come Idealista: inquadra il QR, un tocco, e compare l’icona tra le tue app. Niente store."
        )}
        image="/cloud/living.jpg"
        compact
      />

      <section className="px-5 sm:px-8 md:px-16 py-10 max-w-5xl mx-auto">
        {installed ? (
          <div
            data-testid="pwa-already-box"
            className="rounded-2xl border border-[#C19A6B]/40 bg-[#0B1E3F] text-white px-6 py-8 text-center"
          >
            <p className="text-[10px] uppercase tracking-[0.28em] text-[#C19A6B] mb-2">
              {t("cloud.pwa.title_installed", "App installata")}
            </p>
            <p
              className="text-2xl font-light"
              style={{ fontFamily: "'Fraunces', Georgia, serif" }}
            >
              {t("cloud.pwa.text_installed", "ImmobilCloud è già sulla Home del tuo dispositivo.")}
            </p>
            <Link
              to={`/${lang}/cloud`}
              className="inline-flex mt-6 px-5 py-2.5 rounded-lg bg-[#C19A6B] text-[#0B1E3F] text-sm tracking-wide"
            >
              {t("cloud.pwa.open_home", "Apri ImmobilCloud")}
            </Link>
          </div>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 items-start">
            {/* QR — percorso desktop → telefono */}
            <div
              data-testid="pwa-qr-panel"
              className="rounded-2xl border border-stone-200 bg-[#f7f4ef] p-6 sm:p-8 flex flex-col items-center text-center"
            >
              <p className="text-[10px] uppercase tracking-[0.28em] text-[#C19A6B] mb-2">
                {t("cloud.pwa.qr_eyebrow", "Dal computer")}
              </p>
              <h2
                className="text-2xl font-light text-[#0B1E3F] mb-2"
                style={{ fontFamily: "'Fraunces', Georgia, serif" }}
              >
                {t("cloud.pwa.qr_title", "Inquadra col telefonino")}
              </h2>
              <p className="text-sm text-stone-600 mb-5 max-w-sm">
                {t(
                  "cloud.pwa.qr_text",
                  "Apri la fotocamera, inquadra il QR e apri il link. Poi un tocco su Installa: nasce l’icona ImmobilCloud."
                )}
              </p>
              <PwaQrCode url={installUrl} size={220} />
              <p className="mt-4 text-xs text-stone-500 break-all max-w-xs" data-testid="pwa-install-url">
                {installUrl}
              </p>
            </div>

            {/* CTA install — percorso già sul telefono */}
            <div
              data-testid="pwa-install-panel"
              className="rounded-2xl border border-stone-200 bg-white p-6 sm:p-8"
            >
              <p className="text-[10px] uppercase tracking-[0.28em] text-[#C19A6B] mb-2">
                {t("cloud.pwa.phone_eyebrow", "Sul telefonino")}
              </p>
              <h2
                className="text-2xl font-light text-[#0B1E3F] mb-2"
                style={{ fontFamily: "'Fraunces', Georgia, serif" }}
              >
                {t("cloud.pwa.phone_title", "Un tocco → icona tra le app")}
              </h2>
              <p className="text-sm text-stone-600 mb-6">
                {iosHint
                  ? t(
                      "cloud.pwa.phone_text_ios",
                      "Su iPhone Apple non lascia installare da sola: tocca Condividi e poi Aggiungi a Home — stesso risultato, icona in Home."
                    )
                  : t(
                      "cloud.pwa.phone_text_android",
                      "Su Android/Chrome compare il dialog «Installa app»: conferma e ImmobilCloud si mette accanto alle altre app, a schermo intero."
                    )}
              </p>

              {iosHint ? (
                <ol className="space-y-3 text-sm text-stone-700 mb-6" data-testid="pwa-ios-steps">
                  <li className="flex gap-3">
                    <span className="shrink-0 w-7 h-7 rounded-full bg-[#0B1E3F] text-white text-xs flex items-center justify-center">1</span>
                    <span>{t("cloud.pwa.ios_step1", "Tocca il bottone Condividi (quadrato con freccia) in Safari.")}</span>
                  </li>
                  <li className="flex gap-3">
                    <span className="shrink-0 w-7 h-7 rounded-full bg-[#0B1E3F] text-white text-xs flex items-center justify-center">2</span>
                    <span>{t("cloud.pwa.ios_step2", "Scorri e scegli «Aggiungi a Home».")}</span>
                  </li>
                  <li className="flex gap-3">
                    <span className="shrink-0 w-7 h-7 rounded-full bg-[#0B1E3F] text-white text-xs flex items-center justify-center">3</span>
                    <span>{t("cloud.pwa.ios_step3", "Conferma: compare l’icona ImmobilCloud.")}</span>
                  </li>
                </ol>
              ) : (
                <button
                  type="button"
                  data-testid="pwa-install-cta"
                  onClick={onInstall}
                  className="w-full sm:w-auto px-8 py-3.5 rounded-xl bg-[#0B1E3F] text-white text-sm uppercase tracking-widest hover:bg-[#C19A6B] transition"
                >
                  {canPrompt || isMobile
                    ? t("cloud.pwa.cta_install", "Installa ImmobilCloud")
                    : t("cloud.pwa.cta_open_phone", "Apri questa pagina sul telefonino")}
                </button>
              )}

              {!iosHint && (
                <button
                  type="button"
                  data-testid="pwa-install-cta-secondary"
                  onClick={onInstall}
                  className="mt-3 text-xs uppercase tracking-widest text-[#0B1E3F] underline underline-offset-4"
                >
                  {t("cloud.pwa.cta_retry", "Non compare? Riprova Installa")}
                </button>
              )}

              {status ? (
                <p className="mt-5 text-sm text-[#0B1E3F] bg-[#f7f4ef] border border-stone-200 rounded-xl px-4 py-3" data-testid="pwa-status">
                  {status}
                </p>
              ) : null}

              <p className="mt-6 text-xs text-stone-500">
                {t(
                  "cloud.pwa.honest",
                  "È una web app (PWA): stessa ImmobilCloud, icona e apertura a tutto schermo. Non passa da App Store o Play Store."
                )}
              </p>
            </div>
          </div>
        )}

        <p className="mt-10 text-center text-sm text-stone-500">
          <Link to={`/${lang}/cloud`} className="text-[#0B1E3F] hover:text-[#C19A6B]">
            ← {t("cloud.pwa.back_home", "Torna alla home")}
          </Link>
        </p>
      </section>
    </div>
  );
}
