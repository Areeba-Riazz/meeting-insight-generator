import React, { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { getInsights } from "../api/client";
import { InsightsViewer } from "../components/InsightsViewer";
import { Header } from "../components/Header";
import { AlertCircle, Loader2, ArrowLeft } from "lucide-react";

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:3000";

export default function InsightsPage() {
  const { meetingId: routeId } = useParams();
  const navigate = useNavigate();
  const [meetingId, setMeetingId] = useState<string | null>(routeId ?? null);
  const [insights, setInsights] = useState<Record<string, any> | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [videoUrl, setVideoUrl] = useState<string | null>(null);

  useEffect(() => {
    setMeetingId(routeId ?? null);
  }, [routeId]);

  useEffect(() => {
    const load = async () => {
      if (!meetingId) return;
      setIsLoading(true);
      setError(null);
      try {
        // Try to get insights (will check in-memory store and storage folder)
        const res = await getInsights(meetingId);
        setInsights(res.insights);
        
        // Try to load video
        try {
          const videoPath = `${API_BASE}/storage/${meetingId}/audio/`;
          const metadataRes = await fetch(`${API_BASE}/storage/${meetingId}/metadata.json`);
          if (metadataRes.ok) {
            const metadata = await metadataRes.json();
            const filename = metadata.file_info?.original_filename;
            if (filename) {
              setVideoUrl(`${videoPath}${filename}`);
            }
          }
        } catch (err) {
          console.error("Failed to load video:", err);
        }
      } catch (err: any) {
        setError(err?.message || "Failed to load insights");
      } finally {
        setIsLoading(false);
      }
    };
    load();
  }, [meetingId]);

  return (
    <div style={{ minHeight: "100vh", position: "relative", overflow: "hidden" }}>
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
          0%, 100% { transform: translateY(0px) translateX(0px) rotate(0deg); }
          33% { transform: translateY(-40px) translateX(30px) rotate(5deg); }
          66% { transform: translateY(30px) translateX(-30px) rotate(-5deg); }
        }
        @keyframes floatReverse {
          0%, 100% { transform: translateY(0px) translateX(0px) scale(1); }
          33% { transform: translateY(30px) translateX(-25px) scale(1.1); }
          66% { transform: translateY(-25px) translateX(25px) scale(0.95); }
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
          background: linear-gradient(to bottom, #fafafa 0%, #f0f9ff 100%);
        }
        .animated-bg::before,
        .animated-bg::after {
          content: '';
          position: absolute;
          border-radius: 50%;
          filter: blur(80px);
          opacity: 0.4;
        }
        .animated-bg::before {
          top: 10%;
          left: 10%;
          width: 500px;
          height: 500px;
          background: radial-gradient(circle, rgba(59, 130, 246, 0.15) 0%, transparent 70%);
          animation: float 20s ease-in-out infinite;
        }
        .animated-bg::after {
          bottom: 10%;
          right: 10%;
          width: 400px;
          height: 400px;
          background: radial-gradient(circle, rgba(139, 92, 246, 0.12) 0%, transparent 70%);
          animation: floatReverse 18s ease-in-out infinite;
        }
        .content-wrapper {
          position: relative;
          z-index: 1;
        }
        .floating-shape {
          position: absolute;
          border-radius: 50%;
          background: rgba(59, 130, 246, 0.08);
          pointer-events: none;
        }
        .shape-1 {
          width: 150px;
          height: 150px;
          top: 15%;
          right: 15%;
          animation: float 15s ease-in-out infinite;
        }
        .shape-2 {
          width: 100px;
          height: 100px;
          bottom: 20%;
          left: 10%;
          background: rgba(139, 92, 246, 0.08);
          animation: floatReverse 12s ease-in-out infinite;
        }
        .shape-3 {
          width: 80px;
          height: 80px;
          top: 40%;
          left: 20%;
          background: rgba(16, 185, 129, 0.08);
          animation: float 18s ease-in-out infinite 2s;
        }
      `}</style>

      <div className="animated-bg">
        <div className="floating-shape shape-1" />
        <div className="floating-shape shape-2" />
        <div className="floating-shape shape-3" />
      </div>

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
            <InsightsViewer insights={insights} videoUrl={videoUrl} />
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