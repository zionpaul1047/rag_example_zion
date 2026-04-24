import { createContext, useContext, useEffect, useMemo, useState } from "react";

const API_BASE = "http://127.0.0.1:8000";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [token, setToken] = useState(() => localStorage.getItem("access_token") || "");
  const [user, setUser] = useState(() => {
    const saved = localStorage.getItem("user");
    return saved ? JSON.parse(saved) : null;
  });
  const [loading, setLoading] = useState(false);

  const isAuthenticated = Boolean(token && user);
  const role = user?.role || "guest";

  useEffect(() => {
    if (!token) return;

    let ignore = false;

    async function fetchMe() {
      try {
        const res = await fetch(`${API_BASE}/auth/me`, {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        });

        if (!res.ok) {
          throw new Error("토큰 검증 실패");
        }

        const data = await res.json();

        if (!ignore) {
          setUser(data);
          localStorage.setItem("user", JSON.stringify(data));
        }
      } catch {
        if (!ignore) {
          logout();
        }
      }
    }

    fetchMe();

    return () => {
      ignore = true;
    };
  }, [token]);

  const login = async (username, password) => {
    setLoading(true);

    try {
      const res = await fetch(`${API_BASE}/auth/login`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ username, password }),
      });

      const data = await res.json();

      if (!res.ok) {
        throw new Error(data.detail || "로그인 실패");
      }

      localStorage.setItem("access_token", data.access_token);
      localStorage.setItem("user", JSON.stringify(data.user));

      setToken(data.access_token);
      setUser(data.user);

      return data.user;
    } finally {
      setLoading(false);
    }
  };

  const logout = () => {
    localStorage.removeItem("access_token");
    localStorage.removeItem("user");
    setToken("");
    setUser(null);
  };

  const value = useMemo(
    () => ({
      token,
      user,
      role,
      loading,
      isAuthenticated,
      login,
      logout,
    }),
    [token, user, role, loading, isAuthenticated]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);

  if (!context) {
    throw new Error("useAuth는 AuthProvider 내부에서만 사용할 수 있습니다.");
  }

  return context;
}