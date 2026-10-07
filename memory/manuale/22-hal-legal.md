# Capitolo 22 · HAL Legal

> **Cosa trovi**: chat legale immobiliare con fonti, analisi PDF, storico sessioni. **D-051**: non è consulenza legale vincolante.

## 22.1 · Cos'è e dove lo trovi
- Menu ImmoWeb / ImmobilCloud → **HAL Legal** (route `/:lang/legal`).
- Backend: `/api/app/legal/*` (chat, analyze-pdf, sessions, health).
- Usa Gemini + ricerca Tavily quando configurata (`TAVILY_API_KEY`). Preferire chiavi `tvly-dev-` in sandbox/demo.

## 22.2 · Chat
1. Apri HAL Legal.
2. Scrivi la domanda (contratti, APE, locazioni, privacy annunci…).
3. Ricevi risposta con **citazioni** quando Tavily+Gemini sono ok.
4. Se il contesto è insufficiente, HAL lo dichiara (anti-allucinazione).

### 22.2.1 · Paywall B2C (€1 a domanda) — 7 Ott 2026
- Account **`account_type=b2c`** (privati ImmobilCloud): ogni domanda richiede un credito pagato.
- Prodotto Stripe one-shot: `b2c_hal_legal_query` (€1,00).
- Senza credito: `POST /api/app/legal/chat` → **HTTP 402** `payment_required` + CTA checkout in UI (`LegalApp` → `/billing/b2c/checkout`).
- Credito consumato dopo risposta ok (`b2c_entitlements.check/consume_hal_legal_query_credit`).
- Account **B2B** (agenzia / CRM): nessun paywall €1 su questa chat (resta wallet/piano agenzia dove previsto).
- Effetto post-pagamento: serve webhook Stripe `checkout.session.completed` (vedi Cap. 19 §19.10.6).

## 22.3 · Analisi PDF
- Endpoint `POST /api/app/legal/analyze-pdf`.
- Carica un PDF (contratto/bozza) per riassunto e punti di attenzione.
- Limiti v1: size/timeout; non firma digitale.

## 22.4 · Sessioni
- `GET /sessions`, `GET /sessions/{id}`, `DELETE /sessions/{id}`.
- Storico per utente autenticato.

## 22.5 · Limitazioni v1 (D-051)
- Non sostituisce avvocato/notaio.
- Tavily assente → timeout / fonti deboli (configura `TAVILY_API_KEY`).
- Nessun "parere firmato" scaricabile come atto.
- Academy/formazione legale avanzata fuori scope.
- B2C: senza pagamento (o senza webhook) la domanda non parte / il credito non si attiva.

## 22.6 · Errori comuni
| Problema | Soluzione |
|----------|-----------|
| 402 payment_required | Privato: paga €1 (CTA) oppure attendi webhook se hai già pagato |
| 503 llm / timeout | `GEMINI_API_KEY` + `TAVILY_API_KEY` nel process (vault o `.env` pod) |
| Risposta generica | Fornisci città/legge/contesto nel prompt |
| PDF rifiutato | Controlla formato/size |

## 22.7 · Collegamenti
Cap. 10 HAL Agent · Cap. 12 HAL Knowledge · Cap. 7 Fascicolo · Cap. 19 §19.10 Billing/webhook.

**Versione capitolo**: v1.1 (2026-10-07 · paywall B2C + Tavily sandbox).
