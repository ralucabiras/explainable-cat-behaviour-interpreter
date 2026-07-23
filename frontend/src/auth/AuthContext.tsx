import { createContext, useContext, useEffect, useState, type ReactNode } from "react";
import { api } from "../api";
import type { User } from "../types";

interface AuthValue {
  user: User | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(() =>
    Boolean(localStorage.getItem("whiskerwise_token")),
  );

  useEffect(() => {
    if (!localStorage.getItem("whiskerwise_token")) {
      return;
    }
    void api.me()
      .then(setUser)
      .catch(() => localStorage.removeItem("whiskerwise_token"))
      .finally(() => setLoading(false));
  }, []);

  async function login(email: string, password: string) {
    const response = await api.login(email, password);
    localStorage.setItem("whiskerwise_token", response.access_token);
    setUser(response.user);
  }

  function logout() {
    localStorage.removeItem("whiskerwise_token");
    setUser(null);
  }

  return <AuthContext.Provider value={{ user, loading, login, logout }}>{children}</AuthContext.Provider>;
}

// Auth state and its hook intentionally share this small module.
// eslint-disable-next-line react-refresh/only-export-components
export function useAuth() {
  const value = useContext(AuthContext);
  if (!value) throw new Error("useAuth must be used within AuthProvider");
  return value;
}
