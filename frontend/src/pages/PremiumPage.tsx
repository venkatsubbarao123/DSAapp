import React, { useState, useEffect } from "react";
import { useAuth } from "../context/AuthContext.tsx";
import { fetchApi, APIClientError } from "../services/apiClient.ts";
import {
  OrderCreateResponse,
  PaymentHistoryItem,
} from "../types/auth.ts";
import { LoadingSpinner } from "../components/common/LoadingSpinner.tsx";

export const PremiumPage: React.FC = () => {
  const { isAuthenticated, isPremium, openAuthModal, refreshUser } =
    useAuth();

  const [isCreatingOrder, setIsCreatingOrder] = useState(false);
  const [isVerifying, setIsVerifying] = useState(false);
  const [activeOrder, setActiveOrder] = useState<OrderCreateResponse | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  // Premium gate test state
  const [gateTesting, setGateTesting] = useState(false);
  const [gateResult, setGateResult] = useState<{
    authorized: boolean;
    features: string[];
  } | null>(null);

  // Payment history
  const [history, setHistory] = useState<PaymentHistoryItem[]>([]);
  const [loadingHistory, setLoadingHistory] = useState(false);

  // Fetch payment history when authenticated
  useEffect(() => {
    if (isAuthenticated) {
      setLoadingHistory(true);
      fetchApi<PaymentHistoryItem[]>("/api/v1/payments/history")
        .then((res) => setHistory(res.data || []))
        .catch(() => {})
        .finally(() => setLoadingHistory(false));
    }
  }, [isAuthenticated, isPremium]);

  const handleCreateOrder = async () => {
    if (!isAuthenticated) {
      openAuthModal("login");
      return;
    }

    setIsCreatingOrder(true);
    setErrorMsg(null);
    setSuccessMsg(null);

    try {
      const res = await fetchApi<OrderCreateResponse>(
        "/api/v1/payments/create-order",
        {
          method: "POST",
          body: JSON.stringify({}),
        }
      );
      setActiveOrder(res.data);
      setSuccessMsg(
        `Order ${res.data.order_id} created successfully for ${res.data.currency} ${res.data.amount}.`
      );
    } catch (err) {
      if (err instanceof APIClientError) {
        setErrorMsg(err.message);
      } else {
        setErrorMsg("Failed to initiate payment order.");
      }
    } finally {
      setIsCreatingOrder(false);
    }
  };

  const handleSimulatePaymentVerification = async () => {
    if (!activeOrder) return;

    setIsVerifying(true);
    setErrorMsg(null);

    try {
      const simTxId = `sim_tx_${Date.now()}`;
      await fetchApi(`/api/v1/payments/${activeOrder.order_id}/verify`, {
        method: "POST",
        body: JSON.stringify({ transaction_id: simTxId }),
      });

      setSuccessMsg("Payment verified! Premium membership activated.");
      setActiveOrder(null);
      await refreshUser();
    } catch (err) {
      if (err instanceof APIClientError) {
        setErrorMsg(err.message);
      } else {
        setErrorMsg("Payment verification failed.");
      }
    } finally {
      setIsVerifying(false);
    }
  };

  const handleTestPremiumGate = async () => {
    setGateTesting(true);
    setErrorMsg(null);
    try {
      const res = await fetchApi<{
        authorized: boolean;
        features: string[];
      }>("/api/v1/premium/preview");
      setGateResult(res.data);
    } catch (err) {
      if (err instanceof APIClientError) {
        setErrorMsg(`Gate Access Denied: ${err.message}`);
      } else {
        setErrorMsg("Failed to test premium access gate.");
      }
      setGateResult(null);
    } finally {
      setGateTesting(false);
    }
  };

  return (
    <main
      id="main-content"
      style={{
        flex: 1,
        maxWidth: "1100px",
        margin: "0 auto",
        padding: "var(--space-8) var(--space-6)",
        width: "100%",
        boxSizing: "border-box",
      }}
    >
      {/* Hero Header */}
      <section style={{ textAlign: "center", marginBottom: "var(--space-12)" }}>
        <div
          style={{
            display: "inline-flex",
            alignItems: "center",
            gap: "var(--space-2)",
            backgroundColor: "var(--bg-tertiary)",
            border: "1px solid var(--border-muted)",
            padding: "4px 12px",
            borderRadius: "var(--radius-full)",
            fontSize: "0.8125rem",
            color: "var(--status-warning)",
            fontWeight: 600,
            marginBottom: "var(--space-4)",
          }}
        >
          <span>★</span>
          <span>DSAAPP PRO & ENTERPRISE PREPARATION</span>
        </div>
        <h1
          style={{
            fontSize: "2.5rem",
            fontWeight: 800,
            letterSpacing: "-0.025em",
            marginBottom: "var(--space-4)",
          }}
        >
          Master Algorithms with Production Rigor
        </h1>
        <p
          style={{
            fontSize: "1.125rem",
            color: "var(--text-secondary)",
            maxWidth: "680px",
            margin: "0 auto",
            lineHeight: 1.6,
          }}
        >
          Unlock advanced data structure curricula, in-depth system design deep-dives,
          mock interview evaluations, and personalized curriculum sequencing.
        </p>
      </section>

      {/* Alerts */}
      {errorMsg && (
        <div
          role="alert"
          style={{
            backgroundColor: "var(--status-danger-bg)",
            border: "1px solid var(--status-danger)",
            color: "var(--status-danger)",
            padding: "var(--space-4)",
            borderRadius: "var(--radius-md)",
            marginBottom: "var(--space-6)",
          }}
        >
          {errorMsg}
        </div>
      )}

      {successMsg && (
        <div
          role="status"
          style={{
            backgroundColor: "var(--status-success-bg)",
            border: "1px solid var(--status-success)",
            color: "var(--status-success)",
            padding: "var(--space-4)",
            borderRadius: "var(--radius-md)",
            marginBottom: "var(--space-6)",
          }}
        >
          {successMsg}
        </div>
      )}

      {/* Active Premium Member Banner */}
      {isPremium && (
        <div
          style={{
            backgroundColor: "rgba(234, 179, 8, 0.1)",
            border: "1px solid var(--status-warning)",
            borderRadius: "var(--radius-lg)",
            padding: "var(--space-6)",
            marginBottom: "var(--space-8)",
            display: "flex",
            flexDirection: "column",
            gap: "var(--space-4)",
          }}
        >
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", flexWrap: "wrap", gap: "var(--space-4)" }}>
            <div style={{ display: "flex", alignItems: "center", gap: "var(--space-3)" }}>
              <span style={{ fontSize: "1.5rem", color: "var(--status-warning)" }}>★</span>
              <div>
                <h3 style={{ margin: 0, fontSize: "1.25rem", fontWeight: 700, color: "var(--text-primary)" }}>
                  Active Premium Entitlement
                </h3>
                <p style={{ margin: 0, fontSize: "0.875rem", color: "var(--text-secondary)" }}>
                  Your account has unrestricted access to all Pro features and backend premium gates.
                </p>
              </div>
            </div>
            <button
              onClick={handleTestPremiumGate}
              disabled={gateTesting}
              style={{
                backgroundColor: "var(--bg-tertiary)",
                border: "1px solid var(--border-muted)",
                color: "var(--text-primary)",
                padding: "var(--space-2) var(--space-4)",
                borderRadius: "var(--radius-md)",
                fontWeight: 600,
                fontSize: "0.875rem",
                cursor: gateTesting ? "not-allowed" : "pointer",
                display: "flex",
                alignItems: "center",
                gap: "var(--space-2)",
              }}
            >
              {gateTesting && <LoadingSpinner size="sm" />}
              <span>Test Premium Gate (/api/v1/premium/preview)</span>
            </button>
          </div>

          {gateResult && (
            <div
              style={{
                backgroundColor: "var(--bg-primary)",
                padding: "var(--space-4)",
                borderRadius: "var(--radius-md)",
                border: "1px solid var(--border-subtle)",
              }}
            >
              <div style={{ display: "flex", alignItems: "center", gap: "var(--space-2)", marginBottom: "var(--space-2)", color: "var(--status-success)", fontWeight: 600, fontSize: "0.875rem" }}>
                <span>✓</span>
                <span>Gate Authorization Verified by Server</span>
              </div>
              <div style={{ fontSize: "0.8125rem", color: "var(--text-secondary)" }}>
                Unlocked Features:
                <ul style={{ margin: "var(--space-2) 0 0 var(--space-4)", padding: 0 }}>
                  {gateResult.features.map((feat, idx) => (
                    <li key={idx}>{feat}</li>
                  ))}
                </ul>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Pricing Cards Grid */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(320px, 1fr))",
          gap: "var(--space-8)",
          marginBottom: "var(--space-12)",
        }}
      >
        {/* Free Plan Card */}
        <div
          style={{
            backgroundColor: "var(--bg-secondary)",
            border: "1px solid var(--border-subtle)",
            borderRadius: "var(--radius-xl)",
            padding: "var(--space-8)",
            display: "flex",
            flexDirection: "column",
            justifyContent: "space-between",
          }}
        >
          <div>
            <span
              style={{
                fontSize: "0.875rem",
                fontWeight: 600,
                color: "var(--text-secondary)",
                textTransform: "uppercase",
                letterSpacing: "0.05em",
              }}
            >
              Standard Free
            </span>
            <div style={{ margin: "var(--space-4) 0", display: "flex", alignItems: "baseline", gap: "var(--space-2)" }}>
              <span style={{ fontSize: "2.5rem", fontWeight: 800 }}>₹0</span>
              <span style={{ color: "var(--text-secondary)" }}>/ forever</span>
            </div>
            <p style={{ color: "var(--text-secondary)", fontSize: "0.875rem", marginBottom: "var(--space-6)" }}>
              Essential algorithmic concepts and core problem sets for fundamental practice.
            </p>
            <ul
              style={{
                listStyle: "none",
                padding: 0,
                margin: 0,
                display: "flex",
                flexDirection: "column",
                gap: "var(--space-3)",
                fontSize: "0.875rem",
                color: "var(--text-secondary)",
              }}
            >
              <li>✓ Core Arrays, Strings & Linked Lists</li>
              <li>✓ Basic Time & Space Complexity analysis</li>
              <li>✓ Public community discussion access</li>
              <li>✓ Standard test case evaluation</li>
            </ul>
          </div>

          <div style={{ marginTop: "var(--space-8)" }}>
            <span
              style={{
                display: "block",
                textAlign: "center",
                padding: "var(--space-3)",
                borderRadius: "var(--radius-md)",
                backgroundColor: "var(--bg-tertiary)",
                color: "var(--text-muted)",
                fontSize: "0.875rem",
                fontWeight: 600,
              }}
            >
              Current Default Tier
            </span>
          </div>
        </div>

        {/* Pro Plan Card */}
        <div
          style={{
            backgroundColor: "var(--bg-secondary)",
            border: "2px solid var(--brand-primary)",
            borderRadius: "var(--radius-xl)",
            padding: "var(--space-8)",
            display: "flex",
            flexDirection: "column",
            justifyContent: "space-between",
            position: "relative",
            boxShadow: "0 10px 25px -5px rgba(59, 130, 246, 0.2)",
          }}
        >
          <div
            style={{
              position: "absolute",
              top: "-12px",
              right: "var(--space-6)",
              backgroundColor: "var(--brand-primary)",
              color: "#ffffff",
              padding: "2px 12px",
              borderRadius: "var(--radius-full)",
              fontSize: "0.75rem",
              fontWeight: 700,
              letterSpacing: "0.05em",
            }}
          >
            RECOMMENDED
          </div>

          <div>
            <span
              style={{
                fontSize: "0.875rem",
                fontWeight: 600,
                color: "var(--brand-primary)",
                textTransform: "uppercase",
                letterSpacing: "0.05em",
              }}
            >
              DSAapp Premium
            </span>
            <div style={{ margin: "var(--space-4) 0", display: "flex", alignItems: "baseline", gap: "var(--space-2)" }}>
              <span style={{ fontSize: "2.5rem", fontWeight: 800 }}>₹999</span>
              <span style={{ color: "var(--text-secondary)" }}>/ 365 days</span>
            </div>
            <p style={{ color: "var(--text-secondary)", fontSize: "0.875rem", marginBottom: "var(--space-6)" }}>
              Comprehensive engineering interview prep with advanced algorithms and mock interviews.
            </p>
            <ul
              style={{
                listStyle: "none",
                padding: 0,
                margin: 0,
                display: "flex",
                flexDirection: "column",
                gap: "var(--space-3)",
                fontSize: "0.875rem",
                color: "var(--text-primary)",
              }}
            >
              <li>✓ Advanced Dynamic Programming & Graph Theory</li>
              <li>✓ Distributed System Design Masterclass tracks</li>
              <li>✓ Real-time AI Code Review & hint explanations</li>
              <li>✓ Mock Company Technical Interviews (FAANG-style)</li>
              <li>✓ Full Curated 75 & 150 Question Blueprint roadmaps</li>
            </ul>
          </div>

          <div style={{ marginTop: "var(--space-8)" }}>
            {isPremium ? (
              <span
                style={{
                  display: "block",
                  textAlign: "center",
                  padding: "var(--space-3)",
                  borderRadius: "var(--radius-md)",
                  backgroundColor: "rgba(234, 179, 8, 0.2)",
                  color: "var(--status-warning)",
                  fontSize: "0.875rem",
                  fontWeight: 700,
                }}
              >
                ★ You are an Active Pro Member
              </span>
            ) : (
              <button
                onClick={handleCreateOrder}
                disabled={isCreatingOrder}
                style={{
                  width: "100%",
                  backgroundColor: "var(--brand-primary)",
                  color: "#ffffff",
                  border: "none",
                  borderRadius: "var(--radius-md)",
                  padding: "var(--space-3)",
                  fontSize: "0.875rem",
                  fontWeight: 600,
                  cursor: isCreatingOrder ? "not-allowed" : "pointer",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  gap: "var(--space-2)",
                }}
              >
                {isCreatingOrder && <LoadingSpinner size="sm" />}
                <span>
                  {isAuthenticated ? "Upgrade to Pro (₹999/yr)" : "Sign In to Upgrade"}
                </span>
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Dev Order Verification Dialog */}
      {activeOrder && (
        <section
          style={{
            backgroundColor: "var(--bg-secondary)",
            border: "1px solid var(--border-muted)",
            borderRadius: "var(--radius-lg)",
            padding: "var(--space-6)",
            marginBottom: "var(--space-12)",
          }}
        >
          <h3 style={{ fontSize: "1.125rem", fontWeight: 700, marginBottom: "var(--space-2)" }}>
            Complete Order: {activeOrder.order_id}
          </h3>
          <p style={{ color: "var(--text-secondary)", fontSize: "0.875rem", marginBottom: "var(--space-4)" }}>
            Environment Mode:{" "}
            <code style={{ fontFamily: "var(--font-mono)", color: "var(--status-warning)" }}>
              development_manual
            </code>
            . You can simulate instant payment gateway confirmation to test entitlement activation.
          </p>
          <div style={{ display: "flex", gap: "var(--space-4)", alignItems: "center" }}>
            <button
              onClick={handleSimulatePaymentVerification}
              disabled={isVerifying}
              style={{
                backgroundColor: "var(--status-success)",
                color: "#ffffff",
                border: "none",
                borderRadius: "var(--radius-md)",
                padding: "var(--space-2) var(--space-4)",
                fontWeight: 600,
                fontSize: "0.875rem",
                cursor: isVerifying ? "not-allowed" : "pointer",
                display: "flex",
                alignItems: "center",
                gap: "var(--space-2)",
              }}
            >
              {isVerifying && <LoadingSpinner size="sm" />}
              <span>Simulate Verified Payment (Dev Mode)</span>
            </button>
            <button
              onClick={() => setActiveOrder(null)}
              style={{
                background: "none",
                border: "1px solid var(--border-subtle)",
                color: "var(--text-secondary)",
                borderRadius: "var(--radius-md)",
                padding: "var(--space-2) var(--space-4)",
                fontSize: "0.875rem",
                cursor: "pointer",
              }}
            >
              Cancel
            </button>
          </div>
        </section>
      )}

      {/* Payment History Section */}
      {isAuthenticated && (
        <section
          style={{
            backgroundColor: "var(--bg-secondary)",
            border: "1px solid var(--border-subtle)",
            borderRadius: "var(--radius-lg)",
            padding: "var(--space-6)",
          }}
        >
          <h3 style={{ fontSize: "1.125rem", fontWeight: 700, marginBottom: "var(--space-4)" }}>
            Payment & Transaction History
          </h3>

          {loadingHistory ? (
            <div style={{ display: "flex", justifyContent: "center", padding: "var(--space-6)" }}>
              <LoadingSpinner size="md" />
            </div>
          ) : history.length === 0 ? (
            <p style={{ color: "var(--text-muted)", fontSize: "0.875rem", fontStyle: "italic" }}>
              No transactions recorded yet.
            </p>
          ) : (
            <div style={{ overflowX: "auto" }}>
              <table
                style={{
                  width: "100%",
                  borderCollapse: "collapse",
                  fontSize: "0.875rem",
                  textAlign: "left",
                }}
              >
                <thead>
                  <tr style={{ borderBottom: "1px solid var(--border-subtle)", color: "var(--text-muted)" }}>
                    <th style={{ padding: "var(--space-2) var(--space-4)" }}>Transaction ID</th>
                    <th style={{ padding: "var(--space-2) var(--space-4)" }}>Order ID</th>
                    <th style={{ padding: "var(--space-2) var(--space-4)" }}>Amount</th>
                    <th style={{ padding: "var(--space-2) var(--space-4)" }}>Status</th>
                    <th style={{ padding: "var(--space-2) var(--space-4)" }}>Date</th>
                  </tr>
                </thead>
                <tbody>
                  {history.map((tx) => (
                    <tr
                      key={tx.id}
                      style={{
                        borderBottom: "1px solid var(--border-subtle)",
                        color: "var(--text-secondary)",
                      }}
                    >
                      <td style={{ padding: "var(--space-3) var(--space-4)", fontFamily: "var(--font-mono)", fontSize: "0.75rem" }}>
                        {tx.id.substring(0, 8)}...
                      </td>
                      <td style={{ padding: "var(--space-3) var(--space-4)", fontFamily: "var(--font-mono)", fontSize: "0.75rem" }}>
                        {tx.order_id.substring(0, 8)}...
                      </td>
                      <td style={{ padding: "var(--space-3) var(--space-4)", fontWeight: 600, color: "var(--text-primary)" }}>
                        {tx.currency} {tx.amount}
                      </td>
                      <td style={{ padding: "var(--space-3) var(--space-4)" }}>
                        <span
                          style={{
                            padding: "2px 8px",
                            borderRadius: "var(--radius-sm)",
                            fontSize: "0.75rem",
                            fontWeight: 600,
                            backgroundColor:
                              tx.status === "SUCCESS"
                                ? "var(--status-success-bg)"
                                : "var(--status-danger-bg)",
                            color:
                              tx.status === "SUCCESS"
                                ? "var(--status-success)"
                                : "var(--status-danger)",
                          }}
                        >
                          {tx.status}
                        </span>
                      </td>
                      <td style={{ padding: "var(--space-3) var(--space-4)" }}>
                        {new Date(tx.created_at).toLocaleDateString()}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </section>
      )}
    </main>
  );
};
