import React, { createContext, useContext, useEffect, useState } from 'react';
import { api } from '../services/api';
import { DemoUser, User } from '../types';

interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  activeTenantId: number | null;
  llmProvider: string;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
  quickLogin: (demo: DemoUser) => Promise<void>;
  setActiveTenantId: (tenantId: number | null) => void;
  setLlmProvider: (provider: string) => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [activeTenantId, setActiveTenantId] = useState<number | null>(null);
  const [llmProvider, setLlmProvider] = useState<string>('ollama');

  useEffect(() => {
    const initAuth = async () => {
      const token = api.getAccessToken();
      if (token) {
        try {
          const userData = await api.getMe();
          setUser(userData);
          setActiveTenantId(userData.tenant_id);
        } catch (e) {
          console.warn('Initial session restore failed:', e);
          api.clearTokens();
        }
      }
      setIsLoading(false);
    };
    initAuth();
  }, []);

  const login = async (email: string, password: string) => {
    setIsLoading(true);
    try {
      const res = await api.login(email, password);
      setUser(res.user);
      setActiveTenantId(res.user.tenant_id);
    } finally {
      setIsLoading(false);
    }
  };

  const quickLogin = async (demo: DemoUser) => {
    await login(demo.email, 'password123');
  };

  const logout = () => {
    api.clearTokens();
    setUser(null);
    setActiveTenantId(null);
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        isAuthenticated: !!user,
        isLoading,
        activeTenantId,
        llmProvider,
        login,
        logout,
        quickLogin,
        setActiveTenantId,
        setLlmProvider,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

