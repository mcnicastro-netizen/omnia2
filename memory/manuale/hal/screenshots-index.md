# 📸 Screenshots Index — Manuale OMNIA

Questo file elenca i placeholder `[SCREEN: id]` presenti nel manuale e nelle voci HAL.
Ogni id è unico e riutilizzabile: se lo screenshot è già stato prodotto, riferirsi allo stesso id nei capitoli successivi.

**Convenzione**
- ID in `kebab-case`, con prefisso capitolo (es. `cap1-...`).
- Descrizione = cosa deve mostrare l'immagine (per chi la scatterà: te, uno stagista, o Playwright automation futura).
- Priorità: 🔴 essenziale · 🟡 utile · 🟢 nice-to-have.
- Note: eventuali dati sensibili da mascherare / cornici / annotazioni.

**Come usarlo**
1. Quando produci lo screenshot, aggiungi la data nella colonna **Fatto**.
2. Se cambi qualcosa nell'UI (rename, redesign), rimuovi la data → l'immagine va rifatta.
3. Nome file consigliato: `<id>.png` (es. `cap1-login-form.png`) in `/app/memory/manuale/screenshots/`.

---

## Capitolo 1 · Primo accesso

| # | ID | Cosa mostrare | Priorità | Note | Fatto |
|---|----|---------------|:-:|------|:-:|
| 1 | `cap1-orientamento-generale` | Schermata iniziale ImmoWeb con la barra a sinistra visibile, TopNav in alto e HAL button in evidenza (freccia o riquadro rosso). Usa una demo agency di prova. | 🔴 | Nascondere email reali. Preferibile viewport 1440×900. | — |
| 2 | `cap1-login-form` | Pagina di login (`/it/login`) con campi email/password vuoti. Focus sul pulsante "Accedi". | 🔴 | Nessun dato precompilato. Vuoto pulito. | — |
| 3 | `cap1-forgot-password` | Pagina "Password dimenticata" (`/it/forgot-password`) con campo email + pulsante "Invia link di recupero". | 🟡 | Vuoto pulito. | — |
| 4 | `cap1-onboarding-step4-conferma` | Ultimo passo dell'onboarding wizard: anteprima colori (primario + accento), tagline, tasto **Crea agenzia** in evidenza. | 🔴 | Usa colori demo (blu/oro tipico agenzia). Tagline esempio: *"Casa tua, dal 1985."*. | — |
| 5 | `cap1-sidebar-completa` | Barra a sinistra completa con tutte le voci visibili al ruolo **titolare** (Dashboard, Gruppo, API Keys, Importa, Portali, Immobili, Clienti, Match, Sito web, Virtual Staging, Mutui, HAL Legal, HAL Knowledge, Collaboratori, Piano & Crediti, Impostazioni). | 🔴 | Login come utente demo *agency_admin* attivo su agenzia demo. | — |
| 6 | `cap1-language-switcher` | Menu a tendina della lingua aperto in alto a destra, con IT/EN/ES visibili. Sfondo: dashboard sfocato. | 🟢 | Cattura in modalità *hover/open* del menu. | — |
| 7 | `cap1-selettore-agenzia` | Selettore agenzia aperto in alto a sinistra (utente attivo in 2 o più agenzie demo). | 🟡 | Serve creare un utente demo membro di 2 agenzie. Se costoso da preparare, rimuovere. | — |
| 8 | `cap1-profilo-utente` | Pagina Profilo utente con campi nome/cognome/foto/telefono + sezione **Sicurezza** con pulsante *Cambia password*. | 🟢 | Dati profilo demo, nessun contatto reale. | — |

**Totale Cap. 1**: 8 screenshot (5 essenziali, 2 utili, 1 nice-to-have).

---

## Capitolo 2 · Dashboard

| # | ID | Cosa mostrare | Priorità | Note | Fatto |
|---|----|---------------|:-:|------|:-:|
| 1 | `cap2-dashboard-panoramica` | Vista completa Dashboard subito dopo login: saluto in alto, griglia 6 KPI card, nota in fondo. | 🔴 | Usare agenzia demo *Immobiliare Rossi* con numeri realistici (non tutti 0, non tutti fittizi-perfetti). Consigliato: 12 immobili, 8 lead, 4 match, 2 visite, 3 collab, 1 invito. | — |
| 2 | `cap2-dashboard-kpi-6cards` | Solo la griglia dei 6 riquadri KPI in primo piano (senza header). Utile come "focus" nel manuale. | 🟡 | Stessi dati demo di sopra. Serve per legenda contatori. | — |

**Totale Cap. 2**: 2 screenshot (1 essenziale, 1 utile).

---

## Capitolo 3 · Immobili

| # | ID | Cosa mostrare | Priorità | Note | Fatto |
|---|----|---------------|:-:|------|:-:|
| 1 | `cap3-property-form-nuovo` | Form completo *"+ Nuovo immobile"* con i campi principali visibili (Titolo, Tipologia, Operazione, Indirizzo, Prezzo, Superficie), tab Foto in fondo. | 🔴 | Campi vuoti o con dati demo *Immobiliare Rossi*. Sezione "Privacy" visibile in basso. | — |
| 2 | `cap3-import-csv-flow` | Pagina Importa scheda **📋 Template CSV**: dropzone tratteggiata + link "Scarica template" + preview tabella prime 5 righe. | 🔴 | Consigliato: mostrare fase 3 con tabella già popolata (dati demo). | — |
| 3 | `cap3-xml-import-preview` | Pagina **Importa** (`/app/import`) dopo click "Analizza contenuto": report analisi con ripartizioni per tipologia/città e warning. | 🟡 | Usare un feed XML demo con ~50 immobili. | — |
| 4 | `cap3-photos-dropzone-cover` | Sezione Fotografie in form immobile: dropzone + 4-6 miniature con badge ⭐ Copertina sulla prima. | 🔴 | Foto demo interni case (senza persone). | — |
| 5 | `cap3-privacy-selector` | Menu/riquadro privacy con L1/L2/L3/L4 e descrizione a lato di ciascuno. | 🔴 | Selezionato L2 con etichetta *"Consigliato per la maggior parte degli annunci"*. | — |
| 6 | `cap3-state-select` | Menu Stato aperto: Bozza · Pubblicato · Prenotato · Venduto · Affittato · Ritirato. | 🟡 | Ricorda evidenziare "Pubblicato" con checkmark. | — |
| 7 | `cap3-fascicolo-checklist` | Vista Fascicolo con checklist 10 documenti: alcuni ✅ (APE, Visura), alcuni ⚠️ (Planimetria, Atto), alcuni ⬜ (facoltativi). | 🔴 | Immobile demo tipologia *Appartamento* (mostra anche righe condominio). | — |

**Totale Cap. 3**: 7 screenshot (5 essenziali, 2 utili).

---

## Capitolo 4 · Clienti

| # | ID | Cosa mostrare | Priorità | Note | Fatto |
|---|----|---------------|:-:|------|:-:|
| 1 | `cap4-client-form-nuovo` | Form completo *"+ Nuovo cliente"*: sezione **Anagrafica** compilata con dati demo, sezione **Preferenze di ricerca** con campi visibili, spunta GDPR attiva. | 🔴 | Dati demo: cliente *Anna Verdi · anna.verdi@example.it · +39 333 000 0001 · Acquirente · Nuovo · Origine: Idealista*. | — |
| 2 | `cap4-preferences-form` | Solo sezione **Preferenze di ricerca** con multi-select tipologie + città + range prezzo/superficie compilati. | 🔴 | Preferenze demo: Appartamento + Attico, Belpasso, €150k-€250k, 80-120 m², 3 locali min. | — |
| 3 | `cap4-import-csv-flow` | Pagina **Importa clienti** scheda **📋 Template CSV** dopo caricamento file demo: dropzone + preview tabella prime 5 righe. | 🔴 | 5 righe demo con nomi variegati (Rossi, Bianchi, ecc.). | — |
| 4 | `cap4-smart-import-ai-preview` | Scheda **⚡ Import AI** dopo caricamento file "brutto" (Excel vecchio): tabella preview con badge confidenza per riga. | 🔴 | Includere 1-2 righe evidenziate in giallo *"sotto soglia confidenza"*. | — |
| 5 | `cap4-property-seller-link` | Form immobile con campo *"Cliente venditore / proprietario"* aperto: risultati ricerca (dropdown con 3-4 clienti trovati) o messaggio *"Nessun cliente venditore trovato"*. | 🟡 | Mostra sia lo stato "collegato" sia lo stato "vuoto con suggerimento crea". | — |
| 6 | `cap4-smart-sorting-buckets` | Vista lista Clienti con **linguette bucket** attive in alto: *Tutti · Da chiamare oggi · Roventi 🔥 · Caldi 🌶️ · Tiepidi ☀️ · Freddi ❄️ · Acquirenti · Venditori*. Selezionato "Roventi". Tabella sotto con 5-6 clienti + badge temperatura + numero match + azioni rapide (Chiama, WhatsApp). | 🔴 | Il più importante di questo capitolo. | — |

**Totale Cap. 4**: 6 screenshot (5 essenziali, 1 utile).

---

## Capitolo 5 · Match

| # | ID | Cosa mostrare | Priorità | Note | Fatto |
|---|----|---------------|:-:|------|:-:|
| 1 | `cap5-matches-lista` | Vista principale **Match** con filtro Score minimo `50+ buoni` (default). Elenco 6-8 righe con badge temperatura colorati (rovente/caldo/tiepido/freddo). | 🔴 | Mix di temperature per illustrare la scala visivamente. | — |
| 2 | `cap5-temperature-legenda` | Focus/zoom sui 4 badge temperatura affiancati con range punti sotto ciascuno (`85-100`, `65-84`, `40-64`, `<40`). Può essere anche un banner tabellare. | 🔴 | Utile come "focus" nel manuale. | — |
| 3 | `cap5-scoring-breakdown` | Dettaglio match aperto: sezione **Breakdown** con barre orizzontali per ciascuno dei 14 criteri + punti (es. `Prezzo 15/17`, `Città 12/12`, `Zona 2/5`). Sezione **Cosa manca** con 2-3 righe testuali (es. *"Zona non tra le preferite"*). | 🔴 | Il più importante di Cap. 5. Serve al titolare per capire come è composto lo score. | — |
| 4 | `cap5-lista-filtri` | Vista Match con menu filtro Score minimo aperto (dropdown con le 4 opzioni: 40+/50+/65+/85+). | 🟡 | Frame catturato con dropdown espanso. | — |
| 5 | `cap5-lead-scoring-ai` | Lista Clienti con bottone **⚡ Aggiorna AI (N)** in alto e alcuni clienti con badge temperatura misti. | 🟡 | Riusabile anche in Cap. 4 (già catalogato lì). Duplicare solo se si vuole enfasi. | — |

**Totale Cap. 5**: 5 screenshot (3 essenziali, 2 utili).

---

## Capitolo 6 · Portali / Publishing

| # | ID | Cosa mostrare | Priorità | Note | Fatto |
|---|----|---------------|:-:|------|:-:|
| 1 | `cap6-portali-panoramica` | Pagina **Portali** con hero + 3 metric card in alto (Portali attivi, Disponibili, Catalogo totale) + banner ambra "Compliance HARD attiva + Sync automatico" + tab switcher Attivi/Disponibili sotto. | 🔴 | Agenzia demo *Immobiliare Rossi* con 2 portali attivi (Subito + Bakeca) e 6 disponibili. | — |
| 2 | `cap6-catalog-disponibili` | Scheda **Disponibili** aperta: tabella con 6-8 portali, colonna "Traffico" con stelle, colonna "Modalità" (feed_pull / api_push), bottone verde **Attiva** a destra su ogni riga. | 🔴 | Ordinamento traffic_score decrescente (Subito in cima con ★★★★★). | — |
| 3 | `cap6-modale-attivazione` | Modale **Attiva [portale]**: nome portale in header, note descrittive, form credenziali (es. campo Username per Subito), bottoni "Annulla" (grigio) + "Attiva portale" (verde). | 🔴 | Portale scelto: Wikicasa con campo "API Key" visibile. | — |
| 4 | `cap6-sync-manuale-esito` | Scheda **Attivi** con banner **emerald** sopra la tabella: "Sync subito — 8 immobili pubblicabili, 2 bloccati dal validatore compliance". Riga portale Subito con "Ultimo sync: oggi 14:23 · 8 pubblicati · 2 bloccati". | 🔴 | Banner ha ✕ chiudibile a destra. Nella riga si vedono 3 azioni: Sync, Compliance, Disattiva. | — |
| 5 | `cap6-modale-compliance` | Modale **Compliance Subito.it**: 4 metric card in griglia (Totale 10, Pubblicabili 8, Bloccati 2, Con warning 3) + sezione "Motivi blocco più frequenti" con 3 righe rosse (es. "Meno di 3 foto: 9 immobili") + lista "Immobili bloccati (primi 20)" con titolo + motivi + link "Correggi →". | 🔴 | Il più importante del capitolo. Serve al titolare per capire l'operatività. | — |
| 6 | `cap6-wizard-step4-conferma` | Step 4 del **Wizard Custom Portal**: box con URL feed OMNIA della tua agenzia (es. `.../api/publishing/feed/immobiliare-rossi.xml?dialect=osf_federata`) + bottone **Copia** a destra (dopo il click mostra "Copiato ✓"). | 🟡 | Portale demo custom: "Portale AgenziaLiguria" con dialect osf_federata. | — |

**Totale Cap. 6**: 6 screenshot (5 essenziali, 1 utile).

---

## Capitolo 7 · Fascicolo Immobile

| # | ID | Cosa mostrare | Priorità | Note | Fatto |
|---|----|---------------|:-:|------|:-:|
| 1 | `cap7-fascicolo-panoramica` | Vista d'insieme pagina Fascicolo: hero immobile (titolo/città/tipologia/superficie) + card Prezzo annuncio + card Stima AI + badge coerenza. Poi checklist + sezione Analisi HAL sotto. | 🔴 | Agenzia demo *Immobiliare Rossi*, immobile appartamento Belpasso 95 m². | — |
| 2 | `cap7-fascicolo-stima-badge` | Focus/zoom sulle 3 card in alto: Prezzo annuncio (es. € 195.000) + Stima AI (media + banda min-max, es. € 178.000 · 165k-195k) + badge celeste *In linea con la stima AI*. | 🔴 | Serve come esempio didattico dei 3 stati badge (verde/celeste/ambra). Preparare 3 varianti se possibile. | — |
| 3 | `cap7-checklist-vista` | Vista completa checklist documentale: 5 righe obbligatorie (3 verdi ✅ + 2 rosse 🔴 mancanti), 3 righe consigliate grigie ⚪, 2 righe condominio grigie. Barra progresso in alto `3/5 obbligatori` in ambra. | 🔴 | Il più importante del capitolo. Includere nota inline "APE non caricato ma classe A dichiarata" sulla riga rossa APE. | — |
| 4 | `cap7-upload-flow` | Modale/riga di upload documento: bottone **⬆ Carica** in stato *"..."* (loading) su una riga rossa (es. Planimetria catastale). Sotto la riga, tag documento caricato in verde con nome file (`planimetria-2025.pdf`) + ✕ elimina. | 🟡 | Se lo scatto in loading è complicato, spezza in due immagini (before/after). | — |
| 5 | `cap7-analisi-hal` | Sezione Analisi HAL espansa con report generato: 4-5 bullet con emoji (⚠️ documenti mancanti, ✅ prontezza, 🚨 rischi), timestamp e nota "Analisi HAL (Gemini)" in fondo. | 🔴 | Il testo può essere fittizio ma realistico (es. "Mancano APE e visura, notaio blocca la firma"). | — |

**Totale Cap. 7**: 5 screenshot (4 essenziali, 1 utile).

---

## Capitolo 8 · Sito web agenzia

| # | ID | Cosa mostrare | Priorità | Note | Fatto |
|---|----|---------------|:-:|------|:-:|
| 1 | `cap8-website-panoramica` | Vista completa pagina Sito web: hero + 4 sezioni visibili (Brand Extractor, Temi, Live Preview, Dominio personalizzato). L'iframe della preview mostra il sito pubblico brandato *Immobiliare Rossi*. | 🔴 | Agenzia demo con tema Classic attivo e 6-8 immobili nella vetrina. | — |
| 2 | `cap8-brand-extractor` | Sezione Brand Extractor con URL già estratta (`https://www.nicastroimmobiliare.it/`): pannello risultato con confidence 78/100 verde, 4 chip palette, pill voice=professionale, header=classic, card=shadow_lift + bottone verde **⚡ Applica automaticamente**. | 🔴 | Confidence alta per mostrare il caso "ideale". | — |
| 3 | `cap8-theme-picker` | Griglia 4 card temi (Minimal, Classic, Bold, Luxury) con anteprima palette a 3 chip su ognuna. Card "Classic" evidenziata come **✓ Attivo** in verde. | 🔴 | Serve come colpo d'occhio didattico sui 4 stili. | — |
| 4 | `cap8-scheda-pubblica` | Screenshot della **scheda pubblica di un immobile** aperto dall'anteprima: hero titolo + prezzo grande + griglia foto + tabella caratteristiche + share block (WhatsApp/FB/Email/Copia link). | 🔴 | Immobile demo: appartamento Belpasso 3 locali, tema Classic per estetica istituzionale. Il più importante del capitolo. | — |
| 5 | `cap8-custom-domain-flow` | Sezione Custom Domain con dominio `www.nicastroimmobiliare.it` già in stato **pending** (badge ambra): pannello DNS instructions con record TXT (`_omnia-challenge...`) + CNAME (`agencies.omnia...`) + bottone **Copia** + bottone **Verifica DNS**. | 🟡 | Utile ma opzionale: alcuni founder non arriveranno a questo step subito. | — |

**Totale Cap. 8**: 5 screenshot (4 essenziali, 1 utile).

---

## Capitolo 9 · Virtual Staging

| # | ID | Cosa mostrare | Priorità | Note | Fatto |
|---|----|---------------|:-:|------|:-:|
| 1 | `cap9-staging-panoramica` | Pagina Virtual Staging vista d'insieme: dropzone drag&drop in alto, pillole stile (5) + tipo stanza (6) + modalità (2) + slider num_variants, bottone **Genera render** in verde. | 🔴 | Agenzia demo *Immobiliare Rossi*. Nessun render lanciato ancora. | — |
| 2 | `cap9-staging-pipeline` | Vista job in progress: 3 stage con status live (SAM 2 ✅ done 6.2s $0.001, Flux ⏳ running, Upscale ⚪ queued) + banner "Costo totale finora: $0.06". | 🔴 | Il più importante del capitolo per far capire cosa succede. | — |
| 3 | `cap9-staging-before-after` | Vista Before/After side-by-side: foto sorgente stanza vuota a sinistra, render arredato in modern con watermark "Render virtuale OMNIA" a destra + bottone **Scarica con watermark**. | 🔴 | Il watermark deve essere ben visibile in basso a destra. | — |
| 4 | `cap9-staging-multi-variants` | Vista 4 varianti multi_style: griglia 2×2 con 4 render dello stesso soggiorno (modern, classic, scandi, luxury) + costo totale rendering "72 crediti · $0.22 fal.ai". | 🟡 | Utile ma può essere posticipato. | — |
| 5 | `cap9-staging-history` | Cronologia render utente: tabella con miniature + stile + tipo stanza + timestamp + status + azioni (Download / Salva come foto / Elimina). 6-8 righe di render passati. | 🟡 | Serve per far capire dove ritrovare i vecchi render. | — |

**Totale Cap. 9**: 5 screenshot (3 essenziali, 2 utili).

---

## Capitolo 10 · HAL Agent CRM

| # | ID | Cosa mostrare | Priorità | Note | Fatto |
|---|----|---------------|:-:|------|:-:|
| 1 | `cap10-hal-chat-widget` | Chat widget HAL aperto sopra una pagina ImmoWeb: pannello 380×580 con storico conversazione (2-3 turn), area input in basso, bottone Nuova sessione in header. Ideale con badge *"Sto pensando..."* visibile. | 🔴 | Il colpo d'occhio principale del capitolo. | — |
| 2 | `cap10-hal-chat-tool` | Chat HAL in azione con badge *"🔍 Consulto query_properties..."* → risposta HAL con bullet list di 5 immobili trovati (mock: trilocali Milano, prezzi €280k-320k). | 🔴 | Serve per far capire i tool CRM in azione. | — |
| 3 | `cap10-hal-improve-modal` | Modale *"Migliora con HAL"* aperta su un campo Descrizione: testo originale a sinistra (bozza approssimativa), testo migliorato a destra (paragrafo fluido 800 caratteri), selettore lingua IT/EN/ES con IT attivo, bottone **Applica**. | 🔴 | Il più importante per il caso d'uso PropertyForm/SellPage. | — |
| 4 | `cap10-hal-sessions-list` | Pannello elenco sessioni HAL: 6-8 righe con preview primo messaggio + timestamp + counter messaggi + bottone Elimina per riga. | 🟡 | Utile ma opzionale. | — |
| 5 | `cap10-hal-error-429` | Chat HAL con toast/messaggio rosso *"Limite orario raggiunto (60 msg/h). Attendi la finestra scorrevole"* dopo un rate limit. | 🟡 | Serve per didattica errori — può essere sostituito con testo. | — |

**Totale Cap. 10**: 5 screenshot (3 essenziali, 2 utili).

---

## Capitolo 11 · Mutui comparatore

| # | ID | Cosa mostrare | Priorità | Fatto |
|---|----|---------------|:-:|:-:|
| 1 | `cap11-mutui-panoramica` | Form comparatore + tabella risultati ordinata per TAEG: 4-6 offerte visibili con banca/rata/TAEG + badge "Consap under-36" quando attivo. In fondo disclaimer legale in evidenza. | 🔴 | — |
| 2 | `cap11-mutui-sostenibilita` | Card sostenibilità con reddito 3.000€ + best rata 890€ → badge verde "Sostenibile · 29,7% del reddito" + max_sustainable_rata 1.050€. | 🔴 | — |
| 3 | `cap11-mutui-piano-ammortamento` | Modale piano ammortamento espanso: tabella primi 12 mesi con colonne mese/rata/interessi/capitale/saldo residuo + riepilogo annuale sotto. | 🔴 | — |

**Totale Cap. 11**: 3 screenshot (tutti essenziali).

---

## Capitolo 12 · HAL Knowledge

| # | ID | Cosa mostrare | Priorità | Fatto |
|---|----|---------------|:-:|:-:|
| 1 | `cap12-halk-panoramica` | Pagina HAL Knowledge caricata: titolo *"Chiedi ad HAL"*, campo di testo vuoto con placeholder, 5 domande di esempio cliccabili in basso, badge di stato in alto a destra (`📚 617 chunk · 4200 termini | 🤖 gemini-3-flash-preview`). | 🔴 | — |
| 2 | `cap12-halk-risposta-fonti` | Risposta HAL renderizzata: prosa con marker `[FONTE 1]`, badge verde "Alta confidence · 32%" in alto a destra, blocco *"Fonti citate"* sotto con 3-5 righe (file .yaml del manuale, sezione, percentuale similarity). | 🔴 | — |
| 3 | `cap12-halk-status-badge` | Zoom sul badge di stato in alto a destra della pagina HAL Knowledge, con dettaglio dei contatori (chunks_indexed, vocab_size, model name). | 🟡 | Utile ma opzionale. | — |

**Totale Cap. 12**: 3 screenshot (2 essenziali, 1 utile).

---

## Capitolo 13 · Team & Ruoli (Collaboratori)

| # | ID | Cosa mostrare | Priorità | Fatto |
|---|----|---------------|:-:|:-:|
| 1 | `team-members-list` | Pagina Collaboratori con tab **Membri** attiva: tabella con 3-5 righe (Nome, Email, Ruolo badge `AGENT`/`AGENCY_ADMIN`, Stato "Attivo"). Bottone *"+ Invita membro"* in alto a destra visibile. | 🔴 | — |
| 2 | `team-invite-modal` | Modal "Invita nuovo membro" aperto sopra la pagina Collaboratori: campo Email compilato con `agente@esempio.it`, Nome opzionale, select **Ruolo** aperto che mostra le due opzioni **Agent** e **Agency admin**. | 🔴 | — |
| 3 | `team-accept-invite` | Pagina `/accept-invite` dal punto di vista del collega invitato: intestazione con nome agenzia (*"Nicastro Immobiliare"*) + ruolo assegnato + email in evidenza, form con campi Nome e Password (min 8), bottone "Accetta invito". | 🔴 | — |

**Totale Cap. 13**: 3 screenshot (tutti essenziali).

---

## Capitolo 14 · Import XML (Migrazione)

| # | ID | Cosa mostrare | Priorità | Fatto |
|---|----|---------------|:-:|:-:|
| 1 | `import-xml-upload` | Pagina *"Importa da altro gestionale"* con area drag&drop vuota, bottone *"Scegli file"*, sottotitolo che menziona *"il tuo attuale gestionale"* (mai vendor specifico). | 🔴 | — |
| 2 | `import-xml-preview` | Preview post-upload con banner verde *"Analisi completata: X/Y immobili leggibili"*, 3 cards *"Per tipologia / Per contratto / Per città"*, tabella samples 5 righe, toggle *"Salta immobili già presenti"* attivo, bottoni *"Simulazione"* e *"Importa in OMNIA"*. | 🔴 | — |
| 3 | `import-xml-commit-result` | Banner verde di successo *"✅ Import completato: N immobili importati con successo, M saltati (già presenti)"* dopo il commit reale. | 🟡 | Utile ma opzionale. |

**Totale Cap. 14**: 3 screenshot (2 essenziali, 1 utile).

---

## Capitolo 15 · Social Publisher

| # | ID | Cosa mostrare | Priorità | Fatto |
|---|----|---------------|:-:|:-:|
| 1 | `cap15-social-panoramica` | Pagina Social Publisher con 3 card canali (Facebook Page blu #1877F2, Instagram Business rosa #E4405F, Telegram azzurro #26A5E4), badge status "Attivo" su almeno un canale, elenco *"Post recenti"* con 3-5 righe in basso. | 🔴 | — |
| 2 | `cap15-config-modal` | Modale *"Configura canale Facebook Page"* aperta: campi `Facebook Page ID` e `Page Access Token` compilati (mascherati), pulsante *"Salva credenziali"*, badge testo *"Le credenziali verranno cifrate AES-256-GCM"* per rassicurare l'utente. | 🔴 | — |
| 3 | `cap15-publish-multichannel` | Modale di pubblicazione dalla scheda immobile: 3 checkbox canali (FB/IG/TG), textarea caption pre-riempita con caption default, anteprima foto principale, bottone *"Pubblica adesso"* + indicatore risultato multi-canale (ok/fail per canale). | 🔴 | — |

**Totale Cap. 15**: 3 screenshot (tutti essenziali).

---

## Capitolo 16 · Compliance Portali (deep-dive normativo)

| # | ID | Cosa mostrare | Priorità | Fatto |
|---|----|---------------|:-:|:-:|
| 1 | `compliance-modale-hard` | Modale compliance aperta dalla card portale in PublishingPage: header con nome portale, 4 box metriche (Totale/Pubblicabili/Bloccati/Con warning), elenco top-5 motivi HARD con etichette in italiano (*"Prezzo mancante"*, *"Meno di 3 foto"*, ecc.). | 🔴 | — |
| 2 | `compliance-mapping-campi` | Scheda immobile con evidenziate le 4 sezioni chiave per compliance: **Prezzo**, **Caratteristiche** (superficie + locali), **Efficienza energetica** (classe APE dropdown + IPE), **Localizzazione** (city + province), **Foto** (upload area). | 🔴 | — |
| 3 | `compliance-soft-warnings` | Modale compliance con card *"Con warning"* espansa che mostra 3-4 SOFT (title_too_short, description_too_short, rooms_not_specified, ipe_missing) — badge ambra vs badge rosso HARD. | 🟡 | Utile ma opzionale. |

**Totale Cap. 16**: 3 screenshot (2 essenziali, 1 utile).

---

## Cap. 17 · Domain Vault

Riferimento: `memory/manuale/17-domain-vault.md`

| # | ID | Cosa mostrare | Priorità | Fatto |
|---|----|---------------|:-:|:-:|
| 1 | `cap17-domain-verify` | Pagina DomainVerifyPage: TXT record + CNAME_TARGET evidenziati, stato pending → verified con timestamp. | 🔴 | — |
| 2 | `cap17-domain-sovereignty-policy` | Pagina DomainSovereigntyPolicyPage con la promessa D-054 ("OMNIA never registers a domain"), lista dei registrar consigliati indipendenti. | 🔴 | — |
| 3 | `cap17-rdap-checker` | Pagina domain-check pubblica con risultato RDAP (owner, registrar, expiry date). | 🟡 | Utile ma opzionale. |

**Totale Cap. 17**: 3 screenshot (2 essenziali, 1 utile).

---

## Cap. 18 · Notifiche e attività

Riferimento: `memory/manuale/18-notifiche-attivita.md`

| # | ID | Cosa mostrare | Priorità | Fatto |
|---|----|---------------|:-:|:-:|
| 1 | `cap18-email-welcome` | Email `welcome.it.html` renderizzata in client email (Gmail/Outlook): logo OMNIA, saluto `{{user_name}}`, CTA "Vai alla dashboard". | 🔴 | — |
| 2 | `cap18-email-agency-invite` | Email `agency_invite.it.html`: subject "Sei stato invitato...", nome invitatore, ruolo assegnato, magic-link. | 🔴 | — |
| 3 | `cap18-email-lead-notification` | Email `lead_notification.it.html`: dettagli lead (nome/email/telefono/messaggio) + link scheda immobile. | 🔴 | — |
| 4 | `cap18-email-saved-search` | Email `saved_search_alert.it.html`: digest HTML con tabella max 6 righe immobili + CTA "Vai al mio account". | 🔴 | — |
| 5 | `cap18-toast-success` | Toast sonner verde in ImmoWeb dopo creazione immobile riuscita ("Immobile creato ✓"). | 🟡 | Utile ma opzionale. |
| 6 | `cap18-toast-error` | Toast sonner rosso in BillingPage.jsx dopo checkout fallito ("Pagamento fallito"). | 🟡 | Utile ma opzionale. |
| 7 | `cap18-dashboard-kpi` | Dashboard ImmoWeb con i 6 KPI counter (Immobili attivi, Lead aperti, Nuovi match 7gg, Visite 7gg, Collaboratori, Inviti pendenti) — a evidenziare che NON è un activity feed. | 🔴 | Chiave per D-051. |

**Totale Cap. 18**: 7 screenshot (5 essenziali, 2 utili).

---

## Cap. 19 · Impostazioni agenzia

Riferimento: `memory/manuale/19-impostazioni-agenzia.md`

| # | ID | Cosa mostrare | Priorità | Fatto |
|---|----|---------------|:-:|:-:|
| 1 | `cap19-settings-identity` | SettingsPage sezione Identità: input display_name + input tagline. | 🔴 | — |
| 2 | `cap19-settings-fiscal` | SettingsPage sezione Dati fiscali: legal_name + VAT + CF (in griglia 2 colonne). | 🔴 | — |
| 3 | `cap19-settings-address` | SettingsPage sezione Indirizzo: street + city + province (2 char UP) + CAP in griglia 3 colonne. | 🟡 | Utile ma opzionale. |
| 4 | `cap19-settings-contact` | SettingsPage sezione Contatti: email + telefono in griglia 2 colonne. | 🟡 | Utile ma opzionale. |
| 5 | `cap19-settings-website-external` | SettingsPage modalità Sito web `external` selezionata: bottone verde attivo + pane URL input. | 🔴 | — |
| 6 | `cap19-settings-website-template` | SettingsPage modalità Sito web `omnia_template` selezionata: 3 preview `minimal`/`elegant`/`bold` con tag amber "presto disponibile". | 🔴 | Chiave per D-051 (mostra che sono stub). |
| 7 | `cap19-billing-plans` | BillingPage con listino Founders: 4 card piani (Starter/Pro/Agency/Enterprise) con prezzo mensile + bottone "Attiva". | 🔴 | — |
| 8 | `cap19-billing-credits` | BillingPage sezione credit packages: 6 card (400/1000/2000/5000/10000/20000 crediti) con prezzo. | 🟡 | Utile ma opzionale. |

**Totale Cap. 19**: 8 screenshot (5 essenziali, 3 utili).

---

## Cap. 20 · API Keys e integrazioni (Track B)

Riferimento: `memory/manuale/20-api-keys-integrazioni.md`

| # | ID | Cosa mostrare | Priorità | Fatto |
|---|----|---------------|:-:|:-:|
| 1 | `cap20-apikeys-empty` | ApiKeysPage stato empty (message "Nessuna chiave attiva. Emetti la prima con il form sopra."). | 🟡 | Utile ma opzionale. |
| 2 | `cap20-apikeys-create-form` | Form emissione con 4 input (name/initial_credits/partner_id/allowed_origins textarea) + bottone "Emetti chiave". | 🔴 | — |
| 3 | `cap20-apikeys-issued-box` | Box verde plaintext show-once con `omk_live_...` in font monospace + bottone Copia. | 🔴 | Chiave per D-051 (mostra "one-time"). |
| 4 | `cap20-apikeys-list` | Tabella chiavi attive con colonne Nome/Prefix/Partner/Saldo/Spesi/Stato/Azioni (top-up + revoca). | 🔴 | — |
| 5 | `cap20-apikeys-docs` | Box grigio "Come si usa" con Authorization header + endpoint `/api/v1/*` + widget snippet HTML. | 🟡 | Utile ma opzionale. |

**Totale Cap. 20**: 5 screenshot (3 essenziali, 2 utili).

---

## Cap. 21 · Valutatore immobiliare (dual-tier B2C · post B2C-VAL-01)

Riferimento: `memory/manuale/21-valutatore-immobiliare.md`

| # | ID | Cosa mostrare | Priorità | Fatto |
|---|----|---------------|:-:|:-:|
| 1 | `cap21-valuator-two-tier-cards` | ValuatorPage con le 2 card side-by-side (BASE GRATIS attiva · UNI 10750+PDF €2,99) + banner anonimo ambra. | 🔴 | Chiave per D-051 (mostra il gate commerciale). |
| 2 | `cap21-valuator-base-result-upsell` | Risultato stima base (valore + range + €/m²) + banner emerald upsell "Passa a UNI · €2,99" · NESSUN bottone PDF visibile. | 🔴 | — |
| 3 | `cap21-valuator-uni-form-pro-section` | Tab UNI attivo con sezione superfici commerciali + coefficienti merito espansi + bottone verde "Calcola UNI · €2,99". | 🔴 | — |
| 4 | `cap21-property-detail-cta-box` | PropertyDetailPage con box dual-CTA "Quanto vale questo immobile? [Stima gratuita] [Report UNI €2,99]" sotto il box mutui. | 🟡 | Utile ma opzionale. |
| 5 | `cap21-checkout-success` | Pagina `/it/cloud/checkout/success` con emoji ✅ + polling status Stripe + CTA "Torna al valutatore". | 🟡 | Utile ma opzionale. |

**Totale Cap. 21**: 5 screenshot (3 essenziali, 2 utili).

---

## Regole generali

**Ambiente**
- Ambito consigliato: preview URL (`REACT_APP_BACKEND_URL`) su viewport `1440×900`.
- Login come utente demo dedicato (mai founder / mai account reale).
- Nessun cliente reale, mai indirizzi reali, mai dati fiscali reali.

**Dati fittizi standardizzati**
Usa sempre gli stessi dati demo su tutto il manuale per coerenza:
- Agenzia: *Immobiliare Rossi S.r.l.*
- Titolare: *Marco Rossi · marco.rossi@immobiliarerossi.demo*
- Agente: *Anna Bianchi · anna.bianchi@immobiliarerossi.demo*
- Colori: primario `#1E40AF` · accento `#D97706`
- Città demo: *Belpasso (CT)*

**Formati**
- Formato: PNG.
- Peso: max 300 KB per screenshot (usa TinyPNG o `pngquant` se necessario).
- Aspect ratio: mantieni le proporzioni originali della viewport.

**Nomenclatura file**
`<id>.png` → esempio `cap1-login-form.png`

**Cartella**
Da creare al momento del primo screenshot: `/app/memory/manuale/screenshots/`.

---

## Storico modifiche

| Data | Note |
|------|------|
| Feb 2026 | Prima stesura index (Cap. 1) |
| Ago 2026 | Aggiunte 5 righe Cap. 5 · Match |
| Feb 2026 (Cap. 6) | Aggiunte 6 righe Cap. 6 · Portali / Publishing (5 essenziali, 1 utile) |
| Feb 2026 (Cap. 7) | Aggiunte 5 righe Cap. 7 · Fascicolo Immobile (4 essenziali, 1 utile). Totale index = **39 screenshot** catalogati. |
| Feb 2026 (Cap. 8) | Aggiunte 5 righe Cap. 8 · Sito web agenzia (4 essenziali, 1 utile). Totale index = **44 screenshot** catalogati. |
| Feb 2026 (Cap. 9) | Aggiunte 5 righe Cap. 9 · Virtual Staging (3 essenziali, 2 utili). Totale index = **49 screenshot** catalogati. |
| Feb 2026 (Cap. 10) | Aggiunte 5 righe Cap. 10 · HAL Agent CRM (3 essenziali, 2 utili). Totale index = **54 screenshot** catalogati. |
| Feb 2026 (Cap. 11) | Aggiunte 3 righe Cap. 11 · Mutui (panoramica + sostenibilità + piano ammortamento — tutte essenziali). Totale index = **57 screenshot** catalogati. |
| Feb 2026 (Cap. 12) | Aggiunte 3 righe Cap. 12 · HAL Knowledge (panoramica + risposta+fonti + status-badge). Totale index = **60 screenshot** catalogati. |
| Feb 2026 (Cap. 13) | Aggiunte 3 righe Cap. 13 · Team & Ruoli / Collaboratori (members-list + invite-modal + accept-invite — tutte essenziali). Totale index = **63 screenshot** catalogati. |
| Feb 2026 (Cap. 14) | Aggiunte 3 righe Cap. 14 · Import XML (upload + preview + commit-result — 2 essenziali + 1 utile). Totale index = **66 screenshot** catalogati. |
| Feb 2026 (Cap. 15) | Aggiunte 3 righe Cap. 15 · Social Publisher (panoramica + config-modal + publish-multichannel — tutte essenziali). Totale index = **69 screenshot** catalogati. |
| Feb 2026 (Cap. 16) | Aggiunte 3 righe Cap. 16 · Compliance Portali (modale-hard + mapping-campi + soft-warnings — 2 essenziali + 1 utile). Totale index = **72 screenshot** catalogati. |
| Feb 2026 (Cap. 17) | Aggiunte 3 righe Cap. 17 · Domain Vault (domain-verify + sovereignty-policy + rdap-checker — 2 essenziali + 1 utile). Totale index = **75 screenshot** catalogati. |
| Feb 2026 (Cap. 18) | Aggiunte 7 righe Cap. 18 · Notifiche e attività (email-welcome/agency-invite/lead-notification/saved-search/toast-success/toast-error/dashboard-kpi — 5 essenziali + 2 utili). Totale index = **82 screenshot** catalogati. |
| Feb 2026 (Cap. 19) | Aggiunte 8 righe Cap. 19 · Impostazioni agenzia (settings-identity/fiscal/address/contact/website-external/website-template/billing-plans/billing-credits — 5 essenziali + 3 utili). Totale index = **90 screenshot** catalogati. |
| Feb 2026 (Cap. 20) | Aggiunte 5 righe Cap. 20 · API Keys e integrazioni (apikeys-empty/create-form/issued-box/list/docs — 3 essenziali + 2 utili). Totale index = **95 screenshot** catalogati. |
| 16 Ago 2026 (Cap. 21) | Aggiunte 5 righe Cap. 21 · Valutatore immobiliare (two-tier-cards / base-result-upsell / uni-form-pro / property-detail-cta / checkout-success — 3 essenziali + 2 utili). Totale index = **100 screenshot** catalogati. |
