import React, { useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { api } from "../../../shared/lib/api";
import { useAuth, formatApiErrorDetail } from "../../../shared/lib/auth";

export default function CloudRegisterPage() {
  const { t, i18n } = useTranslation();
  const lang = (i18n.language || "it").slice(0, 2);
  const nav = useNavigate();
  const { refresh } = useAuth();
  const [params] = useSearchParams();
  const presetIntent = params.get("intent");
  const [form, setForm] = useState({
    name: "", email: "", password: "",
    intents: presetIntent ? [presetIntent] : [],
    notification_channels: ["email"],
    gdpr_consent: false,
  });
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");
  const [done, setDone] = useState(null);

  const toggleArray = (key, val) => {
    setForm((f) => ({ ...f, [key]: f[key].includes(val) ? f[key].filter((v) => v !== val) : [...f[key], val] }));
  };

  const submit = async (e) => {
    e.preventDefault();
    setBusy(true); setErr("");
    try {
      const { data } = await api.post("/cloud/auth/register", { ...form, lang });
      setDone(data.user);
      await refresh(); // H6/R7 — sync AuthProvider with the freshly set auth cookies
    } catch (e) {
      setErr(formatApiErrorDetail(e?.response?.data?.detail) || String(e.message || e)); // R5
    } finally { setBusy(false); }
  };

  if (done) {
    return (
      <section className="max-w-md mx-auto py-20 px-5" data-testid="cloud-register-done">
        <div className="bg-white border border-stone-200 rounded-2xl p-8 text-center">
          <p className="text-3xl mb-3">✓</p>
          <h2 className="text-2xl font-light tracking-tight mb-2"
              style={{ fontFamily: "'Fraunces', Georgia, serif" }}>
            {t("cloud.reg_done_title")}
          </h2>
          <p className="text-sm text-stone-600 mb-6">
            {t("cloud.reg_done_text", { name: done.name })}
          </p>
          <button onClick={() => nav(`/${lang}/cloud`)}
            className="px-5 py-2.5 bg-[#0B1E3F] text-white text-xs uppercase tracking-widest rounded-md hover:bg-[#C19A6B]">
            {t("cloud.reg_back_home")}
          </button>
        </div>
      </section>
    );
  }

  return (
    <section className="max-w-xl mx-auto py-12 px-5" data-testid="cloud-register-page">
      <h1 className="text-3xl md:text-4xl font-light tracking-tight mb-2"
          style={{ fontFamily: "'Fraunces', Georgia, serif" }}>
        {t("cloud.reg_title")}
      </h1>
      <p className="text-stone-600 mb-8">{t("cloud.reg_subtitle")}</p>

      <form onSubmit={submit} className="bg-white border border-stone-200 rounded-2xl p-7 space-y-5">
        {err && <p data-testid="reg-error" className="text-sm text-red-700 bg-red-50 border border-red-200 rounded px-3 py-2">{err}</p>}

        <Field label={t("cloud.reg_name")}>
          <input data-testid="reg-name" required value={form.name}
            onChange={(e) => setForm({ ...form, name: e.target.value })}
            className="w-full px-3 py-2.5 border border-stone-300 rounded-md text-sm focus:border-stone-700 outline-none" />
        </Field>

        <Field label="Email">
          <input data-testid="reg-email" required type="email" value={form.email}
            onChange={(e) => setForm({ ...form, email: e.target.value })}
            className="w-full px-3 py-2.5 border border-stone-300 rounded-md text-sm focus:border-stone-700 outline-none" />
        </Field>

        <Field label={t("cloud.reg_password")}>
          <input data-testid="reg-password" required type="password" minLength={8} value={form.password}
            onChange={(e) => setForm({ ...form, password: e.target.value })}
            className="w-full px-3 py-2.5 border border-stone-300 rounded-md text-sm focus:border-stone-700 outline-none" />
          <p className="text-xs text-stone-500 mt-1">{t("cloud.reg_password_hint")}</p>
        </Field>

        <Field label={t("cloud.reg_intents_title")}>
          <div className="space-y-2">
            {[
              { id: "sell", label: t("cloud.reg_intent_sell"), desc: t("cloud.reg_intent_sell_desc") },
              { id: "rent_out", label: t("cloud.reg_intent_rent_out"), desc: t("cloud.reg_intent_rent_out_desc") },
              { id: "get_alerts", label: t("cloud.reg_intent_alerts"), desc: t("cloud.reg_intent_alerts_desc") },
            ].map((opt) => (
              <label key={opt.id} data-testid={`reg-intent-${opt.id}`}
                className={`block p-3 border rounded-lg cursor-pointer transition ${
                  form.intents.includes(opt.id) ? "border-[#0B1E3F] bg-[#0B1E3F]/5" : "border-stone-200 hover:border-stone-400"
                }`}>
                <input type="checkbox" checked={form.intents.includes(opt.id)}
                  onChange={() => toggleArray("intents", opt.id)} className="mr-2" />
                <span className="font-medium text-sm">{opt.label}</span>
                <p className="text-xs text-stone-500 ml-6">{opt.desc}</p>
              </label>
            ))}
          </div>
        </Field>

        <Field label={t("cloud.reg_channels_title")}>
          <div className="space-y-1.5">
            <label className="flex items-center gap-2 text-sm">
              <input type="checkbox" checked={form.notification_channels.includes("email")}
                onChange={() => toggleArray("notification_channels", "email")}
                data-testid="reg-channel-email" />
              ✉️ Email
            </label>
            <label className="flex items-center gap-2 text-sm text-stone-400 cursor-not-allowed" title="Disponibile prossimamente">
              <input type="checkbox" disabled />
              🔔 {t("cloud.reg_channel_push_coming")}
            </label>
          </div>
        </Field>

        <label className="flex items-start gap-2 text-xs text-stone-600">
          <input type="checkbox" checked={form.gdpr_consent}
            onChange={(e) => setForm({ ...form, gdpr_consent: e.target.checked })}
            data-testid="reg-gdpr" required />
          <span>{t("cloud.reg_gdpr_text")}</span>
        </label>

        <button type="submit" disabled={busy || form.intents.length === 0 || !form.gdpr_consent}
          data-testid="reg-submit-btn"
          className="w-full bg-[#0B1E3F] text-white px-6 py-3 rounded-lg font-medium text-sm uppercase tracking-widest hover:bg-[#C19A6B] transition disabled:opacity-50">
          {busy ? t("cloud.reg_submitting") : t("cloud.reg_submit_btn")}
        </button>
      </form>
    </section>
  );
}

function Field({ label, children }) {
  return (
    <div>
      <label className="block text-xs uppercase tracking-widest text-stone-500 mb-1.5">{label}</label>
      {children}
    </div>
  );
}
