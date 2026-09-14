"""OMNIA Legal Kit — Template catalog (M2.5.4c, D-055).

Four legal-adjacent PDF templates that any Italian real estate agency can
use to reclaim data / domain sovereignty from an incumbent vendor.

STRICT RULE (D-051): all templates use GENERIC placeholders like
[NOME_FORNITORE] and [RAGIONE_SOCIALE_FORNITORE]. Never mention any
specific competitor by name — the agency fills them in themselves.

STRICT RULE (D-035 No Paper): the deliverable is a PDF with the agency's
data pre-filled, ready to be sent via PEC (Posta Elettronica Certificata).
No physical printing suggested anywhere in the copy.

Templates:
    - gdpr_20: Richiesta portabilità dei dati (GDPR art. 20)
    - pec_titolarita_dominio: Richiesta formale titolarità dominio al registrar
    - disdetta_fornitore: Disdetta contrattuale al fornitore attuale
    - reclamo_cnr_iit: Reclamo/richiesta info a Registro .it (CNR-IIT)
"""
from __future__ import annotations
from typing import Dict, Any, List


# Each template has:
#   slug, name, target (chi lo riceve), when_to_use, sections=[(heading, body_jinja), ...]
#
# `body_jinja` supports {{ agency_name }}, {{ agency_address }}, {{ agency_pec }},
# {{ agency_piva }}, {{ vendor_name }}, {{ contract_ref }}, {{ domain }}, {{ today }}.
# Missing values collapse to visible placeholders like "[da compilare]".

TEMPLATES: Dict[str, Dict[str, Any]] = {

    # ---------------- 1. GDPR Art. 20 ----------------
    "gdpr_20": {
        "slug": "gdpr_20",
        "name": "Richiesta portabilità dei dati (GDPR art. 20)",
        "target": "Il tuo attuale fornitore del gestionale/CRM",
        "when_to_use": (
            "Da inviare al fornitore che oggi gestisce i dati della tua agenzia "
            "(immobili, contatti, annunci, media). Serve a ottenere una copia "
            "digitale strutturata prima di migrare a un nuovo sistema."
        ),
        "channel": "PEC (Posta Elettronica Certificata) — nessun invio cartaceo",
        "response_days": 30,
        "sections": [
            ("Oggetto", (
                "Esercizio del diritto alla portabilità dei dati personali e aziendali "
                "ai sensi dell'art. 20 del Regolamento UE 2016/679 (GDPR)."
            )),
            ("Premesso che", (
                "- Il sottoscritto {{ signer_name }}, in qualità di legale rappresentante di "
                "{{ agency_name }} (P.IVA {{ agency_piva }}), è titolare del trattamento dei "
                "dati aziendali gestiti tramite il servizio da Voi erogato "
                "(contratto {{ contract_ref }});\n"
                "- Il regolamento (UE) 2016/679, art. 20, riconosce al titolare del "
                "trattamento il diritto di ricevere in un formato strutturato, di uso "
                "comune e leggibile da dispositivo automatico, i dati personali che lo "
                "riguardano forniti a un titolare del trattamento;\n"
                "- L'agenzia scrivente intende migrare a un differente fornitore "
                "di servizi ed ha necessità di ricevere copia integrale dei dati."
            )),
            ("Chiede formalmente", (
                "1. Copia integrale in formato XML/CSV/JSON di TUTTI i dati "
                "riferiti a {{ agency_name }} attualmente memorizzati sui Vostri "
                "sistemi, ivi inclusi (a titolo esemplificativo e non esaustivo):\n"
                "   - Anagrafica immobili con ogni campo, foto, planimetrie e allegati;\n"
                "   - Anagrafica clienti, richieste e ricerche personalizzate;\n"
                "   - Storico interazioni, appuntamenti, comunicazioni, note;\n"
                "   - Contratti, mandati, provvigioni, documenti fiscali;\n"
                "   - Log accessi, credenziali eventualmente conservate, cookie ID.\n\n"
                "2. Elenco dettagliato di eventuali soggetti terzi con cui i dati "
                "sono stati condivisi (portali, servizi cloud, sub-fornitori).\n\n"
                "3. Conferma cancellazione di TUTTI i dati dai Vostri sistemi al "
                "termine del periodo contrattuale, come previsto dall'art. 17 GDPR."
            )),
            ("Modalità di consegna", (
                "I dati richiesti dovranno pervenire in formato digitale entro e "
                "non oltre trenta (30) giorni dalla ricezione della presente, "
                "mediante link di download sicuro trasmesso alla PEC "
                "{{ agency_pec }}.\n\n"
                "In mancanza di riscontro entro il termine indicato, ci riserviamo "
                "di rivolgere segnalazione al Garante per la Protezione dei Dati "
                "Personali (Piazza Venezia 11, 00187 Roma) ai sensi dell'art. 77 "
                "GDPR e di attivare ogni azione legale volta a tutelare i Nostri "
                "diritti."
            )),
            ("Riferimenti normativi", (
                "- Regolamento UE 2016/679 (GDPR), artt. 15, 17, 20, 77\n"
                "- D.Lgs. 196/2003 e successive modifiche (Codice Privacy)\n"
                "- Provvedimento del Garante Privacy n. 246/2018 (portabilità)"
            )),
        ],
    },

    # ---------------- 2. PEC titolarità dominio ----------------
    "pec_titolarita_dominio": {
        "slug": "pec_titolarita_dominio",
        "name": "Richiesta formale titolarità dominio",
        "target": "Il registrar del tuo dominio (Aruba, Register.it, OVH, ecc.)",
        "when_to_use": (
            "Da inviare al registrar per farti confermare formalmente chi è "
            "l'intestatario ufficiale (Registrante) del dominio. Serve quando "
            "il check RDAP mostra dati oscurati o quando sospetti che il "
            "dominio sia intestato a un fornitore terzo."
        ),
        "channel": "PEC (Posta Elettronica Certificata) — nessun invio cartaceo",
        "response_days": 15,
        "sections": [
            ("Oggetto", (
                "Richiesta di conferma formale della titolarità del nome a dominio "
                "{{ domain }} e trasmissione dei dati di intestazione."
            )),
            ("Premesso che", (
                "- Il sottoscritto {{ signer_name }}, in qualità di legale "
                "rappresentante di {{ agency_name }} (P.IVA {{ agency_piva }}), "
                "risulta effettivo utilizzatore del dominio {{ domain }};\n"
                "- Non è possibile verificare con certezza tramite le sole query "
                "WHOIS/RDAP pubbliche chi risulti attualmente intestatario "
                "del dominio in oggetto;\n"
                "- È diritto dell'utilizzatore effettivo del dominio conoscere "
                "l'esatta identità del Registrante e ottenerne copia dei dati "
                "di intestazione."
            )),
            ("Chiede formalmente", (
                "1. Copia dei DATI DI INTESTAZIONE del dominio {{ domain }} così "
                "come conservati nei Vostri sistemi, includendo:\n"
                "   - Registrante (nome, ragione sociale, codice fiscale/P.IVA);\n"
                "   - Contatto amministrativo (Admin-C);\n"
                "   - Contatto tecnico (Tech-C);\n"
                "   - Data prima registrazione, data ultimo rinnovo, data scadenza;\n"
                "   - Storia dei passaggi di intestazione (change of registrant).\n\n"
                "2. Chiarimento in merito a EVENTUALI CLAUSOLE contrattuali che "
                "vincolino il trasferimento del dominio ad altro registrar, "
                "incluse eventuali penali o condizioni di svincolo.\n\n"
                "3. Fornitura del CODICE AUTOINFO (Auth-Info Code / Auth Code) "
                "necessario per l'eventuale trasferimento del dominio ad un altro "
                "registrar, come previsto dalle regole tecniche del Registro .it."
            )),
            ("Modalità di consegna", (
                "La documentazione richiesta dovrà pervenire entro quindici (15) "
                "giorni dalla ricezione della presente, in formato digitale, "
                "trasmessa alla PEC {{ agency_pec }}.\n\n"
                "In caso di silenzio o rifiuto, ci riserviamo di segnalare la "
                "vicenda al Registro del ccTLD .it presso il CNR-IIT di Pisa e al "
                "Garante per la Protezione dei Dati Personali."
            )),
            ("Riferimenti normativi", (
                "- Regolamento del ccTLD .it (Registro Italiano, CNR-IIT)\n"
                "- Regolamento UE 2016/679 (GDPR), art. 15 (diritto di accesso)\n"
                "- ICANN Uniform Domain-Name Dispute-Resolution Policy (UDRP)"
            )),
        ],
    },

    # ---------------- 3. Disdetta fornitore ----------------
    "disdetta_fornitore": {
        "slug": "disdetta_fornitore",
        "name": "Disdetta contratto fornitore",
        "target": "Il tuo attuale fornitore del gestionale/software",
        "when_to_use": (
            "Da inviare al fornitore attuale del gestionale/CRM per comunicare "
            "formalmente la disdetta del contratto in essere. È fondamentale "
            "verificare prima le clausole di preavviso presenti nel contratto "
            "originale."
        ),
        "channel": "PEC (Posta Elettronica Certificata) — nessun invio cartaceo",
        "response_days": 15,
        "sections": [
            ("Oggetto", (
                "Disdetta formale del contratto {{ contract_ref }} — servizi di "
                "software gestionale erogati a {{ agency_name }}."
            )),
            ("Premesso che", (
                "- In data [DATA_STIPULA] {{ agency_name }} ha sottoscritto con "
                "codesta Spett.le società (di seguito \"il Fornitore\") il "
                "contratto {{ contract_ref }} avente ad oggetto la fornitura di "
                "servizi software gestionale;\n"
                "- Il contratto in essere prevede una durata annuale con rinnovo "
                "tacito salvo disdetta da comunicare con preavviso di "
                "[N_GIORNI_PREAVVISO] giorni prima della naturale scadenza;\n"
                "- L'agenzia scrivente ha maturato la decisione di non rinnovare "
                "il contratto alla prossima scadenza."
            )),
            ("Comunica", (
                "1. La FORMALE DISDETTA del contratto {{ contract_ref }} con "
                "efficacia dalla naturale scadenza contrattuale del [DATA_SCADENZA];\n\n"
                "2. La volontà di NON RINNOVARE tacitamente il contratto in "
                "essere per il periodo successivo;\n\n"
                "3. La richiesta esplicita di TERMINARE OGNI ADDEBITO "
                "AUTOMATICO (RID / SDD / carta di credito) a partire dalla "
                "data di scadenza contrattuale."
            )),
            ("Richiede altresì", (
                "1. Conferma scritta di ricevuta della presente disdetta entro "
                "sette (7) giorni;\n\n"
                "2. Trasmissione di TUTTI i dati aziendali in Vostro possesso "
                "in formato strutturato (XML/CSV/JSON), come da separata "
                "richiesta ex art. 20 GDPR trasmessa in pari data;\n\n"
                "3. Conferma della cancellazione totale dei dati al termine "
                "del periodo di servizio, come previsto dall'art. 17 GDPR "
                "e dalle Vostre condizioni generali di contratto;\n\n"
                "4. Chiarimento in merito a EVENTUALI PENALI di uscita "
                "anticipata previste dal contratto, con indicazione del "
                "riferimento clausola e del calcolo dell'importo;\n\n"
                "5. Chiarimento in merito a EVENTUALI SERVIZI ACCESSORI "
                "(dominio, hosting, PEC, caselle email) che non risultino "
                "già intestati a {{ agency_name }} e che dovranno essere "
                "trasferiti o attribuiti alla nostra società senza costi."
            )),
            ("Modalità di consegna", (
                "Ogni comunicazione di riscontro dovrà pervenire alla PEC "
                "{{ agency_pec }}.\n\n"
                "In mancanza di riscontro entro i termini di preavviso "
                "contrattuali, la presente disdetta si intenderà comunque "
                "regolarmente pervenuta e produrrà i suoi effetti alla "
                "naturale scadenza contrattuale."
            )),
            ("Riferimenti normativi", (
                "- Art. 1373 c.c. (recesso unilaterale)\n"
                "- D.Lgs. 206/2005 (Codice del Consumo, ove applicabile)\n"
                "- Regolamento UE 2016/679 (GDPR), artt. 17 e 20"
            )),
        ],
    },

    # ---------------- 4. Reclamo CNR-IIT ----------------
    "reclamo_cnr_iit": {
        "slug": "reclamo_cnr_iit",
        "name": "Reclamo / richiesta informazioni Registro .it (CNR-IIT)",
        "target": "Registro .it — CNR-IIT, Via G. Moruzzi 1, 56124 Pisa",
        "when_to_use": (
            "Da inviare al Registro .it quando il registrar non risponde alla "
            "richiesta di titolarità del dominio o rifiuta di fornire il codice "
            "AuthInfo per il trasferimento. Il Registro .it è l'organismo "
            "indipendente di riferimento per il ccTLD .it."
        ),
        "channel": "PEC (Posta Elettronica Certificata) o modulo online CNR-IIT",
        "response_days": 30,
        "sections": [
            ("Oggetto", (
                "Segnalazione al Registro .it in merito al dominio {{ domain }} "
                "— mancata risposta o diniego del registrar alla richiesta di "
                "titolarità/trasferimento."
            )),
            ("Premesso che", (
                "- Il sottoscritto {{ signer_name }}, in qualità di legale "
                "rappresentante di {{ agency_name }} (P.IVA {{ agency_piva }}), "
                "è effettivo utilizzatore del dominio {{ domain }};\n"
                "- Con PEC datata [DATA_PEC_REGISTRAR] è stato richiesto al "
                "registrar attuale la conferma della titolarità del dominio e/o "
                "il rilascio del codice AuthInfo per il trasferimento;\n"
                "- Alla data della presente il registrar non ha fornito riscontro "
                "adeguato / si è dichiarato indisponibile a rilasciare quanto "
                "richiesto (indicare l'ipotesi che ricorre)."
            )),
            ("Segnala e richiede", (
                "1. L'ACCERTAMENTO da parte del Registro .it della corretta "
                "gestione del dominio {{ domain }} secondo il Regolamento del "
                "ccTLD .it in vigore;\n\n"
                "2. La VERIFICA che i dati anagrafici del Registrante siano "
                "conformi all'effettivo utilizzatore del dominio;\n\n"
                "3. L'ATTIVAZIONE della procedura di TRASFERIMENTO al nuovo "
                "registrar, se le clausole contrattuali del registrar attuale "
                "risultino contrarie al Regolamento CNR-IIT;\n\n"
                "4. Ogni ulteriore azione di TUTELA prevista dal Regolamento "
                "in caso di gestione anomala del dominio da parte del "
                "registrar attuale."
            )),
            ("Modalità di consegna", (
                "Copia del riscontro dovrà pervenire alla PEC {{ agency_pec }}.\n\n"
                "Restiamo a disposizione per fornire ogni documentazione "
                "aggiuntiva utile (copia della PEC inviata al registrar, "
                "estratti WHOIS/RDAP, documentazione dell'utilizzo effettivo "
                "del dominio da parte di {{ agency_name }}).\n\n"
                "Copia della presente viene per conoscenza trasmessa anche "
                "al Garante per la Protezione dei Dati Personali."
            )),
            ("Riferimenti normativi", (
                "- Regolamento di assegnazione e gestione dei nomi a dominio "
                ".it (CNR-IIT)\n"
                "- ICANN Transfer Policy per ccTLD\n"
                "- Regolamento UE 2016/679 (GDPR), art. 15 e art. 20"
            )),
        ],
    },
}


def list_templates() -> List[Dict[str, Any]]:
    """Return the catalog metadata (no body text) for UI/API listing."""
    return [
        {
            "slug": t["slug"],
            "name": t["name"],
            "target": t["target"],
            "when_to_use": t["when_to_use"],
            "channel": t["channel"],
            "response_days": t["response_days"],
        }
        for t in TEMPLATES.values()
    ]


def get_template(slug: str) -> Dict[str, Any]:
    """Raise KeyError if slug is unknown."""
    return TEMPLATES[slug]
