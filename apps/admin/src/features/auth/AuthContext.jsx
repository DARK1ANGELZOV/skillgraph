import { createContext, useContext, useEffect, useMemo, useState } from "react";

import { api } from "../../lib/api";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [session, setSession] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api("/auth/me")
      .then(setSession)
      .catch(() => setSession(null))
      .finally(() => setLoading(false));
  }, []);

  const value = useMemo(
    () => ({
      session,
      loading,
      async login(payload) {
        const data = await api("/auth/login", {
          method: "POST",
          body: JSON.stringify(payload)
        });
        setSession(data);
        return data;
      },
      async registerOwner(payload) {
        const data = await api("/auth/register-owner", {
          method: "POST",
          body: JSON.stringify(payload)
        });
        setSession(data);
        return data;
      },
      async logout() {
        await api("/auth/logout", { method: "POST" });
        setSession(null);
      }
    }),
    [session, loading]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error("useAuth must be used inside AuthProvider");
  }
  return ctx;
}
