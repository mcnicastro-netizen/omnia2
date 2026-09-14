"""OMNIA — Fascicolo Digitale enrichment: ricerca APE e visure OpenAI docs.

Scaffold M4 post-società. Endpoints tornano 503 finché SIAPE_ENABLED / OPENAI_DOCS_ENABLED
non sono attivati con le rispettive API key.

Scope M4:
  - Ricerca APE via portali regionali (SIAPE per regioni convenzionate,
    fallback OCR PDF upload)
  - Ricerca documenti OpenAI (visure catasto, planimetrie, ipoteche)
    tramite modello con function-calling che consulta i portali pubblici.

Ogni ricerca consuma crediti (vedi apps/billing/plans.py::CREDIT_COSTS).
"""
import os
import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from pydantic import BaseModel, Field

from shared.auth.dependencies import get_current_user
from shared.db.connection import Database

logger = logging.getLogger("omnia.docs_search")
router = APIRouter(prefix="/docs", tags=["docs_search"])


class APESearchRequest(BaseModel):
    property_id: str = Field(min_length=1)
    region: str = Field(default="sicilia")  # regione italiana
    codice_ape: Optional[str] = None  # se noto
    codice_fiscale_proprietario: Optional[str] = None
    indirizzo: Optional[str] = None
    comune: Optional[str] = None


class OpenAIDocSearchRequest(BaseModel):
    property_id: str = Field(min_length=1)
    doc_type: str = Field(pattern=r"^(visura|planimetria|ipoteca|catasto)$")
    query_hint: Optional[str] = None


def _siape_enabled() -> bool:
    return (os.environ.get("SIAPE_ENABLED") or "").lower() == "true" and bool(
        os.environ.get("SIAPE_API_KEY")
    )


def _openai_docs_enabled() -> bool:
    return (os.environ.get("OPENAI_DOCS_ENABLED") or "").lower() == "true" and bool(
        os.environ.get("OPENAI_API_KEY")
    )


@router.get("/status")
async def docs_search_status(user: dict = Depends(get_current_user)):
    """Feature-flag status per il frontend."""
    return {
        "ape_search_enabled": _siape_enabled(),
        "openai_docs_enabled": _openai_docs_enabled(),
        "supported_regions": ["sicilia", "lombardia", "lazio", "campania", "piemonte",
                              "veneto", "emilia-romagna", "toscana", "puglia"],
    }


@router.post("/ape/search")
async def ape_search(
    payload: APESearchRequest,
    user: dict = Depends(get_current_user),
):
    """Search APE certificate in SIAPE regional catalog.

    Flow (a programma completato):
      1. Debit 3 credits from agency wallet
      2. Call SIAPE regional API with codice_ape or (CF + indirizzo)
      3. Parse response → PropertyEnergy(energy_class, energy_value, heating)
      4. Update property with fetched data + append to Fascicolo
      5. Return the APE PDF URL + parsed fields
    """
    if not _siape_enabled():
        raise HTTPException(
            status_code=503,
            detail={"error": "ape_search_not_configured",
                    "message": "La ricerca APE via portali regionali è in preparazione. "
                               "Attivazione al completamento della costituzione societaria."},
        )
    # STUB — quando il Founder fornirà SIAPE_API_KEY:
    #   from apps.billing.routes import debit_credits
    #   await debit_credits(user["agency_ids"][0], 3, "ape_search", payload.property_id, "property")
    #   client = SIAPEClient(api_key=os.environ["SIAPE_API_KEY"], region=payload.region)
    #   result = await client.search(codice_ape=..., cf=..., indirizzo=...)
    #   → attach to property + Fascicolo
    raise HTTPException(status_code=503, detail="siape_client_not_yet_wired")


@router.post("/ape/upload-ocr")
async def ape_upload_ocr(
    property_id: str,
    file: UploadFile = File(...),
    user: dict = Depends(get_current_user),
):
    """Fallback: agent uploads APE PDF, OCR extracts fields.

    Available anche senza SIAPE (usa PyMuPDF + regex sui pattern APE standard).
    """
    # STUB scheletro (implementazione OCR reale post-M4)
    raise HTTPException(status_code=503, detail="ape_ocr_pipeline_not_yet_wired")


@router.post("/openai/search")
async def openai_docs_search(
    payload: OpenAIDocSearchRequest,
    user: dict = Depends(get_current_user),
):
    """Ricerca documenti tramite OpenAI con function-calling.

    Flow (post-società):
      1. Debit crediti (visura: 5, catasto: 5, planimetria: 3, ipoteca: 8)
      2. LLM riceve tool: search_catasto(subalterno, foglio, particella),
         search_conservatoria(cf, immobile), etc.
      3. LLM restituisce dati strutturati + PDF url
      4. Salva in Fascicolo del property_id
    """
    if not _openai_docs_enabled():
        raise HTTPException(
            status_code=503,
            detail={"error": "openai_docs_not_configured",
                    "message": "Ricerca documenti OpenAI in preparazione."},
        )
    raise HTTPException(status_code=503, detail="openai_docs_client_not_yet_wired")
