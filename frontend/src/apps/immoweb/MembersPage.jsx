import React, { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import AgencyShell from "./components/AgencyShell";
import InviteMemberModal from "./components/InviteMemberModal";
import { api } from "../../shared/lib/api";
import { useAuth } from "../../shared/lib/auth";

export default function MembersPage() {
  const { t } = useTranslation();
  const { user } = useAuth();
  const [tab, setTab] = useState("members");
  const [members, setMembers] = useState([]);
  const [invites, setInvites] = useState([]);
  const [loading, setLoading] = useState(true);
  const [modalOpen, setModalOpen] = useState(false);
  const [toast, setToast] = useState("");

  const canInvite = user?.role === "agency_admin" || user?.role === "super_admin";

  const load = async () => {
    setLoading(true);
    try {
      const [m, i] = await Promise.all([
        api.get("/app/agencies/me/members").catch(() => ({ data: [] })),
        canInvite
          ? api.get("/app/agencies/me/invites").catch(() => ({ data: [] }))
          : Promise.resolve({ data: [] }),
      ]);
      setMembers(m.data || []);
      setInvites(i.data || []);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const onInvited = (invite) => {
    setToast(t("members.invite_sent", { email: invite.email }));
    load();
    setTimeout(() => setToast(""), 3500);
  };

  const revoke = async (id) => {
    try {
      await api.delete(`/app/agencies/me/invites/${id}`);
      load();
    } catch {
      // ignore
    }
  };

  return (
    <AgencyShell current="members">
      <section data-testid="members-page" className="space-y-6">
        <div className="flex items-end justify-between flex-wrap gap-4">
          <div>
            <h1
              className="text-3xl md:text-4xl tracking-tight"
              style={{ fontFamily: "'Fraunces', Georgia, serif" }}
            >
              {t("members.title")}
            </h1>
            <p className="text-stone-600 mt-1">{t("members.subtitle")}</p>
          </div>
          {canInvite && (
            <button
              data-testid="open-invite-modal"
              onClick={() => setModalOpen(true)}
              className="px-5 py-2.5 bg-stone-900 text-stone-50 text-xs uppercase tracking-widest font-medium rounded-md hover:bg-stone-700 transition"
            >
              + {t("members.invite_btn")}
            </button>
          )}
        </div>

        {/* Tabs */}
        <div className="flex border-b border-stone-200" role="tablist">
          <TabBtn active={tab === "members"} onClick={() => setTab("members")} testid="tab-members">
            {t("members.tab_members")} ({members.length})
          </TabBtn>
          {canInvite && (
            <TabBtn active={tab === "invites"} onClick={() => setTab("invites")} testid="tab-invites">
              {t("members.tab_invites")} ({invites.filter((x) => x.status === "pending").length})
            </TabBtn>
          )}
        </div>

        {/* Toast */}
        {toast && (
          <p data-testid="invite-toast" className="text-sm text-emerald-800 bg-emerald-50 border border-emerald-200 rounded-md px-4 py-2">
            ✓ {toast}
          </p>
        )}

        {/* MEMBERS LIST */}
        {tab === "members" && (
          <div data-testid="members-list" className="bg-white border border-stone-200 rounded-lg overflow-hidden">
            {loading ? (
              <p className="p-6 text-sm text-stone-500">{t("common.loading")}</p>
            ) : members.length === 0 ? (
              <p className="p-6 text-sm text-stone-500">{t("members.no_members")}</p>
            ) : (
              <table className="w-full text-sm">
                <thead className="bg-stone-50 border-b border-stone-200">
                  <tr className="text-left text-xs uppercase tracking-widest text-stone-500">
                    <th className="px-4 py-3 font-medium">{t("members.table_name")}</th>
                    <th className="px-4 py-3 font-medium">{t("members.table_email")}</th>
                    <th className="px-4 py-3 font-medium">{t("members.table_role")}</th>
                    <th className="px-4 py-3 font-medium">{t("members.table_status")}</th>
                  </tr>
                </thead>
                <tbody>
                  {members.map((m) => (
                    <tr key={m.id} className="border-b border-stone-100 last:border-0" data-testid={`member-row-${m.id}`}>
                      <td className="px-4 py-3 font-medium text-stone-900">{m.name}</td>
                      <td className="px-4 py-3 text-stone-600">{m.email}</td>
                      <td className="px-4 py-3">
                        <span className="inline-block px-2 py-0.5 text-xs uppercase tracking-widest rounded bg-stone-100 text-stone-700">
                          {m.role}
                        </span>
                      </td>
                      <td className="px-4 py-3">
                        <span
                          className={`inline-block px-2 py-0.5 text-xs uppercase tracking-widest rounded ${
                            m.is_active
                              ? "bg-emerald-50 text-emerald-700"
                              : "bg-stone-100 text-stone-500"
                          }`}
                        >
                          {m.is_active ? t("members.status_active") : "—"}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        )}

        {/* INVITES LIST */}
        {tab === "invites" && (
          <div data-testid="invites-list" className="bg-white border border-stone-200 rounded-lg overflow-hidden">
            {loading ? (
              <p className="p-6 text-sm text-stone-500">{t("common.loading")}</p>
            ) : invites.length === 0 ? (
              <p className="p-6 text-sm text-stone-500">{t("members.no_invites")}</p>
            ) : (
              <table className="w-full text-sm">
                <thead className="bg-stone-50 border-b border-stone-200">
                  <tr className="text-left text-xs uppercase tracking-widest text-stone-500">
                    <th className="px-4 py-3 font-medium">{t("members.table_email")}</th>
                    <th className="px-4 py-3 font-medium">{t("members.table_role")}</th>
                    <th className="px-4 py-3 font-medium">{t("members.table_status")}</th>
                    <th className="px-4 py-3 font-medium text-right">{t("members.table_actions")}</th>
                  </tr>
                </thead>
                <tbody>
                  {invites.map((inv) => (
                    <tr key={inv.id} className="border-b border-stone-100 last:border-0" data-testid={`invite-row-${inv.id}`}>
                      <td className="px-4 py-3 font-medium text-stone-900">{inv.email}</td>
                      <td className="px-4 py-3 text-stone-600 uppercase text-xs tracking-widest">{inv.role}</td>
                      <td className="px-4 py-3">
                        <StatusBadge status={inv.status} t={t} />
                      </td>
                      <td className="px-4 py-3 text-right">
                        {inv.status === "pending" && (
                          <button
                            data-testid={`revoke-invite-${inv.id}`}
                            onClick={() => revoke(inv.id)}
                            className="text-xs uppercase tracking-widest text-red-700 hover:text-red-900"
                          >
                            {t("members.revoke")}
                          </button>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        )}
      </section>

      <InviteMemberModal open={modalOpen} onClose={() => setModalOpen(false)} onInvited={onInvited} />
    </AgencyShell>
  );
}

function TabBtn({ active, onClick, testid, children }) {
  return (
    <button
      onClick={onClick}
      data-testid={testid}
      className={`px-4 py-2.5 text-xs uppercase tracking-widest font-medium transition border-b-2 -mb-px ${
        active
          ? "border-stone-900 text-stone-900"
          : "border-transparent text-stone-500 hover:text-stone-900"
      }`}
    >
      {children}
    </button>
  );
}

function StatusBadge({ status, t }) {
  const map = {
    pending: { txt: t("members.status_pending"), cls: "bg-amber-50 text-amber-700" },
    accepted: { txt: t("members.status_accepted"), cls: "bg-emerald-50 text-emerald-700" },
    revoked: { txt: t("members.status_revoked"), cls: "bg-stone-100 text-stone-500" },
    expired: { txt: t("members.status_expired"), cls: "bg-red-50 text-red-700" },
  };
  const cfg = map[status] || map.pending;
  return (
    <span className={`inline-block px-2 py-0.5 text-xs uppercase tracking-widest rounded ${cfg.cls}`}>
      {cfg.txt}
    </span>
  );
}
