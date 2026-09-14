"""OMNIA — HAL Knowledge (M5.S2, Sprint 2).

RAG (Retrieval Augmented Generation) sul corpus di documentazione OMNIA:
    - /app/memory/PRD.md
    - /app/memory/ROADMAP.md
    - /app/memory/DECISIONS.md
    - /app/memory/AUDIT_M2.md
    - /app/memory/PROGRAMMA_OMNIA.md
    - /app/memory/manuale/*.md (quando pronti)

Approccio (D-061):
- Retrieval: TF-IDF + cosine similarity (nessuna API call, zero costi).
  Corpus piccolo (~2500 righe, ~80 chunks) → TF-IDF batte in latenza gli embeddings
  neurali senza degradare la qualità per domande italiane su documenti tecnici.
- Generation: Gemini 3 Flash Preview via Emergent LLM Key (streaming SSE).
- Confidence gate: se il best cosine sim < 0.15 → risposta "insufficient_context".
- Idempotenza: chunk indicizzato con MD5 del file, re-ingest solo se cambiato.

Collezioni:
- `hal_knowledge_chunks`: {id, file, section, chunk_id, text, md5_source, token_count, updated_at}
- `hal_knowledge_meta`:   {id="singleton", tfidf_vocab, idf, matrix, corpus_md5s, updated_at}
- `hal_knowledge_sessions`: {id, agency_id, user_id, question, answer, sources, confidence, tokens, ts}

Router: /api/app/hal/knowledge/*
"""
from __future__ import annotations

import hashlib
import json
import logging
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from uuid import uuid4

import numpy as np
import yaml
from scipy.sparse import csr_matrix
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import Field
from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from shared.auth.dependencies import require_roles
from shared.db.connection import Database
from shared.models.base import OmniaBaseModel, utcnow_iso

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/hal/knowledge", tags=["hal-knowledge"])

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

MEMORY_ROOT = Path("/app/memory")
CORPUS_FILES = [
    "PRD.md",
    "ROADMAP.md",
    "DECISIONS.md",
    "AUDIT_M2.md",
    "PROGRAMMA_OMNIA.md",
    "ASPETTI_DA_APPROFONDIRE.md",
    "BUSINESS_MODEL.md",
    # CHANGELOG.md ESCLUSO dal corpus RAG (TASK B-ter, 6-Ago-2026):
    # documento di log troppo denso, cambia ogni giorno e — soprattutto —
    # può contenere query test o esempi che creano feedback loop nel TF-IDF.
]
MANUAL_DIR = MEMORY_ROOT / "manuale"
HAL_YAML_DIR = MANUAL_DIR / "hal"  # voci HAL atomiche (Cap. 1..N)

CHUNK_WORDS = 500          # ~500 parole per chunk
CHUNK_OVERLAP = 50         # 50 parole di overlap
TOP_K = 5                  # numero di chunk recuperati per query
CONFIDENCE_MIN = 0.08      # sotto questa soglia → insufficient_context (TF-IDF scale)
CONFIDENCE_HIGH = 0.20     # sopra questa soglia → high-confidence answer

MODEL_PROVIDER = "gemini"
MODEL_NAME = "gemini-3-flash-preview"


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------

class KnowledgeAskRequest(OmniaBaseModel):
    question: str = Field(min_length=3, max_length=1000)
    session_id: Optional[str] = None


class KnowledgeChunk(OmniaBaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    file: str
    section: Optional[str] = None
    chunk_id: Union[int, str]  # int per .md sequenziale, str stabile (voce YAML id) per manuale
    text: str
    md5_source: str
    token_count: int = 0
    updated_at: str = Field(default_factory=utcnow_iso)


# ---------------------------------------------------------------------------
# Chunking
# ---------------------------------------------------------------------------

_HEADING_RE = re.compile(r"^(#{1,4})\s+(.+?)\s*$", re.M)


def _extract_sections(md_text: str) -> List[Dict[str, str]]:
    """Split a markdown file into sections keyed by the nearest heading.

    Returns a list of {section, text} preserving reading order.
    """
    sections: List[Dict[str, str]] = []
    current_title = "(intro)"
    buffer: List[str] = []
    for line in md_text.splitlines():
        m = _HEADING_RE.match(line)
        if m:
            if buffer:
                sections.append({"section": current_title, "text": "\n".join(buffer).strip()})
                buffer = []
            current_title = m.group(2).strip()
        else:
            buffer.append(line)
    if buffer:
        sections.append({"section": current_title, "text": "\n".join(buffer).strip()})
    return [s for s in sections if s["text"]]


def _split_words(text: str, size: int, overlap: int) -> List[str]:
    words = text.split()
    if len(words) <= size:
        return [text] if words else []
    chunks = []
    step = size - overlap
    for i in range(0, len(words), step):
        chunk = words[i : i + size]
        if not chunk:
            break
        chunks.append(" ".join(chunk))
        if i + size >= len(words):
            break
    return chunks


def _chunk_file(file_name: str, md_text: str) -> List[Dict[str, Any]]:
    md5 = hashlib.md5(md_text.encode("utf-8")).hexdigest()
    sections = _extract_sections(md_text)
    out: List[Dict[str, Any]] = []
    idx = 0
    for sec in sections:
        for chunk in _split_words(sec["text"], CHUNK_WORDS, CHUNK_OVERLAP):
            out.append({
                "file": file_name,
                "section": sec["section"],
                "chunk_id": idx,
                "text": chunk,
                "md5_source": md5,
                "token_count": len(chunk.split()),
            })
            idx += 1
    return out


def _render_voce_hal(v: Dict[str, Any]) -> str:
    """Serializza una voce HAL YAML atomica in testo indicizzabile.

    Struttura documentata in IMPORT_HAL.md:
    [TITOLO] · [MODULO] · [DOMANDA] · [A COSA SERVE] · [QUANDO SI USA] ·
    [PASSI] · [ERRORI COMUNI] · [PERMESSI] · [TAGS]
    """
    contenuto = v.get("contenuto", {}) or {}
    lines: List[str] = [
        f"[TITOLO] {v.get('titolo', '')}",
        f"[MODULO] {v.get('modulo', '')}",
        f"[DOMANDA] {v.get('domanda_naturale', '')}",
        f"[A COSA SERVE] {contenuto.get('a_cosa_serve', '').strip()}",
        f"[QUANDO SI USA] {contenuto.get('quando_si_usa', '').strip()}",
    ]
    passi = contenuto.get("passi") or []
    if passi:
        lines.append("[PASSI]")
        for p in passi:
            lines.append(f"- {p}")
    errori = contenuto.get("errori_comuni") or []
    if errori:
        lines.append("[ERRORI COMUNI]")
        for e in errori:
            problema = (e.get("problema") or "").strip()
            soluzione = (e.get("soluzione") or "").strip()
            lines.append(f"- {problema} -> {soluzione}")
    permessi = contenuto.get("permessi") or []
    if permessi:
        lines.append("[PERMESSI]")
        for perm in permessi:
            lines.append(f"- {perm}")
    tags = v.get("tags") or []
    if tags:
        lines.append(f"[TAGS] {', '.join(tags)}")
    return "\n".join(lines)


def _chunk_yaml_hal_file(file_name: str, raw_bytes: bytes) -> List[Dict[str, Any]]:
    """Estrae chunk atomici da un file YAML del manuale HAL.

    - 1 voce YAML = 1 chunk indipendente (chunk_id = v["id"], stringa stabile)
    - md5_source = MD5 del file YAML intero (invalidazione file-level)
    - metadata preservati per filtering/boosting futuri
    """
    md5 = hashlib.md5(raw_bytes).hexdigest()
    try:
        data = yaml.safe_load(raw_bytes.decode("utf-8")) or {}
    except yaml.YAMLError as exc:
        logger.exception("HAL YAML parse failed for %s: %s", file_name, exc)
        return []
    voci = data.get("voci") or []
    out: List[Dict[str, Any]] = []
    for v in voci:
        vid = v.get("id")
        if not vid:
            continue
        text = _render_voce_hal(v)
        out.append({
            "file": file_name,
            "section": v.get("modulo") or "",
            "chunk_id": vid,           # stringa stabile (es. "clienti.smart-import-ai")
            "text": text,
            "md5_source": md5,
            "token_count": len(text.split()),
            "metadata": {
                "id": vid,
                "modulo": v.get("modulo"),
                "livello": v.get("livello"),
                "tags": v.get("tags") or [],
                "correlati": v.get("correlati") or [],
                "domanda_naturale": v.get("domanda_naturale"),
            },
        })
    return out


# ---------------------------------------------------------------------------
# Ingestion (idempotent)
# ---------------------------------------------------------------------------

async def _list_corpus_files() -> List[Path]:
    files: List[Path] = []
    for name in CORPUS_FILES:
        p = MEMORY_ROOT / name
        if p.exists():
            files.append(p)
    # NOTA (Feb 2026 · Fix RAG Pattern A):
    # I file .md del manuale (memory/manuale/*.md) NON vengono più indicizzati.
    # I chunk atomici YAML (memory/manuale/hal/*.yaml) sono la SOLA sorgente
    # di retrieval per il manuale. I .md restano documenti di lettura umana.
    # Motivazione: il chunker word-window sulle prose markdown produceva
    # blocchi da ~500 parole che vincevano contro i chunk atomici YAML in
    # cosine similarity, degradando la precisione retrieval (Pattern A).
    return files


def _list_hal_yaml_files() -> List[Path]:
    """Elenca i file .yaml del manuale HAL, escludendo hal-index* (metadata)."""
    if not HAL_YAML_DIR.exists():
        return []
    out: List[Path] = []
    for f in sorted(HAL_YAML_DIR.glob("*.yaml")):
        if f.name.startswith("hal-index"):
            continue
        out.append(f)
    return out


async def ingest_corpus(force: bool = False) -> Dict[str, Any]:
    """Ingest markdown + HAL YAML corpus into `hal_knowledge_chunks`.

    Idempotent: if the file's MD5 matches the last-known md5 for that file,
    the file is skipped unless force=True.

    - .md files: chunk per sezione con word window (CHUNK_WORDS/OVERLAP).
    - .yaml del manuale HAL: 1 voce = 1 chunk atomico (chunk_id = v["id"]).
    """
    db = Database.get()
    report = {"scanned": 0, "reingested": [], "skipped": [], "removed": [], "total_chunks": 0}

    # --- 0. Cleanup: rimuovi chunk di file non più nel corpus attivo -----
    # Fix Pattern A (Feb 2026): dopo l'esclusione di memory/manuale/*.md
    # dal corpus RAG, i chunk .md del manuale eventualmente presenti in DB
    # da vecchi reindex vanno eliminati per evitare che continuino a essere
    # recuperati come fonti dominanti.
    active_files = {p.name for p in await _list_corpus_files()}
    active_files.update(p.name for p in _list_hal_yaml_files())
    orphan_files = await db.hal_knowledge_chunks.distinct("file")
    for fname in orphan_files:
        if fname not in active_files:
            res = await db.hal_knowledge_chunks.delete_many({"file": fname})
            if res.deleted_count:
                report["removed"].append({"file": fname, "chunks": res.deleted_count})

    # --- 1. Corpus .md tradizionale ------------------------------------
    for path in await _list_corpus_files():
        report["scanned"] += 1
        text = path.read_text(encoding="utf-8")
        md5 = hashlib.md5(text.encode("utf-8")).hexdigest()
        existing = await db.hal_knowledge_chunks.find_one(
            {"file": path.name}, {"md5_source": 1}
        )
        existing_md5 = existing.get("md5_source") if existing else None
        if not force and existing_md5 == md5:
            report["skipped"].append(path.name)
            continue
        await db.hal_knowledge_chunks.delete_many({"file": path.name})
        chunks = _chunk_file(path.name, text)
        if chunks:
            for c in chunks:
                c["id"] = str(uuid4())
                c["updated_at"] = utcnow_iso()
            await db.hal_knowledge_chunks.insert_many(chunks)
        report["reingested"].append({"file": path.name, "chunks": len(chunks)})
        report["total_chunks"] += len(chunks)

    # --- 2. Manuale HAL YAML (1 voce = 1 chunk atomico) ----------------
    for path in _list_hal_yaml_files():
        report["scanned"] += 1
        raw = path.read_bytes()
        md5 = hashlib.md5(raw).hexdigest()
        existing = await db.hal_knowledge_chunks.find_one(
            {"file": path.name}, {"md5_source": 1}
        )
        existing_md5 = existing.get("md5_source") if existing else None
        if not force and existing_md5 == md5:
            report["skipped"].append(path.name)
            continue
        await db.hal_knowledge_chunks.delete_many({"file": path.name})
        chunks = _chunk_yaml_hal_file(path.name, raw)
        if chunks:
            for c in chunks:
                c["id"] = str(uuid4())
                c["updated_at"] = utcnow_iso()
            await db.hal_knowledge_chunks.insert_many(chunks)
        report["reingested"].append({"file": path.name, "chunks": len(chunks)})
        report["total_chunks"] += len(chunks)

    # Rebuild TF-IDF index only if something actually changed
    if report["reingested"] or report["removed"] or force:
        await _rebuild_tfidf_index()
    return report


# ---------------------------------------------------------------------------
# TF-IDF index (persisted in Mongo as pickle blob — small, ≪1MB)
# ---------------------------------------------------------------------------

_ITALIAN_STOPS = {
    # Compact italian stopword list — full one is huge, this covers ~90% of noise.
    "il", "la", "lo", "gli", "le", "i", "un", "una", "uno", "di", "a", "da", "in", "con",
    "su", "per", "tra", "fra", "e", "ed", "o", "od", "ma", "però", "che", "chi", "cui",
    "come", "quando", "dove", "cosa", "questo", "questa", "questi", "queste", "quello",
    "quella", "quelli", "quelle", "se", "sì", "no", "non", "più", "meno", "molto", "poco",
    "ho", "hai", "ha", "abbiamo", "avete", "hanno", "sono", "sei", "siamo", "siete", "essere",
    "avere", "fare", "del", "della", "dei", "delle", "al", "alla", "ai", "alle", "dal",
    "dalla", "dai", "dalle", "nel", "nella", "nei", "nelle", "sul", "sulla", "sui", "sulle",
    "col", "come", "anche", "ancora", "già", "ora", "solo", "tra", "ecc", "the", "of", "and",
    "in", "to", "for", "on", "with", "is", "are",
}


async def _rebuild_tfidf_index() -> None:
    db = Database.get()
    cursor = db.hal_knowledge_chunks.find({}, {"id": 1, "text": 1}).sort([("file", 1), ("chunk_id", 1)])
    docs = await cursor.to_list(None)
    if not docs:
        await db.hal_knowledge_meta.update_one(
            {"id": "singleton"},
            {"$set": {"id": "singleton", "empty": True, "updated_at": utcnow_iso()}},
            upsert=True,
        )
        return
    corpus_texts = [d["text"] for d in docs]
    corpus_ids = [d["id"] for d in docs]
    vectorizer = TfidfVectorizer(
        lowercase=True,
        strip_accents="unicode",
        ngram_range=(1, 2),
        min_df=1,
        max_df=0.95,
        stop_words=list(_ITALIAN_STOPS),
    )
    matrix = vectorizer.fit_transform(corpus_texts)
    # H9 — JSON-serialized index (no pickle: a compromised DB must never lead to RCE)
    index_json = json.dumps({
        "vocab": {term: int(i) for term, i in vectorizer.vocabulary_.items()},
        "idf": vectorizer.idf_.tolist(),
        "data": matrix.data.tolist(),
        "indices": matrix.indices.tolist(),
        "indptr": matrix.indptr.tolist(),
        "shape": list(matrix.shape),
        "ids": corpus_ids,
    })
    await db.hal_knowledge_meta.update_one(
        {"id": "singleton"},
        {"$set": {
            "id": "singleton",
            "empty": False,
            "index_size": len(corpus_ids),
            "vocab_size": len(vectorizer.vocabulary_),
            "index_json": index_json,
            "updated_at": utcnow_iso(),
        },
         "$unset": {"blob": ""}},
        upsert=True,
    )
    logger.info("hal_knowledge tfidf rebuilt: %d chunks, %d terms", len(corpus_ids), len(vectorizer.vocabulary_))


_CACHE: Dict[str, Any] = {"blob_ts": None, "cv": None, "idf": None, "matrix": None, "ids": None}


async def _load_index() -> Optional[Dict[str, Any]]:
    db = Database.get()
    meta = await db.hal_knowledge_meta.find_one({"id": "singleton"})
    if not meta or meta.get("empty"):
        return None
    if not meta.get("index_json"):
        # Legacy pickle-based index: rebuild once in the new JSON format.
        await _rebuild_tfidf_index()
        meta = await db.hal_knowledge_meta.find_one({"id": "singleton"})
        if not meta or not meta.get("index_json"):
            return None
    ts = meta.get("updated_at")
    if _CACHE["blob_ts"] == ts and _CACHE["cv"] is not None:
        return _CACHE
    payload = json.loads(meta["index_json"])
    matrix = csr_matrix(
        (payload["data"], payload["indices"], payload["indptr"]),
        shape=tuple(payload["shape"]),
    )
    cv = CountVectorizer(
        lowercase=True,
        strip_accents="unicode",
        ngram_range=(1, 2),
        stop_words=list(_ITALIAN_STOPS),
        vocabulary=payload["vocab"],
    )
    _CACHE.update({
        "blob_ts": ts,
        "cv": cv,
        "idf": np.asarray(payload["idf"]),
        "matrix": matrix,
        "ids": payload["ids"],
    })
    return _CACHE


# ---------------------------------------------------------------------------
# Retrieval + generation
# ---------------------------------------------------------------------------

async def retrieve_chunks(query: str, k: int = TOP_K) -> List[Dict[str, Any]]:
    idx = await _load_index()
    if idx is None:
        return []
    counts = idx["cv"].transform([query])
    q_vec = counts.multiply(idx["idf"]).tocsr()
    sims = cosine_similarity(q_vec, idx["matrix"])[0]
    top_indices = np.argsort(sims)[::-1][:k]
    top = []
    db = Database.get()
    for pos in top_indices:
        sim = float(sims[pos])
        if sim <= 0:
            continue
        chunk_id = idx["ids"][pos]
        doc = await db.hal_knowledge_chunks.find_one(
            {"id": chunk_id}, {"_id": 0, "file": 1, "section": 1, "text": 1, "chunk_id": 1}
        )
        if doc:
            top.append({**doc, "similarity": round(sim, 4)})
    return top


def _build_prompt(question: str, chunks: List[Dict[str, Any]]) -> str:
    if not chunks:
        return question
    ctx_lines = []
    for i, c in enumerate(chunks, 1):
        ctx_lines.append(f"[FONTE {i} · {c['file']} · sezione: {c.get('section') or 'n/a'}]\n{c['text']}\n")
    context = "\n---\n".join(ctx_lines)
    return f"""Rispondi alla domanda dell'utente basandoti ESCLUSIVAMENTE sulle fonti qui sotto.
Se le fonti non contengono la risposta, di' onestamente "Non ho abbastanza contesto nel corpus OMNIA per rispondere". NON inventare informazioni.
Quando citi una fonte, usa il formato [FONTE N] alla fine della frase.
Rispondi in italiano, tono professionale e conciso, massimo 300 parole.

FONTI:
{context}

DOMANDA UTENTE:
{question}

RISPOSTA:"""


async def generate_answer(prompt: str, session_id: str) -> Dict[str, Any]:
    """Non-streaming generation via Emergent LLM Key + Gemini 3 Flash Preview."""
    from emergentintegrations.llm.chat import LlmChat, UserMessage
    api_key = os.environ.get("EMERGENT_LLM_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="emergent_llm_key_not_configured")
    chat = LlmChat(
        api_key=api_key,
        session_id=session_id,
        system_message="Sei HAL Knowledge, l'assistente informativo di OMNIA Real Estate Lab. Rispondi solo con informazioni presenti nelle fonti fornite.",
    ).with_model(MODEL_PROVIDER, MODEL_NAME)
    response = await chat.send_message(UserMessage(text=prompt))
    text = getattr(response, "text", None) or str(response)
    return {"text": text.strip()}


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

_ROLES = ("agency_admin", "super_admin", "branch_admin", "group_admin", "agent")


@router.get("/status")
async def hal_status(user: dict = Depends(require_roles(*_ROLES))):
    db = Database.get()
    total = await db.hal_knowledge_chunks.count_documents({})
    manual_hal_chunks = await db.hal_knowledge_chunks.count_documents(
        {"file": {"$regex": r"\.yaml$"}}
    )
    meta = await db.hal_knowledge_meta.find_one({"id": "singleton"}, {"_id": 0, "blob": 0})
    return {
        "chunks_indexed": total,
        "manual_hal_indexed": manual_hal_chunks,  # >0 quando le voci YAML del manuale sono attive
        "index": meta or {"empty": True},
        "model": {"provider": MODEL_PROVIDER, "name": MODEL_NAME},
        "corpus_files": CORPUS_FILES,
    }


@router.post("/reindex")
async def hal_reindex(
    force: bool = False,
    user: dict = Depends(require_roles("super_admin")),
):
    """Only super_admin can reingest. Idempotent when force=False."""
    report = await ingest_corpus(force=force)
    return report


@router.post("/ask")
async def hal_ask(
    body: KnowledgeAskRequest,
    request: Request,
    user: dict = Depends(require_roles(*_ROLES)),
):
    """RAG one-shot Q&A. Non-streaming (simpler & sufficient for M5.S2)."""
    question = body.question.strip()
    session_id = body.session_id or f"halk-{user.get('id') or 'anon'}-{uuid4().hex[:8]}"
    chunks = await retrieve_chunks(question, k=TOP_K)
    best_sim = max((c["similarity"] for c in chunks), default=0.0)

    if not chunks or best_sim < CONFIDENCE_MIN:
        db = Database.get()
        await db.hal_knowledge_sessions.insert_one({
            "id": str(uuid4()),
            "agency_id": (user.get("agency_ids") or [None])[0],
            "user_id": user.get("id"),
            "question": question,
            "answer": None,
            "sources": [],
            "confidence": round(best_sim, 4),
            "status": "insufficient_context",
            "created_at": utcnow_iso(),
        })
        return {
            "answer": "Non ho abbastanza contesto nel corpus OMNIA per rispondere a questa domanda. Puoi riformularla o contattare il team OMNIA.",
            "sources": [],
            "confidence": round(best_sim, 4),
            "status": "insufficient_context",
        }

    prompt = _build_prompt(question, chunks)
    try:
        gen = await generate_answer(prompt, session_id=session_id)
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("hal_ask generation failed")
        raise HTTPException(status_code=502, detail=f"generation_error:{type(e).__name__}")

    sources = [
        {
            "file": c["file"],
            "section": c.get("section"),
            "chunk_id": c.get("chunk_id"),
            "similarity": c["similarity"],
        }
        for c in chunks
    ]
    status = "high" if best_sim >= CONFIDENCE_HIGH else "medium"
    db = Database.get()
    await db.hal_knowledge_sessions.insert_one({
        "id": str(uuid4()),
        "session_id": session_id,
        "agency_id": (user.get("agency_ids") or [None])[0],
        "user_id": user.get("id"),
        "question": question,
        "answer": gen["text"],
        "sources": sources,
        "confidence": round(best_sim, 4),
        "status": status,
        "created_at": utcnow_iso(),
    })
    return {
        "answer": gen["text"],
        "sources": sources,
        "confidence": round(best_sim, 4),
        "status": status,
        "session_id": session_id,
    }


@router.get("/history")
async def hal_history(
    limit: int = 20,
    user: dict = Depends(require_roles(*_ROLES)),
):
    db = Database.get()
    limit = max(1, min(limit, 100))
    q = {"user_id": user.get("id")} if user.get("role") != "super_admin" else {}
    cursor = db.hal_knowledge_sessions.find(q, {"_id": 0}).sort("created_at", -1).limit(limit)
    items = await cursor.to_list(limit)
    return {"items": items, "total": len(items)}
