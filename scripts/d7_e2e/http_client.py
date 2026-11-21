"""Cookie + CSRF HTTP client for staging API."""
from __future__ import annotations

import http.cookiejar
import json
import urllib.error
import urllib.request
from typing import Any, Optional, Tuple

from . import config


class StagingClient:
    def __init__(self, api_base: str = config.STAGING_API_URL, origin: str = config.STAGING_FE_URL):
        self.api_base = api_base.rstrip("/")
        self.origin = origin.rstrip("/")
        self.cj = http.cookiejar.CookieJar()
        self.opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(self.cj))
        self.csrf: Optional[str] = None

    def request(
        self,
        method: str,
        path: str,
        data: Any = None,
        *,
        headers: Optional[dict] = None,
        timeout: int = 45,
    ) -> Tuple[int, Any]:
        h = {
            "Accept": "application/json",
            "Origin": self.origin,
            "Referer": self.origin + "/",
        }
        if self.csrf:
            h["X-CSRF-Token"] = self.csrf
        if headers:
            h.update(headers)
        body = None
        if data is not None:
            body = json.dumps(data).encode("utf-8")
            h["Content-Type"] = "application/json"
        url = self.api_base + path
        req = urllib.request.Request(url, data=body, headers=h, method=method)
        try:
            with self.opener.open(req, timeout=timeout) as resp:
                raw = resp.read()
                self._capture_csrf(resp)
                return resp.status, self._parse(raw)
        except urllib.error.HTTPError as e:
            raw = e.read()
            self._capture_csrf(e)
            return e.code, self._parse(raw)

    def _capture_csrf(self, resp) -> None:
        for c in self.cj:
            if c.name == "omnia_csrf":
                self.csrf = c.value
        hdr = resp.headers.get("X-CSRF-Token") or resp.headers.get("x-csrf-token")
        if hdr:
            self.csrf = hdr

    @staticmethod
    def _parse(raw: bytes) -> Any:
        text = raw.decode("utf-8", errors="replace") if raw else ""
        if not text:
            return None
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return text[:800]

    def health(self) -> Tuple[int, Any]:
        return self.request("GET", "/api/health")

    def login(self, email: str, password: str) -> Tuple[int, Any]:
        self.health()
        return self.request("POST", "/api/auth/login", {"email": email, "password": password})
