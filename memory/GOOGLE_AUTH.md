# Accesso con Google (Sign-In)

OMNIA supporta **Continua con Google** su login e registrazione (GIS · ID token).  
**Stato 28-Ott-2026 · D-134**: live OK — Client ID Web reale su Railway + vault Environment.

## Cosa serve (Console Google)

1. [Google Cloud Console](https://console.cloud.google.com/) → progetto OMNIA
2. **Schermata di consenso OAuth** (External) + email supporto + (se Testing) test user Founder
3. **API e servizi → Credenziali → + Crea credenziali → ID client OAuth**
4. Tipo: **Applicazione Web**
5. **Origini JavaScript autorizzate** (produzione):
   - `https://omniarealestateecosystem.it`
   - `https://www.omniarealestateecosystem.it`
   - `https://app.omniarealestateecosystem.it`
   - `https://cloud.omniarealestateecosystem.it`
   - `https://omnia-frontend-kappa.vercel.app`
   - (dev) `http://127.0.0.1:43122` / `http://127.0.0.1:43123`
6. URI di reindirizzamento: **non obbligatori** per GIS (niente Client Secret)
7. Copia il **Client ID** — deve finire con `.apps.googleusercontent.com` (lunghezza tipica ~70+)

## Config OMNIA

| Dove | Variabile | Note |
|------|-----------|------|
| **Railway** `omnia-api` → Variables | `GOOGLE_CLIENT_ID` | **Obbligatorio per login live** |
| Cursor Environment omnia2 → Secrets | `GOOGLE_CLIENT_ID` | Agent / dogfood Cloud |
| `backend/.env` locale | `GOOGLE_CLIENT_ID` | Dev |

```bash
GOOGLE_CLIENT_ID=123456789-xxxx.apps.googleusercontent.com
```

**Anti-errore**: un valore corto / senza `apps.googleusercontent.com` → Google `401: invalid_client` (è successo con un placeholder in vault).

Dopo cambio su Railway: Deploy. Dopo vault Cursor: **nuovo agent** (il pod corrente non hot-reload).

FE: `GET /api/auth/google/config` → bottone solo se `enabled` + `client_id`.

Link operativi:
- Cursor Secrets: https://cursor.com/dashboard/cloud-agents/environments/e/b80b635c-b592-11f1-bb68-864e54d14197
- Railway: dashboard → progetto **omnia-api** → service **omnia-api** → Variables

## Comportamento

- Nuovo utente Google → account `client`, email verificata, poi onboarding agenzia se serve
- Email già registrata con password → collega Google e fa login
- Account solo-Google → il login password invita a usare Google

## Verifica

```bash
curl -s "$OMNIA_API_PUBLIC_URL/api/auth/google/config"
# enabled true + client_id che finisce con .apps.googleusercontent.com
```

Smoke UI: `https://app.omniarealestateecosystem.it/it/login` → Continua con Google.

| Sintomo | Causa | Fix |
|---------|--------|-----|
| `401: invalid_client` | Client ID assente/placeholder/revocato | Ricrea Web client · aggiorna Railway+vault |
| Origin non autorizzata | URL pagina non in JS origins | Aggiungi origin esatto (https, no path) |
| Bottone assente | `enabled: false` | Manca `GOOGLE_CLIENT_ID` nel processo API |

## Decision log

- **D-078**: Login Google abilitato (opzionale).
- **P-021**: era OFF in audit — **chiuso** 28-Ott con D-134 live.
- **28-Ott-2026 · D-134**: placeholder sostituito; consenso + Web client; Railway+Environment allineati.
