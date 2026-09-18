/**
 * OMNIA — Shared API client (axios)
 * - Reads REACT_APP_BACKEND_URL from .env
 * - Automatically sends Accept-Language header from current i18n lang
 * - Silent session refresh on 401 (access cookie TTL is short; refresh cookie lasts days)
 */
import axios from "axios";
import i18n from "../i18n/config";

const BACKEND_URL = (process.env.REACT_APP_BACKEND_URL || "").replace(/\/$/, "");
// Empty BACKEND_URL → same-origin /api (dev proxy or reverse proxy / tunnel)
export const API_BASE = BACKEND_URL ? `${BACKEND_URL}/api` : "/api";

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

/** Single-flight refresh so parallel 401s don't stampede. */
export function refreshSession() {
  if (!refreshPromise) {
    refreshPromise = api
      .post("/auth/refresh")
      .then((r) => r.data)
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
  // CSRF double-submit when SameSite=None (prod): mirror omnia_csrf cookie → header
  try {
    const method = (config.method || "get").toUpperCase();
    if (["POST", "PUT", "PATCH", "DELETE"].includes(method) && typeof document !== "undefined") {
      const m = document.cookie.match(/(?:^|;\s*)omnia_csrf=([^;]+)/);
      if (m && m[1]) {
        config.headers["X-CSRF-Token"] = decodeURIComponent(m[1]);
      }
    }
  } catch {
    /* ignore */
  }
  return config;
});

api.interceptors.response.use(
  (r) => r,
  async (error) => {
    if (process.env.NODE_ENV !== "production") {
      console.error("[OMNIA API]", error?.response?.status, error?.message);
    }

    const status = error?.response?.status;
    const config = error?.config || {};
    const url = config.url || "";

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
    return Promise.reject(error);
  }
);
