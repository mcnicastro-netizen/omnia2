/**
 * MC-040 — Accetta proposta Main Admin commerciale (Cabina / deep-link notifica).
 */
import { useMemo, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { api } from "@/shared/lib/api";
import AgencyShell from "@/apps/immoweb/components/AgencyShell";
import { Button } from "@/components/ui/button";
import { toast } from "sonner";

export default function MainAdminTransferPage() {
  const { i18n } = useTranslation();
  const lang = (i18n.language || "it").slice(0, 2);
  const nav = useNavigate();
  const [params] = useSearchParams();
  const transferId = (params.get("transfer_id") || "").trim();
  const token = (params.get("token") || "").trim();
  const [busy, setBusy] = useState(false);
  const [done, setDone] = useState(false);

  const canAccept = useMemo(() => Boolean(transferId && token), [transferId, token]);

  const onAccept = async () => {
    if (!canAccept) return;
    setBusy(true);
    try {
      await api.post("/billing/commercial/main-admin/transfer/accept", {
        transfer_id: transferId,
        token,
      });
      setDone(true);
      toast.success("Main Admin accettato");
    } catch (e) {
      const detail = e?.response?.data?.detail;
      const err =
        (typeof detail === "object" && detail?.error) ||
        (typeof detail === "string" ? detail : null) ||
        "accept_failed";
      toast.error(`Impossibile accettare: ${err}`);
    } finally {
      setBusy(false);
    }
  };

  return (
    <AgencyShell>
      <div className="max-w-lg mx-auto py-10 px-4" data-testid="main-admin-transfer-page">
        <h1 className="text-xl font-semibold text-[#0B1E3F]">Proposta Main Admin</h1>
        <p className="mt-2 text-sm text-stone-600">
          Hai ricevuto una proposta di Main Admin commerciale. Accettandola diventi
          l&apos;unico amministratore commerciale del cliente (P.IVA).
        </p>
        {!canAccept && (
          <p className="mt-4 text-sm text-amber-800 bg-amber-50 border border-amber-200 rounded-md p-3">
            Link incompleto: mancano transfer_id o token. Apri la notifica dalla campanella.
          </p>
        )}
        {done ? (
          <div className="mt-6 space-y-3">
            <p className="text-sm text-emerald-800">Proposta accettata.</p>
            <Button
              type="button"
              onClick={() => nav(`/${lang}/app/settings/billing`)}
              data-testid="main-admin-transfer-goto-billing"
            >
              Vai a Piano &amp; Crediti
            </Button>
          </div>
        ) : (
          <Button
            type="button"
            className="mt-6"
            disabled={!canAccept || busy}
            onClick={onAccept}
            data-testid="main-admin-transfer-accept"
          >
            {busy ? "Attendere…" : "Accetta"}
          </Button>
        )}
      </div>
    </AgencyShell>
  );
}
