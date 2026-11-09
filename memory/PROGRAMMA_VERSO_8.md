# Programma → **8 su tutte le lenti**

**Data**: 9 Novembre 2026 · Founder: «dobbiamo arrivare ad 8 in tutto»  
**Baseline** (post staging split + themes split + A-040 + SaaS fascicolo/blob/trash):

| Lente | Ora (stima) | Target | Gap |
|---|:-:|:-:|---|
| Storia vendibile | **~7,5** | **8** | pitch ok; manca prova commerciale ripetibile (Nicastro + pack live in main) |
| SaaS multi-tenant | **~5,8** | **8** | AuthZ oltre fascicolo · orphan GC · backup/restore · GDPR pacchetto Founders |
| Velocità evoluzione | **8** | **8** | tenere il ritmo; non spezzarlo con mega-refactor paralleli |
| Manutenibilità 12m | **~6,5** | **8** | portal · theme_render · FE Sell/PropertyDetail · helper tenant |
| Coerenza codice↔decisioni | **8** | **8** | non degradare (ogni onda aggiorna DECISIONS/CHANGELOG/HAL) |

**Regola d’ordine**: un filo alla volta. Mai mischiare SaaS + elefante FE nello stesso PR. Ogni onda = merge su `main` + smoke + riga changelog.

---

## Definizione di **8** (DoD per lente)

### Storia = 8
- Gallery **8 temi live** su `main` (PR #137) + listino D-151 in Brand Studio visibile.
- Nicastro dogfood: sito white-label + Perché OMNIA paperless (D-148) allineati.
- Un percorso demo ripetibile (A-037 minimo o clone keep-brand) senza inventare feature.
- Stripe one-shot template **non** obbligatorio per il voto 8 storia; lo è per monetizzare Starter.

### SaaS = 8
Checklist minima (da SoT `OMNIA_AUDIT_STATE` / A-035), tutte PASS:
1. **AuthZ cluster**: fascicolo ✅ già; sweep IDOR su media sensibili / modulistica / documenti paralleli (D-095).
2. **Media lifecycle**: trash→blob ✅ · fascicolo delete ✅ · **orphan GC scanner** in APScheduler (D-102).
3. **Backup/restore**: backup collections B2C complete; restore **singola agenzia** testabile (D-096) — smoke doc+runbook.
4. **Jobs**: registro owner single-instance rispettato (D-101); niente doppio cron silenzioso.
5. **GDPR Founders**: erase path documentato · DSAR assistito email · DPA stub/link (D-099) — self-serve export resta roadmap, non blocker 8.
6. Smoke multi-agency: 2 agenzie, zero leak cross-tenant su 5 endpoint critici.

### Manutenibilità = 8
Niente file “cervello unico” sopra ~700 LOC nei path caldi, oppure moduli con confini chiari:
1. `public_portal.py` (1119) → split MOVE-ONLY (auth/session · listings · media serve).
2. `theme_render.py` (988) → `theme_css.py` + `theme_home.py` (o equivalente); catalog resta separato.
3. FE: `SellPage.jsx` (1625) + `PropertyDetailPage.jsx` (1276) → hooks/sections; smoke visual invariato.
4. Helper tenant: `require_agency_id` unico (SUGGERIMENTI §1) su ≥5 router nuovi/toccati.
5. Gate: ogni split ha test di regressione ≥ quelli pre-split; zero cambio comportamento.

### Velocità + Coerenza = restano 8
- Max **1 elefante** o **1 cluster SaaS** per onda agent.
- Nessun New Project / Origin-tmp.
- Decisioni nuove → `DECISIONS.md` prima del codice se cambiano prodotto.

---

## Onde (sequenza fissa)

| Onda | Nome | Lente | Deliverable | Esito atteso |
|:-:|---|---|---|---|
| **0** | Lock baseline | tutte | Merge #137 gallery 8 · sync HAL Cap.8 · tabella voti in diario | Storia **7,5→~7,8** |
| **1** | Storia solida | Storia | Dogfood Nicastro: preview 2 temi MLS on/off + paperless in pitch · A-037 checklist onesta | Storia **8** |
| **2** | Elefante portal | Manut. | Split `public_portal.py` MOVE-ONLY | Manut. **~6,8** |
| **3** | Elefante theme_render | Manut. | Split CSS/home da `theme_render` | Manut. **~7,1** |
| **4** | Elefante FE Sell | Manut. | `SellPage` → sezioni/hooks + smoke B2C | Manut. **~7,4** |
| **5** | Elefante FE scheda | Manut. | `PropertyDetailPage` split + smoke | Manut. **~7,7** |
| **6** | AuthZ sweep | SaaS | IDOR matrix media/modulistica (oltre fascicolo) | SaaS **~6,3** |
| **7** | Orphan GC | SaaS | Scanner blob orfani + job APScheduler (D-102) | SaaS **~6,8** |
| **8** | Backup/restore | SaaS | Collections complete + restore 1-agency dry-run | SaaS **~7,4** |
| **9** | GDPR Founders | SaaS | Erase/DSAR/DPA path documentato + smoke | SaaS **~7,8** |
| **10** | Tenant helpers + chiusura | Manut.+SaaS | `shared/auth/tenant` · smoke 2-agency · ricalcolo voti | Manut. **8** · SaaS **8** |

**Opzionale parallelo (non blocca 8)**: Stripe checkout template D-151 · clone D-023 full · GTM-01.

---

## Cosa *non* fare in questo programma
- Riaprire listino crediti/bak (D-114) dentro le onde 0–10.
- Worker dedicato multi-pod (D-103 vieta ora).
- Mega-refactor “tutto FE” in un PR.
- Dichiarare SaaS=8 solo perché fascicolo AuthZ è verde.

---

## Come misurare (rituale fine onda)
1. Aggiornare riga in `docs/audit/portale-diario/YYYY-MM-DD.md` con voti.
2. Una frase onesta per lente (cosa manca ancora al 8).
3. Solo a fine **onda 10**: dichiarare «tutte a 8» in `CHANGELOG` + HAL reindex.

---

## Prossimo «vai»
Default consigliato: **Onda 0** (merge gallery 8) → subito **Onda 1** (dogfood storia) *oppure* **Onda 2** (portal) se priorità resta manutenibilità.
