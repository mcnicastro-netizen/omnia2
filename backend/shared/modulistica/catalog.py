"""Modulistica catalog — Italian real-estate agency templates (M5.S7).

These are operational drafts for CRM use. They are NOT certified legal advice.
Every generated PDF carries a disclaimer. Founder + lawyer review before production.

Initial pack (PROGRAMMA M5.S7):
  1. proposta_acquisto
  2. mandato_vendita
  3. mandato_locazione
  4. preliminare
  5. lettera_condomini
  6. informativa_privacy (P0 compliance)
  7. scheda_aml (antiriciclaggio base)
"""
from __future__ import annotations
from typing import Any, Dict, List, Optional


TEMPLATES: Dict[str, Dict[str, Any]] = {

    "proposta_acquisto": {
        "slug": "proposta_acquisto",
        "name": "Proposta irrevocabile di acquisto",
        "category": "compravendita",
        "when_to_use": "Quando un acquirente formalizza un'offerta sull'immobile.",
        "signers": ["buyer", "seller"],
        "fields": [
            "agency_name", "agency_piva", "agency_address", "agency_rea",
            "buyer_name", "buyer_cf", "buyer_address", "buyer_email",
            "seller_name", "seller_cf", "seller_address",
            "property_address", "property_city", "property_cadastral",
            "offer_price", "deposit_amount", "validity_days", "commission_pct",
            "today",
        ],
        "sections": [
            ("Premessa", (
                "Il/La sottoscritto/a {{ buyer_name }} (C.F. {{ buyer_cf }}), residente in "
                "{{ buyer_address }}, di seguito «Proponente», formula la presente proposta "
                "irrevocabile di acquisto per l'immobile sito in {{ property_address }}, "
                "{{ property_city }} (riferimenti catastali: {{ property_cadastral }}), "
                "di proprietà di {{ seller_name }} (C.F. {{ seller_cf }})."
            )),
            ("Oggetto e prezzo", (
                "Il Proponente offre di acquistare l'immobile al prezzo di euro {{ offer_price }} "
                "(oltre oneri di legge). A titolo di caparra confirmatoria versa euro "
                "{{ deposit_amount }} tramite l'agenzia {{ agency_name }} (P.IVA {{ agency_piva }})."
            )),
            ("Validità", (
                "La presente proposta è irrevocabile per {{ validity_days }} giorni dalla data "
                "{{ today }}. In caso di accettazione del Proprietario entro tale termine, "
                "le parti si impegnano a stipulare il preliminare e successivamente il rogito."
            )),
            ("Provvigione", (
                "Le parti riconoscono all'agenzia {{ agency_name }} (REA {{ agency_rea }}) "
                "il diritto alla provvigione nella misura del {{ commission_pct }}% sul prezzo "
                "di vendita, dovuta al momento dell'accettazione della proposta, salvo diversi "
                "accordi scritti."
            )),
            ("Dichiarazioni", (
                "Il Proponente dichiara di aver visionato l'immobile, di aver ricevuto "
                "informativa privacy e di agire in proprio (salvo diversa dichiarazione allegata). "
                "L'agenzia agisce in qualità di mediatore ai sensi della L. 39/1989."
            )),
        ],
    },

    "mandato_vendita": {
        "slug": "mandato_vendita",
        "name": "Incarico / mandato di vendita",
        "category": "mandati",
        "when_to_use": "All'acquisizione dell'incarico di mediazione per la vendita.",
        "signers": ["seller", "agency"],
        "fields": [
            "agency_name", "agency_piva", "agency_address", "agency_rea", "agency_pec",
            "seller_name", "seller_cf", "seller_address", "seller_email", "seller_phone",
            "property_address", "property_city", "property_type", "asking_price",
            "exclusive", "duration_months", "commission_pct", "today",
        ],
        "sections": [
            ("Parti", (
                "Tra {{ seller_name }} (C.F. {{ seller_cf }}), residente in {{ seller_address }}, "
                "di seguito «Conferente», e {{ agency_name }} (P.IVA {{ agency_piva }}, "
                "REA {{ agency_rea }}), con sede in {{ agency_address }}, di seguito «Mediatore»."
            )),
            ("Oggetto", (
                "Il Conferente conferisce al Mediatore incarico {{ exclusive }} di promuovere "
                "la vendita dell'immobile sito in {{ property_address }}, {{ property_city }} "
                "(tipologia: {{ property_type }}) al prezzo richiesto di euro {{ asking_price }}."
            )),
            ("Durata", (
                "L'incarico ha durata di {{ duration_months }} mesi a decorrere dal {{ today }}, "
                "rinnovabile salvo disdetta scritta."
            )),
            ("Provvigione e pubblicità", (
                "In caso di conclusione dell'affare per effetto dell'attività del Mediatore, "
                "è dovuta provvigione pari al {{ commission_pct }}% del prezzo di vendita. "
                "Il Conferente autorizza la pubblicazione di annunci (anche online) e l'uso di "
                "foto/planimetrie, nel rispetto della privacy e dei livelli di pubblicità scelti."
            )),
            ("Obblighi", (
                "Il Conferente consegna la documentazione utile (APE, planimetria, atto di "
                "provenienza, documento d'identità) e comunica tempestivamente ogni variazione. "
                "Il Mediatore opera con diligenza professionale e trasparenza."
            )),
        ],
    },

    "mandato_locazione": {
        "slug": "mandato_locazione",
        "name": "Incarico / mandato di locazione",
        "category": "mandati",
        "when_to_use": "All'acquisizione dell'incarico di mediazione per la locazione.",
        "signers": ["landlord", "agency"],
        "fields": [
            "agency_name", "agency_piva", "agency_address", "agency_rea",
            "landlord_name", "landlord_cf", "landlord_address",
            "property_address", "property_city", "property_type",
            "rent_monthly", "duration_months", "commission_months", "exclusive", "today",
        ],
        "sections": [
            ("Parti", (
                "Tra {{ landlord_name }} (C.F. {{ landlord_cf }}), residente in {{ landlord_address }}, "
                "di seguito «Locatore», e {{ agency_name }} (P.IVA {{ agency_piva }}), Mediatore."
            )),
            ("Oggetto", (
                "Il Locatore conferisce incarico {{ exclusive }} di ricercare un conduttore per "
                "l'immobile in {{ property_address }}, {{ property_city }} ({{ property_type }}), "
                "con canone mensile richiesto di euro {{ rent_monthly }}."
            )),
            ("Durata e compenso", (
                "Incarico della durata di {{ duration_months }} mesi dal {{ today }}. "
                "Compenso del Mediatore: {{ commission_months }} mensilità di canone "
                "(o diversa misura pattuita per iscritto), dovuto alla conclusione del contratto."
            )),
            ("Documentazione", (
                "Il Locatore fornisce APE, planimetria, regolamento condominiale se applicabile, "
                "e dichiara la disponibilità dell'immobile alla locazione secondo le norme vigenti."
            )),
        ],
    },

    "preliminare": {
        "slug": "preliminare",
        "name": "Preliminare di compravendita (bozza)",
        "category": "compravendita",
        "when_to_use": "Bozza di compromesso tra venditore e acquirente (da validare con legale/notaio).",
        "signers": ["buyer", "seller"],
        "fields": [
            "agency_name", "agency_piva",
            "buyer_name", "buyer_cf", "buyer_address",
            "seller_name", "seller_cf", "seller_address",
            "property_address", "property_city", "property_cadastral",
            "sale_price", "deposit_amount", "deed_deadline", "today",
        ],
        "sections": [
            ("Parti e oggetto", (
                "Con il presente contratto preliminare, {{ seller_name }} (C.F. {{ seller_cf }}) "
                "promette di vendere a {{ buyer_name }} (C.F. {{ buyer_cf }}) l'immobile sito in "
                "{{ property_address }}, {{ property_city }} (catasto: {{ property_cadastral }})."
            )),
            ("Prezzo e caparra", (
                "Il prezzo è fissato in euro {{ sale_price }}. Alla firma del presente atto "
                "l'acquirente versa euro {{ deposit_amount }} a titolo di caparra confirmatoria "
                "(art. 1385 c.c.), tramite l'agenzia mediatrice {{ agency_name }}."
            )),
            ("Rogito", (
                "Le parti si impegnano a stipulare l'atto pubblico di compravendita entro il "
                "{{ deed_deadline }} innanzi a notaio di comune gradimento. "
                "L'immobile sarà trasferito libero da ipoteche, trascrizioni e iscrizioni "
                "pregiudizievoli, salvo quanto dichiarato."
            )),
            ("Mediazione", (
                "Le parti riconoscono l'intervento di {{ agency_name }} (P.IVA {{ agency_piva }}) "
                "quale mediatore dell'affare. Data della bozza: {{ today }}."
            )),
            ("Avvertenza", (
                "La presente è una bozza operativa generata dal gestionale. Prima della firma "
                "definitiva occorre revisione da parte di un professionista abilitato "
                "(avvocato/notaio) e verifica documentale completa (visure, APE, urbanistica)."
            )),
        ],
    },

    "lettera_condomini": {
        "slug": "lettera_condomini",
        "name": "Lettera informativa ai condòmini",
        "category": "comunicazioni",
        "when_to_use": "Per informare il condominio di visite / vendita / lavori correlati all'incarico.",
        "signers": ["agency"],
        "fields": [
            "agency_name", "agency_address", "agency_phone", "agency_email",
            "admin_name", "admin_pec",
            "property_address", "property_city", "seller_name",
            "purpose", "today",
        ],
        "sections": [
            ("Destinatario", (
                "Spett.le Amministratore {{ admin_name }} — PEC {{ admin_pec }}."
            )),
            ("Oggetto", (
                "Informativa relativa all'unità immobiliare in {{ property_address }}, "
                "{{ property_city }} — proprietario {{ seller_name }}."
            )),
            ("Comunicazione", (
                "Con la presente, {{ agency_name }} (sede {{ agency_address }}) comunica che "
                "è stato conferito incarico di mediazione avente ad oggetto: {{ purpose }}.\n\n"
                "Si richiede cortese collaborazione per l'eventuale rilascio di documentazione "
                "condominiale (regolamento, millesimi, bilanci, attestazione spese) necessaria "
                "al fascicolo pre-rogito / pre-locazione."
            )),
            ("Contatti", (
                "Per ogni chiarimento: {{ agency_phone }} — {{ agency_email }}. Data: {{ today }}."
            )),
        ],
    },

    "informativa_privacy": {
        "slug": "informativa_privacy",
        "name": "Informativa privacy clienti (GDPR)",
        "category": "compliance",
        "when_to_use": "All'acquisizione di un nuovo cliente / lead / firmatario.",
        "signers": ["client"],
        "fields": [
            "agency_name", "agency_piva", "agency_address", "agency_email", "agency_pec",
            "dpo_email", "client_name", "today",
        ],
        "sections": [
            ("Titolare del trattamento", (
                "Titolare: {{ agency_name }} (P.IVA {{ agency_piva }}), sede {{ agency_address }}. "
                "Contatti: {{ agency_email }} / PEC {{ agency_pec }}. "
                "DPO (se nominato): {{ dpo_email }}."
            )),
            ("Finalità e basi giuridiche", (
                "I dati di {{ client_name }} sono trattati per: (a) esecuzione di misure "
                "precontrattuali e contrattuali di mediazione immobiliare; (b) adempimenti "
                "di legge (antiriciclaggio, fiscalità); (c) con consenso, attività di marketing "
                "diretto. Basi: art. 6.1.b, 6.1.c e, ove richiesto, 6.1.a GDPR."
            )),
            ("Conservazione e diritti", (
                "I dati sono conservati per il tempo necessario alle finalità e agli obblighi "
                "di legge. L'interessato può esercitare i diritti di cui agli artt. 15-22 GDPR "
                "scrivendo a {{ agency_email }}. Data informativa: {{ today }}."
            )),
        ],
    },

    "scheda_aml": {
        "slug": "scheda_aml",
        "name": "Scheda adeguata verifica clientela (AML)",
        "category": "compliance",
        "when_to_use": "Identificazione antiriciclaggio del cliente in mediazione.",
        "signers": ["client", "agency"],
        "fields": [
            "agency_name", "agency_piva",
            "client_name", "client_cf", "client_doc_type", "client_doc_number",
            "client_doc_issuer", "client_doc_expiry", "client_address",
            "pep_declared", "funds_origin", "operation_type", "today",
        ],
        "sections": [
            ("Identificazione", (
                "Cliente: {{ client_name }} — C.F. {{ client_cf }} — residenza {{ client_address }}. "
                "Documento: {{ client_doc_type }} n. {{ client_doc_number }}, rilasciato da "
                "{{ client_doc_issuer }}, scadenza {{ client_doc_expiry }}."
            )),
            ("Operazione", (
                "Tipo operazione: {{ operation_type }}. Origine dichiarata dei fondi: "
                "{{ funds_origin }}. Dichiarazione PEP: {{ pep_declared }}."
            )),
            ("Conservazione", (
                "La presente scheda è conservata da {{ agency_name }} (P.IVA {{ agency_piva }}) "
                "secondo gli obblighi antiriciclaggio applicabili ai mediatori. Data: {{ today }}."
            )),
        ],
    },
}


def list_templates() -> List[Dict[str, Any]]:
    """Public catalog (no section bodies — lighter for UI/API)."""
    out = []
    for t in TEMPLATES.values():
        out.append({
            "slug": t["slug"],
            "name": t["name"],
            "category": t["category"],
            "when_to_use": t["when_to_use"],
            "signers": t["signers"],
            "fields": t["fields"],
        })
    return out


def get_template(slug: str) -> Optional[Dict[str, Any]]:
    return TEMPLATES.get(slug)
