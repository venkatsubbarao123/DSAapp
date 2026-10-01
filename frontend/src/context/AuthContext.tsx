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
  setRefreshToken,
  getRefreshToken,
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

  // Attempt silent session refresh on initialization using stored tokens or httpOnly cookie
  useEffect(() => {
    let isMounted = true;

    async function initSession() {
      let authenticated = false;

      // 1. Try currently stored access token
      try {
        const storedAccess = localStorage.getItem("dsaapp_access_token");
        if (storedAccess) {
          setAccessToken(storedAccess);
          if (isMounted) setTokenState(storedAccess);
          const currentUser = await fetchCurrentUser();
          if (currentUser) {
            authenticated = true;
          }
        }
      } catch {}

      // 2. If access token is missing or expired, attempt refresh
      if (!authenticated) {
        try {
          const storedRefresh = getRefreshToken();
          const refreshRes = await fetchApi<AuthResponseData>(
            "/api/v1/auth/refresh",
            {
              method: "POST",
              body: storedRefresh ? JSON.stringify({ refresh_token: storedRefresh }) : undefined,
            }
          );
          if (refreshRes?.data?.access_token) {
            setAccessToken(refreshRes.data.access_token);
            if (refreshRes.data.refresh_token) {
              setRefreshToken(refreshRes.data.refresh_token);
            }
            if (isMounted) {
              setTokenState(refreshRes.data.access_token);
              if (refreshRes.data.user) {
                setUser(refreshRes.data.user);
              } else {
                await fetchCurrentUser();
              }
            }
            authenticated = true;
          }
        } catch {
          setAccessToken(null);
          setRefreshToken(null);
          if (isMounted) {
            setUser(null);
            setTokenState(null);
          }
        }
      }

      if (isMounted) {
        setIsLoading(false);
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
        if (res.data.refresh_token) {
          setRefreshToken(res.data.refresh_token);
        }
        setTokenState(res.data.access_token);
        if (res.data.user) {
          setUser(res.data.user);
        } else {
          await fetchCurrentUser();
        }
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
        if (res.data.refresh_token) {
          setRefreshToken(res.data.refresh_token);
        }
        setTokenState(res.data.access_token);
        if (res.data.user) {
          setUser(res.data.user);
        } else {
          await fetchCurrentUser();
        }
        closeAuthModal();
      }
    },
    [fetchCurrentUser, closeAuthModal]
  );

  const logout = useCallback(async () => {
    try {
      const storedRefresh = getRefreshToken();
      await fetchApi("/api/v1/auth/logout", {
        method: "POST",
        body: storedRefresh ? JSON.stringify({ refresh_token: storedRefresh }) : undefined,
      });
    } catch {
      // Best-effort logout notification
    } finally {
      setAccessToken(null);
      setRefreshToken(null);
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
