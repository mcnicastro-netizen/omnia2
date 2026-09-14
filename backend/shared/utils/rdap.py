"""OMNIA — RDAP client for domain ownership lookup (M2.5.4b, D-054).

Uses `rdap.org` as the universal bootstrap frontend: it accepts any TLD and
transparently proxies to the correct registry RDAP server. If it fails, we
fall back to the IANA-published RDAP server list for the top Italian TLDs.

Design:
- Pure httpx async, no external deps beyond what's already installed.
- 5s connect + 8s read timeout — RDAP servers are usually fast but registry
  can be slow at peak. We fail closed (return `ok=False`) rather than hang.
- Result shape is normalized so downstream code doesn't need to know the
  RDAP JSON quirks (each registry serializes contacts slightly differently).
"""
from __future__ import annotations
import re
from typing import Any, Dict, List, Optional

import httpx

_UNIVERSAL_RDAP = "https://rdap.org/domain/{domain}"
# Fallback for IT/EU when rdap.org has hiccups
_TLD_SERVERS = {
    "it": "https://rdap.pubtest.nic.it/domain/{domain}",
    "eu": "https://rdap.eu/domain/{domain}",
    "com": "https://rdap.verisign.com/com/v1/domain/{domain}",
    "net": "https://rdap.verisign.com/net/v1/domain/{domain}",
    "org": "https://rdap.publicinterestregistry.org/rdap/domain/{domain}",
}

_TIMEOUT = httpx.Timeout(connect=5.0, read=8.0, write=5.0, pool=5.0)

_ALLOWED_DOMAIN = re.compile(r"^[a-z0-9]([a-z0-9-]*[a-z0-9])?(\.[a-z0-9]([a-z0-9-]*[a-z0-9])?)+$")


def normalize_domain(raw: str) -> Optional[str]:
    """Lowercase, strip protocol/www/path. Return None if invalid."""
    if not raw:
        return None
    d = raw.strip().lower()
    d = re.sub(r"^https?://", "", d)
    d = re.sub(r"^www\.", "", d)
    d = d.split("/")[0].split("?")[0].split(":")[0]
    if not _ALLOWED_DOMAIN.match(d):
        return None
    if len(d) > 253:
        return None
    return d


def _tld(domain: str) -> str:
    return domain.rsplit(".", 1)[-1]


def _extract_entities(entities: List[Dict[str, Any]], role: str) -> List[Dict[str, Any]]:
    """RDAP entities have a `roles` array. Return entities matching `role`."""
    result = []
    for e in entities or []:
        roles = e.get("roles") or []
        if role in roles:
            result.append(e)
    return result


def _vcard_field(entity: Dict[str, Any], field: str) -> Optional[str]:
    """Read a jCard property (fn, org, email, ...) — RDAP normal encoding."""
    vcard = entity.get("vcardArray")
    if not vcard or len(vcard) < 2:
        return None
    for row in vcard[1]:
        if not isinstance(row, list) or len(row) < 4:
            continue
        if row[0] == field:
            val = row[3]
            if isinstance(val, list):
                return " ".join(str(x) for x in val if x)
            return str(val) if val else None
    return None


def _entity_display_name(entity: Dict[str, Any]) -> Optional[str]:
    return _vcard_field(entity, "fn") or _vcard_field(entity, "org") or None


def _extract_event(rdap: Dict[str, Any], action: str) -> Optional[str]:
    """RDAP events: registration, expiration, last changed, ..."""
    for ev in rdap.get("events") or []:
        if ev.get("eventAction") == action:
            return ev.get("eventDate")
    return None


def _extract_nameservers(rdap: Dict[str, Any]) -> List[str]:
    """Some registries hide NS behind different keys — try both."""
    out: List[str] = []
    for ns in rdap.get("nameservers") or []:
        n = ns.get("ldhName") or ns.get("unicodeName")
        if n:
            out.append(str(n).lower())
    return sorted(set(out))


async def _fetch(url: str) -> Optional[Dict[str, Any]]:
    """Return parsed JSON, or None on any transport/parsing failure."""
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT, follow_redirects=True,
                                     headers={"Accept": "application/rdap+json",
                                              "User-Agent": "OMNIA-DomainChecker/1.0"}) as c:
            r = await c.get(url)
        if r.status_code == 404:
            return {"__notFound": True}
        if r.status_code >= 400:
            return None
        return r.json()
    except Exception:
        return None


async def rdap_lookup(domain: str) -> Dict[str, Any]:
    """Query RDAP for `domain` and return a normalized result.

    Returned shape (always):
        {
          "ok": bool,
          "domain": str,
          "not_found": bool,              # true if registry replied 404
          "registrant": str | None,       # display name (fn or org)
          "registrant_type": str | None,  # "kind" jCard field if present
          "registrar": str | None,        # registrar entity fn/org
          "nameservers": [str, ...],
          "created_at": str | None,       # ISO 8601 event date
          "expires_at": str | None,
          "last_changed": str | None,
          "raw_source": str,              # which RDAP URL succeeded
          "error": str | None,
        }
    """
    domain = domain.lower().strip()
    result_base: Dict[str, Any] = {
        "ok": False, "domain": domain, "not_found": False,
        "registrant": None, "registrant_type": None,
        "registrar": None, "nameservers": [],
        "created_at": None, "expires_at": None, "last_changed": None,
        "raw_source": None, "error": None,
    }

    # Try rdap.org first (universal bootstrap), then TLD-specific fallback.
    candidates = [_UNIVERSAL_RDAP.format(domain=domain)]
    tld_srv = _TLD_SERVERS.get(_tld(domain))
    if tld_srv:
        candidates.append(tld_srv.format(domain=domain))

    rdap: Optional[Dict[str, Any]] = None
    used_url: Optional[str] = None
    for url in candidates:
        data = await _fetch(url)
        if data and not data.get("__notFound"):
            rdap = data
            used_url = url
            break
        if data and data.get("__notFound"):
            return {**result_base, "not_found": True, "raw_source": url, "ok": True}

    if not rdap:
        return {**result_base, "error": "rdap_unreachable"}

    entities = rdap.get("entities") or []
    reg_entities = _extract_entities(entities, "registrant")
    registrar_entities = _extract_entities(entities, "registrar")

    registrant_name: Optional[str] = None
    registrant_kind: Optional[str] = None
    if reg_entities:
        registrant_name = _entity_display_name(reg_entities[0])
        registrant_kind = _vcard_field(reg_entities[0], "kind")

    registrar_name: Optional[str] = None
    if registrar_entities:
        registrar_name = _entity_display_name(registrar_entities[0])

    return {
        "ok": True,
        "domain": domain,
        "not_found": False,
        "registrant": registrant_name,
        "registrant_type": registrant_kind,
        "registrar": registrar_name,
        "nameservers": _extract_nameservers(rdap),
        "created_at": _extract_event(rdap, "registration"),
        "expires_at": _extract_event(rdap, "expiration"),
        "last_changed": _extract_event(rdap, "last changed"),
        "raw_source": used_url,
        "error": None,
    }
