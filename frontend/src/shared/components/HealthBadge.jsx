import React from "react";
import { useTranslation } from "react-i18next";
import { api } from "../lib/api";
import Brand from "./Brand";

/**
 * HealthBadge: small UI widget that hits the backend health endpoint
 * for a specific app and shows green/red dot + label.
 *
 * Props:
 *   - app: "core" | "cloud" | "app" | "learn" | "global"
 *   - label: optional override (treated as brand name → not translated)
 */
export default function HealthBadge({ app, label }) {
  const { t, i18n } = useTranslation();
  const [status, setStatus] = React.useState("checking");
  const [detail, setDetail] = React.useState("");

  React.useEffect(() => {
    let mounted = true;
    const url = app === "global" ? "/health" : `/${app}/health`;
    api
      .get(url)
      .then((r) => {
        if (!mounted) return;
        setStatus("ok");
        setDetail(r.data?.message?.text || "");
      })
      .catch(() => {
        if (!mounted) return;
        setStatus("error");
        setDetail(t("health.error"));
      });
    return () => {
      mounted = false;
    };
  }, [app, i18n.language, t]);

  const dot =
    status === "ok"
      ? "bg-emerald-500"
      : status === "error"
      ? "bg-red-500"
      : "bg-amber-400 animate-pulse";

  return (
    <div
      data-testid={`health-badge-${app}`}
      className="flex items-center gap-2 text-xs font-medium tracking-wide text-stone-700 min-w-0"
    >
      <span className={`h-2 w-2 rounded-full flex-shrink-0 ${dot}`} />
      <Brand className="flex-shrink-0">{label || app}</Brand>
      {detail && <span className="text-stone-500 truncate">— {detail}</span>}
    </div>
  );
}
