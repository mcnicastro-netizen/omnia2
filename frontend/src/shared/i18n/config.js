/**
 * OMNIA — i18n configuration (react-i18next)
 * Decision D-014: IT default + EN + ES, browser language auto-detection
 */
import i18n from "i18next";
import LanguageDetector from "i18next-browser-languagedetector";
import { initReactI18next } from "react-i18next";

import it from "./locales/it.json";
import en from "./locales/en.json";
import es from "./locales/es.json";

export const SUPPORTED_LANGS = ["it", "en", "es"];
export const DEFAULT_LANG = "it";

i18n
  .use(LanguageDetector)
  .use(initReactI18next)
  .init({
    resources: {
      it: { translation: it },
      en: { translation: en },
      es: { translation: es },
    },
    fallbackLng: DEFAULT_LANG,
    supportedLngs: SUPPORTED_LANGS,
    nonExplicitSupportedLngs: true, // it-IT → it
    detection: {
      order: ["path", "localStorage", "navigator", "htmlTag"],
      lookupLocalStorage: "omnia_lang",
      caches: ["localStorage"],
    },
    interpolation: {
      escapeValue: false, // React already escapes
    },
    returnEmptyString: false,
  });

export default i18n;
