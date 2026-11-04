# Portale ImmobilCloud — stato API esterne (probe 4 Nov 2026, Europe/Rome)

Ambiente: Cloud Agent omnia2 · API locale `43121` · secret vault PRESENT (check-secrets OK).  
Valori secret **mai** stampati.

## Tabella

| API | Ruolo portale | Sandbox ora | Note |
|-----|---------------|-------------|------|
| **Stripe** `sk_test` | Visura, planimetria, staging €, boost, slot publish | **OK** | `STRIPE_ENABLED=true`, balance 200. Live solo a go-live. |
| **OpenAPI.it Catasto** | Visura PDF + planimetria | **OK sandbox** | ping 200 su `test.catasto.openapi.it` · catalog `/cloud/visura` e `/cloud/planimetria` `openapi_enabled=true` |
| **Resend** | Email lead/alert/welcome | **OK** | Dominio `omniarealestateecosystem.it` |
| **Gemini** | HAL improve, safety LLM, staging critique | **OK** | models list 200 |
| **fal.ai** | Virtual staging foto | **OK** | auth 200 |
| **Nominatim OSM** | Geocode / fallback ANNCSU | **OK** | pubblico |
| **ANNCSU via OMNIA** | Autocomplete indirizzi Vendi | **OK** | health + suggest (fallback Nominatim se serve) |
| **Google OAuth** | Login Google B2C | **PRESENT** | `GOOGLE_CLIENT_ID` formato OK (no click-login probe) |
| **Tavily** | HAL Legal search | **SCADUTA / 401** | Key in vault ma API risponde 401 — rinnovare in console Tavily (sandbox/prod stessa key di solito) |
| **Yousign / YouTrust** | Firma elettronica | **SCADUTA sandbox** | Key 401 su `api-sandbox.yousign.app` · inventario: scadenza 25/10/2026 · ticket rotazione: nuova key sandbox non emessa → `ESIGN_PROVIDER=mock`. **Non bloccante portale B2C** (è CRM modulistica). Ripresa tipicamente su **account/prod** YouTrust. |

## Flussi portale → dipendenze

| Flusso UI | Dipendenze | Stato dogfood |
|-----------|------------|---------------|
| Registrazione / login / Google | JWT, Resend (verify/welcome), Google OAuth | OK (Resend+JWT); Google client presente |
| Vendi + geocode indirizzo | ANNCSU/Nominatim | OK |
| Staging AI a pagamento | Stripe test + fal (+ Gemini critique) | OK |
| Boost / slot annuncio | Stripe test | OK |
| Visura catastale | Stripe test + OpenAPI sandbox | OK |
| Planimetria catastale | Stripe test + OpenAPI sandbox | OK |
| Contatti / inbox / alert email | Resend | OK |
| HAL Legal (search web) | Tavily (+ Gemini) | **Tavily KO** → Legal senza search esterna |
| Firma documenti (CRM) | Yousign | **mock** (sandbox key morta) |

## Solo produzione (non rinnovabili / non usabili in sandbox)

1. **Stripe live** (`sk_live` / `pk_live`) — pagamento reale; Cloud dogfood resta su test.
2. **OpenAPI.it live** (`OPENAPI_MODE=live` + key prod) — PDF ufficiali a pagamento wallet; sandbox oggi funziona per dogfood.
3. **YouTrust/Yousign** — sandbox key scaduta e non re-emessa post-revoca; firma reale = percorso produzione/console YouTrust + `ESIGN_PROVIDER=yousign`.

## Azioni consigliate (ordine)

1. **Tavily**: nuova API key in console → vault → nuovo agent (sblocca HAL Legal search).
2. **Yousign**: attendere/emettere key prod o nuova sandbox se console lo permette; fino ad allora lasciare `mock` (portale OK).
3. Go-live: Stripe live + OpenAPI live + Resend già su dominio verified.
