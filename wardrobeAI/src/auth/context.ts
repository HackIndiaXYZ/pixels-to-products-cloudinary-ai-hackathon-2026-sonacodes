import { createContext } from 'react';
import type { UserProfile } from '../api/client';

export interface AuthContextValue {
  user: UserProfile | null;
  loading: boolean;
  csrfReady: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (name: string, email: string, password: string, confirmPassword: string) => Promise<void>;
  logout: () => Promise<void>;
}

export const AuthContext = createContext<AuthContextValue | null>(null);
