import React, { createContext, useContext, useEffect, useState, useCallback } from "react";
import { api } from "./api";

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

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);

  const refresh = useCallback(async () => {
    try {
      const { data } = await api.get("/auth/me");
      setUser(data);
      return data;
    } catch {
      setUser(false);
      return null;
    }
  }, []);

  useEffect(() => {
    let mounted = true;
    api
      .get("/auth/me")
      .then((r) => {
        if (mounted) setUser(r.data);
      })
      .catch(() => {
        if (mounted) setUser(false);
      });
    // M9 — 401 on any protected call → drop the local session (ProtectedRoute redirects to login)
    const onUnauthorized = () => setUser((u) => (u ? false : u));
    window.addEventListener("omnia:unauthorized", onUnauthorized);
    return () => {
      mounted = false;
      window.removeEventListener("omnia:unauthorized", onUnauthorized);
    };
  }, []);

  const login = async (email, password) => {
    const { data } = await api.post("/auth/login", { email, password });
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

  const value = { user, login, register, logout, refresh };
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used inside AuthProvider");
  return ctx;
}
