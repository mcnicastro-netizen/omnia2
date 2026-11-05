"""OMNIA — Domain ownership lookup (M2.5.4b, D-054) · fix D-144.

Sources (in order):
1. RDAP via rdap.org + TLD-specific servers (when the TLD is in IANA bootstrap).
2. WHOIS for TLDs without production RDAP — notably **.it** (Registro.it has
   WHOIS, not a public RDAP in the IANA dns.json bootstrap). Treating an
   rdap.org 404 on .it as «domain free» was a false negative (dogfood Founder
   05-Nov-2026: nicastroimmobiliare.it → NOT REGISTERED while live for years).
3. DNS existence (NS/A/AAAA) as last resort: never claim «libero» if DNS answers.

Design:
- Pure httpx/asyncio + stdlib socket whois — no new deps.
- Fail closed to `error` / DNS-confirmed registered, never false «is_free».
"""
from __future__ import annotations

import asyncio
import re
import socket
from typing import Any, Dict, List, Optional, Tuple

import httpx

_UNIVERSAL_RDAP = "https://rdap.org/domain/{domain}"
# Only TLDs with known production RDAP. .it is intentionally absent (no IANA RDAP).
_TLD_SERVERS = {
    "eu": "https://rdap.eu/domain/{domain}",
    "com": "https://rdap.verisign.com/com/v1/domain/{domain}",
    "net": "https://rdap.verisign.com/net/v1/domain/{domain}",
    "org": "https://rdap.publicinterestregistry.org/rdap/domain/{domain}",
    "fr": "https://rdap.nic.fr/domain/{domain}",
}

# Authoritative WHOIS hosts for TLDs without reliable public RDAP
_WHOIS_HOSTS = {
    "it": "whois.nic.it",
}

_TIMEOUT = httpx.Timeout(connect=5.0, read=8.0, write=5.0, pool=5.0)
_ALLOWED_DOMAIN = re.compile(
    r"^[a-z0-9]([a-z0-9-]*[a-z0-9])?(\.[a-z0-9]([a-z0-9-]*[a-z0-9])?)+$"
)


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
    result = []
    for e in entities or []:
        roles = e.get("roles") or []
        if role in roles:
            result.append(e)
    return result


def _vcard_field(entity: Dict[str, Any], field: str) -> Optional[str]:
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
    for ev in rdap.get("events") or []:
        if ev.get("eventAction") == action:
            return ev.get("eventDate")
    return None


def _extract_nameservers(rdap: Dict[str, Any]) -> List[str]:
    out: List[str] = []
    for ns in rdap.get("nameservers") or []:
        n = ns.get("ldhName") or ns.get("unicodeName")
        if n:
            out.append(str(n).lower())
    return sorted(set(out))


async def _fetch_rdap(url: str) -> Tuple[str, Optional[Dict[str, Any]]]:
    """Return (status, payload). status: ok | not_found | error."""
    try:
        async with httpx.AsyncClient(
            timeout=_TIMEOUT,
            follow_redirects=True,
            headers={
                "Accept": "application/rdap+json",
                "User-Agent": "OMNIA-DomainChecker/1.1",
            },
        ) as c:
            r = await c.get(url)
        if r.status_code == 404:
            return "not_found", {"__notFound": True}
        if r.status_code >= 400:
            return "error", None
        return "ok", r.json()
    except Exception:
        return "error", None


def _parse_whois_it(text: str) -> Optional[Dict[str, Any]]:
    """Parse Registro.it WHOIS text into our normalized fields."""
    if not text:
        return None
    low = text.lower()
    if "status:" in low and re.search(r"status:\s*available", low):
        return {"not_found": True}
    if "domain:" not in low and "not found" in low:
        return {"not_found": True}
    if "domain:" not in low:
        return None

    def _field(label: str) -> Optional[str]:
        m = re.search(rf"^{re.escape(label)}:\s*(.+)$", text, re.I | re.M)
        return m.group(1).strip() if m else None

    # Registrant Organization is under the Registrant section
    registrant = None
    m_org = re.search(
        r"Registrant\s*\n(?:.*\n)*?\s*Organization:\s*(.+)",
        text,
        re.I,
    )
    if m_org:
        registrant = m_org.group(1).strip()
    if not registrant:
        m_name = re.search(
            r"Registrant\s*\n(?:.*\n)*?\s*Name:\s*(.+)",
            text,
            re.I,
        )
        if m_name:
            registrant = m_name.group(1).strip()

    registrar = None
    m_reg = re.search(
        r"Registrar\s*\n(?:.*\n)*?\s*Organization:\s*(.+)",
        text,
        re.I,
    )
    if m_reg:
        registrar = m_reg.group(1).strip()
    if not registrar:
        registrar = _field("Registrar")

    nameservers: List[str] = []
    in_ns = False
    for line in text.splitlines():
        if re.match(r"^Nameservers\s*$", line.strip(), re.I):
            in_ns = True
            continue
        if in_ns:
            if not line.strip():
                if nameservers:
                    break
                continue
            if ":" in line and not line.strip().endswith(":"):
                # new section
                break
            if re.match(r"^[A-Za-z0-9.-]+\.[A-Za-z]{2,}$", line.strip()):
                nameservers.append(line.strip().lower())

    def _it_date(label: str) -> Optional[str]:
        raw = _field(label)
        if not raw:
            return None
        # "2019-04-08 12:46:52" → ISO-ish
        return raw.replace(" ", "T") + ("+00:00" if "T" in raw.replace(" ", "T") else "")

    created = _it_date("Created")
    # Prefer Expire Date for .it
    expires = _field("Expire Date")
    if expires:
        expires = expires.strip() + "T00:00:00+00:00" if "T" not in expires else expires
    last = _it_date("Last Update")

    return {
        "not_found": False,
        "registrant": registrant,
        "registrar": registrar,
        "nameservers": sorted(set(nameservers)),
        "created_at": created,
        "expires_at": expires,
        "last_changed": last,
    }


async def _whois_lookup(domain: str) -> Optional[Dict[str, Any]]:
    host = _WHOIS_HOSTS.get(_tld(domain))
    if not host:
        return None

    def _sync() -> str:
        with socket.create_connection((host, 43), timeout=10) as s:
            s.sendall(f"{domain}\r\n".encode("ascii", "ignore"))
            chunks: List[bytes] = []
            while True:
                buf = s.recv(4096)
                if not buf:
                    break
                chunks.append(buf)
            return b"".join(chunks).decode("utf-8", "replace")

    try:
        text = await asyncio.to_thread(_sync)
    except Exception:
        return None
    if _tld(domain) == "it":
        parsed = _parse_whois_it(text)
        if parsed is None:
            return None
        return {**parsed, "raw_source": f"whois://{host}/{domain}"}
    return None


async def _dns_exists(domain: str) -> bool:
    """True if the domain resolves NS or A/AAAA — strong signal it is registered."""

    def _check() -> bool:
        try:
            socket.getaddrinfo(domain, None)
            return True
        except socket.gaierror:
            pass
        try:
            # NS lookup via getaddrinfo on a common host pattern is weak;
            # try resolving www as secondary evidence.
            socket.getaddrinfo(f"www.{domain}", None)
            return True
        except socket.gaierror:
            return False

    try:
        return await asyncio.to_thread(_check)
    except Exception:
        return False


def _from_rdap_json(domain: str, rdap: Dict[str, Any], used_url: str) -> Dict[str, Any]:
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


async def rdap_lookup(domain: str) -> Dict[str, Any]:
    """Lookup domain ownership data. Prefer RDAP; .it → WHOIS; never false «free»."""
    domain = domain.lower().strip()
    result_base: Dict[str, Any] = {
        "ok": False,
        "domain": domain,
        "not_found": False,
        "registrant": None,
        "registrant_type": None,
        "registrar": None,
        "nameservers": [],
        "created_at": None,
        "expires_at": None,
        "last_changed": None,
        "raw_source": None,
        "error": None,
    }

    candidates: List[str] = []
    tld = _tld(domain)
    # For TLDs without IANA RDAP (e.g. .it), skip universal bootstrap — it 404s
    # and historically caused false «not_registered».
    if tld not in _WHOIS_HOSTS:
        candidates.append(_UNIVERSAL_RDAP.format(domain=domain))
    tld_srv = _TLD_SERVERS.get(tld)
    if tld_srv:
        candidates.append(tld_srv.format(domain=domain))

    saw_not_found = False
    for url in candidates:
        status, data = await _fetch_rdap(url)
        if status == "ok" and data and not data.get("__notFound"):
            return _from_rdap_json(domain, data, url)
        if status == "not_found":
            saw_not_found = True
            # keep trying other candidates / whois — do NOT return early

    # WHOIS fallback (authoritative for .it)
    whois = await _whois_lookup(domain)
    if whois is not None:
        if whois.get("not_found"):
            # Confirm with DNS before declaring free
            if await _dns_exists(domain):
                # Never claim «libero» if DNS answers — ownership unknown.
                return {
                    **result_base,
                    "ok": True,
                    "not_found": False,
                    "raw_source": whois.get("raw_source") or "dns",
                    "error": None,
                    "registrar": None,
                    "registrant": None,
                }
            return {
                **result_base,
                "ok": True,
                "not_found": True,
                "raw_source": whois.get("raw_source"),
            }
        return {
            **result_base,
            "ok": True,
            "not_found": False,
            "registrant": whois.get("registrant"),
            "registrar": whois.get("registrar"),
            "nameservers": whois.get("nameservers") or [],
            "created_at": whois.get("created_at"),
            "expires_at": whois.get("expires_at"),
            "last_changed": whois.get("last_changed"),
            "raw_source": whois.get("raw_source"),
        }

    # DNS last resort: registered but ownership unknown
    if await _dns_exists(domain):
        return {
            **result_base,
            "ok": True,
            "not_found": False,
            "raw_source": "dns",
            "error": None,
            "registrant": None,
            "registrar": None,
        }

    if saw_not_found and tld not in _WHOIS_HOSTS:
        return {**result_base, "ok": True, "not_found": True, "raw_source": "rdap"}

    return {**result_base, "error": "rdap_unreachable"}
