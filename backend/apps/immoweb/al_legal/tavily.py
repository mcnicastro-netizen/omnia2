"""Tavily web-search client for AL Legal.

Restricts queries to Italian authoritative legal sources by default.
Async, server-side only. Falls back to empty results on errors so the
agent can still respond with a "fonti non disponibili" disclaimer.
"""
from __future__ import annotations

import logging
import os
from typing import Any, Dict, List, Optional

import httpx

logger = logging.getLogger("omnia.legal.tavily")

TAVILY_URL = "https://api.tavily.com/search"
TAVILY_API_KEY = os.environ.get("TAVILY_API_KEY")

# Authoritative Italian legal sources only (D-028).
# Priority order: PRIMARY (state-published) first → SECONDARY (institutional) → TERTIARY (legal portals).
# Tavily respects the include_domains list order as a soft hint; the result `score` is the real ranker.
# Brocardi REMOVED (founder decision 25-Giu-2026): inconsistently reliable for binding citations.
LEGAL_DOMAINS = [
    # PRIMARY — state-published, binding source of truth
    "normattiva.it",          # official gazzetta della Repubblica
    "gazzettaufficiale.it",   # Gazzetta Ufficiale italiana
    # SECONDARY — institutional, high authority
    "agenziaentrate.gov.it",  # tax authority (circolari, risoluzioni)
    "cassazione.it",          # Corte Suprema di Cassazione
    "notariato.it",           # Consiglio Nazionale del Notariato
    # TERTIARY — legal portals (well-cited, secondary references only)
    "altalex.com",
]


async def web_search(
    query: str,
    *,
    max_results: int = 5,
    include_domains: Optional[List[str]] = None,
    timeout: float = 20.0,
) -> List[Dict[str, Any]]:
    """Run a Tavily search and return a list of citation dicts.

    Each citation: {title, url, snippet, score}.
    Returns [] on any error (so the agent can still respond with a disclaimer).
    """
    if not TAVILY_API_KEY:
        logger.warning("TAVILY_API_KEY missing — skipping web search")
        return []

    payload = {
        "api_key": TAVILY_API_KEY,           # supports body auth too
        "query": query,
        "search_depth": "advanced",
        "max_results": max_results,
        "include_domains": include_domains or LEGAL_DOMAINS,
        "include_answer": False,
        "include_raw_content": False,
    }

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.post(TAVILY_URL, json=payload)
        if resp.status_code != 200:
            logger.warning("Tavily HTTP %s: %s", resp.status_code, resp.text[:200])
            return []
        data = resp.json()
    except httpx.TimeoutException:
        logger.warning("Tavily timeout for query=%r", query[:80])
        return []
    except Exception as e:
        logger.warning("Tavily error: %s", e)
        return []

    out: List[Dict[str, Any]] = []
    for r in data.get("results", []) or []:
        url = r.get("url") or ""
        snippet = (r.get("content") or "").strip()
        if not url or not snippet:
            continue
        out.append({
            "title": (r.get("title") or url)[:200],
            "url": url,
            "snippet": snippet[:1200],
            "score": float(r.get("score") or 0.0),
        })
    return out


def format_sources_for_prompt(citations: List[Dict[str, Any]]) -> str:
    """Render citations as numbered block to inject into the agent prompt."""
    if not citations:
        return "Nessuna fonte normativa disponibile per questa query. Avvisa l'utente."
    lines: List[str] = []
    for i, c in enumerate(citations, start=1):
        lines.append(f"[{i}] {c['title']}\n    URL: {c['url']}\n    {c['snippet']}")
    return "\n\n".join(lines)
