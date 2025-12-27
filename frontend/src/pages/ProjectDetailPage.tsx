import React, { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { Header } from "../components/Header";
import { ToastContainer } from "../components/Toast";
import { FloatingChat } from "../components/FloatingChat";
import { useToast } from "../hooks/useToast";
import {
  getProject,
  getProjectMeetings,
  deleteProjectMeeting,
} from "../api/client";
import type { Project, ProjectMeeting } from "../types/api";
import {
  ArrowLeft,
  Plus,
  Trash2,
  Loader2,
  Clock,
  CheckCircle2,
  AlertCircle,
  FileVideo,
} from "lucide-react";

export default function ProjectDetailPage() {
  const { projectId } = useParams<{ projectId: string }>();
  const navigate = useNavigate();
  const { toasts, showError, showSuccess, dismissToast } = useToast();
  const [project, setProject] = useState<Project | null>(null);
  const [meetings, setMeetings] = useState<ProjectMeeting[]>([]);
  const [loading, setLoading] = useState(true);
  const [deletingId, setDeletingId] = useState<string | null>(null);

  useEffect(() => {
    if (projectId) {
      loadProject();
      loadMeetings();
    }
  }, [projectId]);

  const loadProject = async () => {
    if (!projectId) return;
    try {
      const data = await getProject(projectId);
      setProject(data);
    } catch (err: any) {
      showError(err?.message || "Failed to load project");
    }
  };

  const loadMeetings = async () => {
    if (!projectId) return;
    setLoading(true);
    try {
      const response = await getProjectMeetings(projectId);
      setMeetings(response.meetings);
    } catch (err: any) {
      showError(err?.message || "Failed to load meetings");
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteMeeting = async (meetingId: string, meetingName: string) => {
    if (!projectId) return;
    if (!confirm(`Are you sure you want to delete "${meetingName}"?`)) {
      return;
    }

    setDeletingId(meetingId);
    try {
      await deleteProjectMeeting(projectId, meetingId);
      showSuccess("Meeting deleted successfully");
      await loadMeetings();
    } catch (err: any) {
      showError(err?.message || "Failed to delete meeting");
    } finally {
      setDeletingId(null);
    }
  };

  const formatDate = (dateString: string) => {
    try {
      const date = new Date(dateString);
      return date.toLocaleDateString("en-US", {
        month: "short",
        day: "numeric",
        year: "numeric",
        hour: "2-digit",
        minute: "2-digit",
      });
    } catch {
      return dateString;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case "completed":
        return "#10b981";
      case "processing":
      case "uploading":
        return "#3b82f6";
      case "error":
        return "#ef4444";
      default:
        return "#6b7280";
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case "completed":
        return <CheckCircle2 style={{ width: "1rem", height: "1rem" }} />;
      case "error":
        return <AlertCircle style={{ width: "1rem", height: "1rem" }} />;
      default:
        return <Loader2 style={{ width: "1rem", height: "1rem", animation: "spin 1s linear infinite" }} />;
    }
  };

  if (!projectId) {
    return <div>Invalid project ID</div>;
  }

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
        @keyframes shimmer {
          0% { background-position: -200% 0; }
          100% { background-position: 200% 0; }
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
      <ToastContainer toasts={toasts} onDismiss={dismissToast} />

      {/* Main Content */}
      <div className="content-wrapper" style={{ maxWidth: 1200, margin: "0 auto", padding: "3rem 1.5rem" }}>
        {/* Header Section */}
        <div style={{ marginBottom: "2.5rem", animation: "fadeIn 0.4s ease-out" }}>
          <button
            onClick={() => navigate("/projects")}
            style={{
              padding: "0.5rem",
              background: "white",
              border: "1px solid #e5e7eb",
              borderRadius: "8px",
              cursor: "pointer",
              display: "inline-flex",
              alignItems: "center",
              gap: "0.5rem",
              marginBottom: "1rem",
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
            <span style={{ fontSize: "0.875rem", color: "#374151", fontWeight: 500 }}>Back to Projects</span>
          </button>

          <div style={{ display: "flex", alignItems: "start", justifyContent: "space-between", marginBottom: "1rem" }}>
            <div>
              {project ? (
                <>
                  <h1 style={{
                    fontSize: "2.25rem",
                    fontWeight: 700,
                    background: "linear-gradient(135deg, #111827 0%, #4b5563 100%)",
                    WebkitBackgroundClip: "text",
                    WebkitTextFillColor: "transparent",
                    backgroundClip: "text",
                    marginBottom: "0.5rem",
                    lineHeight: 1.2,
                  }}>
                    {project.name}
                  </h1>
                  {project.description && (
                    <p style={{ fontSize: "1rem", color: "#6b7280", marginBottom: "0.5rem" }}>
                      {project.description}
                    </p>
                  )}
                  <div style={{ fontSize: "0.875rem", color: "#9ca3af" }}>
                    {project.meetings_count || 0} {project.meetings_count === 1 ? "meeting" : "meetings"}
                  </div>
                </>
              ) : (
                <div style={{ display: "flex", alignItems: "center", gap: "0.75rem" }}>
                  <Loader2 style={{ width: "1.5rem", height: "1.5rem", animation: "spin 1s linear infinite", color: "#6b7280" }} />
                  <span style={{ fontSize: "1.125rem", color: "#6b7280" }}>Loading project...</span>
                </div>
              )}
            </div>
            <button
              onClick={() => navigate(`/projects/${projectId}/upload`)}
              style={{
                padding: "0.75rem 1.5rem",
                background: "linear-gradient(135deg, #3b82f6 0%, #2563eb 100%)",
                color: "white",
                border: "none",
                borderRadius: "10px",
                fontSize: "0.95rem",
                fontWeight: 600,
                cursor: "pointer",
                display: "flex",
                alignItems: "center",
                gap: "0.5rem",
                transition: "transform 0.2s ease, box-shadow 0.2s ease",
                boxShadow: "0 4px 12px rgba(59, 130, 246, 0.3)",
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
              <Plus style={{ width: "1rem", height: "1rem" }} />
              Upload Meeting
            </button>
          </div>
        </div>

        {/* Meetings List */}
        {loading ? (
          <div style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            padding: "4rem 2rem",
            color: "#6b7280",
          }}>
            <Loader2 style={{ width: "1.5rem", height: "1.5rem", marginRight: "0.75rem", animation: "spin 1s linear infinite" }} />
            <span style={{ fontSize: "0.95rem", fontWeight: 500 }}>Loading meetings...</span>
          </div>
        ) : meetings.length === 0 ? (
          <div style={{
            background: "white",
            border: "1px solid #e5e7eb",
            borderRadius: "16px",
            padding: "4rem 2rem",
            textAlign: "center",
            animation: "fadeIn 0.4s ease-out",
          }}>
            <div style={{ fontSize: "4rem", marginBottom: "1rem" }}>📹</div>
            <h2 style={{ fontSize: "1.5rem", fontWeight: 600, color: "#111827", marginBottom: "0.5rem" }}>
              No meetings yet
            </h2>
            <p style={{ fontSize: "1rem", color: "#6b7280", marginBottom: "2rem" }}>
              Upload your first meeting to get started
            </p>
            <button
              onClick={() => navigate(`/projects/${projectId}/upload`)}
              style={{
                padding: "0.75rem 1.5rem",
                background: "linear-gradient(135deg, #3b82f6 0%, #2563eb 100%)",
                color: "white",
                border: "none",
                borderRadius: "8px",
                fontSize: "0.9rem",
                fontWeight: 600,
                cursor: "pointer",
                display: "inline-flex",
                alignItems: "center",
                gap: "0.5rem",
                transition: "transform 0.2s ease, box-shadow 0.2s ease",
                boxShadow: "0 4px 12px rgba(59, 130, 246, 0.3)",
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
              <Plus style={{ width: "1rem", height: "1rem" }} />
              Upload Meeting
            </button>
          </div>
        ) : (
          <div style={{
            display: "flex",
            flexDirection: "column",
            gap: "1rem",
            animation: "fadeIn 0.4s ease-out",
          }}>
            {meetings.map((meeting) => (
              <div
                key={meeting.id}
                onClick={() => {
                  if (meeting.has_insights) {
                    navigate(`/insights/${meeting.id}`);
                  }
                }}
                style={{
                  background: "white",
                  border: "1px solid #e5e7eb",
                  borderRadius: "12px",
                  padding: "1.5rem",
                  cursor: meeting.has_insights ? "pointer" : "default",
                  transition: "all 0.2s ease",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "space-between",
                  boxShadow: "0 1px 3px rgba(0, 0, 0, 0.05)",
                }}
                onMouseEnter={(e) => {
                  if (meeting.has_insights) {
                    e.currentTarget.style.transform = "translateX(4px)";
                    e.currentTarget.style.boxShadow = "0 4px 12px rgba(0, 0, 0, 0.1)";
                    e.currentTarget.style.borderColor = "#d1d5db";
                  }
                }}
                onMouseLeave={(e) => {
                  if (meeting.has_insights) {
                    e.currentTarget.style.transform = "translateX(0)";
                    e.currentTarget.style.boxShadow = "0 1px 3px rgba(0, 0, 0, 0.05)";
                    e.currentTarget.style.borderColor = "#e5e7eb";
                  }
                }}
              >
                <div style={{ display: "flex", alignItems: "center", gap: "1rem", flex: 1 }}>
                  <div style={{
                    width: "3rem",
                    height: "3rem",
                    background: meeting.has_insights
                      ? "linear-gradient(135deg, #10b981 0%, #059669 100%)"
                      : "linear-gradient(135deg, #6b7280 0%, #4b5563 100%)",
                    borderRadius: "10px",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    flexShrink: 0,
                  }}>
                    <FileVideo style={{ width: "1.5rem", height: "1.5rem", color: "white" }} />
                  </div>
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <h3 style={{
                      fontSize: "1.125rem",
                      fontWeight: 600,
                      color: "#111827",
                      marginBottom: "0.25rem",
                      overflow: "hidden",
                      textOverflow: "ellipsis",
                      whiteSpace: "nowrap",
                    }}>
                      {meeting.meeting_name}
                    </h3>
                    <div style={{ display: "flex", alignItems: "center", gap: "1rem", flexWrap: "wrap" }}>
                      <div style={{
                        display: "flex",
                        alignItems: "center",
                        gap: "0.5rem",
                        fontSize: "0.875rem",
                        color: getStatusColor(meeting.status),
                        fontWeight: 500,
                      }}>
                        {getStatusIcon(meeting.status)}
                        <span style={{ textTransform: "capitalize" }}>{meeting.status}</span>
                      </div>
                      <div style={{
                        display: "flex",
                        alignItems: "center",
                        gap: "0.25rem",
                        fontSize: "0.875rem",
                        color: "#6b7280",
                      }}>
                        <Clock style={{ width: "0.875rem", height: "0.875rem" }} />
                        {formatDate(meeting.upload_timestamp)}
                      </div>
                    </div>
                  </div>
                </div>
                <div style={{ display: "flex", alignItems: "center", gap: "0.75rem" }}>
                  {meeting.has_insights && (
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        navigate(`/insights/${meeting.id}`);
                      }}
                      style={{
                        padding: "0.5rem 1rem",
                        background: "#eff6ff",
                        color: "#3b82f6",
                        border: "1px solid #bfdbfe",
                        borderRadius: "6px",
                        fontSize: "0.875rem",
                        fontWeight: 500,
                        cursor: "pointer",
                        transition: "all 0.2s ease",
                      }}
                      onMouseEnter={(e) => {
                        e.currentTarget.style.background = "#dbeafe";
                        e.currentTarget.style.borderColor = "#93c5fd";
                      }}
                      onMouseLeave={(e) => {
                        e.currentTarget.style.background = "#eff6ff";
                        e.currentTarget.style.borderColor = "#bfdbfe";
                      }}
                    >
                      View Insights
                    </button>
                  )}
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      handleDeleteMeeting(meeting.id, meeting.meeting_name);
                    }}
                    disabled={deletingId === meeting.id}
                    style={{
                      padding: "0.5rem",
                      background: deletingId === meeting.id ? "#f3f4f6" : "transparent",
                      border: "none",
                      borderRadius: "6px",
                      cursor: deletingId === meeting.id ? "not-allowed" : "pointer",
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "center",
                      transition: "background 0.2s ease",
                      opacity: deletingId === meeting.id ? 0.5 : 1,
                    }}
                    onMouseEnter={(e) => {
                      if (deletingId !== meeting.id) {
                        e.currentTarget.style.background = "#fef2f2";
                      }
                    }}
                    onMouseLeave={(e) => {
                      if (deletingId !== meeting.id) {
                        e.currentTarget.style.background = "transparent";
                      }
                    }}
                  >
                    {deletingId === meeting.id ? (
                      <Loader2 style={{ width: "1rem", height: "1rem", color: "#dc2626", animation: "spin 1s linear infinite" }} />
                    ) : (
                      <Trash2 style={{ width: "1rem", height: "1rem", color: "#dc2626" }} />
                    )}
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
      <FloatingChat context={project ? `Viewing project: ${project.name}. ${project.description || ""}` : undefined} />
    </div>
  );
}

