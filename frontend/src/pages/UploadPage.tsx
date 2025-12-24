import React, { useCallback, useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { uploadMeeting, getStatus } from "../api/client";
import { UploadForm } from "../components/UploadForm";
import { Header } from "../components/Header";
import { ToastContainer } from "../components/Toast";
import { useToast } from "../hooks/useToast";
import { CheckCircle2, Loader2, AlertCircle, ArrowRight, RotateCcw } from "lucide-react";

type Status =
  | "idle"
  | "queued"
  | "processing"
  | "loading_model"
  | "extracting_audio"
  | "transcribing"
  | "diarizing"
  | "saving_transcript"
  | "generating_insights"
  | "saving_results"
  | "completed"
  | `error: ${string}`
  | string;

const STAGES: Array<{ key: Status; label: string; helper: string; icon: string }> = [
  { key: "queued", label: "Queued", helper: "Preparing job", icon: "⏳" },
  { key: "loading_model", label: "Loading Model", helper: "Loading Whisper AI model", icon: "🤖" },
  { key: "extracting_audio", label: "Extracting Audio", helper: "Processing media file", icon: "🎵" },
  { key: "transcribing", label: "Transcribing", helper: "Converting speech to text", icon: "✍️" },
  { key: "diarizing", label: "Identifying Speakers", helper: "Detecting who said what", icon: "👥" },
  { key: "saving_transcript", label: "Saving Transcript", helper: "Storing transcription", icon: "💾" },
  { key: "generating_insights", label: "Analyzing Content", helper: "Running AI analysis", icon: "🧠" },
  { key: "saving_results", label: "Finalizing", helper: "Saving insights", icon: "📊" },
  { key: "completed", label: "Completed", helper: "Ready to view", icon: "✅" },
];

const progressForStatus = (status: Status) => {
  if (status.startsWith("error")) return 10;
  const normalizedStatus = status === "processing" ? "loading_model" : status;
  const order = STAGES.map((s) => s.key);
  const idx = order.indexOf(normalizedStatus);
  const clampedIdx = idx === -1 ? 0 : idx;
  return Math.round((clampedIdx / (order.length - 1)) * 100);
};

const stageForStatus = (status: Status) => {
  const found = STAGES.find((s) => s.key === status);
  if (found) return found.label;
  if (status.startsWith("error")) return "Error";
  if (status === "processing") return "Video Processing";
  return "Idle";
};

const helperForStatus = (status: Status) => {
  const found = STAGES.find((s) => s.key === status);
  if (found) return found.helper;
  if (status === "processing") return "Initializing pipeline";
  return "";
};

export default function UploadPage() {
  const navigate = useNavigate();
  const { toasts, showError, dismissToast } = useToast();
  const [meetingId, setMeetingId] = useState<string | null>(null);
  const [status, setStatus] = useState<Status>("idle");
  const [error, setError] = useState<string | null>(null);
  const [uploadProgress, setUploadProgress] = useState<number>(0);
  const [progress, setProgress] = useState<number>(0);
  const [stage, setStage] = useState<string | null>(null);
  const [isUploading, setIsUploading] = useState(false);

  const handleUpload = useCallback(async (file: File) => {
    setError(null);
    setMeetingId(null);
    setUploadProgress(0);
    setProgress(0);
    setStage(null);
    setIsUploading(true);
    try {
      const resp = await uploadMeeting(file, (progressPercent: number) => {
        setUploadProgress(progressPercent);
      });
      setMeetingId(resp.meeting_id);
      setStatus(resp.status as Status);
      // Upload complete - transition to processing immediately
      setIsUploading(false);
    } catch (err: any) {
      const errorMessage = err?.message || "Upload failed";
      const isConnectionError =
        errorMessage.includes("CONNECTION_ERROR:") ||
        errorMessage.includes("Failed to fetch") ||
        errorMessage.includes("NetworkError") ||
        errorMessage.includes("Network request failed") ||
        err?.name === "TypeError";

      if (isConnectionError) {
        const cleanMessage = errorMessage.replace("CONNECTION_ERROR: ", "");
        showError(cleanMessage || "Backend server is not connected. Please check if the server is running.");
        setStatus("idle");
        setMeetingId(null);
        setIsUploading(false);
      } else {
        setError(errorMessage);
        setStatus("idle");
        setIsUploading(false);
      }
    }
  }, [showError]);

  useEffect(() => {
    if (!meetingId) return;
    let cancelled = false;
    const shouldStop = (s: string) => s.startsWith("completed") || s.startsWith("error");

    const poll = async () => {
      try {
        const resp = await getStatus(meetingId);
        if (cancelled) return;

        console.log(`[Frontend] Polled status: ${resp.status}, progress: ${resp.progress}%, stage: ${resp.stage}`);
        setStatus(resp.status as Status);
        
        // Use backend progress if available, otherwise calculate from status
        if (resp.progress !== undefined && resp.progress !== null) {
          setProgress(resp.progress);
        } else {
          setProgress(progressForStatus(resp.status as Status));
        }
        
        if (resp.stage) {
          setStage(resp.stage);
        }
        if (resp.status === "completed") {
          navigate(`/insights/${meetingId}`);
        } else if (!shouldStop(resp.status)) {
          setTimeout(poll, 1000);  // Poll every 1 second for real-time updates
        }
      } catch (err: any) {
        if (!cancelled) {
          setError(err?.message || "Status check failed");
          setTimeout(poll, 1000);
        }
      }
    };

    // Start polling immediately after upload completes
    poll();
    return () => { cancelled = true; };
  }, [meetingId, navigate]);

  const isProcessing = status !== "idle" && !status.startsWith("error") && status !== "completed";

  return (
    <div style={{ minHeight: "100vh", background: "#fafafa", position: "relative", overflow: "hidden" }}>
      <style>{`
        @keyframes shimmer {
          0% { background-position: -200% 0; }
          100% { background-position: 200% 0; }
        }
        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
        @keyframes fadeIn {
          from { opacity: 0; transform: translateY(10px); }
          to { opacity: 1; transform: translateY(0); }
        }
        @keyframes float {
          0%, 100% { transform: translateY(0px) translateX(0px); }
          33% { transform: translateY(-30px) translateX(20px); }
          66% { transform: translateY(20px) translateX(-20px); }
        }
        @keyframes pulse-glow {
          0%, 100% { box-shadow: 0 0 20px rgba(59, 130, 246, 0.3); }
          50% { box-shadow: 0 0 30px rgba(59, 130, 246, 0.5); }
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
      <ToastContainer toasts={toasts} onDismiss={dismissToast} />

      {/* Main Content */}
      <div className="content-wrapper" style={{ maxWidth: 800, margin: "0 auto", padding: "3rem 1.5rem" }}>
        {!isUploading && !isProcessing && status === "idle" ? (
          <div style={{ animation: "fadeIn 0.4s ease-out" }}>
            {/* Hero Section */}
            <div style={{ textAlign: "center", marginBottom: "3rem" }}>
              <h1 style={{ fontSize: "2.5rem", fontWeight: 700, color: "#111827", marginBottom: "1rem", lineHeight: 1.2 }}>
                Transform Your Meetings<br />into Actionable Insights
              </h1>
              <p style={{ fontSize: "1.125rem", color: "#6b7280", maxWidth: 600, margin: "0 auto" }}>
                Upload your recording and let AI extract key insights, action items, and speaker contributions
              </p>
            </div>

            {/* Upload Card */}
            <div style={{
              background: "white",
              border: "1px solid #e5e7eb",
              borderRadius: "16px",
              padding: "2.5rem",
              boxShadow: "0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03)",
              marginBottom: "2rem"
            }}>
              <UploadForm onUpload={handleUpload} isUploading={isUploading} />

              {error && (
                <div style={{
                  marginTop: "1.5rem",
                  padding: "1rem 1.25rem",
                  background: "#fef2f2",
                  border: "1px solid #fecaca",
                  borderRadius: "10px",
                  display: "flex",
                  alignItems: "start",
                  gap: "0.75rem"
                }}>
                  <AlertCircle style={{ width: "1.25rem", height: "1.25rem", color: "#dc2626", flexShrink: 0, marginTop: "0.125rem" }} />
                  <div style={{ color: "#dc2626", fontSize: "0.9rem", flex: 1 }}>{error}</div>
                </div>
              )}
            </div>

            {/* Feature Pills */}
            <div style={{ display: "flex", flexWrap: "wrap", gap: "0.75rem", justifyContent: "center" }}>
              <div style={{
                padding: "0.625rem 1.25rem",
                background: "#eff6ff",
                border: "1px solid #dbeafe",
                borderRadius: "999px",
                fontSize: "0.875rem",
                fontWeight: 500,
                color: "#1e40af",
                display: "flex",
                alignItems: "center",
                gap: "0.5rem"
              }}>
                <span>⚡</span>
                Fast AI Processing
              </div>
              <div style={{
                padding: "0.625rem 1.25rem",
                background: "#f5f3ff",
                border: "1px solid #e9d5ff",
                borderRadius: "999px",
                fontSize: "0.875rem",
                fontWeight: 500,
                color: "#6b21a8",
                display: "flex",
                alignItems: "center",
                gap: "0.5rem"
              }}>
                <span>👥</span>
                Speaker Identification
              </div>
              <div style={{
                padding: "0.625rem 1.25rem",
                background: "#f0fdf4",
                border: "1px solid #bbf7d0",
                borderRadius: "999px",
                fontSize: "0.875rem",
                fontWeight: 500,
                color: "#15803d",
                display: "flex",
                alignItems: "center",
                gap: "0.5rem"
              }}>
                <span>📊</span>
                Actionable Insights
              </div>
            </div>
          </div>
        ) : (
          <div style={{ animation: "fadeIn 0.4s ease-out" }}>
            <div style={{
              background: "white",
              border: "1px solid #e5e7eb",
              borderRadius: "16px",
              padding: "2.5rem",
              boxShadow: "0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03)"
            }}>

              {/* Status Header */}
              <div style={{ marginBottom: "2rem" }}>
                <div style={{ display: "flex", alignItems: "center", gap: "0.75rem", marginBottom: "0.75rem" }}>
                  {status === "completed" ? (
                    <div style={{
                      width: "2.5rem",
                      height: "2.5rem",
                      background: "linear-gradient(135deg, #10b981 0%, #059669 100%)",
                      borderRadius: "12px",
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "center"
                    }}>
                      <CheckCircle2 style={{ width: "1.5rem", height: "1.5rem", color: "white" }} />
                    </div>
                  ) : status.startsWith("error") ? (
                    <div style={{
                      width: "2.5rem",
                      height: "2.5rem",
                      background: "linear-gradient(135deg, #ef4444 0%, #dc2626 100%)",
                      borderRadius: "12px",
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "center"
                    }}>
                      <AlertCircle style={{ width: "1.5rem", height: "1.5rem", color: "white" }} />
                    </div>
                  ) : (
                    <div style={{
                      width: "2.5rem",
                      height: "2.5rem",
                      background: "linear-gradient(135deg, #3b82f6 0%, #2563eb 100%)",
                      borderRadius: "12px",
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "center",
                      animation: "pulse-glow 2s ease-in-out infinite"
                    }}>
                      <Loader2 style={{ width: "1.5rem", height: "1.5rem", color: "white", animation: "spin 1s linear infinite" }} />
                    </div>
                  )}
                  <h2 style={{ fontSize: "1.5rem", fontWeight: 600, color: "#111827", margin: 0 }}>
                    {isUploading ? "Uploading File..." : stageForStatus(status)}
                  </h2>
                </div>
                {!isUploading && (
                  <p style={{ fontSize: "0.9rem", color: "#6b7280", margin: 0, marginLeft: "3.25rem" }}>
                    {stage || helperForStatus(status)}
                  </p>
                )}
              </div>

              {/* Progress Bar */}
              <div style={{ marginBottom: "2rem" }}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "0.75rem" }}>
                  <span style={{ fontSize: "0.875rem", fontWeight: 500, color: "#6b7280" }}>Progress</span>
                  <span style={{ fontSize: "0.875rem", fontWeight: 600, color: "#3b82f6" }}>
                    {isUploading ? `${uploadProgress}%` : `${Math.round(progress)}%`}
                  </span>
                </div>
                <div style={{ background: "#e5e7eb", height: "10px", borderRadius: "999px", overflow: "hidden" }}>
                  {isUploading ? (
                    <div style={{
                      width: "100%",
                      height: "100%",
                      background: "linear-gradient(90deg, #3b82f6 0%, #8b5cf6 50%, #3b82f6 100%)",
                      backgroundSize: "200% 100%",
                      animation: "shimmer 1.5s ease-in-out infinite"
                    }} />
                  ) : (
                    <div style={{
                      width: isUploading ? `${uploadProgress}%` : `${Math.round(progress)}%`,
                      height: "100%",
                      background: status.startsWith("error")
                        ? "linear-gradient(90deg, #ef4444 0%, #dc2626 100%)"
                        : status === "completed"
                          ? "linear-gradient(90deg, #10b981 0%, #059669 100%)"
                          : "linear-gradient(90deg, #3b82f6 0%, #2563eb 100%)",
                      transition: "width 0.5s ease, background 0.3s ease",
                      boxShadow: "0 0 10px rgba(59, 130, 246, 0.4)"
                    }} />
                  )}
                </div>
              </div>

              {/* Stage Stepper */}
              {!isUploading && isProcessing && (
                <div style={{ marginBottom: "2rem" }}>
                  <div style={{ fontSize: "0.875rem", fontWeight: 600, color: "#374151", marginBottom: "1rem" }}>
                    Processing Stages
                  </div>
                  <div style={{ display: "flex", flexDirection: "column", gap: "0.5rem" }}>
                    {STAGES.filter(s => s.key !== "completed").map((stageItem, idx) => {
                      const currentStageIdx = STAGES.findIndex(s => s.key === status);
                      const isCurrentStage = stageItem.key === status;
                      const isPastStage = idx < currentStageIdx;
                      const isFutureStage = idx > currentStageIdx;
                      
                      return (
                        <div
                          key={stageItem.key}
                          style={{
                            display: "flex",
                            alignItems: "center",
                            gap: "0.75rem",
                            padding: "0.75rem 1rem",
                            background: isCurrentStage ? "#eff6ff" : isPastStage ? "#f0fdf4" : "#fafafa",
                            border: `1px solid ${isCurrentStage ? "#3b82f6" : isPastStage ? "#86efac" : "#e5e7eb"}`,
                            borderRadius: "8px",
                            transition: "all 0.3s ease",
                            opacity: isFutureStage ? 0.5 : 1
                          }}
                        >
                          <div style={{
                            width: "2rem",
                            height: "2rem",
                            display: "flex",
                            alignItems: "center",
                            justifyContent: "center",
                            background: isCurrentStage ? "#3b82f6" : isPastStage ? "#10b981" : "#e5e7eb",
                            borderRadius: "6px",
                            fontSize: "1rem",
                            flexShrink: 0,
                            transition: "all 0.3s ease"
                          }}>
                            {isPastStage ? "✓" : stageItem.icon}
                          </div>
                          <div style={{ flex: 1, minWidth: 0 }}>
                            <div style={{
                              fontSize: "0.875rem",
                              fontWeight: 600,
                              color: isCurrentStage ? "#1e40af" : isPastStage ? "#065f46" : "#6b7280",
                              marginBottom: "0.125rem"
                            }}>
                              {stageItem.label}
                              {isCurrentStage && (
                                <span style={{
                                  marginLeft: "0.5rem",
                                  display: "inline-flex",
                                  alignItems: "center"
                                }}>
                                  <Loader2 style={{
                                    width: "0.875rem",
                                    height: "0.875rem",
                                    animation: "spin 1s linear infinite"
                                  }} />
                                </span>
                              )}
                            </div>
                            <div style={{
                              fontSize: "0.75rem",
                              color: isCurrentStage ? "#3b82f6" : isPastStage ? "#10b981" : "#9ca3af"
                            }}>
                              {isCurrentStage && stage ? stage : stageItem.helper}
                            </div>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              )}

              {/* Meeting ID */}
              {meetingId && (
                <div style={{
                  marginBottom: "2rem",
                  padding: "1rem 1.25rem",
                  background: "#f9fafb",
                  border: "1px solid #e5e7eb",
                  borderRadius: "10px"
                }}>
                  <div style={{ fontSize: "0.75rem", fontWeight: 600, color: "#6b7280", textTransform: "uppercase", letterSpacing: "0.05em", marginBottom: "0.5rem" }}>
                    Meeting ID
                  </div>
                  <div style={{ fontFamily: "monospace", fontSize: "0.9rem", fontWeight: 600, color: "#111827" }}>
                    {meetingId}
                  </div>
                </div>
              )}


              {/* Error State */}
              {status.startsWith("error") && (
                <div style={{
                  padding: "1.5rem",
                  background: "#fef2f2",
                  border: "1px solid #fecaca",
                  borderRadius: "10px",
                  marginBottom: "1rem"
                }}>
                  <div style={{ display: "flex", alignItems: "start", gap: "0.75rem", marginBottom: "1rem" }}>
                    <AlertCircle style={{ width: "1.25rem", height: "1.25rem", color: "#dc2626", flexShrink: 0, marginTop: "0.125rem" }} />
                    <div>
                      <div style={{ fontWeight: 600, color: "#991b1b", marginBottom: "0.25rem" }}>Processing Failed</div>
                      <div style={{ fontSize: "0.875rem", color: "#dc2626" }}>
                        {status.replace("error: ", "")}
                      </div>
                    </div>
                  </div>
                  <button
                    onClick={() => {
                      setStatus("idle");
                      setMeetingId(null);
                      setError(null);
                    }}
                    style={{
                      width: "100%",
                      padding: "0.75rem",
                      background: "linear-gradient(135deg, #ef4444 0%, #dc2626 100%)",
                      color: "white",
                      border: "none",
                      borderRadius: "8px",
                      fontSize: "0.9rem",
                      fontWeight: 600,
                      cursor: "pointer",
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "center",
                      gap: "0.5rem",
                      transition: "transform 0.2s ease, box-shadow 0.2s ease",
                      boxShadow: "0 4px 12px rgba(239, 68, 68, 0.25)"
                    }}
                    onMouseEnter={(e) => {
                      e.currentTarget.style.transform = "translateY(-1px)";
                      e.currentTarget.style.boxShadow = "0 6px 16px rgba(239, 68, 68, 0.3)";
                    }}
                    onMouseLeave={(e) => {
                      e.currentTarget.style.transform = "translateY(0)";
                      e.currentTarget.style.boxShadow = "0 4px 12px rgba(239, 68, 68, 0.25)";
                    }}
                  >
                    <RotateCcw style={{ width: "0.875rem", height: "0.875rem" }} />
                    Try Again
                  </button>
                </div>
              )}

              {/* Completed State */}
              {status === "completed" && meetingId && (
                <div>
                  <div style={{
                    padding: "1.75rem",
                    background: "linear-gradient(135deg, #ecfdf5 0%, #d1fae5 100%)",
                    border: "1px solid #86efac",
                    borderRadius: "12px",
                    textAlign: "center",
                    marginBottom: "1.25rem"
                  }}>
                    <CheckCircle2 style={{ width: "3rem", height: "3rem", color: "#10b981", margin: "0 auto 1rem" }} />
                    <div style={{ fontSize: "1.25rem", fontWeight: 600, color: "#065f46", marginBottom: "0.5rem" }}>
                      Processing Complete
                    </div>
                    <div style={{ fontSize: "0.9rem", color: "#047857" }}>
                      Your transcript is ready to view
                    </div>
                  </div>

                  <div style={{ display: "flex", gap: "0.75rem" }}>
                    <button
                      onClick={() => navigate(`/insights/${meetingId}`)}
                      style={{
                        flex: 1,
                        padding: "0.875rem 1.5rem",
                        background: "linear-gradient(135deg, #3b82f6 0%, #2563eb 100%)",
                        color: "white",
                        border: "none",
                        borderRadius: "10px",
                        fontSize: "0.95rem",
                        fontWeight: 600,
                        cursor: "pointer",
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "center",
                        gap: "0.5rem",
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
                      View Transcript
                      <ArrowRight style={{ width: "1rem", height: "1rem" }} />
                    </button>
                    <button
                      onClick={() => {
                        setStatus("idle");
                        setMeetingId(null);
                        setError(null);
                      }}
                      style={{
                        padding: "0.875rem 1.5rem",
                        background: "white",
                        color: "#374151",
                        border: "1px solid #d1d5db",
                        borderRadius: "10px",
                        fontSize: "0.95rem",
                        fontWeight: 600,
                        cursor: "pointer",
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
                      Upload Another
                    </button>
                  </div>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}