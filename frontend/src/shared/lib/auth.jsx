import React, { createContext, useContext, useEffect, useState, useCallback } from "react";
import { api, refreshSession } from "./api";

/**
 * AuthContext — 3 states:
 *   - user === null       → checking session
 *   - user === false      → not authenticated
 *   - user === {...}      → authenticated
 */
const AuthContext = createContext(null);

export function formatApiErrorDetail(detail) {
  if (detail == null) return "Something went wrong. Please try again.";
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail))
    return detail
      .map((e) => (e && typeof e.msg === "string" ? e.msg : JSON.stringify(e)))
      .filter(Boolean)
      .join(" ");
  if (detail && typeof detail.msg === "string") return detail.msg;
  return String(detail);
}

async function loadSessionUser() {
  try {
    const { data } = await api.get("/auth/me");
    return data;
  } catch {
    // Access cookie TTL is 15m; refresh cookie lasts 7d — restore silently
    await refreshSession();
    const { data } = await api.get("/auth/me");
    return data;
  }
}

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);

  const refresh = useCallback(async () => {
    try {
      const data = await loadSessionUser();
      setUser(data);
      return data;
    } catch {
      setUser(false);
      return null;
    }
  }, []);

  useEffect(() => {
    let mounted = true;
    loadSessionUser()
      .then((data) => {
        if (mounted) setUser(data);
      })
      .catch(() => {
        if (mounted) setUser(false);
      });
    // M9 — 401 after failed refresh → drop the local session (ProtectedRoute → login)
    const onUnauthorized = () => setUser((u) => (u ? false : u));
    window.addEventListener("omnia:unauthorized", onUnauthorized);
    return () => {
      mounted = false;
      window.removeEventListener("omnia:unauthorized", onUnauthorized);
    };
  }, []);

  const login = async (email, password) => {
    const { data } = await api.post("/auth/login", { email, password });
    if (data?.mfa_required) {
      return data;
    }
    setUser(data);
    return data;
  };

  const verifyMfa = async (mfaToken, code) => {
    const { data } = await api.post("/auth/mfa/verify", { mfa_token: mfaToken, code });
    setUser(data);
    return data;
  };

  const loginWithGoogle = async (credential) => {
    const { data } = await api.post("/auth/google", { credential });
    if (data?.mfa_required) {
      return data;
    }
    setUser(data);
    return data;
  };

  const register = async (payload) => {
    const { data } = await api.post("/auth/register", payload);
    setUser(data);
    return data;
  };

  const logout = async () => {
    try {
      await api.post("/auth/logout");
    } catch {
      // ignore
    }
    setUser(false);
  };

  const value = { user, login, loginWithGoogle, verifyMfa, register, logout, refresh };
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used inside AuthProvider");
  return ctx;
}
