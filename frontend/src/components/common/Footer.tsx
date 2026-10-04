import React from "react";

export const Footer: React.FC = () => {
  return (
    <footer
      style={{
        borderTop: "1px solid var(--border-subtle)",
        backgroundColor: "var(--bg-secondary)",
        padding: "var(--space-8) var(--space-6)",
        marginTop: "auto",
        color: "var(--text-muted)",
      }}
    >
      <div
        style={{
          maxWidth: "1200px",
          margin: "0 auto",
        }}
      >
        {/* Main Footer */}
        <div
          style={{
            display: "flex",
            flexWrap: "wrap",
            justifyContent: "space-between",
            gap: "var(--space-8)",
            textAlign: "left",
          }}
        >
          {/* Platform */}
          <div style={{ minWidth: "240px", flex: 1 }}>
            <h3
              style={{
                margin: "0 0 var(--space-2)",
                color: "var(--text-primary)",
                fontSize: "1.05rem",
              }}
            >
              DSAapp
            </h3>

            <p style={{ margin: 0, lineHeight: 1.6 }}>
              Secure Production Coding Education Platform
            </p>
          </div>

          {/* About Developer */}
          <div style={{ minWidth: "280px", flex: 1 }}>
            <h3
              style={{
                margin: "0 0 var(--space-3)",
                color: "var(--text-primary)",
                fontSize: "1.05rem",
              }}
            >
              About Developer
            </h3>

            <p
              style={{
                margin: "0 0 var(--space-1)",
                color: "var(--text-primary)",
                fontWeight: 600,
              }}
            >
              Choppavarapu Venkata Subba Rao
            </p>

            <p style={{ margin: "0 0 var(--space-3)" }}>
              AI/ML Developer
            </p>

            <div
              style={{
                display: "flex",
                flexDirection: "column",
                gap: "var(--space-2)",
              }}
            >
              <a
                href="tel:7093260994"
                style={{
                  color: "var(--text-muted)",
                  textDecoration: "none",
                }}
              >
                📞 7093260994
              </a>

              <a
                href="mailto:venkatsubbarao000@gmail.com"
                style={{
                  color: "var(--text-muted)",
                  textDecoration: "none",
                }}
              >
                📧 venkatsubbarao000@gmail.com
              </a>

              <a
                href="https://www.linkedin.com/in/venkatasubbarao09"
                target="_blank"
                rel="noopener noreferrer"
                style={{
                  color: "var(--text-muted)",
                  textDecoration: "none",
                }}
              >
                💼 LinkedIn
              </a>

              <a
                href="https://github.com/venkatsubbarao123"
                target="_blank"
                rel="noopener noreferrer"
                style={{
                  color: "var(--text-muted)",
                  textDecoration: "none",
                }}
              >
                💻 GitHub
              </a>
            </div>
          </div>

          {/* Platform Information */}
          <div style={{ minWidth: "240px", flex: 1 }}>
            <h3
              style={{
                margin: "0 0 var(--space-3)",
                color: "var(--text-primary)",
                fontSize: "1.05rem",
              }}
            >
              Platform
            </h3>

            <p style={{ margin: "0 0 var(--space-2)" }}>
              Phase 1 Architecture Foundation
            </p>

            <p style={{ margin: "0 0 var(--space-2)" }}>
              WCAG 2.1 AA Compliant
            </p>

            <p style={{ margin: 0 }}>
              Strict Security Enforced
            </p>
          </div>
        </div>

        {/* Bottom Copyright */}
        <div
          style={{
            marginTop: "var(--space-6)",
            paddingTop: "var(--space-4)",
            borderTop: "1px solid var(--border-subtle)",
            textAlign: "center",
            fontSize: "0.8125rem",
          }}
        >
          © {new Date().getFullYear()} DSAapp. All rights reserved.
        </div>
      </div>
    </footer>
  );
};