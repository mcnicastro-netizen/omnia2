import React, { useState } from "react";
import { useTranslation } from "react-i18next";
import { api } from "../../../shared/lib/api";
import { formatApiErrorDetail } from "../../../shared/lib/auth";

/**
 * Invite a member to the agency. Sends magic-link email.
 */
export default function InviteMemberModal({ open, onClose, onInvited }) {
  const { t } = useTranslation();
  const [email, setEmail] = useState("");
  const [name, setName] = useState("");
  const [role, setRole] = useState("agent");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");

  if (!open) return null;

  const submit = async (e) => {
    e.preventDefault();
    setError("");
    setSubmitting(true);
    try {
      const { data } = await api.post("/app/agencies/me/invites", {
        email: email.trim(),
        name_hint: name.trim() || null,
        role,
      });
      onInvited?.(data);
      setEmail("");
      setName("");
      setRole("agent");
      onClose();
    } catch (err) {
      setError(formatApiErrorDetail(err?.response?.data?.detail) || t("members.invite_error"));
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-stone-900/60 backdrop-blur-sm p-4"
      data-testid="invite-modal-backdrop"
      onClick={onClose}
    >
      <div
        className="bg-white w-full max-w-md rounded-xl border border-stone-200 shadow-xl"
        data-testid="invite-modal"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="px-6 py-5 border-b border-stone-200">
          <h2
            className="text-xl font-semibold text-stone-900"
            style={{ fontFamily: "'Fraunces', Georgia, serif" }}
          >
            {t("members.invite_modal_title")}
          </h2>
          <p className="text-sm text-stone-500 mt-1">{t("members.invite_modal_subtitle")}</p>
        </div>

        <form onSubmit={submit} className="px-6 py-5 space-y-4">
          <div>
            <label className="block text-xs uppercase tracking-widest text-stone-500 mb-1.5">
              {t("members.invite_email")}
            </label>
            <input
              type="email"
              required
              autoFocus
              data-testid="invite-email-input"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full px-3 py-2.5 border border-stone-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-stone-900/10 focus:border-stone-900"
              placeholder="agente@esempio.it"
            />
          </div>
          <div>
            <label className="block text-xs uppercase tracking-widest text-stone-500 mb-1.5">
              {t("members.invite_name")}
            </label>
            <input
              type="text"
              data-testid="invite-name-input"
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="w-full px-3 py-2.5 border border-stone-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-stone-900/10 focus:border-stone-900"
            />
          </div>
          <div>
            <label className="block text-xs uppercase tracking-widest text-stone-500 mb-1.5">
              {t("members.invite_role")}
            </label>
            <select
              data-testid="invite-role-select"
              value={role}
              onChange={(e) => setRole(e.target.value)}
              className="w-full px-3 py-2.5 border border-stone-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-stone-900/10 focus:border-stone-900"
            >
              <option value="agent">{t("auth.role_agent")}</option>
              <option value="agency_admin">{t("auth.role_agency_admin")}</option>
            </select>
          </div>

          {error && (
            <p data-testid="invite-error" className="text-sm text-red-700 bg-red-50 border border-red-200 rounded-md px-3 py-2">
              {error}
            </p>
          )}

          <div className="flex justify-end gap-3 pt-2">
            <button
              type="button"
              onClick={onClose}
              data-testid="invite-cancel-btn"
              className="px-4 py-2 text-sm text-stone-700 hover:text-stone-900"
            >
              {t("members.invite_cancel")}
            </button>
            <button
              type="submit"
              disabled={submitting}
              data-testid="invite-submit-btn"
              className="px-5 py-2.5 bg-stone-900 text-stone-50 text-xs uppercase tracking-widest font-medium rounded-md hover:bg-stone-700 disabled:opacity-50 transition"
            >
              {submitting ? t("common.loading") : t("members.invite_send")}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
