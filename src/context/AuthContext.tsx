import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import { authApi, type LoginCredentials, type User } from "@/api/auth";
import { setCsrfToken } from "@/api/client";

interface AuthContextType {
  user: User | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (credentials: LoginCredentials) => Promise<void>;
  logout: () => Promise<void>;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | null>(null);

interface AuthProviderProps {
  children: ReactNode;
}

export function AuthProvider({ children }: AuthProviderProps) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [sessionExpired, setSessionExpired] = useState(false);

  const refreshUser = useCallback(async () => {
    try {
      const userData = await authApi.getMe();
      setUser(userData);
      setSessionExpired(false);
    } catch {
      setUser(null);
      setCsrfToken(null);
    }
  }, []);

  const login = useCallback(async (credentials: LoginCredentials) => {
    const response = await authApi.login({
      ...credentials,
      username: credentials.username.trim(),
    });
    if (response.csrf_token) {
      setCsrfToken(response.csrf_token);
    }
    const userData = await authApi.getMe(response.access_token);
    setUser(userData);
    setSessionExpired(false);
  }, []);

  const logout = useCallback(async () => {
    try {
      await authApi.logout();
    } finally {
      setUser(null);
      setCsrfToken(null);
    }
  }, []);

  useEffect(() => {
    const checkAuth = async () => {
      setIsLoading(true);
      try {
        const userData = await authApi.getMe(undefined, true);
        setUser(userData);

        try {
          const refreshResponse = await authApi.refresh();
          if (refreshResponse.csrf_token) {
            setCsrfToken(refreshResponse.csrf_token);
          }
        } catch {
          // Keep authenticated session when access cookie is valid but refresh fails.
        }
      } catch {
        setUser(null);
      } finally {
        setIsLoading(false);
      }
    };

    checkAuth();
  }, []);

  useEffect(() => {
    const handleSessionExpired = () => {
      setSessionExpired(true);
      setUser(null);
      setCsrfToken(null);
    };

    window.addEventListener("auth:session-expired", handleSessionExpired);
    return () => {
      window.removeEventListener("auth:session-expired", handleSessionExpired);
    };
  }, []);

  const value = useMemo(
    () => ({
      user,
      isLoading,
      isAuthenticated: !!user,
      login,
      logout,
      refreshUser,
      sessionExpired,
    }),
    [user, isLoading, login, logout, refreshUser, sessionExpired],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextType {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}

export function useUser(): User | null {
  const { user } = useAuth();
  return user;
}

export function useIsAuthenticated(): boolean {
  const { isAuthenticated } = useAuth();
  return isAuthenticated;
}
