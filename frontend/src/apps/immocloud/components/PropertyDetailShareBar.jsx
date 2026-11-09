/* OMNIA — PropertyDetail ShareBar (MOVE-ONLY). */
import React, { useState } from "react";
import { useTranslation } from "react-i18next";

/* Share bar: WhatsApp, Facebook, X, email, copy link (+ native share on mobile) */
export default function ShareBar({ title, publicUrl }) {
  const { t } = useTranslation();
  const [copied, setCopied] = useState(false);
  const shareText = t("cloud.share_text", { title });
  const enc = encodeURIComponent;

  const copyLink = async () => {
    try {
      await navigator.clipboard.writeText(publicUrl);
    } catch {
      const ta = document.createElement("textarea");
      ta.value = publicUrl;
      document.body.appendChild(ta);
      ta.select();
      document.execCommand("copy");
      document.body.removeChild(ta);
    }
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const nativeShare = () => navigator.share({ title, text: shareText, url: publicUrl }).catch(() => {});

  const btnCls = "w-8 h-8 rounded-full border border-stone-200 bg-white flex items-center justify-center text-stone-600 hover:text-white transition";

  return (
    <div data-testid="detail-share-bar" className="flex items-center gap-2 mt-3">
      <span className="text-[11px] uppercase tracking-widest text-stone-500 mr-1">{t("cloud.share_label")}</span>
      <a
        data-testid="share-whatsapp" title={t("cloud.share_whatsapp")} aria-label={t("cloud.share_whatsapp")}
        href={`https://wa.me/?text=${enc(`${shareText}\n${publicUrl}`)}`}
        target="_blank" rel="noopener noreferrer"
        className={`${btnCls} hover:bg-[#25D366] hover:border-[#25D366]`}
      >
        <svg viewBox="0 0 24 24" className="w-4 h-4" fill="currentColor"><path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413z"/></svg>
      </a>
      <a
        data-testid="share-facebook" title={t("cloud.share_facebook")} aria-label={t("cloud.share_facebook")}
        href={`https://www.facebook.com/sharer/sharer.php?u=${enc(publicUrl)}`}
        target="_blank" rel="noopener noreferrer"
        className={`${btnCls} hover:bg-[#1877F2] hover:border-[#1877F2]`}
      >
        <svg viewBox="0 0 24 24" className="w-4 h-4" fill="currentColor"><path d="M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z"/></svg>
      </a>
      <a
        data-testid="share-x" title={t("cloud.share_x")} aria-label={t("cloud.share_x")}
        href={`https://twitter.com/intent/tweet?text=${enc(shareText)}&url=${enc(publicUrl)}`}
        target="_blank" rel="noopener noreferrer"
        className={`${btnCls} hover:bg-black hover:border-black`}
      >
        <svg viewBox="0 0 24 24" className="w-3.5 h-3.5" fill="currentColor"><path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z"/></svg>
      </a>
      <a
        data-testid="share-email" title={t("cloud.share_email")} aria-label={t("cloud.share_email")}
        href={`mailto:?subject=${enc(title || "")}&body=${enc(`${shareText}\n\n${publicUrl}`)}`}
        className={`${btnCls} hover:bg-[#0B1E3F] hover:border-[#0B1E3F]`}
      >
        <svg viewBox="0 0 24 24" className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth="2"><rect x="2" y="4" width="20" height="16" rx="2"/><path d="m22 7-10 7L2 7"/></svg>
      </a>
      <button
        data-testid="share-copy" type="button" title={t("cloud.share_copy")} aria-label={t("cloud.share_copy")}
        onClick={copyLink}
        className={`${btnCls} hover:bg-[#C19A6B] hover:border-[#C19A6B]`}
      >
        <svg viewBox="0 0 24 24" className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth="2"><rect x="9" y="9" width="13" height="13" rx="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>
      </button>
      {typeof navigator !== "undefined" && navigator.share && (
        <button
          data-testid="share-native" type="button" title={t("cloud.share_native")} aria-label={t("cloud.share_native")}
          onClick={nativeShare}
          className={`${btnCls} hover:bg-stone-700 hover:border-stone-700`}
        >
          <svg viewBox="0 0 24 24" className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="18" cy="5" r="3"/><circle cx="6" cy="12" r="3"/><circle cx="18" cy="19" r="3"/><path d="m8.59 13.51 6.83 3.98m-.01-10.98-6.82 3.98"/></svg>
        </button>
      )}
      {copied && (
        <span data-testid="share-copied-toast" className="text-xs text-emerald-700 bg-emerald-50 border border-emerald-200 rounded px-2 py-0.5">
          {t("cloud.share_copied")}
        </span>
      )}
    </div>
  );
}

