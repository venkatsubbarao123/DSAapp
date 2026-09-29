import React from "react";
import { useAuth } from "../../context/AuthContext.tsx";

interface HeaderProps {
  currentPath: string;
  onNavigate: (path: string) => void;
  serviceHealthy?: boolean;
}

export const Header: React.FC<HeaderProps> = ({
  currentPath,
  onNavigate,
  serviceHealthy,
}) => {
  const { user, isAuthenticated, isPremium, logout, openAuthModal } = useAuth();

  const displayName =
    user?.profile?.display_name || user?.email.split("@")[0] || "User";

  return (
    <header
      style={{
        borderBottom: "1px solid var(--border-subtle)",
        backgroundColor: "var(--bg-secondary)",
        padding: "0 var(--space-6)",
        height: "64px",
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        position: "sticky",
        top: 0,
        zIndex: 50,
      }}
    >
      <div style={{ display: "flex", alignItems: "center", gap: "var(--space-8)" }}>
        <button
          onClick={() => onNavigate("/")}
          style={{
            background: "none",
            border: "none",
            color: "var(--text-primary)",
            fontSize: "1.25rem",
            fontWeight: 700,
            cursor: "pointer",
            display: "flex",
            alignItems: "center",
            gap: "var(--space-2)",
            padding: "var(--space-1) var(--space-2)",
            borderRadius: "var(--radius-sm)",
          }}
          aria-label="DSAapp Home"
        >
          <span
            style={{
              color: "var(--brand-primary)",
              backgroundColor: "var(--bg-tertiary)",
              padding: "2px 8px",
              borderRadius: "var(--radius-sm)",
              border: "1px solid var(--border-muted)",
              fontFamily: "var(--font-mono)",
            }}
          >
            DSA
          </span>
          <span>app</span>
        </button>

        <nav aria-label="Main Navigation">
          <ul
            style={{
              display: "flex",
              listStyle: "none",
              gap: "var(--space-2)",
              margin: 0,
              padding: 0,
            }}
          >
            <li>
              <button
                onClick={() => onNavigate("/")}
                style={{
                  background: currentPath === "/" ? "var(--bg-tertiary)" : "none",
                  border: "none",
                  color: currentPath === "/" ? "var(--text-primary)" : "var(--text-secondary)",
                  fontWeight: currentPath === "/" ? 600 : 400,
                  fontSize: "0.875rem",
                  padding: "var(--space-2) var(--space-4)",
                  borderRadius: "var(--radius-md)",
                  cursor: "pointer",
                  transition: "all 0.15s ease",
                }}
              >
                Overview
              </button>
            </li>
            <li>
              <button
                onClick={() => onNavigate("/curriculum")}
                style={{
                  background: currentPath.startsWith("/curriculum") ? "var(--bg-tertiary)" : "none",
                  border: "none",
                  color: currentPath.startsWith("/curriculum") ? "var(--text-primary)" : "var(--text-secondary)",
                  fontWeight: currentPath.startsWith("/curriculum") ? 600 : 400,
                  fontSize: "0.875rem",
                  padding: "var(--space-2) var(--space-4)",
                  borderRadius: "var(--radius-md)",
                  cursor: "pointer",
                  transition: "all 0.15s ease",
                }}
              >
                Curriculum
              </button>
            </li>
            <li>
              <button
                onClick={() => onNavigate("/topics")}
                style={{
                  background: currentPath.startsWith("/topics") ? "var(--bg-tertiary)" : "none",
                  border: "none",
                  color: currentPath.startsWith("/topics") ? "var(--text-primary)" : "var(--text-secondary)",
                  fontWeight: currentPath.startsWith("/topics") ? 600 : 400,
                  fontSize: "0.875rem",
                  padding: "var(--space-2) var(--space-4)",
                  borderRadius: "var(--radius-md)",
                  cursor: "pointer",
                  transition: "all 0.15s ease",
                }}
              >
                Topics
              </button>
            </li>
            <li>
              <button
                onClick={() => onNavigate("/problems")}
                style={{
                  background: currentPath.startsWith("/problems") ? "var(--bg-tertiary)" : "none",
                  border: "none",
                  color: currentPath.startsWith("/problems") ? "var(--text-primary)" : "var(--text-secondary)",
                  fontWeight: currentPath.startsWith("/problems") ? 600 : 400,
                  fontSize: "0.875rem",
                  padding: "var(--space-2) var(--space-4)",
                  borderRadius: "var(--radius-md)",
                  cursor: "pointer",
                  transition: "all 0.15s ease",
                }}
              >
                Problems
              </button>
            </li>
            {isAuthenticated && (
              <>
                <li>
                  <button
                    onClick={() => onNavigate("/progress")}
                    style={{
                      background: currentPath === "/progress" ? "var(--bg-tertiary)" : "none",
                      border: "none",
                      color: currentPath === "/progress" ? "var(--text-primary)" : "var(--text-secondary)",
                      fontWeight: currentPath === "/progress" ? 600 : 400,
                      fontSize: "0.875rem",
                      padding: "var(--space-2) var(--space-4)",
                      borderRadius: "var(--radius-md)",
                      cursor: "pointer",
                      transition: "all 0.15s ease",
                    }}
                  >
                    Progress
                  </button>
                </li>
                <li>
                  <button
                    onClick={() => onNavigate("/submissions")}
                    style={{
                      background: currentPath.startsWith("/submissions") ? "var(--bg-tertiary)" : "none",
                      border: "none",
                      color: currentPath.startsWith("/submissions") ? "var(--text-primary)" : "var(--text-secondary)",
                      fontWeight: currentPath.startsWith("/submissions") ? 600 : 400,
                      fontSize: "0.875rem",
                      padding: "var(--space-2) var(--space-4)",
                      borderRadius: "var(--radius-md)",
                      cursor: "pointer",
                      transition: "all 0.15s ease",
                    }}
                  >
                    Submissions
                  </button>
                </li>
                <li>
                  <button
                    onClick={() => onNavigate("/mistakes")}
                    style={{
                      background: currentPath === "/mistakes" ? "var(--bg-tertiary)" : "none",
                      border: "none",
                      color: currentPath === "/mistakes" ? "var(--text-primary)" : "var(--text-secondary)",
                      fontWeight: currentPath === "/mistakes" ? 600 : 400,
                      fontSize: "0.875rem",
                      padding: "var(--space-2) var(--space-4)",
                      borderRadius: "var(--radius-md)",
                      cursor: "pointer",
                      transition: "all 0.15s ease",
                    }}
                  >
                    Mistakes
                  </button>
                </li>
                <li>
                  <button
                    onClick={() => onNavigate("/revision")}
                    style={{
                      background: currentPath === "/revision" ? "var(--bg-tertiary)" : "none",
                      border: "none",
                      color: currentPath === "/revision" ? "var(--text-primary)" : "var(--text-secondary)",
                      fontWeight: currentPath === "/revision" ? 600 : 400,
                      fontSize: "0.875rem",
                      padding: "var(--space-2) var(--space-4)",
                      borderRadius: "var(--radius-md)",
                      cursor: "pointer",
                      transition: "all 0.15s ease",
                    }}
                  >
                    Revision
                  </button>
                </li>
                <li>
                  <button
                    onClick={() => onNavigate("/ai")}
                    style={{
                      background: currentPath.startsWith("/ai") ? "var(--bg-tertiary)" : "none",
                      border: "none",
                      color: currentPath.startsWith("/ai") ? "var(--brand-primary)" : "var(--text-secondary)",
                      fontWeight: currentPath.startsWith("/ai") ? 700 : 500,
                      fontSize: "0.875rem",
                      padding: "var(--space-2) var(--space-4)",
                      borderRadius: "var(--radius-md)",
                      cursor: "pointer",
                      transition: "all 0.15s ease",
                    }}
                  >
                    AI Tutor
                  </button>
                </li>
              </>
            )}
            <li>
              <button
                onClick={() => onNavigate("/visualizers")}
                style={{
                  background: currentPath.startsWith("/visualiz") ? "var(--bg-tertiary)" : "none",
                  border: "none",
                  color: currentPath.startsWith("/visualiz") ? "var(--brand-primary)" : "var(--text-secondary)",
                  fontWeight: currentPath.startsWith("/visualiz") ? 700 : 500,
                  fontSize: "0.875rem",
                  padding: "var(--space-2) var(--space-4)",
                  borderRadius: "var(--radius-md)",
                  cursor: "pointer",
                  transition: "all 0.15s ease",
                }}
              >
                Visualizers
              </button>
            </li>

            <li>
              <button
                onClick={() => onNavigate("/premium")}
                style={{
                  background: currentPath === "/premium" ? "var(--bg-tertiary)" : "none",
                  border: "none",
                  color: currentPath === "/premium" ? "var(--text-primary)" : "var(--text-secondary)",
                  fontWeight: currentPath === "/premium" ? 600 : 400,
                  fontSize: "0.875rem",
                  padding: "var(--space-2) var(--space-4)",
                  borderRadius: "var(--radius-md)",
                  cursor: "pointer",
                  display: "flex",
                  alignItems: "center",
                  gap: "var(--space-1)",
                  transition: "all 0.15s ease",
                }}
              >
                <span style={{ color: "var(--status-warning)" }}>★</span>
                <span>Pro & Pricing</span>
              </button>
            </li>
            <li>
              <button
                onClick={() => onNavigate("/status")}
                style={{
                  background: currentPath === "/status" ? "var(--bg-tertiary)" : "none",
                  border: "none",
                  color: currentPath === "/status" ? "var(--text-primary)" : "var(--text-secondary)",
                  fontWeight: currentPath === "/status" ? 600 : 400,
                  fontSize: "0.875rem",
                  padding: "var(--space-2) var(--space-4)",
                  borderRadius: "var(--radius-md)",
                  cursor: "pointer",
                  transition: "all 0.15s ease",
                }}
              >
                System Status
              </button>
            </li>
          </ul>
        </nav>
      </div>

      <div style={{ display: "flex", alignItems: "center", gap: "var(--space-4)" }}>
        {serviceHealthy !== undefined && (
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: "var(--space-2)",
              fontSize: "0.75rem",
              padding: "4px 10px",
              borderRadius: "var(--radius-full)",
              backgroundColor: serviceHealthy ? "var(--status-success-bg)" : "var(--status-danger-bg)",
              color: serviceHealthy ? "var(--status-success)" : "var(--status-danger)",
              border: `1px solid ${serviceHealthy ? "var(--status-success)" : "var(--status-danger)"}`,
            }}
          >
            <span
              style={{
                width: "6px",
                height: "6px",
                borderRadius: "var(--radius-full)",
                backgroundColor: "currentColor",
              }}
            />
            {serviceHealthy ? "API Online" : "API Offline"}
          </div>
        )}

        {/* Auth State Actions */}
        {isAuthenticated ? (
          <div style={{ display: "flex", alignItems: "center", gap: "var(--space-3)" }}>
            {/* User display badge */}
            <div
              style={{
                display: "flex",
                alignItems: "center",
                gap: "var(--space-2)",
                padding: "4px 8px",
                borderRadius: "var(--radius-md)",
                backgroundColor: "var(--bg-tertiary)",
                border: "1px solid var(--border-subtle)",
                fontSize: "0.8125rem",
              }}
            >
              <span style={{ fontWeight: 600, color: "var(--text-primary)" }}>{displayName}</span>
              <span
                style={{
                  fontSize: "0.6875rem",
                  fontFamily: "var(--font-mono)",
                  padding: "1px 6px",
                  borderRadius: "var(--radius-sm)",
                  backgroundColor: "var(--bg-secondary)",
                  color: "var(--text-muted)",
                  border: "1px solid var(--border-subtle)",
                }}
              >
                {user?.role}
              </span>
              {isPremium ? (
                <span
                  style={{
                    fontSize: "0.6875rem",
                    fontWeight: 700,
                    padding: "1px 6px",
                    borderRadius: "var(--radius-sm)",
                    backgroundColor: "rgba(234, 179, 8, 0.2)",
                    color: "var(--status-warning)",
                    border: "1px solid var(--status-warning)",
                  }}
                >
                  PRO
                </span>
              ) : (
                <button
                  onClick={() => onNavigate("/premium")}
                  style={{
                    fontSize: "0.6875rem",
                    fontWeight: 700,
                    padding: "2px 6px",
                    borderRadius: "var(--radius-sm)",
                    backgroundColor: "var(--brand-primary)",
                    color: "#ffffff",
                    border: "none",
                    cursor: "pointer",
                  }}
                >
                  Upgrade
                </button>
              )}
            </div>

            <button
              onClick={() => logout()}
              style={{
                background: "none",
                border: "1px solid var(--border-subtle)",
                color: "var(--text-secondary)",
                fontSize: "0.8125rem",
                padding: "4px 10px",
                borderRadius: "var(--radius-md)",
                cursor: "pointer",
              }}
            >
              Sign Out
            </button>
          </div>
        ) : (
          <div style={{ display: "flex", alignItems: "center", gap: "var(--space-2)" }}>
            <button
              onClick={() => openAuthModal("login")}
              style={{
                background: "none",
                border: "1px solid var(--border-subtle)",
                color: "var(--text-primary)",
                fontSize: "0.8125rem",
                padding: "6px 14px",
                borderRadius: "var(--radius-md)",
                cursor: "pointer",
                fontWeight: 500,
              }}
            >
              Sign In
            </button>
            <button
              onClick={() => openAuthModal("register")}
              style={{
                backgroundColor: "var(--brand-primary)",
                border: "none",
                color: "#ffffff",
                fontSize: "0.8125rem",
                padding: "6px 14px",
                borderRadius: "var(--radius-md)",
                cursor: "pointer",
                fontWeight: 600,
              }}
            >
              Create Account
            </button>
          </div>
        )}

        <span
          style={{
            fontSize: "0.75rem",
            color: "var(--text-muted)",
            fontFamily: "var(--font-mono)",
            border: "1px solid var(--border-subtle)",
            padding: "2px 8px",
            borderRadius: "var(--radius-sm)",
          }}
        >
          v0.4.0-phase4
        </span>
      </div>
    </header>
  );
};
