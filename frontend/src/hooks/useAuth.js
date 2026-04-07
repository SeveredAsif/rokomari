import { useState } from "react";

export function useAuth() {
  const [token, setToken] = useState(localStorage.getItem("token"));
  const [user, setUser] = useState(() => {
    const raw = localStorage.getItem("user");
    return raw ? JSON.parse(raw) : null;
  });

  const login = (access_token, me) => {
    localStorage.setItem("token", access_token);
    localStorage.setItem("user", JSON.stringify(me));
    setToken(access_token);
    setUser(me);
  };

  const logout = () => {
    localStorage.clear();
    setToken(null);
    setUser(null);
  };

  return { token, user, login, logout };
}