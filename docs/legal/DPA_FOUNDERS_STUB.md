# Data Processing Agreement (DPA) — stub Founders OMNIA

**Versione:** stub 0.1 · 9 Novembre 2026 · **D-099**  
**Stato:** bozza operativa per primi clienti · **da rivedere con legale** prima di firma commerciale ampia  
**Lingua:** italiano (versione EN su richiesta)

---

## 1. Parti

- **Titolare del trattamento (Cliente):** `[RAGIONE_SOCIALE]` · P.IVA `[PIVA]` · sede `[INDIRIZZO]` · contatto privacy `[EMAIL_PRIVACY_CLIENTE]`
- **Responsabile del trattamento (Fornitore):** OMNIA / soggetto contrattuale Founder · contatto `privacy@omniarealestateecosystem.it`

## 2. Oggetto

Il Fornitore tratta dati personali per conto del Cliente esclusivamente per erogare la piattaforma OMNIA (gestionale immobili, portale, servizi correlati sottoscritti).

## 3. Categorie di dati e interessati

| Categoria | Esempi | Interessati |
|-----------|--------|-------------|
| Account | email, nome, log accesso | utenti Cliente / privati B2C |
| CRM | anagrafiche clienti, richieste | clienti del Cliente |
| Immobili / media | schede, foto, documenti fascicolo | proprietari / prospect |
| Consensi / audit | `consent_events`, log erase | utenti |

## 4. Finalità e istruzioni

Trattamento solo per: hosting applicativo, backup, supporto, sicurezza, obblighi di legge. Nessuna vendita di dati a terzi. Sub-responsabili cloud (hosting, email, AI media) elencati in allegato tecnico aggiornato dal Fornitore.

## 5. Sicurezza (sintesi)

Misure: autenticazione, isolamento tenant per `agency_id`, cifratura in transito (TLS), backup con retention limitata, procedure erase/export self-service utente, AuthZ su documenti sensibili.

## 6. Diritti degli interessati

Il Cliente resta interfaccia primaria verso gli interessati. Il Fornitore assiste con procedura **DSAR Founders** (`docs/ops/GDPR_FOUNDERS.md`): export, rettifica, erase dove tecnicamente applicabile.

## 7. Durata e cancellazione

Alla cessazione del contratto: account non operativi; wipe/retention secondo runbook offboarding (D-098 V1 controllata) e retention backup. «Elimina per sempre» in prodotto = fuori dall’area operativa utente, non garanzia assenza da bak non scaduti (D-097).

## 8. Trasferimenti extra-UE

Se un sub-responsabile tratta fuori SEE: clausole contrattuali tipo / trasferimenti ammessi — **da completare con legale** e elenco fornitori.

## 9. Firme

| | Cliente | Fornitore |
|--|---------|-----------|
| Nome | | |
| Ruolo | | |
| Data | | |
| Firma | | |

---

*Questo stub non è consulenza legale. Non usare come unico DPA per clienti enterprise senza revisione.*
