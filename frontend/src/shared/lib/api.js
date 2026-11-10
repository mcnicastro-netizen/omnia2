/**
 * OMNIA — Shared API client (axios)
 * - Reads REACT_APP_BACKEND_URL from .env
 * - Automatically sends Accept-Language header from current i18n lang
 * - Silent session refresh on 401 (access cookie TTL is short; refresh cookie lasts days)
 * - CSRF: prefer sessionStorage mirror of X-CSRF-Token (cross-site FE cannot read api.* cookie)
 */
import axios from "axios";
import i18n from "../i18n/config";

const BACKEND_URL = (process.env.REACT_APP_BACKEND_URL || "").replace(/\/$/, "");
// Empty BACKEND_URL → same-origin /api (dev proxy or reverse proxy / tunnel)
export const API_BASE = BACKEND_URL ? `${BACKEND_URL}/api` : "/api";

/**
 * Absolute URL for img/a against Object Storage paths.
 * DB keeps relative /api/media/... ; on cloud/www FE host that path 404s and thumbs vanish.
 * data:/blob:/http(s) pass through unchanged.
 */
export function resolveMediaUrl(url) {
  if (!url || typeof url !== "string") return "";
  if (
    url.startsWith("data:") ||
    url.startsWith("blob:") ||
    /^https?:\/\//i.test(url)
  ) {
    return url;
  }
  if (url.startsWith("/") && BACKEND_URL) {
    return `${BACKEND_URL}${url}`;
  }
  return url;
}

const CSRF_STORAGE_KEY = "omnia_csrf_token";

export const api = axios.create({
  baseURL: API_BASE,
  timeout: 30000, // R6 — le chiamate AI/PDF possono superare 15s; override per-call dove serve
});

let refreshPromise = null;

function isAuthPath(url = "") {
  return (
    url.includes("/auth/login") ||
    url.includes("/auth/register") ||
    url.includes("/auth/refresh") ||
    url.includes("/auth/logout") ||
    url.includes("/auth/google") ||
    url.includes("/auth/mfa/") ||
    url.includes("/auth/forgot") ||
    url.includes("/auth/reset")
  );
}

function readCsrfFromDocumentCookie() {
  try {
    if (typeof document === "undefined") return "";
    const m = document.cookie.match(/(?:^|;\s*)omnia_csrf=([^;]+)/);
    return m && m[1] ? decodeURIComponent(m[1]) : "";
  } catch {
    return "";
  }
}

function readCsrfToken() {
  try {
    if (typeof sessionStorage !== "undefined") {
      const stored = sessionStorage.getItem(CSRF_STORAGE_KEY);
      if (stored) return stored;
    }
  } catch {
    /* private mode */
  }
  return readCsrfFromDocumentCookie();
}

function storeCsrfToken(token) {
  if (!token) return;
  try {
    if (typeof sessionStorage !== "undefined") {
      sessionStorage.setItem(CSRF_STORAGE_KEY, token);
    }
  } catch {
    /* ignore */
  }
}

function captureCsrfFromResponse(response) {
  const h = response?.headers;
  if (!h) return;
  const token =
    (typeof h.get === "function" ? h.get("x-csrf-token") : null) ||
    h["x-csrf-token"] ||
    h["X-CSRF-Token"];
  if (token) storeCsrfToken(String(token));
}

/** Single-flight refresh so parallel 401s don't stampede. */
export function refreshSession() {
  if (!refreshPromise) {
    refreshPromise = api
      .post("/auth/refresh")
      .then((r) => {
        captureCsrfFromResponse(r);
        return r.data;
      })
      .finally(() => {
        refreshPromise = null;
      });
  }
  return refreshPromise;
}

api.interceptors.request.use((config) => {
  config.headers["Accept-Language"] = i18n.language || "it";
  // Always send cookies (for httpOnly auth cookies)
  config.withCredentials = true;
  // FormData: leave Content-Type unset so the browser sets multipart boundary.
  // A stale application/json header breaks logo/KYC uploads.
  try {
    if (typeof FormData !== "undefined" && config.data instanceof FormData) {
      if (config.headers && typeof config.headers.delete === "function") {
        config.headers.delete("Content-Type");
      } else if (config.headers) {
        delete config.headers["Content-Type"];
        delete config.headers["content-type"];
      }
    }
  } catch {
    /* ignore */
  }
  // CSRF double-submit: sessionStorage mirror (cross-site) → document.cookie fallback
  try {
    const method = (config.method || "get").toUpperCase();
    if (["POST", "PUT", "PATCH", "DELETE"].includes(method)) {
      const tok = readCsrfToken();
      if (tok) config.headers["X-CSRF-Token"] = tok;
    }
  } catch {
    /* ignore */
  }
  return config;
});

api.interceptors.response.use(
  (r) => {
    captureCsrfFromResponse(r);
    // Vercel SPA rewrite can return index.html with 200 for /api/* when
    // REACT_APP_BACKEND_URL was empty at build — treat as unreachable API.
    const ct = String(r?.headers?.["content-type"] || "");
    const data = r?.data;
    const looksHtml =
      ct.includes("text/html") ||
      (typeof data === "string" && /^\s*<(!doctype|html)\b/i.test(data));
    if (looksHtml) {
      const err = new Error("API returned HTML instead of JSON (check REACT_APP_BACKEND_URL)");
      err.response = r;
      err.config = r.config;
      err.code = "ERR_API_HTML";
      if (typeof window !== "undefined") {
        window.dispatchEvent(
          new CustomEvent("omnia:api-unreachable", {
            detail: { status: r.status, url: r.config?.url, message: err.message },
          }),
        );
      }
      return Promise.reject(err);
    }
    if (typeof window !== "undefined") {
      window.dispatchEvent(new CustomEvent("omnia:api-reachable"));
    }
    return r;
  },
  async (error) => {
    if (process.env.NODE_ENV !== "production") {
      console.error("[OMNIA API]", error?.response?.status, error?.message);
    }

    const status = error?.response?.status;
    const config = error?.config || {};
    const url = config.url || "";
    captureCsrfFromResponse(error?.response);

    // Access expired → try refresh once, then retry the original call
    if (status === 401 && !config.__isRetry && !isAuthPath(url)) {
      try {
        await refreshSession();
        config.__isRetry = true;
        return api.request(config);
      } catch {
        window.dispatchEvent(new CustomEvent("omnia:unauthorized"));
        return Promise.reject(error);
      }
    }

    if (status === 401 && !isAuthPath(url)) {
      window.dispatchEvent(new CustomEvent("omnia:unauthorized"));
    }

    // P-052 — network / gateway down (no spinner forever without signal)
    // Do NOT treat CSRF 403 as unreachable — that is a client token issue.
    const detail = error?.response?.data?.detail;
    const csrfFail =
      status === 403 &&
      detail &&
      typeof detail === "object" &&
      detail.error === "csrf_failed";
    const unreachable =
      !csrfFail &&
      (!error.response ||
        status === 502 ||
        status === 503 ||
        status === 504 ||
        error.code === "ECONNABORTED" ||
        error.message === "Network Error");
    if (unreachable && typeof window !== "undefined") {
      window.dispatchEvent(
        new CustomEvent("omnia:api-unreachable", {
          detail: { status: status || null, url, message: error?.message },
        }),
      );
    }
    return Promise.reject(error);
  }
);
