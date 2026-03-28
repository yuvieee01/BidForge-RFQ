/**
 * auth.js — Auth context + provider
 */
import { createContext, useContext, useState, useEffect } from 'react';
import { authService } from '../services';
import { setServerTimeOffset } from '../hooks/useServerTime';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem('access_token');
    if (token) {
      authService.me()
        .then((res) => {
          setUser(res.data.data.user);
          if (res.data.data.server_time) {
            setServerTimeOffset(res.data.data.server_time);
          }
        })
        .catch(() => {
          localStorage.removeItem('access_token');
          localStorage.removeItem('refresh_token');
        })
        .finally(() => setLoading(false));
    } else {
      setLoading(false);
    }
  }, []);

  const login = async (email, password) => {
    const res = await authService.login({ email, password });
    const { access, refresh, user: u, server_time } = res.data.data;
    localStorage.setItem('access_token', access);
    localStorage.setItem('refresh_token', refresh);
    if (server_time) setServerTimeOffset(server_time);
    setUser(u);
    return u;
  };

  const logout = () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, loading, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => useContext(AuthContext);
