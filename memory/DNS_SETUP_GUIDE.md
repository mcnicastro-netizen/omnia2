# 🌐 GUIDA CONFIGURAZIONE DNS — omniarealestateecosystem.it

> **Obiettivo**: Configurare il dominio `omniarealestateecosystem.it` per puntare al deploy Emergent, con sottodomini per i 3 pilastri OMNIA.
> **Quando**: Sessione M1.S4 (deploy preview)
> **Prerequisito**: Dominio acquistato (✅ confermato dal Founder)

---

## 📋 STEP 1 — Identifica il tuo registrar

Dove hai comprato il dominio? I più comuni in Italia:
- **Aruba.it** → Pannello: https://admin.aruba.it
- **Register.it** → Pannello: https://controlpanel.register.it
- **Namecheap** → Pannello: https://ap.www.namecheap.com
- **GoDaddy** → Pannello: https://account.godaddy.com
- **OVH** → Pannello: https://www.ovh.com/manager

> Se non lo ricordi, cerca nella tua email "ordine dominio omniarealestateecosystem". Il registrar avrà mandato una conferma.

Una volta dentro il pannello, cerca la sezione: **"DNS"** / **"Zone DNS"** / **"Gestione DNS"** / **"DNS Records"**.

---

## 📋 STEP 2 — Ottieni l'URL del deploy Emergent

1. Vai su https://app.emergent.sh
2. Apri il progetto OMNIA
3. Premi il bottone **"Deploy"** in alto a destra
4. Segui il wizard fino a ottenere l'URL pubblico del deploy, tipo:
   ```
   https://omnia-xxxx.emergent.host
   ```
5. **Annota questo URL** — ci servirà per i record DNS.

> ⚠️ Il deploy Emergent è separato dal preview. L'URL di preview attuale (`audit-tool-12.preview.emergentagent.com`) NON è quello di produzione.

---

## 📋 STEP 3 — Configura i record DNS

Nel pannello DNS del tuo registrar, **cancella tutti i record A/CNAME esistenti** sul dominio principale (eccetto MX se hai email già attive) e aggiungi:

### 🟢 Dominio apex (omniarealestateecosystem.it)

| Tipo | Host/Nome | Valore | TTL |
|---|---|---|---|
| `A` | `@` (o vuoto) | `<IP fornito da Emergent>` | 3600 |
| `CNAME` | `www` | `omnia-xxxx.emergent.host` | 3600 |

> 🔵 **Nota**: Se Emergent fornisce un CNAME invece di un IP, usa `ALIAS` o `ANAME` invece di `A` per il dominio apex (alcuni registrar lo chiamano "CNAME flattening").

### 🟢 Sottodomini per le 3 app

| Tipo | Host/Nome | Valore | TTL |
|---|---|---|---|
| `CNAME` | `cloud` | `omnia-xxxx.emergent.host` | 3600 |
| `CNAME` | `app` | `omnia-xxxx.emergent.host` | 3600 |
| `CNAME` | `learn` | `omnia-xxxx.emergent.host` | 3600 |
| `CNAME` | `api` | `omnia-xxxx.emergent.host` | 3600 |

> Tutti puntano allo stesso URL Emergent. Sarà il **reverse proxy** Emergent + il routing path-based del frontend a smistare il traffico.

### Risultato atteso (post-propagazione)
- `https://omniarealestateecosystem.it` → Landing (IT/EN/ES)
- `https://www.omniarealestateecosystem.it` → Redirect a apex
- `https://cloud.omniarealestateecosystem.it` → ImmobilCloud (B2C)
- `https://app.omniarealestateecosystem.it` → ImmoWeb (B2B CRM)
- `https://learn.omniarealestateecosystem.it` → Omnia Academy (LMS)
- `https://api.omniarealestateecosystem.it` → API FastAPI

---

## 📋 STEP 4 — Configura il dominio personalizzato su Emergent

1. Vai su https://app.emergent.sh → progetto OMNIA → **Settings** → **Custom Domain**
2. Aggiungi i 5 domini uno per uno:
   - `omniarealestateecosystem.it`
   - `www.omniarealestateecosystem.it`
   - `cloud.omniarealestateecosystem.it`
   - `app.omniarealestateecosystem.it`
   - `learn.omniarealestateecosystem.it`
   - `api.omniarealestateecosystem.it`
3. Emergent ti chiederà di verificare ogni dominio (di solito basta che i DNS siano corretti).
4. **HTTPS/SSL**: Emergent genera automaticamente certificati Let's Encrypt **wildcard** una volta verificati i DNS. Non serve config manuale.

---

## 📋 STEP 5 — Tempi di propagazione

I record DNS si propagano in:
- **5-30 minuti** nella maggior parte dei casi (TTL basso)
- **Fino a 24-48h** worst case (TTL alto, DNS resolver pigro)

Verifica con:
```bash
# Da terminale
dig omniarealestateecosystem.it
dig cloud.omniarealestateecosystem.it
dig app.omniarealestateecosystem.it
dig learn.omniarealestateecosystem.it

# O da browser:
https://www.whatsmydns.net/#A/omniarealestateecosystem.it
```

---

## 📋 STEP 6 — Aggiorna le env vars dopo il deploy

Dopo che il dominio è attivo, **aggiorna**:

### `/app/backend/.env`
```env
CORS_ORIGINS="https://omniarealestateecosystem.it,https://www.omniarealestateecosystem.it,https://cloud.omniarealestateecosystem.it,https://app.omniarealestateecosystem.it,https://learn.omniarealestateecosystem.it"
FRONTEND_URL="https://omniarealestateecosystem.it"
```

### `/app/frontend/.env`
```env
REACT_APP_BACKEND_URL="https://api.omniarealestateecosystem.it"
```

Poi: `sudo supervisorctl restart backend frontend`

---

## 🚨 PROBLEMI COMUNI

### "Il dominio non risolve dopo 2 ore"
- Controlla che i record siano salvati (alcuni registrar richiedono "Applica modifiche")
- Verifica il TTL (più basso = più veloce)
- Prova `dig +short omniarealestateecosystem.it` — se restituisce vuoto, i DNS non sono ancora attivi

### "HTTPS non funziona (errore certificato)"
- Aspetta 10-15 min dopo che i DNS sono propagati: Let's Encrypt impiega tempo
- Verifica che TUTTI i sottodomini siano configurati su Emergent (Custom Domain)
- Se persiste, contatta support@emergent.sh

### "Sottodomini puntano alla Landing invece dell'app corretta"
- Il routing path-based gestisce questo via JS (vedi `App.js`). Se il sottodominio non è ancora mappato lato frontend, vedrai la Landing.
- **TODO M1.S4**: Aggiungere logica `App.js` che detecta `window.location.hostname` e redirige a `/cloud/*`, `/app/*`, `/learn/*` se il sottodominio è cloud./app./learn.

---

## 🎯 CHECKLIST FINALE

- [ ] DNS A/CNAME configurati su apex + 4 sottodomini
- [ ] Domini aggiunti su Emergent Custom Domain
- [ ] HTTPS verde su tutti i sottodomini
- [ ] CORS_ORIGINS aggiornato nel backend
- [ ] REACT_APP_BACKEND_URL aggiornato nel frontend
- [ ] Test manuale: apri ogni URL e verifica che renderizzi l'app corretta
- [ ] Test mobile: stessa cosa da smartphone

---

*Quando hai i DNS configurati, fammelo sapere e proseguiamo con la verifica deploy.*
