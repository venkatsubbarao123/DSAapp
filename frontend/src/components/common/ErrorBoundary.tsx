import { Component, ErrorInfo, ReactNode } from "react";

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
}

interface State {
  hasError: boolean;
  errorMessage: string;
}

export class ErrorBoundary extends Component<Props, State> {
  public override state: State = {
    hasError: false,
    errorMessage: "",
  };

  public static getDerivedStateFromError(error: Error): State {
    return {
      hasError: true,
      errorMessage: error.message || "An unexpected application error occurred.",
    };
  }

  public override componentDidCatch(error: Error, errorInfo: ErrorInfo): void {
    // In production, send to observability service
    console.error("ErrorBoundary caught an unhandled render error:", error, errorInfo);
  }

  public handleReset = (): void => {
    this.setState({ hasError: false, errorMessage: "" });
    window.location.reload();
  };

  public override render(): ReactNode {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback;
      }

      return (
        <main
          role="alert"
          style={{
            minHeight: "60vh",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            padding: "var(--space-6)",
          }}
        >
          <div
            style={{
              maxWidth: "480px",
              width: "100%",
              backgroundColor: "var(--bg-card)",
              border: "1px solid var(--status-danger)",
              borderRadius: "var(--radius-lg)",
              padding: "var(--space-8)",
              textAlign: "center",
              boxShadow: "var(--shadow-lg)",
            }}
          >
            <div
              style={{
                width: "48px",
                height: "48px",
                borderRadius: "var(--radius-full)",
                backgroundColor: "var(--status-danger-bg)",
                color: "var(--status-danger)",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                margin: "0 auto var(--space-4)",
                fontSize: "1.5rem",
                fontWeight: "bold",
              }}
            >
              !
            </div>
            <h1
              style={{
                fontSize: "1.25rem",
                fontWeight: 600,
                color: "var(--text-primary)",
                marginBottom: "var(--space-2)",
              }}
            >
              Application Error
            </h1>
            <p
              style={{
                color: "var(--text-secondary)",
                fontSize: "0.875rem",
                marginBottom: "var(--space-6)",
                lineHeight: 1.6,
              }}
            >
              {this.state.errorMessage}
            </p>
            <button
              onClick={this.handleReset}
              style={{
                backgroundColor: "var(--brand-primary)",
                color: "#ffffff",
                border: "none",
                borderRadius: "var(--radius-md)",
                padding: "var(--space-2) var(--space-6)",
                fontSize: "0.875rem",
                fontWeight: 500,
                cursor: "pointer",
                transition: "background-color 0.15s ease",
              }}
            >
              Reload Application
            </button>
          </div>
        </main>
      );
    }

    return this.props.children;
  }
}
