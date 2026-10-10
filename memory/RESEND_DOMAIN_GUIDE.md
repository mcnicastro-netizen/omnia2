# 📧 Resend Domain Setup — OMNIA

**Stato email:** ✅ **VERIFIED** (dal 26-Giu-2026)  
**DNS:** Cloudflare (delegato da Aruba) — vedi anche [`DNS_SETUP_GUIDE.md`](./DNS_SETUP_GUIDE.md)  
**Ultimo aggiornamento:** 10 Ottobre 2026 (allineamento stack omnia2; **Vercel ancora pending**)

> **SoT sito/API/DNS FE:** `DNS_SETUP_GUIDE.md` (non Emergent).  
> Questo file resta SoT per **email Resend** + storia migrazione DNS.

---

## 🎯 Configurazione finale

| Parametro | Valore |
|---|---|
| **Sender email** | `OMNIA <info@omniarealestateecosystem.it>` |
| **Dominio Resend** | `omniarealestateecosystem.it` |
| **Resend Domain ID** | `37e0ca6a-2b7e-4b9d-85c6-cd3406d1c5b4` |
| **Region** | `eu-west-1` (GDPR-compliant) |
| **API Key** | `RESEND_API_KEY` in vault / `backend/.env` |
| **DNS provider** | **Cloudflare** (delegato da Aruba) |
| **Nameserver Cloudflare** | `brit.ns.cloudflare.com`, `jose.ns.cloudflare.com` |
| **Registrar** | Aruba (resta come registrar) |

---

## 🛣️ Storia della migrazione DNS (25-Giu-2026)

### Tentativo 1: Aruba DNS diretto
Inseriti 3 record TXT su Aruba via pannello DNS:
- ✅ `resend._domainkey` (DKIM)
- ✅ `send` (SPF TXT)
- ❌ `send` MX → **Aruba non accettava MX custom**

Risultato: dominio Resend resta `pending` perché manca il record MX.

### Tentativo 2: Migrazione DNS → Cloudflare
**Decisione Founder (25-Giu-2026, log CHANGELOG / HANDOFF):** spostare i DNS su Cloudflare; Aruba resta registrar.

**Procedura completata**:
1. Account Cloudflare con `info@omniarealestateecosystem.it`
2. Dominio `omniarealestateecosystem.it` → piano Free
3. Import record Aruba
4. Proxy: 🟠 site · ☁️ mail/TXT/MX Resend
5. MX `send` → `feedback-smtp.eu-west-1.amazonses.com` (prio 10)
6. NS Aruba → `brit.ns.cloudflare.com` + `jose.ns.cloudflare.com`
7. Propagazione → Resend **VERIFIED**

---

## 📋 Record DNS — email (TENERE)

### Email Aruba (casella @omniarealestateecosystem.it)
| Tipo | Nome | Valore | Priorità | Proxy |
|---|---|---|---|---|
| MX | @ | mx.omniarealestateecosystem.it | 10 | ☁️ |
| A | mx | IP Aruba mail (×N) | — | ☁️ |

### Resend (transazionale OMNIA)
| Tipo | Nome | Valore | Priorità |
|---|---|---|---|
| TXT | resend._domainkey | DKIM (valore da Resend dashboard) | — |
| TXT | send | `v=spf1 include:amazonses.com ~all` | — |
| MX | send | feedback-smtp.eu-west-1.amazonses.com | 10 |
| TXT | _dmarc | `v=DMARC1; p=none; rua=mailto:info@omniarealestateecosystem.it; …` | — |

---

## ⚠️ Record site / app — NON usare più Emergent

**Legacy (da sostituire al deploy Vercel):**

| Tipo | Nome | Valore vecchio | Nota |
|---|---|---|---|
| CNAME | app | `audit-tool-12.emergent.host` | ❌ host Emergent abbandonato |
| CNAME | cloud | `audit-tool-12.emergent.host` | ❌ idem |

**Target nuovo:** dopo deploy Vercel, CNAME/A come da dashboard Vercel — procedura in [`DNS_SETUP_GUIDE.md`](./DNS_SETUP_GUIDE.md) §4.

Finché Vercel non è live, apex/www possono dare **403** (DNS ok, origin assente). Per demo usare il tunnel Cloud (`omnia-stack.sh`).

---

## 🔄 Verifica Resend (se serve)

```bash
cd backend && set -a && source .env && set +a
python3 << 'EOF'
import os, httpx
key = os.environ.get("RESEND_API_KEY")
DOMAIN_ID = "37e0ca6a-2b7e-4b9d-85c6-cd3406d1c5b4"
r = httpx.get(
    f"https://api.resend.com/domains/{DOMAIN_ID}",
    headers={"Authorization": f"Bearer {key}"},
    timeout=15,
)
print(r.status_code, r.json().get("status"), r.json().get("records"))
EOF
```

Atteso: `status: verified`.

Test invio: `SENDER_EMAIL` deve essere `OMNIA <info@omniarealestateecosystem.it>` (non `onboarding@resend.dev`).

---

## 🚨 Troubleshooting

| Sintomo | Causa | Fix |
|---|---|---|
| Mail casella Aruba KO | MX/`mx` con proxy 🟠 | DNS only ☁️ |
| Resend pending | NS non CF / record incompleti | Verifica NS + record § Resend |
| Spam | DMARC `p=none` | OK in monitor; poi `quarantine` |
| Sito 403 | Vercel non collegato | Deploy Vercel + aggiorna CNAME (DNS_SETUP_GUIDE) |
| Demo non apre su dominio | Domino prod non ready | Usa tunnel `SHARE_URL.txt` |

---

## 📌 Decision log

- **25-Giu-2026**: migrazione DNS Aruba → Cloudflare per sbloccare Resend. Aruba = registrar.
- **26-Giu-2026**: Resend VERIFIED · primo invio ufficiale.
- **10-Ott-2026**: guide allineate a omnia2; **deploy Vercel ancora pending**; Emergent CNAME = legacy.
