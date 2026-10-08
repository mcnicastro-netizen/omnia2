import React from "react";
import { Link, useLocation } from "react-router-dom";
import { useTranslation } from "react-i18next";

const DOCS = {
  privacy: {
    titleKey: "cloud.legal_privacy_title",
    bodyKey: "cloud.legal_privacy_body",
  },
  cookie: {
    titleKey: "cloud.legal_cookie_title",
    bodyKey: "cloud.legal_cookie_body",
  },
  termini: {
    titleKey: "cloud.legal_terms_title",
    bodyKey: "cloud.legal_terms_body",
  },
};

function docFromPath(pathname) {
  const seg = (pathname || "").split("/").filter(Boolean).pop();
  return DOCS[seg] ? seg : "privacy";
}

/** Static legal docs for B2C footer (P-005). Paths: /:lang/privacy|cookie|termini */
export default function LegalDocPage() {
  const { t, i18n } = useTranslation();
  const lang = (i18n.language || "it").slice(0, 2);
  const { pathname } = useLocation();
  const doc = docFromPath(pathname);
  const meta = DOCS[doc];
  const paragraphs = t(meta.bodyKey, { returnObjects: true });
  const lines = Array.isArray(paragraphs) ? paragraphs : [String(paragraphs)];

  return (
    <main className="min-h-screen bg-[#fbf9f5] text-[#0B1E3F]" data-testid={`legal-doc-${doc}`}>
      <div className="max-w-2xl mx-auto px-5 sm:px-8 py-14">
        <p className="text-[11px] uppercase tracking-[0.28em] text-[#C19A6B] mb-3">ImmobilCloud</p>
        <h1
          className="text-3xl font-light tracking-tight mb-8"
          style={{ fontFamily: "'Fraunces', Georgia, serif" }}
        >
          {t(meta.titleKey)}
        </h1>
        <div className="space-y-4 text-sm text-stone-700 leading-relaxed">
          {lines.map((p, i) => (
            <p key={i}>{p}</p>
          ))}
        </div>
        <p className="mt-10">
          <Link
            to={`/${lang}/cloud`}
            className="text-xs uppercase tracking-widest text-[#0B1E3F] underline underline-offset-4 hover:text-[#C19A6B]"
          >
            ← ImmobilCloud
          </Link>
        </p>
      </div>
    </main>
  );
}
