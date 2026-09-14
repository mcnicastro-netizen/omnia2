# 📧 Resend Domain Setup — OMNIA

**Stato attuale**: ✅ **VERIFIED** — dominio operativo dal 26-Giu-2026 mattina
**Ultimo aggiornamento**: 26 Giugno 2026 (mattina)

---

## 🎯 Configurazione finale

| Parametro | Valore |
|---|---|
| **Sender email** | `OMNIA <info@omniarealestateecosystem.it>` |
| **Dominio Resend** | `omniarealestateecosystem.it` |
| **Resend Domain ID** | `37e0ca6a-2b7e-4b9d-85c6-cd3406d1c5b4` |
| **Region** | `eu-west-1` (GDPR-compliant) |
| **API Key** | `RESEND_API_KEY` in `/app/backend/.env` |
| **DNS provider** | **Cloudflare** (delegato da Aruba) |
| **Nameserver Cloudflare** | `brit.ns.cloudflare.com`, `jose.ns.cloudflare.com` |
| **Registrar** | Aruba (resta come registrar) |

---

## 🛣️ Storia della migrazione DNS (25-Giu-2026)

### Tentativo 1: Aruba DNS diretto
Inseriti 3 record TXT su Aruba via pannello DNS:
- ✅ `resend._domainkey` (DKIM)
- ✅ `send` (SPF TXT)
- ❌ `send` MX → **Aruba non permette MX custom** (limitazione strutturale)

Risultato: dominio Resend resta `pending` perché manca il record MX.

### Tentativo 2: Migrazione DNS → Cloudflare
**Decisione (D-029)**: spostare i DNS del dominio su Cloudflare mantenendo Aruba come registrar.
**Motivazione**:
- Cloudflare supporta tutti i tipi di record (incluso MX custom su sottodominio)
- Gratis
- Bonus: CDN, SSL universale, anti-DDoS, propagazione veloce
- Reversibile

**Procedura completata**:
1. Creato account Cloudflare con `info@omniarealestateecosystem.it`
2. Aggiunto dominio `omniarealestateecosystem.it` → piano Free
3. Cloudflare ha importato automaticamente tutti i record Aruba
4. Configurati proxy correttamente:
   - 🟠 Proxy ON: `@` (radice), `www`, `admin`, `_domainconnect`
   - ☁️ DNS only: tutti gli `mx` (mail Aruba), `app`, `cloud`, tutti i TXT, tutti gli MX
5. Aggiunto record MX `send` → `feedback-smtp.eu-west-1.amazonses.com` priorità 10
6. Cambiati nameserver su Aruba: `brit.ns.cloudflare.com` + `jose.ns.cloudflare.com`
7. ⏳ In attesa propagazione (1-4 ore tipico, max 24h)

---

## 📋 Record DNS finali su Cloudflare

### Site
| Tipo | Nome | Valore | Proxy |
|---|---|---|---|
| A | @ | 172.66.2.113 | 🟠 |
| A | @ | 162.159.142.117 | 🟠 |
| CNAME | www | omniarealestateecosystem.it | 🟠 |
| CNAME | admin | admin.redirect.aruba.it | 🟠 |
| CNAME | _domainconnect | _domainconnect.hst.aruba.it | 🟠 |

### Email Aruba (mail principale @omniarealestateecosystem.it)
| Tipo | Nome | Valore | Priorità | Proxy |
|---|---|---|---|---|
| MX | @ | mx.omniarealestateecosystem.it | 10 | ☁️ |
| A | mx | 62.149.128.74 / .151 / .154 / .157 / .160 / .163 / .166 | — | ☁️ (×7) |

### Subdomain OMNIA → Emergent preview
| Tipo | Nome | Valore | Proxy |
|---|---|---|---|
| CNAME | app | audit-tool-12.emergent.host | ☁️ |
| CNAME | cloud | audit-tool-12.emergent.host | ☁️ |

⚠️ **TODO**: aggiungere CNAME `learn` → `audit-tool-12.emergent.host` (per Academy). Backend CORS si aspetta `learn.omniarealestateecosystem.it`.

### Resend (email transazionale OMNIA)
| Tipo | Nome | Valore | Priorità |
|---|---|---|---|
| TXT | resend._domainkey | `p=MIGfMA0GCSqG...wIDAQAB` (DKIM) | — |
| TXT | send | `v=spf1 include:amazonses.com ~all` (SPF) | — |
| MX | send | feedback-smtp.eu-west-1.amazonses.com | 10 |
| TXT | _dmarc | `v=DMARC1; p=none; rua=mailto:info@omniarealestateecosystem.it; pct=100; adkim=s; aspf=s` | — |

---

## 🔄 Cosa fare al prossimo accesso

### 1. Verificare propagazione nameserver
```bash
python3 -c "
import httpx
r = httpx.get('https://dns.google/resolve', params={'name':'omniarealestateecosystem.it','type':'NS'})
print(r.json())
"
```
Atteso: 2 nameserver Cloudflare (`brit.ns.cloudflare.com`, `jose.ns.cloudflare.com`).

### 2. Forzare verifica dominio Resend
```bash
cd /app/backend && python3 << 'EOF'
import os, httpx
from dotenv import load_dotenv
load_dotenv('/app/backend/.env')
key = os.environ.get('RESEND_API_KEY')
DOMAIN_ID = '37e0ca6a-2b7e-4b9d-85c6-cd3406d1c5b4'
httpx.post(f'https://api.resend.com/domains/{DOMAIN_ID}/verify', headers={'Authorization': f'Bearer {key}'}, timeout=15)
r = httpx.get(f'https://api.resend.com/domains/{DOMAIN_ID}', headers={'Authorization': f'Bearer {key}'}, timeout=15)
print(r.json())
EOF
```
Atteso: `status: verified` su tutti e 3 i record (DKIM, SPF TXT, SPF MX).

### 3. Test invio email live
```bash
cd /app/backend && python3 << 'EOF'
import os, resend
from dotenv import load_dotenv
load_dotenv('/app/backend/.env')
resend.api_key = os.environ.get('RESEND_API_KEY')
r = resend.Emails.send({
    'from': os.environ.get('SENDER_EMAIL'),
    'to': ['mcnicastro@gmail.com'],
    'subject': '[OMNIA] Verifica dominio Resend - PASSED',
    'html': '<h1>OMNIA Resend Domain Verified</h1><p>Mail di test dal sender ufficiale.</p>'
})
print(r)
EOF
```
Verificare arrivo in **INBOX** (non spam) con sender pulito `OMNIA <info@omniarealestateecosystem.it>`.

### 4. Setup webhook bounce (opzionale, raccomandato)
Andare su Resend Dashboard → Webhooks → aggiungere endpoint POST per ricevere notifiche bounce/complaint in tempo reale.

---

## 🚨 Troubleshooting

| Sintomo | Causa | Fix |
|---|---|---|
| `status: pending` su tutti i record | Nameserver Cloudflare non propagati | Aspetta, max 24h |
| `status: pending` solo su MX `send` | MX non propagato | Aspetta, max 1h dopo propagazione NS |
| Mail finisce in spam | DMARC `p=none` (modalità monitor) | OK per ora, dopo 2 settimane senza problemi alzare a `p=quarantine` |
| Mail Aruba `@omniarealestateecosystem.it` non funziona | Record `mx` A o MX `@` con proxy ON | Rimettere "DNS only" |
| Sito B2C non risponde | CNAME `app` o `cloud` proxied | Rimettere "DNS only" |

---

## 📌 Decision log
- **D-029** (25-Giu-2026): Migrazione DNS Aruba → Cloudflare per sbloccare verifica dominio Resend. Aruba mantiene il ruolo di registrar.
