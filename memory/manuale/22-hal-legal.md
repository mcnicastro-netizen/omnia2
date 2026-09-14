# Capitolo 22 · HAL Legal

> **Cosa trovi**: chat legale immobiliare con fonti, analisi PDF, storico sessioni. **D-051**: non è consulenza legale vincolante.

## 22.1 · Cos'è e dove lo trovi
- Menu ImmoWeb → **HAL Legal** (route `/:lang/legal`).
- Backend: `/api/app/legal/*` (chat, analyze-pdf, sessions, health).
- Usa Gemini + ricerca Tavily quando configurata (`TAVILY_API_KEY`).

## 22.2 · Chat
1. Apri HAL Legal.
2. Scrivi la domanda (contratti, APE, locazioni, privacy annunci…).
3. Ricevi risposta con **citazioni** quando disponibili.
4. Se il contesto è insufficiente, HAL lo dichiara (anti-allucinazione).

## 22.3 · Analisi PDF
- Endpoint `POST /api/app/legal/analyze-pdf`.
- Carica un PDF (contratto/bozza) per riassunto e punti di attenzione.
- Limiti v1: size/timeout; non firma digitale.

## 22.4 · Sessioni
- `GET /sessions`, `GET /sessions/{id}`, `DELETE /sessions/{id}`.
- Storico per utente autenticato.

## 22.5 · Limitazioni v1 (D-051)
- Non sostituisce avvocato/notaio.
- Tavily assente → qualità fonti ridotta.
- Nessun "parere firmato" scaricabile come atto.
- Academy/formazione legale avanzata fuori scope.

## 22.6 · Errori comuni
| Problema | Soluzione |
|----------|-----------|
| 503 llm | Configura `GEMINI_API_KEY` |
| Risposta generica | Fornisci città/legge/contesto nel prompt |
| PDF rifiutato | Controlla formato/size |

## 22.7 · Collegamenti
Cap. 10 HAL Agent · Cap. 12 HAL Knowledge · Cap. 7 Fascicolo.

**Versione capitolo**: v1.0 (2026-09-14 · Cursor M3).
