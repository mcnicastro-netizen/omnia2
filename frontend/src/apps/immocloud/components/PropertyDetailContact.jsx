/* OMNIA — PropertyDetail contact panel (MOVE-ONLY). */
import React, { useState } from "react";
import { useTranslation } from "react-i18next";
import { API, waHref } from "./propertyDetailUtils";

function IconMail({ className = "w-4 h-4" }) {
  return (
    <svg viewBox="0 0 24 24" className={className} fill="none" stroke="currentColor" strokeWidth="1.75" aria-hidden>
      <rect x="3" y="5" width="18" height="14" rx="2" />
      <path d="m3 7 9 6 9-6" />
    </svg>
  );
}

function IconPhone({ className = "w-4 h-4" }) {
  return (
    <svg viewBox="0 0 24 24" className={className} fill="none" stroke="currentColor" strokeWidth="1.75" aria-hidden>
      <path d="M6.5 3.5 9 6l-1.8 1.8a12 12 0 0 0 6.5 6.5L15.5 13l2.5 2.5c.4.4.5 1 .2 1.5A15 15 0 0 1 5 5.3c.5-.3 1.1-.2 1.5.2Z" />
    </svg>
  );
}

function IconWhatsApp({ className = "w-4 h-4" }) {
  return (
    <svg viewBox="0 0 24 24" className={className} fill="currentColor" aria-hidden>
      <path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413z" />
    </svg>
  );
}

function ChannelLink({ testid, href, icon, label, external }) {
  return (
    <a
      data-testid={testid}
      href={href}
      {...(external ? { target: "_blank", rel: "noopener noreferrer" } : {})}
      className="group flex items-center gap-3 rounded-xl border border-stone-200/90 bg-white/70 px-3 py-2.5 text-sm text-[#0B1E3F] transition duration-200 hover:-translate-y-0.5 hover:border-[#C19A6B]/60 hover:bg-white hover:shadow-[0_8px_24px_-12px_rgba(11,30,63,0.25)]"
    >
      <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-[#0B1E3F]/[0.06] text-[#0B1E3F] transition group-hover:bg-[#C19A6B]/15 group-hover:text-[#8a6a45]">
        {icon}
      </span>
      <span className="min-w-0 flex-1 truncate font-medium tracking-tight">{label}</span>
      <span className="text-[10px] uppercase tracking-[0.2em] text-stone-400 transition group-hover:text-[#C19A6B]">→</span>
    </a>
  );
}

export default function ContactPanel({ pid, propertyTitle, publisher, agency }) {
  const { t } = useTranslation();
  const kind = publisher?.kind || (agency ? "agency" : "private");
  const isPrivate = kind === "private";
  const channels = publisher?.channels || {};
  const name =
    publisher?.display_name ||
    agency?.display_name ||
    (isPrivate ? t("cloud.publisher_private") : t("cloud.publisher_agency"));
  const city = agency?.city;
  const logo = agency?.logo_url;
  const initial = (name || "P").trim().charAt(0).toUpperCase();
  const email = isPrivate ? channels.email : (channels.email || agency?.email);
  const phone = isPrivate ? channels.phone : (channels.phone || agency?.phone);
  const whatsapp = isPrivate ? channels.whatsapp : channels.whatsapp;
  const wa = whatsapp ? waHref(whatsapp) : null;
  const acceptsMessages = publisher?.accepts_messages !== false;

  const [form, setForm] = useState({
    name: "", surname: "", email: "", phone: "",
    message: t("cloud.contact_default_message", { title: propertyTitle || "" }),
    visit_requested: false,
    gdpr_consent: false,
  });
  const [busy, setBusy] = useState(false);
  const [done, setDone] = useState(false);
  const [error, setError] = useState("");

  const onSubmit = async (e) => {
    e.preventDefault();
    if (!form.gdpr_consent) {
      setError(t("cloud.contact_err_gdpr"));
      return;
    }
    setBusy(true);
    setError("");
    try {
      const r = await fetch(`${API}/property/${pid}/contact`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(form),
      });
      const d = await r.json();
      if (!r.ok) {
        setError(d.detail || t("cloud.contact_err_generic"));
      } else {
        setDone(true);
      }
    } catch {
      setError(t("cloud.contact_err_generic"));
    } finally {
      setBusy(false);
    }
  };

  const fieldCls =
    "w-full rounded-xl border border-stone-200/90 bg-white/80 px-3.5 py-2.5 text-sm text-stone-900 outline-none transition placeholder:text-stone-400 focus:border-[#0B1E3F] focus:bg-white focus:ring-2 focus:ring-[#0B1E3F]/10";

  return (
    <div
      data-testid={isPrivate ? "private-publisher-card" : "detail-agency-card"}
      className="relative overflow-hidden rounded-2xl border border-stone-200/80 bg-gradient-to-b from-[#fbf8f3] to-white shadow-[0_20px_50px_-28px_rgba(11,30,63,0.35)] animate-[contactIn_480ms_ease-out]"
    >
      <style>{`
        @keyframes contactIn {
          from { opacity: 0; transform: translateY(10px); }
          to { opacity: 1; transform: translateY(0); }
        }
      `}</style>

      {/* Header identity */}
      <div className="relative border-b border-stone-200/70 bg-[#0B1E3F] px-5 pb-5 pt-5 text-white">
        <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(ellipse_at_top_right,rgba(193,154,107,0.28),transparent_55%)]" aria-hidden />
        <p className="relative text-[10px] uppercase tracking-[0.3em] text-[#E8D5B5]/90 mb-3">
          {isPrivate ? t("cloud.publisher_private") : t("cloud.detail_agency_label")}
        </p>
        <div className="relative flex items-center gap-3.5">
          {logo ? (
            <img
              src={logo}
              alt={name}
              className="h-14 w-14 rounded-xl object-contain bg-white/95 border border-white/20 p-1"
            />
          ) : (
            <div
              className="flex h-14 w-14 items-center justify-center rounded-xl bg-white/10 text-2xl font-light text-[#E8D5B5] ring-1 ring-white/20"
              style={{ fontFamily: "'Fraunces', Georgia, serif" }}
            >
              {initial}
            </div>
          )}
          <div className="min-w-0">
            <h3
              className="truncate text-xl font-medium leading-tight text-white"
              style={{ fontFamily: "'Fraunces', Georgia, serif" }}
            >
              {name}
            </h3>
            {city && <p className="mt-0.5 truncate text-xs text-white/65">{city}</p>}
          </div>
        </div>
      </div>

      <div className="space-y-5 p-5">
        {(email || phone || wa) && (
          <div className="space-y-2" data-testid="publisher-channels">
            {email && (
              <ChannelLink
                testid={isPrivate ? "publisher-email" : "agency-email"}
                href={`mailto:${email}`}
                icon={<IconMail />}
                label={email}
              />
            )}
            {phone && (
              <ChannelLink
                testid={isPrivate ? "publisher-phone" : "agency-phone"}
                href={`tel:${phone}`}
                icon={<IconPhone />}
                label={phone}
              />
            )}
            {wa && (
              <ChannelLink
                testid="publisher-whatsapp"
                href={wa}
                icon={<IconWhatsApp className="w-4 h-4 text-[#1f6b45]" />}
                label="WhatsApp"
                external
              />
            )}
          </div>
        )}

        {acceptsMessages && (
          done ? (
            <div data-testid="contact-done" className="rounded-xl bg-[#f7f4ef] px-4 py-6 text-center">
              <p className="text-[10px] uppercase tracking-[0.28em] text-[#C19A6B] mb-2">ImmobilCloud</p>
              <h4
                className="text-lg text-[#0B1E3F] mb-1"
                style={{ fontFamily: "'Fraunces', Georgia, serif" }}
              >
                {t("cloud.contact_done_title")}
              </h4>
              <p className="text-xs leading-relaxed text-stone-600">
                {isPrivate ? t("cloud.contact_done_desc_private") : t("cloud.contact_done_desc")}
              </p>
            </div>
          ) : (
            <form data-testid="contact-form" onSubmit={onSubmit} className="space-y-3">
              {(email || phone || wa) && (
                <div className="flex items-center gap-3 py-1">
                  <div className="h-px flex-1 bg-gradient-to-r from-transparent via-stone-200 to-transparent" />
                  <span className="text-[10px] uppercase tracking-[0.22em] text-stone-400">
                    {t("cloud.contact_or_message")}
                  </span>
                  <div className="h-px flex-1 bg-gradient-to-r from-transparent via-stone-200 to-transparent" />
                </div>
              )}
              <div>
                <h4
                  className="text-base text-[#0B1E3F]"
                  style={{ fontFamily: "'Fraunces', Georgia, serif" }}
                >
                  {isPrivate ? t("cloud.contact_title_private") : t("cloud.contact_title")}
                </h4>
                <p className="mt-1 text-xs leading-relaxed text-stone-500">
                  {isPrivate ? t("cloud.contact_desc_private") : t("cloud.contact_desc")}
                </p>
              </div>

              <input
                data-testid="contact-name"
                placeholder={t("cloud.contact_name")}
                required
                value={form.name}
                onChange={(e) => setForm({ ...form, name: e.target.value })}
                className={fieldCls}
              />
              <input
                data-testid="contact-email"
                type="email"
                placeholder={t("cloud.contact_email")}
                required
                value={form.email}
                onChange={(e) => setForm({ ...form, email: e.target.value })}
                className={fieldCls}
              />
              <input
                data-testid="contact-phone"
                placeholder={t("cloud.contact_phone")}
                value={form.phone}
                onChange={(e) => setForm({ ...form, phone: e.target.value })}
                className={fieldCls}
              />
              <textarea
                data-testid="contact-message"
                rows={4}
                required
                minLength={10}
                placeholder={t("cloud.contact_message")}
                value={form.message}
                onChange={(e) => setForm({ ...form, message: e.target.value })}
                className={`${fieldCls} resize-y min-h-[96px]`}
              />

              <label className="flex items-center gap-2.5 text-xs text-stone-700 cursor-pointer select-none">
                <input
                  type="checkbox"
                  data-testid="contact-visit"
                  checked={form.visit_requested}
                  onChange={(e) => setForm({ ...form, visit_requested: e.target.checked })}
                  className="h-4 w-4 rounded border-stone-300 text-[#0B1E3F] focus:ring-[#C19A6B]"
                />
                {t("cloud.contact_visit")}
              </label>

              <label className="flex items-start gap-2.5 text-xs leading-relaxed text-stone-600 cursor-pointer select-none">
                <input
                  type="checkbox"
                  data-testid="contact-gdpr"
                  required
                  checked={form.gdpr_consent}
                  onChange={(e) => setForm({ ...form, gdpr_consent: e.target.checked })}
                  className="mt-0.5 h-4 w-4 rounded border-stone-300 text-[#0B1E3F] focus:ring-[#C19A6B]"
                />
                <span>{t("cloud.contact_gdpr")}</span>
              </label>

              {error && (
                <p data-testid="contact-error" className="text-xs text-rose-700 bg-rose-50 border border-rose-200/80 rounded-xl px-3 py-2">
                  {error}
                </p>
              )}

              <button
                type="submit"
                data-testid="contact-submit"
                disabled={busy}
                className="w-full rounded-xl bg-[#0B1E3F] py-3 text-xs font-medium uppercase tracking-[0.2em] text-white transition duration-200 hover:bg-[#C19A6B] hover:shadow-[0_12px_28px_-14px_rgba(193,154,107,0.9)] disabled:opacity-50"
              >
                {busy ? t("cloud.contact_submitting") : t("cloud.contact_submit")}
              </button>
            </form>
          )
        )}
      </div>
    </div>
  );
}

