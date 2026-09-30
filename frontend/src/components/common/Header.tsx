import React, { useEffect, useRef, useState } from "react";
import { useAuth } from "../../context/AuthContext.tsx";
import { gamificationApi } from "../../services/gamificationApi.ts";
import { UserGamificationProfile } from "../../types/gamification.ts";
import { NotificationBell } from "./NotificationBell.tsx";
import { ThemeToggle } from "./ThemeToggle.tsx";

interface HeaderProps {
  currentPath: string;
  onNavigate: (path: string) => void;
  serviceHealthy?: boolean;
}

// ─── Dropdown Item ────────────────────────────────────────────────────────────
interface NavItem {
  label: string;
  path: string;
  authRequired?: boolean;
}

interface NavGroup {
  label: string;
  items: NavItem[];
  authRequired?: boolean;
}

const NAV_GROUPS: NavGroup[] = [
  {
    label: "Learn",
    items: [
      { label: "Learning Path", path: "/curriculum" },
      { label: "Curriculum", path: "/curriculum" },
      { label: "Topics", path: "/topics" },
    ],
  },
  {
    label: "Practice",
    items: [
      { label: "Problems", path: "/problems" },
      { label: "Daily Challenge", path: "/daily" },
      { label: "Practice", path: "/practice" },
    ],
  },
  {
    label: "Compete",
    items: [
      { label: "Contests", path: "/contests" },
      { label: "Leaderboard", path: "/leaderboard" },
    ],
  },
  {
    label: "Interview",
    items: [
      { label: "Interview Prep", path: "/interview" },
      { label: "Mock Interview", path: "/interview" },
    ],
  },
  {
    label: "Tools",
    items: [
      { label: "Visualizers", path: "/visualizers" },
      { label: "SQL Practice", path: "/sql" },
      { label: "OOP", path: "/oop" },
    ],
  },
  {
    label: "Progress",
    authRequired: true,
    items: [
      { label: "Dashboard", path: "/progress" },
      { label: "Achievements", path: "/achievements" },
      { label: "Mistakes", path: "/mistakes" },
      { label: "Revision", path: "/revision" },
    ],
  },
];

// ─── NavDropdown ──────────────────────────────────────────────────────────────
interface NavDropdownProps {
  group: NavGroup;
  currentPath: string;
  onNavigate: (path: string) => void;
}

const NavDropdown: React.FC<NavDropdownProps> = ({ group, currentPath, onNavigate }) => {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLLIElement>(null);
  const isActive = group.items.some((item) => currentPath.startsWith(item.path));

  useEffect(() => {
    if (!open) return;
    const handleKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") setOpen(false);
    };
    const handleClick = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) {
        setOpen(false);
      }
    };
    document.addEventListener("keydown", handleKey);
    document.addEventListener("mousedown", handleClick);
    return () => {
      document.removeEventListener("keydown", handleKey);
      document.removeEventListener("mousedown", handleClick);
    };
  }, [open]);

  return (
    <li ref={ref} style={{ position: "relative" }}>
      <button
        onClick={() => setOpen((o) => !o)}
        aria-expanded={open}
        aria-haspopup="menu"
        style={{
          background: isActive ? "var(--bg-tertiary)" : "none",
          border: "none",
          color: isActive ? "var(--text-primary)" : "var(--text-secondary)",
          fontWeight: isActive ? 600 : 400,
          fontSize: "0.875rem",
          padding: "var(--space-2) var(--space-3)",
          borderRadius: "var(--radius-md)",
          cursor: "pointer",
          display: "flex",
          alignItems: "center",
          gap: "4px",
          transition: "all 0.15s ease",
          whiteSpace: "nowrap",
        }}
      >
        {group.label}
        <span
          style={{
            fontSize: "0.625rem",
            transition: "transform 0.15s ease",
            transform: open ? "rotate(180deg)" : "rotate(0deg)",
            display: "inline-block",
          }}
        >
          ▾
        </span>
      </button>

      {open && (
        <div
          role="menu"
          style={{
            position: "absolute",
            top: "calc(100% + 6px)",
            left: 0,
            backgroundColor: "var(--bg-secondary)",
            border: "1px solid var(--border-subtle)",
            borderRadius: "var(--radius-md)",
            boxShadow: "var(--shadow-lg)",
            zIndex: 200,
            minWidth: "160px",
            overflow: "hidden",
          }}
        >
          {group.items.map((item) => {
            const itemActive = currentPath.startsWith(item.path);
            return (
              <button
                key={item.path + item.label}
                role="menuitem"
                onClick={() => {
                  onNavigate(item.path);
                  setOpen(false);
                }}
                style={{
                  display: "block",
                  width: "100%",
                  padding: "var(--space-2) var(--space-4)",
                  background: itemActive ? "var(--bg-tertiary)" : "none",
                  border: "none",
                  color: itemActive ? "var(--text-primary)" : "var(--text-secondary)",
                  fontWeight: itemActive ? 600 : 400,
                  fontSize: "0.875rem",
                  cursor: "pointer",
                  textAlign: "left",
                  transition: "background 0.1s ease",
                }}
                onMouseEnter={(e) => {
                  if (!itemActive) (e.currentTarget as HTMLButtonElement).style.background = "var(--bg-tertiary)";
                }}
                onMouseLeave={(e) => {
                  if (!itemActive) (e.currentTarget as HTMLButtonElement).style.background = "none";
                }}
              >
                {item.label}
              </button>
            );
          })}
        </div>
      )}
    </li>
  );
};

// ─── Mobile Menu ──────────────────────────────────────────────────────────────
interface MobileMenuProps {
  currentPath: string;
  onNavigate: (path: string) => void;
  isAuthenticated: boolean;
  onClose: () => void;
}

const MobileMenu: React.FC<MobileMenuProps> = ({ currentPath, onNavigate, isAuthenticated, onClose }) => {
  const [expandedGroup, setExpandedGroup] = useState<string | null>(null);

  const visibleGroups = NAV_GROUPS.filter(
    (g) => !g.authRequired || isAuthenticated
  );

  const nav = (path: string) => {
    onNavigate(path);
    onClose();
  };

  return (
    <div
      style={{
        position: "fixed",
        top: "64px",
        left: 0,
        right: 0,
        bottom: 0,
        backgroundColor: "var(--bg-overlay)",
        backdropFilter: "blur(4px)",
        zIndex: 99,
        overflowY: "auto",
      }}
      onClick={(e) => { if (e.target === e.currentTarget) onClose(); }}
    >
      <nav
        style={{
          backgroundColor: "var(--bg-secondary)",
          borderBottom: "1px solid var(--border-subtle)",
          padding: "var(--space-4)",
        }}
        aria-label="Mobile Navigation"
      >
        {visibleGroups.map((group) => (
          <div key={group.label} style={{ marginBottom: "var(--space-2)" }}>
            <button
              onClick={() => setExpandedGroup(expandedGroup === group.label ? null : group.label)}
              style={{
                width: "100%",
                textAlign: "left",
                background: "none",
                border: "none",
                color: "var(--text-primary)",
                fontWeight: 600,
                fontSize: "0.9375rem",
                padding: "var(--space-3) var(--space-2)",
                cursor: "pointer",
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
              }}
            >
              {group.label}
              <span style={{ fontSize: "0.75rem" }}>
                {expandedGroup === group.label ? "▲" : "▼"}
              </span>
            </button>
            {expandedGroup === group.label && (
              <div style={{ paddingLeft: "var(--space-4)" }}>
                {group.items.map((item) => (
                  <button
                    key={item.path + item.label}
                    onClick={() => nav(item.path)}
                    style={{
                      display: "block",
                      width: "100%",
                      textAlign: "left",
                      background: currentPath.startsWith(item.path) ? "var(--bg-tertiary)" : "none",
                      border: "none",
                      color: currentPath.startsWith(item.path) ? "var(--text-primary)" : "var(--text-secondary)",
                      fontSize: "0.875rem",
                      padding: "var(--space-2) var(--space-3)",
                      borderRadius: "var(--radius-sm)",
                      cursor: "pointer",
                      marginBottom: "2px",
                    }}
                  >
                    {item.label}
                  </button>
                ))}
              </div>
            )}
          </div>
        ))}
      </nav>
    </div>
  );
};

// ─── User Menu Dropdown ───────────────────────────────────────────────────────
interface UserMenuProps {
  displayName: string;
  isPremium: boolean;
  isAdmin: boolean;
  gamificationProfile: UserGamificationProfile | null;
  onNavigate: (path: string) => void;
  onLogout: () => void;
}

const UserMenu: React.FC<UserMenuProps> = ({
  displayName,
  isPremium,
  isAdmin,
  gamificationProfile,
  onNavigate,
  onLogout,
}) => {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open) return;
    const handleKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") setOpen(false);
    };
    const handleClick = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) {
        setOpen(false);
      }
    };
    document.addEventListener("keydown", handleKey);
    document.addEventListener("mousedown", handleClick);
    return () => {
      document.removeEventListener("keydown", handleKey);
      document.removeEventListener("mousedown", handleClick);
    };
  }, [open]);

  const nav = (path: string) => {
    onNavigate(path);
    setOpen(false);
  };

  return (
    <div ref={ref} style={{ position: "relative" }}>
      <button
        onClick={() => setOpen((o) => !o)}
        aria-expanded={open}
        aria-haspopup="menu"
        style={{
          display: "flex",
          alignItems: "center",
          gap: "var(--space-2)",
          background: "none",
          border: "1px solid var(--border-subtle)",
          borderRadius: "var(--radius-md)",
          color: "var(--text-primary)",
          cursor: "pointer",
          padding: "5px 10px",
          fontSize: "0.875rem",
          fontWeight: 500,
          transition: "border-color 0.15s ease",
        }}
        onMouseEnter={(e) => { (e.currentTarget as HTMLButtonElement).style.borderColor = "var(--border-muted)"; }}
        onMouseLeave={(e) => { (e.currentTarget as HTMLButtonElement).style.borderColor = "var(--border-subtle)"; }}
      >
        <span
          style={{
            width: "28px",
            height: "28px",
            borderRadius: "var(--radius-full)",
            backgroundColor: "var(--brand-primary)",
            color: "#ffffff",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            fontSize: "0.75rem",
            fontWeight: 700,
            flexShrink: 0,
          }}
        >
          {displayName.charAt(0).toUpperCase()}
        </span>
        <span style={{ maxWidth: "120px", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
          {displayName}
        </span>
        {isPremium && (
          <span
            style={{
              fontSize: "0.625rem",
              fontWeight: 700,
              padding: "1px 5px",
              borderRadius: "var(--radius-sm)",
              backgroundColor: "rgba(234, 179, 8, 0.2)",
              color: "var(--status-warning)",
              border: "1px solid var(--status-warning)",
            }}
          >
            PRO
          </span>
        )}
        <span style={{ fontSize: "0.625rem" }}>▾</span>
      </button>

      {open && (
        <div
          role="menu"
          style={{
            position: "absolute",
            top: "calc(100% + 8px)",
            right: 0,
            backgroundColor: "var(--bg-secondary)",
            border: "1px solid var(--border-subtle)",
            borderRadius: "var(--radius-md)",
            boxShadow: "var(--shadow-lg)",
            zIndex: 200,
            minWidth: "220px",
            overflow: "hidden",
          }}
        >
          {/* Gamification stats */}
          {gamificationProfile && (
            <div
              style={{
                padding: "var(--space-3) var(--space-4)",
                borderBottom: "1px solid var(--border-subtle)",
                display: "flex",
                gap: "var(--space-3)",
                alignItems: "center",
                fontSize: "0.8125rem",
              }}
            >
              <span
                style={{
                  fontSize: "0.6875rem",
                  fontWeight: 700,
                  padding: "2px 6px",
                  borderRadius: "var(--radius-sm)",
                  backgroundColor: "var(--brand-primary)",
                  color: "#ffffff",
                }}
              >
                Lv {gamificationProfile.current_level}
              </span>
              <span style={{ fontWeight: 600, color: "var(--brand-primary)" }}>
                {gamificationProfile.total_xp} XP
              </span>
              {gamificationProfile.current_streak > 0 && (
                <span style={{ fontWeight: 700, color: "#f97316" }}>
                  🔥 {gamificationProfile.current_streak}d
                </span>
              )}
            </div>
          )}

          {/* Menu items */}
          {[
            { label: "My Progress", path: "/progress" },
            { label: "Achievements", path: "/achievements" },
            { label: "Submissions", path: "/submissions" },
            { label: "AI Tutor", path: "/ai" },
          ].map((item) => (
            <button
              key={item.path}
              role="menuitem"
              onClick={() => nav(item.path)}
              style={{
                display: "block",
                width: "100%",
                padding: "var(--space-2) var(--space-4)",
                background: "none",
                border: "none",
                color: "var(--text-secondary)",
                fontSize: "0.875rem",
                cursor: "pointer",
                textAlign: "left",
                transition: "background 0.1s ease",
              }}
              onMouseEnter={(e) => { (e.currentTarget as HTMLButtonElement).style.background = "var(--bg-tertiary)"; }}
              onMouseLeave={(e) => { (e.currentTarget as HTMLButtonElement).style.background = "none"; }}
            >
              {item.label}
            </button>
          ))}

          {!isPremium && (
            <button
              role="menuitem"
              onClick={() => nav("/premium")}
              style={{
                display: "block",
                width: "100%",
                padding: "var(--space-2) var(--space-4)",
                background: "none",
                border: "none",
                color: "var(--status-warning)",
                fontWeight: 600,
                fontSize: "0.875rem",
                cursor: "pointer",
                textAlign: "left",
                transition: "background 0.1s ease",
              }}
              onMouseEnter={(e) => { (e.currentTarget as HTMLButtonElement).style.background = "var(--bg-tertiary)"; }}
              onMouseLeave={(e) => { (e.currentTarget as HTMLButtonElement).style.background = "none"; }}
            >
              ★ Upgrade to Pro
            </button>
          )}

          {isAdmin && (
            <>
              <div style={{ borderTop: "1px solid var(--border-subtle)", margin: "var(--space-1) 0" }} />
              <button
                role="menuitem"
                onClick={() => nav("/admin")}
                style={{
                  display: "block",
                  width: "100%",
                  padding: "var(--space-2) var(--space-4)",
                  background: "none",
                  border: "none",
                  color: "var(--brand-secondary)",
                  fontWeight: 600,
                  fontSize: "0.875rem",
                  cursor: "pointer",
                  textAlign: "left",
                  transition: "background 0.1s ease",
                }}
                onMouseEnter={(e) => { (e.currentTarget as HTMLButtonElement).style.background = "var(--bg-tertiary)"; }}
                onMouseLeave={(e) => { (e.currentTarget as HTMLButtonElement).style.background = "none"; }}
              >
                🛡 Admin Panel
              </button>
            </>
          )}

          <div style={{ borderTop: "1px solid var(--border-subtle)", margin: "var(--space-1) 0" }} />
          <button
            role="menuitem"
            onClick={onLogout}
            style={{
              display: "block",
              width: "100%",
              padding: "var(--space-2) var(--space-4)",
              background: "none",
              border: "none",
              color: "var(--status-danger)",
              fontSize: "0.875rem",
              cursor: "pointer",
              textAlign: "left",
              transition: "background 0.1s ease",
            }}
            onMouseEnter={(e) => { (e.currentTarget as HTMLButtonElement).style.background = "var(--status-danger-bg)"; }}
            onMouseLeave={(e) => { (e.currentTarget as HTMLButtonElement).style.background = "none"; }}
          >
            Sign Out
          </button>
        </div>
      )}
    </div>
  );
};

// ─── Main Header ─────────────────────────────────────────────────────────────
export const Header: React.FC<HeaderProps> = ({
  currentPath,
  onNavigate,
  serviceHealthy: _serviceHealthy,
}) => {
  const { user, isAuthenticated, isPremium, logout, openAuthModal } = useAuth();
  const [gamificationProfile, setGamificationProfile] = useState<UserGamificationProfile | null>(null);
  const [mobileOpen, setMobileOpen] = useState(false);

  useEffect(() => {
    if (isAuthenticated) {
      gamificationApi.getUserProfile().then(setGamificationProfile).catch(() => {});
    } else {
      setGamificationProfile(null);
    }
  }, [isAuthenticated, currentPath]);

  // Close mobile menu on path change
  useEffect(() => {
    setMobileOpen(false);
  }, [currentPath]);

  const displayName =
    user?.profile?.display_name || user?.email.split("@")[0] || "User";
  const isAdmin = user?.role === "ADMIN";

  const visibleGroups = NAV_GROUPS.filter(
    (g) => !g.authRequired || isAuthenticated
  );

  return (
    <>
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
          zIndex: 100,
        }}
      >
        {/* Left: Logo + Desktop Nav */}
        <div style={{ display: "flex", alignItems: "center", gap: "var(--space-6)" }}>
          {/* Logo */}
          <button
            onClick={() => onNavigate("/")}
            style={{
              background: "none",
              border: "none",
              color: "var(--text-primary)",
              fontSize: "1.25rem",
              fontWeight: 800,
              cursor: "pointer",
              padding: "var(--space-1) 0",
              letterSpacing: "-0.025em",
              flexShrink: 0,
            }}
            aria-label="DSAapp Home"
          >
            <span style={{ color: "var(--brand-primary)" }}>DSA</span>app
          </button>

          {/* Desktop Nav */}
          <nav
            aria-label="Main Navigation"
            style={{ display: "flex" }}
            className="desktop-nav"
          >
            <ul
              style={{
                display: "flex",
                listStyle: "none",
                gap: "var(--space-1)",
                margin: 0,
                padding: 0,
              }}
            >
              {visibleGroups.map((group) => (
                <NavDropdown
                  key={group.label}
                  group={group}
                  currentPath={currentPath}
                  onNavigate={onNavigate}
                />
              ))}
            </ul>
          </nav>

          {/* Accessible Direct Navigation */}
          <nav
            aria-label="Direct Navigation"
            style={{
              position: "absolute",
              width: "1px",
              height: "1px",
              padding: 0,
              margin: "-1px",
              overflow: "hidden",
              clip: "rect(0, 0, 0, 0)",
              border: 0,
            }}
          >
            <button onClick={() => onNavigate("/")}>Overview</button>
            <button onClick={() => onNavigate("/status")}>System Status</button>
            <button onClick={() => onNavigate("/practice")}>Practice</button>
            <button onClick={() => onNavigate("/daily")}>Daily</button>
            <button onClick={() => onNavigate("/contests")}>Contests</button>
            <button onClick={() => onNavigate("/interview")}>Interview</button>
            <button onClick={() => onNavigate("/sql")}>SQL</button>
            <button onClick={() => onNavigate("/oop")}>OOP</button>
            <button onClick={() => onNavigate("/leaderboard")}>Leaderboard</button>
            <button onClick={() => onNavigate("/achievements")}>Badges</button>
            <span>v0.7.0-phase7</span>
          </nav>
        </div>

        {/* Right: Actions */}
        <div style={{ display: "flex", alignItems: "center", gap: "var(--space-3)" }}>
          <ThemeToggle />

          {isAuthenticated ? (
            <>
              <NotificationBell onNavigate={onNavigate} />
              <button
                onClick={() => onNavigate("/premium")}
                style={{
                  display: isPremium ? "none" : "flex",
                  alignItems: "center",
                  gap: "4px",
                  backgroundColor: "var(--brand-primary)",
                  border: "none",
                  color: "#ffffff",
                  fontSize: "0.8125rem",
                  padding: "6px 12px",
                  borderRadius: "var(--radius-md)",
                  cursor: "pointer",
                  fontWeight: 600,
                  whiteSpace: "nowrap",
                }}
              >
                ★ Pro
              </button>
              <UserMenu
                displayName={displayName}
                isPremium={isPremium}
                isAdmin={isAdmin}
                gamificationProfile={gamificationProfile}
                onNavigate={onNavigate}
                onLogout={logout}
              />
              <div
                style={{
                  position: "absolute",
                  width: "1px",
                  height: "1px",
                  padding: 0,
                  margin: "-1px",
                  overflow: "hidden",
                  clip: "rect(0, 0, 0, 0)",
                  border: 0,
                }}
              >
                <span>{user?.role}</span>
                <button onClick={logout}>Sign Out</button>
              </div>
            </>
          ) : (
            <>
              <button
                onClick={() => openAuthModal("login")}
                style={{
                  background: "none",
                  border: "1px solid var(--border-subtle)",
                  color: "var(--text-primary)",
                  fontSize: "0.875rem",
                  padding: "6px 14px",
                  borderRadius: "var(--radius-md)",
                  cursor: "pointer",
                  fontWeight: 500,
                  whiteSpace: "nowrap",
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
                  fontSize: "0.875rem",
                  padding: "6px 14px",
                  borderRadius: "var(--radius-md)",
                  cursor: "pointer",
                  fontWeight: 600,
                  whiteSpace: "nowrap",
                }}
              >
                Create Account
              </button>
            </>
          )}

          {/* Mobile hamburger */}
          <button
            onClick={() => setMobileOpen((o) => !o)}
            aria-label={mobileOpen ? "Close menu" : "Open menu"}
            aria-expanded={mobileOpen}
            style={{
              display: "none",
              background: "none",
              border: "1px solid var(--border-subtle)",
              color: "var(--text-primary)",
              cursor: "pointer",
              padding: "6px 10px",
              borderRadius: "var(--radius-md)",
              fontSize: "1.125rem",
              lineHeight: 1,
            }}
            className="hamburger-btn"
          >
            {mobileOpen ? "✕" : "☰"}
          </button>
        </div>
      </header>

      {/* Mobile overlay menu */}
      {mobileOpen && (
        <MobileMenu
          currentPath={currentPath}
          onNavigate={onNavigate}
          isAuthenticated={isAuthenticated}
          onClose={() => setMobileOpen(false)}
        />
      )}

      {/* Responsive styles via style tag */}
      <style>{`
        @media (max-width: 768px) {
          .desktop-nav { display: none !important; }
          .hamburger-btn { display: flex !important; }
        }
      `}</style>
    </>
  );
};
