import { createContext, useCallback, useContext, useEffect, useState, type ReactNode } from 'react';
import { api, signIn, signOut, type AuthUser } from '../utils/api';
import { useShipment } from './useShipment';

interface AuthContextValue {
  user: AuthUser | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
}
const AuthContext = createContext<AuthContextValue | null>(null);
export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [loading, setLoading] = useState(true);
  const { setShipmentId } = useShipment();
  const clear = useCallback(() => { setUser(null); setShipmentId(null); }, [setShipmentId]);
  useEffect(() => {
    let active = true;
    api.get<{ user: AuthUser }>('/auth/me').then(({ data }) => { if (active) setUser(data.user); })
      .catch(() => { if (active) setUser(null); }).finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, []);
  useEffect(() => {
    window.addEventListener('clearancex:unauthorized', clear);
    return () => window.removeEventListener('clearancex:unauthorized', clear);
  }, [clear]);
  const login = async (email: string, password: string) => { const next = await signIn(email, password); setShipmentId(null); setUser(next); };
  const logout = async () => { await signOut(); clear(); };
  return <AuthContext.Provider value={{ user, loading, login, logout }}>{children}</AuthContext.Provider>;
}
export function useAuth() {
  const value = useContext(AuthContext);
  if (!value) throw new Error('AuthProvider is required');
  return value;
}
