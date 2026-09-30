import React, {
  createContext,
  useContext,
  useEffect,
  useState,
  useCallback,
  ReactNode,
} from "react";
import {
  User,
  LoginRequest,
  RegisterRequest,
  AuthResponseData,
} from "../types/auth.ts";
import {
  fetchApi,
  setAccessToken,
} from "../services/apiClient.ts";

interface AuthContextType {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  isPremium: boolean;
  isLoading: boolean;
  authModalOpen: boolean;
  authModalMode: "login" | "register";
  openAuthModal: (mode?: "login" | "register") => void;
  closeAuthModal: () => void;
  login: (data: LoginRequest) => Promise<void>;
  register: (data: RegisterRequest) => Promise<void>;
  logout: () => Promise<void>;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [token, setTokenState] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [authModalOpen, setAuthModalOpen] = useState<boolean>(false);
  const [authModalMode, setAuthModalMode] = useState<"login" | "register">("login");

  const openAuthModal = useCallback((mode: "login" | "register" = "login") => {
    setAuthModalMode(mode);
    setAuthModalOpen(true);
  }, []);

  const closeAuthModal = useCallback(() => {
    setAuthModalOpen(false);
  }, []);

  const fetchCurrentUser = useCallback(async (): Promise<User | null> => {
    try {
      const res = await fetchApi<User>("/api/v1/auth/me");
      setUser(res.data);
      return res.data;
    } catch {
      setUser(null);
      return null;
    }
  }, []);

  const refreshUser = useCallback(async () => {
    await fetchCurrentUser();
  }, [fetchCurrentUser]);

  // Attempt silent session refresh on initialization using httpOnly cookie
  useEffect(() => {
    let isMounted = true;

    async function initSession() {
      try {
        const stored = localStorage.getItem("dsaapp_access_token");
        if (stored) {
          setAccessToken(stored);
          if (isMounted) {
            setTokenState(stored);
            await fetchCurrentUser();
          }
        }
      } catch {}

      try {
        const refreshRes = await fetchApi<AuthResponseData>(
          "/api/v1/auth/refresh",
          { method: "POST" }
        );
        if (refreshRes?.data?.access_token) {
          setAccessToken(refreshRes.data.access_token);
          if (isMounted) {
            setTokenState(refreshRes.data.access_token);
            await fetchCurrentUser();
          }
        }
      } catch {
        const stored = localStorage.getItem("dsaapp_access_token");
        if (!stored) {
          setAccessToken(null);
          if (isMounted) {
            setUser(null);
            setTokenState(null);
          }
        }
      } finally {
        if (isMounted) {
          setIsLoading(false);
        }
      }
    }

    initSession();

    return () => {
      isMounted = false;
    };
  }, [fetchCurrentUser]);

  const login = useCallback(
    async (credentials: LoginRequest) => {
      const res = await fetchApi<AuthResponseData>("/api/v1/auth/login", {
        method: "POST",
        body: JSON.stringify(credentials),
      });

      if (res.data?.access_token) {
        setAccessToken(res.data.access_token);
        setTokenState(res.data.access_token);
        await fetchCurrentUser();
        closeAuthModal();
      }
    },
    [fetchCurrentUser, closeAuthModal]
  );

  const register = useCallback(
    async (payload: RegisterRequest) => {
      const res = await fetchApi<AuthResponseData>("/api/v1/auth/register", {
        method: "POST",
        body: JSON.stringify(payload),
      });

      if (res.data?.access_token) {
        setAccessToken(res.data.access_token);
        setTokenState(res.data.access_token);
        await fetchCurrentUser();
        closeAuthModal();
      }
    },
    [fetchCurrentUser, closeAuthModal]
  );

  const logout = useCallback(async () => {
    try {
      await fetchApi("/api/v1/auth/logout", { method: "POST" });
    } catch {
      // Best-effort logout notification
    } finally {
      setAccessToken(null);
      setTokenState(null);
      setUser(null);
    }
  }, []);

  const value: AuthContextType = {
    user,
    token,
    isAuthenticated: Boolean(user),
    isPremium: Boolean(user?.premium_active),
    isLoading,
    authModalOpen,
    authModalMode,
    openAuthModal,
    closeAuthModal,
    login,
    register,
    logout,
    refreshUser,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
};
