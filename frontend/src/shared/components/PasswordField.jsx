import React, { useState } from "react";
import { useTranslation } from "react-i18next";

function EyeIcon({ open }) {
  if (open) {
    return (
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" aria-hidden="true">
        <path d="M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7S2 12 2 12Z" stroke="currentColor" strokeWidth="1.6" />
        <circle cx="12" cy="12" r="3" stroke="currentColor" strokeWidth="1.6" />
      </svg>
    );
  }
  return (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <path d="M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7S2 12 2 12Z" stroke="currentColor" strokeWidth="1.6" />
      <circle cx="12" cy="12" r="3" stroke="currentColor" strokeWidth="1.6" />
      <path d="M4 4l16 16" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" />
    </svg>
  );
}

/**
 * Password input with show/hide toggle (occhietto).
 * Pass through standard input props (value, onChange, required, minLength, …).
 */
export default function PasswordField({
  className = "w-full px-3 py-2.5 pr-12 border border-stone-200 rounded-lg text-sm focus:border-[#0B1E3F] outline-none",
  "data-testid": testId = "password-field",
  autoComplete = "new-password",
  ...rest
}) {
  const { t } = useTranslation();
  const [show, setShow] = useState(false);
  return (
    <div className="relative">
      <input
        {...rest}
        type={show ? "text" : "password"}
        autoComplete={autoComplete}
        data-testid={testId}
        className={className}
      />
      <button
        type="button"
        data-testid={`${testId}-toggle`}
        onClick={() => setShow((v) => !v)}
        className="absolute right-2 top-1/2 -translate-y-1/2 p-2 text-stone-500 hover:text-stone-900"
        aria-label={
          show
            ? t("auth.hide_password", "Nascondi password")
            : t("auth.show_password", "Mostra password")
        }
        title={
          show
            ? t("auth.hide_password", "Nascondi password")
            : t("auth.show_password", "Mostra password")
        }
      >
        <EyeIcon open={show} />
      </button>
    </div>
  );
}
