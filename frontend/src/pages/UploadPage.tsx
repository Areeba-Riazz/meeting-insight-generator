import React, { useCallback, useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { uploadMeeting, getStatus } from "../api/client";
import { UploadForm } from "../components/UploadForm";
import { Header } from "../components/Header";
import { ToastContainer } from "../components/Toast";
import { FloatingChat } from "../components/FloatingChat";
import { useToast } from "../hooks/useToast";
import { CheckCircle2, Loader2, AlertCircle, ArrowRight, RotateCcw, ChevronDown, ChevronUp, ArrowLeft } from "lucide-react";

type Status =
  | "idle"
  | "uploading"
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
  { key: "uploading", label: "Uploading", helper: "Saving video file", icon: "📤" },
  { key: "processing", label: "Initializing", helper: "Starting processing pipeline", icon: "⚙️" },
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
  const order = STAGES.map((s) => s.key);
  const idx = order.indexOf(status);
  const clampedIdx = idx === -1 ? 0 : idx;
  return Math.round((clampedIdx / (order.length - 1)) * 100);
};

const stageForStatus = (status: Status) => {
  const found = STAGES.find((s) => s.key === status);
  if (found) return found.label;
  if (status.startsWith("error")) return "Error";
  return "Processing";
};

const helperForStatus = (status: Status) => {
  const found = STAGES.find((s) => s.key === status);
  if (found) return found.helper;
  return "";
};

export default function UploadPage() {
  const navigate = useNavigate();
  const { projectId } = useParams<{ projectId?: string }>();
  const { toasts, showError, dismissToast } = useToast();
  const [meetingId, setMeetingId] = useState<string | null>(null);
  const [status, setStatus] = useState<Status>("idle");
  const [error, setError] = useState<string | null>(null);
  const [progress, setProgress] = useState<number>(0);
  const [stage, setStage] = useState<string | null>(null);
  const [showDetails, setShowDetails] = useState<boolean>(false);
  const [isRequestInProgress, setIsRequestInProgress] = useState<boolean>(false);

  const handleUpload = useCallback(async (file: File) => {
    console.log("[UploadPage] Starting upload for file:", file.name);
    setError(null);
    setMeetingId(null);
    setProgress(0);
    setStage(null);
    setShowDetails(false);
    setIsRequestInProgress(true);
    
    try {
      console.log("[UploadPage] Calling uploadMeeting API...", projectId ? `with projectId: ${projectId}` : "");
      const resp = await uploadMeeting(file, projectId);
      console.log("[UploadPage] Upload response received:", resp);
      
      setMeetingId(resp.meeting_id);
      setStatus(resp.status as Status);
      setIsRequestInProgress(false);
      // Polling will start automatically via useEffect
    } catch (err: any) {
      console.error("[UploadPage] Upload error:", err);
      setIsRequestInProgress(false);
      
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
      } else {
        setError(errorMessage);
        setStatus("idle");
      }
    }
  }, [showError]);

  useEffect(() => {
    if (!meetingId) return;
    let cancelled = false;
    let pollCount = 0;
    const maxConsecutiveErrors = 5;
    let consecutiveErrors = 0;
    const shouldStop = (s: string) => s.startsWith("completed") || s.startsWith("error");

    const poll = async () => {
      try {
        const resp = await getStatus(meetingId);
        if (cancelled) return;

        pollCount++;
        consecutiveErrors = 0; // Reset error count on success
        
        console.log(`[Frontend] Poll #${pollCount} - Status: ${resp.status}, Progress: ${resp.progress}%, Stage: ${resp.stage}`);
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
          // Navigate based on whether we have a projectId
          if (projectId) {
            navigate(`/projects/${projectId}`);
          } else {
            navigate(`/insights/${meetingId}`);
          }
        } else if (!shouldStop(resp.status)) {
          setTimeout(poll, 1000);  // Poll every 1 second for real-time updates
        }
      } catch (err: any) {
        if (!cancelled) {
          consecutiveErrors++;
          console.error(`[Frontend] Status poll error (${consecutiveErrors}/${maxConsecutiveErrors}):`, err);
          
          if (consecutiveErrors >= maxConsecutiveErrors) {
            setError(`Failed to fetch status after ${maxConsecutiveErrors} attempts. Please refresh the page.`);
            setStatus("idle");
          } else {
            // Continue polling despite errors (might be temporary network issue)
            setTimeout(poll, 2000);  // Slightly longer delay on error
          }
        }
      }
    };

    // Start polling immediately
    poll();
    return () => { cancelled = true; };
  }, [meetingId, navigate, projectId]);

  const isUploading = status === "uploading" || isRequestInProgress;
  const isProcessing = status !== "idle" && status !== "uploading" && !status.startsWith("error") && status !== "completed" && !isRequestInProgress;

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
          0%, 100% { transform: translateY(0px) translateX(0px) rotate(0deg); }
          33% { transform: translateY(-40px) translateX(30px) rotate(5deg); }
          66% { transform: translateY(30px) translateX(-30px) rotate(-5deg); }
        }
        @keyframes floatReverse {
          0%, 100% { transform: translateY(0px) translateX(0px) scale(1); }
          33% { transform: translateY(30px) translateX(-25px) scale(1.1); }
          66% { transform: translateY(-25px) translateX(25px) scale(0.95); }
        }
        @keyframes pulse {
          0%, 100% { opacity: 0.3; }
          50% { opacity: 0.5; }
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
      <ToastContainer toasts={toasts} onDismiss={dismissToast} />

      {/* Main Content */}
      <div className="content-wrapper" style={{ maxWidth: 800, margin: "0 auto", padding: "3rem 1.5rem" }}>
        {/* Show back button if accessed from project */}
        {projectId && (
          <button
            onClick={() => navigate(`/projects/${projectId}`)}
            style={{
              padding: "0.5rem",
              background: "white",
              border: "1px solid #e5e7eb",
              borderRadius: "8px",
              cursor: "pointer",
              display: "inline-flex",
              alignItems: "center",
              gap: "0.5rem",
              marginBottom: "1.5rem",
              transition: "all 0.2s ease",
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
            <ArrowLeft style={{ width: "1rem", height: "1rem", color: "#374151" }} />
            <span style={{ fontSize: "0.875rem", color: "#374151", fontWeight: 500 }}>Back to Project</span>
          </button>
        )}

        {!isUploading && !isProcessing && status === "idle" ? (
          <div style={{ animation: "fadeIn 0.4s ease-out" }}>
            {/* Hero Section - only show if not from project */}
            {!projectId && (
              <div style={{ textAlign: "center", marginBottom: "2.5rem" }}>
                <div style={{ 
                  display: "inline-block", 
                  padding: "0.375rem 0.875rem", 
                  background: "linear-gradient(135deg, #eff6ff 0%, #f5f3ff 100%)",
                  border: "1px solid #dbeafe",
                  borderRadius: "999px",
                  fontSize: "0.75rem",
                  fontWeight: 600,
                  color: "#3b82f6",
                  marginBottom: "1rem",
                  letterSpacing: "0.05em",
                  textTransform: "uppercase"
                }}>
                  ✨ AI-Powered Analysis
                </div>
                <h1 style={{ 
                  fontSize: "2.25rem", 
                  fontWeight: 700, 
                  background: "linear-gradient(135deg, #111827 0%, #4b5563 100%)",
                  WebkitBackgroundClip: "text",
                  WebkitTextFillColor: "transparent",
                  backgroundClip: "text",
                  marginBottom: "0.75rem", 
                  lineHeight: 1.2 
                }}>
                  Transform Meetings into Insights
                </h1>
                <p style={{ 
                  fontSize: "1rem", 
                  color: "#6b7280", 
                  maxWidth: 480, 
                  margin: "0 auto",
                  lineHeight: 1.6
                }}>
                  Upload your recording and let AI extract key insights, action items, and speaker contributions automatically
                </p>
              </div>
            )}

            {/* Upload Card */}
            <div style={{
              background: "rgba(255, 255, 255, 0.8)",
              backdropFilter: "blur(10px)",
              border: "1px solid rgba(229, 231, 235, 0.5)",
              borderRadius: "20px",
              padding: "2.5rem",
              boxShadow: "0 10px 40px rgba(0, 0, 0, 0.08), 0 2px 8px rgba(0, 0, 0, 0.04)",
              marginBottom: projectId ? "0" : "2rem"
            }}>
              {projectId && (
                <div style={{ marginBottom: "1.5rem" }}>
                  <h2 style={{ fontSize: "1.5rem", fontWeight: 600, color: "#111827", marginBottom: "0.5rem" }}>
                    Upload Meeting
                  </h2>
                  <p style={{ fontSize: "0.875rem", color: "#6b7280" }}>
                    Upload an audio or video file to process and add to this project
                  </p>
                </div>
              )}

              <UploadForm onUpload={handleUpload} isUploading={isRequestInProgress} />

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

            {/* Feature Pills - only show if not from project */}
            {!projectId && (
              <div style={{ display: "flex", flexWrap: "wrap", gap: "0.625rem", justifyContent: "center" }}>
                <div style={{
                  padding: "0.5rem 1rem",
                  background: "rgba(239, 246, 255, 0.6)",
                  backdropFilter: "blur(8px)",
                  border: "1px solid rgba(219, 234, 254, 0.8)",
                  borderRadius: "999px",
                  fontSize: "0.8125rem",
                  fontWeight: 500,
                  color: "#1e40af",
                  display: "flex",
                  alignItems: "center",
                  gap: "0.375rem"
                }}>
                  <span>⚡</span>
                  Fast AI Processing
                </div>
                <div style={{
                  padding: "0.5rem 1rem",
                  background: "rgba(245, 243, 255, 0.6)",
                  backdropFilter: "blur(8px)",
                  border: "1px solid rgba(233, 213, 255, 0.8)",
                  borderRadius: "999px",
                  fontSize: "0.8125rem",
                  fontWeight: 500,
                  color: "#6b21a8",
                  display: "flex",
                  alignItems: "center",
                  gap: "0.375rem"
                }}>
                  <span>👥</span>
                  Speaker Identification
                </div>
                <div style={{
                  padding: "0.5rem 1rem",
                  background: "rgba(240, 253, 244, 0.6)",
                  backdropFilter: "blur(8px)",
                  border: "1px solid rgba(187, 247, 208, 0.8)",
                  borderRadius: "999px",
                  fontSize: "0.8125rem",
                  fontWeight: 500,
                  color: "#15803d",
                  display: "flex",
                  alignItems: "center",
                  gap: "0.375rem"
                }}>
                  <span>📊</span>
                  Actionable Insights
                </div>
              </div>
            )}
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
                    {isRequestInProgress && !meetingId ? "Uploading File..." : stageForStatus(status)}
                  </h2>
                </div>
                <p style={{ fontSize: "1rem", color: "#6b7280", margin: 0, marginLeft: "3.25rem", fontWeight: 500 }}>
                  {isRequestInProgress && !meetingId ? "Sending file to server" : (stage || helperForStatus(status))}
                </p>
              </div>

              {/* Progress Bar */}
              <div style={{ marginBottom: "2rem" }}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "0.75rem" }}>
                  <span style={{ fontSize: "0.875rem", fontWeight: 500, color: "#6b7280" }}>Progress</span>
                  <span style={{ fontSize: "0.875rem", fontWeight: 600, color: "#3b82f6" }}>
                    {isRequestInProgress && !meetingId ? "..." : `${Math.round(progress)}%`}
                  </span>
                </div>
                <div style={{ background: "#e5e7eb", height: "10px", borderRadius: "999px", overflow: "hidden" }}>
                  {isRequestInProgress && !meetingId ? (
                    <div style={{
                      width: "100%",
                      height: "100%",
                      background: "linear-gradient(90deg, #3b82f6 0%, #8b5cf6 50%, #3b82f6 100%)",
                      backgroundSize: "200% 100%",
                      animation: "shimmer 1.5s ease-in-out infinite"
                    }} />
                  ) : (
                    <div style={{
                      width: `${Math.round(progress)}%`,
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

              {/* Accordion for Detailed Substeps */}
              {(isUploading || isProcessing) && (
                <div style={{ marginBottom: "2rem" }}>
                  <button
                    onClick={() => setShowDetails(!showDetails)}
                    style={{
                      width: "100%",
                      padding: "0.875rem 1rem",
                      background: "#f9fafb",
                      border: "1px solid #e5e7eb",
                      borderRadius: "8px",
                      fontSize: "0.875rem",
                      fontWeight: 600,
                      color: "#374151",
                      cursor: "pointer",
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "space-between",
                      transition: "all 0.2s ease"
                    }}
                    onMouseEnter={(e) => {
                      e.currentTarget.style.background = "#f3f4f6";
                      e.currentTarget.style.borderColor = "#d1d5db";
                    }}
                    onMouseLeave={(e) => {
                      e.currentTarget.style.background = "#f9fafb";
                      e.currentTarget.style.borderColor = "#e5e7eb";
                    }}
                  >
                    <span>{showDetails ? "Hide" : "Show"} Processing Details</span>
                    {showDetails ? (
                      <ChevronUp style={{ width: "1rem", height: "1rem" }} />
                    ) : (
                      <ChevronDown style={{ width: "1rem", height: "1rem" }} />
                    )}
                  </button>

                  {showDetails && (
                    <div style={{ 
                      marginTop: "1rem",
                      padding: "1rem",
                      background: "#fafafa",
                      border: "1px solid #e5e7eb",
                      borderRadius: "8px",
                      animation: "fadeIn 0.3s ease-out"
                    }}>
                      <div style={{ fontSize: "0.75rem", fontWeight: 600, color: "#6b7280", textTransform: "uppercase", letterSpacing: "0.05em", marginBottom: "0.75rem" }}>
                        All Processing Stages
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
                                padding: "0.625rem 0.875rem",
                                background: isCurrentStage ? "#eff6ff" : isPastStage ? "#f0fdf4" : "#ffffff",
                                border: `1px solid ${isCurrentStage ? "#3b82f6" : isPastStage ? "#86efac" : "#e5e7eb"}`,
                                borderRadius: "6px",
                                transition: "all 0.3s ease",
                                opacity: isFutureStage ? 0.5 : 1
                              }}
                            >
                              <div style={{
                                width: "1.75rem",
                                height: "1.75rem",
                                display: "flex",
                                alignItems: "center",
                                justifyContent: "center",
                                background: isCurrentStage ? "#3b82f6" : isPastStage ? "#10b981" : "#e5e7eb",
                                borderRadius: "6px",
                                fontSize: "0.875rem",
                                flexShrink: 0,
                                transition: "all 0.3s ease"
                              }}>
                                {isPastStage ? "✓" : stageItem.icon}
                              </div>
                              <div style={{ flex: 1, minWidth: 0 }}>
                                <div style={{
                                  fontSize: "0.8rem",
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
                                        width: "0.75rem",
                                        height: "0.75rem",
                                        animation: "spin 1s linear infinite"
                                      }} />
                                    </span>
                                  )}
                                </div>
                                <div style={{
                                  fontSize: "0.7rem",
                                  color: isCurrentStage ? "#3b82f6" : isPastStage ? "#10b981" : "#9ca3af"
                                }}>
                                  {stageItem.helper}
                                </div>
                              </div>
                            </div>
                          );
                        })}
                      </div>
                    </div>
                  )}
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
                      onClick={() => {
                        if (projectId) {
                          navigate(`/projects/${projectId}`);
                        } else {
                          navigate(`/insights/${meetingId}`);
                        }
                      }}
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
      <FloatingChat context={projectId ? `Uploading meeting to project` : "Uploading a new meeting"} />
    </div>
  );
}