# Accesso con Google (Sign-In)

OMNIA supporta **Continua con Google** su login e registrazione (come Cursor/Emergent).

## Cosa serve

1. Progetto su [Google Cloud Console](https://console.cloud.google.com/)
2. **APIs & Services → Credentials → Create credentials → OAuth client ID**
3. Tipo: **Web application**
4. **Authorized JavaScript origins** (esempi):
   - `http://127.0.0.1:43122` (dev)
   - `https://tuodominio.com` (produzione)
   - URL preview tunnel se lo usi
5. Copia il **Client ID** (…`.apps.googleusercontent.com`)

Non serve Client Secret per questo flusso (ID token GIS).

## Config OMNIA

In `backend/.env`:

```bash
GOOGLE_CLIENT_ID=123456789-xxxx.apps.googleusercontent.com
```

Riavvia il backend. Il frontend legge `/api/auth/google/config` e mostra il bottone solo se la chiave c’è.

## Comportamento

- Nuovo utente Google → account `client`, email verificata, poi onboarding agenzia se serve
- Email già registrata con password → collega Google e fa login
- Account solo-Google → il login password invita a usare Google

## Verifica

```bash
curl -s http://127.0.0.1:43121/api/auth/google/config
# {"enabled": true, "client_id": "..."}  quando configurato
# {"enabled": false, "client_id": null}  altrimenti (bottone nascosto)
```
