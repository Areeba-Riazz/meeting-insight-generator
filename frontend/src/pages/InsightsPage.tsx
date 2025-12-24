import React, { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { getInsights, getStatus } from "../api/client";
import { InsightsViewer } from "../components/InsightsViewer";
import { Header } from "../components/Header";
import { AlertCircle, Loader2, CheckCircle2, ArrowLeft } from "lucide-react";

type Status = "idle" | "queued" | "processing" | "completed" | `error: ${string}` | string;

export default function InsightsPage() {
  const { meetingId: routeId } = useParams();
  const navigate = useNavigate();
  const [meetingId, setMeetingId] = useState<string | null>(routeId ?? null);
  const [status, setStatus] = useState<Status>("idle");
  const [insights, setInsights] = useState<Record<string, any> | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    setMeetingId(routeId ?? null);
  }, [routeId]);

  useEffect(() => {
    const load = async () => {
      if (!meetingId) return;
      setIsLoading(true);
      setError(null);
      try {
        const st = await getStatus(meetingId);
        setStatus(st.status as Status);
        if (st.status === "completed") {
          const res = await getInsights(meetingId);
          setInsights(res.insights);
        } else {
          setError("Processing not completed yet. Please return to upload page.");
        }
      } catch (err: any) {
        setError(err?.message || "Failed to load insights");
      } finally {
        setIsLoading(false);
      }
    };
    load();
  }, [meetingId]);

  const getStatusColor = () => {
    if (status === "completed") return { bg: "#ecfdf5", border: "#86efac", text: "#065f46" };
    if (status.startsWith("error")) return { bg: "#fef2f2", border: "#fca5a5", text: "#991b1b" };
    if (status === "processing") return { bg: "#eff6ff", border: "#93c5fd", text: "#1e40af" };
    return { bg: "#f9fafb", border: "#e5e7eb", text: "#6b7280" };
  };

  const statusColor = getStatusColor();

  return (
    <div style={{ minHeight: "100vh", background: "#fafafa", position: "relative", overflow: "hidden" }}>
      <style>{`
        @keyframes fadeIn {
          from { opacity: 0; transform: translateY(10px); }
          to { opacity: 1; transform: translateY(0); }
        }
        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
        @keyframes float {
          0%, 100% { transform: translateY(0px) translateX(0px); }
          33% { transform: translateY(-30px) translateX(20px); }
          66% { transform: translateY(20px) translateX(-20px); }
        }
        .animated-bg {
          position: fixed;
          top: 0;
          left: 0;
          right: 0;
          bottom: 0;
          z-index: 0;
          overflow: hidden;
          pointer-events: none;
        }
        .animated-bg::before {
          content: '';
          position: absolute;
          top: -10%;
          left: -10%;
          width: 120%;
          height: 120%;
          background: 
            radial-gradient(circle at 20% 30%, rgba(59, 130, 246, 0.06) 0%, transparent 50%),
            radial-gradient(circle at 80% 70%, rgba(139, 92, 246, 0.06) 0%, transparent 50%),
            radial-gradient(circle at 50% 50%, rgba(16, 185, 129, 0.04) 0%, transparent 50%);
          animation: float 25s ease-in-out infinite;
        }
        .content-wrapper {
          position: relative;
          z-index: 1;
        }
      `}</style>

      <div className="animated-bg" />

      <Header />

      {/* Main Content */}
      <div className="content-wrapper" style={{ maxWidth: 1200, margin: "0 auto", padding: "3rem 1.5rem" }}>

        {/* Hero Section */}
        <div style={{ marginBottom: "2.5rem", animation: "fadeIn 0.4s ease-out" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "1rem", marginBottom: "1rem" }}>
            <button
              onClick={() => navigate("/")}
              style={{
                padding: "0.5rem",
                background: "white",
                border: "1px solid #e5e7eb",
                borderRadius: "8px",
                cursor: "pointer",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                transition: "all 0.2s ease"
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.background = "#f9fafb";
                e.currentTarget.style.borderColor = "#d1d5db";
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.background = "white";
                e.currentTarget.style.borderColor = "#e5e7eb";
              }}
            >
              <ArrowLeft style={{ width: "1.25rem", height: "1.25rem", color: "#374151" }} />
            </button>
            <div>
              <h1 style={{ fontSize: "2rem", fontWeight: 700, color: "#111827", marginBottom: "0.25rem" }}>
                Meeting Insights
              </h1>
              <p style={{ fontSize: "1rem", color: "#6b7280", margin: 0 }}>
                Review transcript, topics, decisions, action items, sentiment, and summary
              </p>
            </div>
          </div>
        </div>

        {/* Status Card */}
        <div style={{
          background: "white",
          border: "1px solid #e5e7eb",
          borderRadius: "16px",
          padding: "2rem",
          boxShadow: "0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03)",
          marginBottom: "1.5rem",
          animation: "fadeIn 0.5s ease-out"
        }}>
          <div style={{ display: "flex", alignItems: "center", gap: "0.75rem", marginBottom: "1.5rem" }}>
            <div style={{
              width: "2rem",
              height: "2rem",
              background: status === "completed"
                ? "linear-gradient(135deg, #10b981 0%, #059669 100%)"
                : status.startsWith("error")
                  ? "linear-gradient(135deg, #ef4444 0%, #dc2626 100%)"
                  : "linear-gradient(135deg, #3b82f6 0%, #2563eb 100%)",
              borderRadius: "8px",
              display: "flex",
              alignItems: "center",
              justifyContent: "center"
            }}>
              {status === "completed" ? (
                <CheckCircle2 style={{ width: "1.125rem", height: "1.125rem", color: "white" }} />
              ) : status.startsWith("error") ? (
                <AlertCircle style={{ width: "1.125rem", height: "1.125rem", color: "white" }} />
              ) : (
                <Loader2 style={{ width: "1.125rem", height: "1.125rem", color: "white", animation: "spin 1s linear infinite" }} />
              )}
            </div>
            <h2 style={{ fontSize: "1.125rem", fontWeight: 600, color: "#111827", margin: 0 }}>
              Processing Status
            </h2>
          </div>

          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", gap: "1.5rem" }}>
            <div>
              <div style={{ fontSize: "0.75rem", fontWeight: 600, color: "#6b7280", textTransform: "uppercase", letterSpacing: "0.05em", marginBottom: "0.5rem" }}>
                Meeting ID
              </div>
              <div style={{
                fontFamily: "monospace",
                fontSize: "0.9rem",
                fontWeight: 600,
                color: "#111827",
                padding: "0.5rem 0.75rem",
                background: "#f9fafb",
                borderRadius: "6px",
                border: "1px solid #e5e7eb"
              }}>
                {meetingId || "—"}
              </div>
            </div>
            <div>
              <div style={{ fontSize: "0.75rem", fontWeight: 600, color: "#6b7280", textTransform: "uppercase", letterSpacing: "0.05em", marginBottom: "0.5rem" }}>
                Status
              </div>
              <div style={{
                display: "inline-block",
                padding: "0.5rem 1rem",
                background: statusColor.bg,
                border: `1px solid ${statusColor.border}`,
                borderRadius: "6px",
                fontSize: "0.875rem",
                fontWeight: 600,
                color: statusColor.text
              }}>
                {status}
              </div>
            </div>
          </div>

          {status !== "completed" && (
            <div style={{ marginTop: "1.5rem" }}>
              <button
                onClick={() => navigate("/")}
                style={{
                  padding: "0.625rem 1.25rem",
                  background: "white",
                  color: "#374151",
                  border: "1px solid #d1d5db",
                  borderRadius: "8px",
                  fontSize: "0.875rem",
                  fontWeight: 600,
                  cursor: "pointer",
                  display: "flex",
                  alignItems: "center",
                  gap: "0.5rem",
                  transition: "all 0.2s ease"
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.background = "#f9fafb";
                  e.currentTarget.style.borderColor = "#9ca3af";
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.background = "white";
                  e.currentTarget.style.borderColor = "#d1d5db";
                }}
              >
                <ArrowLeft style={{ width: "0.875rem", height: "0.875rem" }} />
                Back to Upload
              </button>
            </div>
          )}
        </div>

        {/* Error Card */}
        {error && (
          <div style={{
            background: "#fef2f2",
            border: "1px solid #fecaca",
            borderRadius: "12px",
            padding: "1.25rem",
            marginBottom: "1.5rem",
            display: "flex",
            alignItems: "start",
            gap: "0.75rem",
            animation: "fadeIn 0.5s ease-out"
          }}>
            <AlertCircle style={{ width: "1.25rem", height: "1.25rem", color: "#dc2626", flexShrink: 0, marginTop: "0.125rem" }} />
            <div>
              <div style={{ fontWeight: 600, color: "#991b1b", marginBottom: "0.25rem" }}>Error</div>
              <div style={{ color: "#dc2626", fontSize: "0.875rem" }}>{error}</div>
            </div>
          </div>
        )}

        {/* Insights Card */}
        <div style={{
          background: "white",
          border: "1px solid #e5e7eb",
          borderRadius: "16px",
          padding: "2rem",
          boxShadow: "0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03)",
          animation: "fadeIn 0.6s ease-out"
        }}>
          <div style={{ display: "flex", alignItems: "center", gap: "0.75rem", marginBottom: "1.5rem" }}>
            <div style={{
              width: "2rem",
              height: "2rem",
              background: "linear-gradient(135deg, #8b5cf6 0%, #7c3aed 100%)",
              borderRadius: "8px",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              fontSize: "1rem"
            }}>
              🧠
            </div>
            <h2 style={{ fontSize: "1.125rem", fontWeight: 600, color: "#111827", margin: 0 }}>
              Insights
            </h2>
          </div>

          {isLoading && (
            <div style={{
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              padding: "3rem",
              color: "#6b7280"
            }}>
              <Loader2 style={{ width: "1.5rem", height: "1.5rem", marginRight: "0.75rem", animation: "spin 1s linear infinite" }} />
              <span style={{ fontSize: "0.95rem", fontWeight: 500 }}>Loading insights...</span>
            </div>
          )}

          {!isLoading && insights ? (
            <InsightsViewer insights={insights} />
          ) : (
            !isLoading && (
              <div style={{
                textAlign: "center",
                padding: "3rem 1rem",
                background: "#f9fafb",
                borderRadius: "10px",
                border: "1px dashed #e5e7eb"
              }}>
                <div style={{ fontSize: "2.5rem", marginBottom: "1rem" }}>📊</div>
                <div style={{ fontSize: "1rem", fontWeight: 500, color: "#6b7280", marginBottom: "1rem" }}>
                  No insights available yet
                </div>
                <button
                  onClick={() => navigate("/")}
                  style={{
                    padding: "0.75rem 1.5rem",
                    background: "linear-gradient(135deg, #3b82f6 0%, #2563eb 100%)",
                    color: "white",
                    border: "none",
                    borderRadius: "8px",
                    fontSize: "0.9rem",
                    fontWeight: 600,
                    cursor: "pointer",
                    transition: "transform 0.2s ease, box-shadow 0.2s ease",
                    boxShadow: "0 4px 12px rgba(59, 130, 246, 0.3)"
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.transform = "translateY(-2px)";
                    e.currentTarget.style.boxShadow = "0 6px 16px rgba(59, 130, 246, 0.4)";
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.transform = "translateY(0)";
                    e.currentTarget.style.boxShadow = "0 4px 12px rgba(59, 130, 246, 0.3)";
                  }}
                >
                  Upload Meeting to View Insights
                </button>
              </div>
            )
          )}
        </div>
      </div>
    </div>
  );
}