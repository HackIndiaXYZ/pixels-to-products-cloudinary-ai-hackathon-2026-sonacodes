import { useEffect, useState, type ReactNode } from 'react';
import {
  fetchCurrentUser,
  fetchCsrf,
  loginAccount,
  logoutAccount,
  registerAccount,
  setCsrfToken,
  type UserProfile,
} from '../api/client';
import { AuthContext } from './context';

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<UserProfile | null>(null);
  const [loading, setLoading] = useState(true);
  const [csrfReady, setCsrfReady] = useState(false);

  useEffect(() => {
    let active = true;
    async function initialize() {
      try {
        const csrf = await fetchCsrf();
        setCsrfToken(csrf.csrf_token);
        if (!active) return;
        setCsrfReady(true);
        try {
          const profile = await fetchCurrentUser();
          if (active) setUser(profile);
        } catch {
          if (active) setUser(null);
        }
      } catch {
        if (active) setUser(null);
      } finally {
        if (active) setLoading(false);
      }
    }
    void initialize();
    return () => { active = false; };
  }, []);

  useEffect(() => {
    function onUnauthorized() {
      setUser(null);
      if (window.location.pathname === '/app') window.location.replace('/login');
    }
    window.addEventListener('wardrobeai:unauthorized', onUnauthorized);
    return () => window.removeEventListener('wardrobeai:unauthorized', onUnauthorized);
  }, []);

  async function login(email: string, password: string) {
    setUser(await loginAccount({ email, password }));
  }

  async function register(name: string, email: string, password: string, confirmPassword: string) {
    setUser(await registerAccount({ name, email, password, confirm_password: confirmPassword }));
  }

  async function logout() {
    await logoutAccount();
    setUser(null);
  }

  return (
    <AuthContext.Provider value={{ user, loading, csrfReady, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

