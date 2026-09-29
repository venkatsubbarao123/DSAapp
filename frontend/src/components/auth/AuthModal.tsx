import React, { useState, useEffect } from "react";
import { useAuth } from "../../context/AuthContext.tsx";
import { APIClientError } from "../../services/apiClient.ts";
import { LoadingSpinner } from "../common/LoadingSpinner.tsx";

export const AuthModal: React.FC = () => {
  const { authModalOpen, authModalMode, closeAuthModal, openAuthModal, login, register } =
    useAuth();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [displayName, setDisplayName] = useState("");
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const isRegister = authModalMode === "register";

  // Reset state when modal opens or mode changes
  useEffect(() => {
    if (authModalOpen) {
      setErrorMsg(null);
      setPassword("");
    }
  }, [authModalOpen, authModalMode]);

  // Handle escape key to close modal
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape" && authModalOpen) {
        closeAuthModal();
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [authModalOpen, closeAuthModal]);

  if (!authModalOpen) return null;

  // Real-time password complexity validation for register
  const hasMinLen = password.length >= 8;
  const hasLetter = /[a-zA-Z]/.test(password);
  const hasDigit = /[0-9]/.test(password);
  const isPasswordValid = hasMinLen && hasLetter && hasDigit;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg(null);

    if (isRegister && !isPasswordValid) {
      setErrorMsg(
        "Password must be at least 8 characters and contain both letters and numbers."
      );
      return;
    }

    setIsSubmitting(true);
    try {
      if (isRegister) {
        await register({
          email: email.trim(),
          password,
          display_name: displayName.trim() || undefined,
        });
      } else {
        await login({
          email: email.trim(),
          password,
        });
      }
    } catch (err) {
      if (err instanceof APIClientError) {
        if (err.code === "HTTP_429") {
          setErrorMsg("Too many attempts. Please slow down and try again later.");
        } else {
          setErrorMsg(err.message);
        }
      } else {
        setErrorMsg("An unexpected error occurred. Please try again.");
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="auth-modal-title"
      style={{
        position: "fixed",
        top: 0,
        left: 0,
        width: "100%",
        height: "100%",
        backgroundColor: "rgba(0, 0, 0, 0.75)",
        backdropFilter: "blur(4px)",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        zIndex: 1000,
        padding: "var(--space-4)",
      }}
      onClick={(e) => {
        if (e.target === e.currentTarget) closeAuthModal();
      }}
    >
      <div
        style={{
          backgroundColor: "var(--bg-secondary)",
          border: "1px solid var(--border-muted)",
          borderRadius: "var(--radius-lg)",
          width: "100%",
          maxWidth: "440px",
          padding: "var(--space-6)",
          boxShadow: "0 20px 25px -5px rgba(0, 0, 0, 0.5), 0 8px 10px -6px rgba(0, 0, 0, 0.5)",
          position: "relative",
        }}
      >
        {/* Close Button */}
        <button
          onClick={closeAuthModal}
          style={{
            position: "absolute",
            top: "var(--space-4)",
            right: "var(--space-4)",
            background: "none",
            border: "none",
            color: "var(--text-muted)",
            fontSize: "1.25rem",
            cursor: "pointer",
            padding: "var(--space-1) var(--space-2)",
            borderRadius: "var(--radius-sm)",
          }}
          aria-label="Close dialog"
        >
          ✕
        </button>

        {/* Modal Header */}
        <div style={{ marginBottom: "var(--space-6)" }}>
          <h2
            id="auth-modal-title"
            style={{
              fontSize: "1.5rem",
              fontWeight: 700,
              color: "var(--text-primary)",
              marginBottom: "var(--space-2)",
            }}
          >
            {isRegister ? "Create Your DSAapp Account" : "Sign In to DSAapp"}
          </h2>
          <p style={{ color: "var(--text-secondary)", fontSize: "0.875rem" }}>
            {isRegister
              ? "Join the production-grade engineering and DSA learning platform."
              : "Welcome back! Enter your credentials to access your session."}
          </p>
        </div>

        {/* Error Alert */}
        {errorMsg && (
          <div
            role="alert"
            style={{
              backgroundColor: "var(--status-danger-bg)",
              border: "1px solid var(--status-danger)",
              color: "var(--status-danger)",
              padding: "var(--space-3) var(--space-4)",
              borderRadius: "var(--radius-md)",
              marginBottom: "var(--space-4)",
              fontSize: "0.875rem",
            }}
          >
            {errorMsg}
          </div>
        )}

        {/* Auth Form */}
        <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: "var(--space-4)" }}>
          {isRegister && (
            <div>
              <label
                htmlFor="auth-display-name"
                style={{
                  display: "block",
                  fontSize: "0.875rem",
                  fontWeight: 500,
                  color: "var(--text-secondary)",
                  marginBottom: "var(--space-1)",
                }}
              >
                Display Name (Optional)
              </label>
              <input
                id="auth-display-name"
                type="text"
                value={displayName}
                onChange={(e) => setDisplayName(e.target.value)}
                placeholder="e.g. Ada Lovelace"
                style={{
                  width: "100%",
                  padding: "var(--space-2) var(--space-3)",
                  backgroundColor: "var(--bg-tertiary)",
                  border: "1px solid var(--border-subtle)",
                  borderRadius: "var(--radius-md)",
                  color: "var(--text-primary)",
                  fontSize: "0.875rem",
                  outline: "none",
                  boxSizing: "border-box",
                }}
              />
            </div>
          )}

          <div>
            <label
              htmlFor="auth-email"
              style={{
                display: "block",
                fontSize: "0.875rem",
                fontWeight: 500,
                color: "var(--text-secondary)",
                marginBottom: "var(--space-1)",
              }}
            >
              Email Address <span style={{ color: "var(--status-danger)" }}>*</span>
            </label>
            <input
              id="auth-email"
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="engineer@example.com"
              style={{
                width: "100%",
                padding: "var(--space-2) var(--space-3)",
                backgroundColor: "var(--bg-tertiary)",
                border: "1px solid var(--border-subtle)",
                borderRadius: "var(--radius-md)",
                color: "var(--text-primary)",
                fontSize: "0.875rem",
                outline: "none",
                boxSizing: "border-box",
              }}
            />
          </div>

          <div>
            <label
              htmlFor="auth-password"
              style={{
                display: "block",
                fontSize: "0.875rem",
                fontWeight: 500,
                color: "var(--text-secondary)",
                marginBottom: "var(--space-1)",
              }}
            >
              Password <span style={{ color: "var(--status-danger)" }}>*</span>
            </label>
            <input
              id="auth-password"
              type="password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••••••"
              style={{
                width: "100%",
                padding: "var(--space-2) var(--space-3)",
                backgroundColor: "var(--bg-tertiary)",
                border: "1px solid var(--border-subtle)",
                borderRadius: "var(--radius-md)",
                color: "var(--text-primary)",
                fontSize: "0.875rem",
                outline: "none",
                boxSizing: "border-box",
              }}
            />

            {/* Password strength checklist in registration mode */}
            {isRegister && password.length > 0 && (
              <div
                style={{
                  marginTop: "var(--space-2)",
                  fontSize: "0.75rem",
                  display: "flex",
                  flexDirection: "column",
                  gap: "2px",
                }}
              >
                <span style={{ color: hasMinLen ? "var(--status-success)" : "var(--text-muted)" }}>
                  {hasMinLen ? "✓" : "○"} At least 8 characters
                </span>
                <span style={{ color: hasLetter ? "var(--status-success)" : "var(--text-muted)" }}>
                  {hasLetter ? "✓" : "○"} Contains at least one letter
                </span>
                <span style={{ color: hasDigit ? "var(--status-success)" : "var(--text-muted)" }}>
                  {hasDigit ? "✓" : "○"} Contains at least one number
                </span>
              </div>
            )}
          </div>

          <button
            type="submit"
            disabled={isSubmitting}
            style={{
              marginTop: "var(--space-2)",
              backgroundColor: "var(--brand-primary)",
              color: "#ffffff",
              border: "none",
              borderRadius: "var(--radius-md)",
              padding: "var(--space-3)",
              fontWeight: 600,
              fontSize: "0.875rem",
              cursor: isSubmitting ? "not-allowed" : "pointer",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              gap: "var(--space-2)",
              transition: "opacity 0.15s ease",
              opacity: isSubmitting ? 0.7 : 1,
            }}
          >
            {isSubmitting ? (
              <>
                <LoadingSpinner size="sm" />
                <span>{isRegister ? "Creating Account..." : "Signing In..."}</span>
              </>
            ) : (
              <span>{isRegister ? "Create Account" : "Sign In"}</span>
            )}
          </button>
        </form>

        {/* Mode Switcher */}
        <div
          style={{
            marginTop: "var(--space-6)",
            textAlign: "center",
            fontSize: "0.875rem",
            color: "var(--text-secondary)",
            borderTop: "1px solid var(--border-subtle)",
            paddingTop: "var(--space-4)",
          }}
        >
          {isRegister ? (
            <>
              Already have an account?{" "}
              <button
                type="button"
                onClick={() => openAuthModal("login")}
                style={{
                  background: "none",
                  border: "none",
                  color: "var(--brand-primary)",
                  fontWeight: 600,
                  cursor: "pointer",
                  padding: 0,
                }}
              >
                Sign In
              </button>
            </>
          ) : (
            <>
              Don't have an account?{" "}
              <button
                type="button"
                onClick={() => openAuthModal("register")}
                style={{
                  background: "none",
                  border: "none",
                  color: "var(--brand-primary)",
                  fontWeight: 600,
                  cursor: "pointer",
                  padding: 0,
                }}
              >
                Create Account
              </button>
            </>
          )}
        </div>
      </div>
    </div>
  );
};
