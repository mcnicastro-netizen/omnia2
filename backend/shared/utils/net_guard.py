"""OMNIA — SSRF guard: valida URL esterni prima di fetch server-side (C7)."""
import ipaddress
import socket
from urllib.parse import urlparse

from fastapi import HTTPException


def assert_public_url(url: str) -> None:
    """Raise 400 if the URL is not a public http(s) endpoint (blocks private/loopback/metadata IPs)."""
    try:
        u = urlparse(url or "")
    except Exception:
        raise HTTPException(status_code=400, detail="invalid_url")
    if u.scheme not in ("http", "https") or not u.hostname:
        raise HTTPException(status_code=400, detail="invalid_url_scheme")
    try:
        infos = socket.getaddrinfo(u.hostname, u.port or (443 if u.scheme == "https" else 80), proto=socket.IPPROTO_TCP)
    except socket.gaierror:
        raise HTTPException(status_code=400, detail="unresolvable_host")
    for info in infos:
        ip = ipaddress.ip_address(info[4][0])
        if (ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved
                or ip.is_multicast or ip.is_unspecified):
            raise HTTPException(status_code=400, detail="url_not_allowed")
