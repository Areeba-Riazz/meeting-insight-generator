import React, { useState, useEffect } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import { 
  FolderOpen, 
  ChevronRight, 
  ChevronDown, 
  FileVideo, 
  Loader2,
  X,
  Home
} from "lucide-react";
import { listProjects, getProjectMeetings } from "../api/client";
import type { Project, ProjectMeeting } from "../types/api";

interface SidebarProps {
  isOpen: boolean;
  onClose: () => void;
}

export function Sidebar({ isOpen, onClose }: SidebarProps) {
  const navigate = useNavigate();
  const location = useLocation();
  const [projects, setProjects] = useState<Project[]>([]);
  const [expandedProjects, setExpandedProjects] = useState<Set<string>>(new Set());
  const [meetingsByProject, setMeetingsByProject] = useState<Record<string, ProjectMeeting[]>>({});
  const [loadingProjects, setLoadingProjects] = useState(false);
  const [loadingMeetings, setLoadingMeetings] = useState<Set<string>>(new Set());

  useEffect(() => {
    if (isOpen) {
      loadProjects();
    }
  }, [isOpen]);

  const loadProjects = async () => {
    setLoadingProjects(true);
    try {
      const response = await listProjects();
      setProjects(response.projects);
    } catch (err) {
      console.error("Failed to load projects:", err);
    } finally {
      setLoadingProjects(false);
    }
  };

  const toggleProject = async (projectId: string) => {
    const newExpanded = new Set(expandedProjects);
    if (newExpanded.has(projectId)) {
      newExpanded.delete(projectId);
    } else {
      newExpanded.add(projectId);
      // Load meetings if not already loaded
      if (!meetingsByProject[projectId]) {
        await loadMeetings(projectId);
      }
    }
    setExpandedProjects(newExpanded);
  };

  const loadMeetings = async (projectId: string) => {
    setLoadingMeetings(prev => new Set(prev).add(projectId));
    try {
      const response = await getProjectMeetings(projectId);
      setMeetingsByProject(prev => ({
        ...prev,
        [projectId]: response.meetings
      }));
    } catch (err) {
      console.error(`Failed to load meetings for project ${projectId}:`, err);
    } finally {
      setLoadingMeetings(prev => {
        const next = new Set(prev);
        next.delete(projectId);
        return next;
      });
    }
  };

  const formatDate = (dateString: string) => {
    try {
      const date = new Date(dateString);
      return date.toLocaleDateString("en-US", {
        month: "short",
        day: "numeric",
        year: "numeric",
      });
    } catch {
      return dateString;
    }
  };

  const isProjectActive = (projectId: string) => {
    return location.pathname === `/projects/${projectId}`;
  };

  const isMeetingActive = (meetingId: string) => {
    return location.pathname === `/insights/${meetingId}`;
  };

  return (
    <>
      <style>{`
        @keyframes slideIn {
          from { transform: translateX(-100%); }
          to { transform: translateX(0); }
        }
        @keyframes fadeIn {
          from { opacity: 0; }
          to { opacity: 1; }
        }
      `}</style>

      {/* Overlay */}
      {isOpen && (
        <div
          onClick={onClose}
          style={{
            position: "fixed",
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            background: "rgba(0, 0, 0, 0.5)",
            zIndex: 998,
            animation: "fadeIn 0.2s ease-out",
          }}
        />
      )}

      {/* Sidebar */}
      <aside
        style={{
          position: "fixed",
          top: 0,
          left: 0,
          height: "100vh",
          width: "320px",
          background: "white",
          boxShadow: isOpen ? "4px 0 24px rgba(0, 0, 0, 0.15)" : "none",
          transform: isOpen ? "translateX(0)" : "translateX(-100%)",
          transition: "transform 0.3s ease, box-shadow 0.3s ease",
          zIndex: 999,
          overflowY: "auto",
          display: "flex",
          flexDirection: "column",
        }}
      >
        {/* Header */}
        <div style={{
          padding: "1.5rem",
          borderBottom: "1px solid #e5e7eb",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          background: "linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%)",
        }}>
          <div style={{ display: "flex", alignItems: "center", gap: "0.75rem" }}>
            <div style={{
              width: "2rem",
              height: "2rem",
              background: "linear-gradient(135deg, #3b82f6 0%, #2563eb 100%)",
              borderRadius: "6px",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              fontWeight: 700,
              fontSize: "0.875rem",
              color: "white",
            }}>
              MI
            </div>
            <div>
              <div style={{ fontWeight: 700, fontSize: "0.95rem", color: "#111827" }}>
                Navigation
              </div>
              <div style={{ fontSize: "0.75rem", color: "#6b7280" }}>
                Projects & Meetings
              </div>
            </div>
          </div>
          <button
            onClick={onClose}
            style={{
              padding: "0.5rem",
              background: "transparent",
              border: "none",
              borderRadius: "6px",
              cursor: "pointer",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              transition: "background 0.2s ease",
            }}
            onMouseEnter={(e) => e.currentTarget.style.background = "#f3f4f6"}
            onMouseLeave={(e) => e.currentTarget.style.background = "transparent"}
          >
            <X style={{ width: "1.25rem", height: "1.25rem", color: "#6b7280" }} />
          </button>
        </div>

        {/* Content */}
        <div style={{ flex: 1, overflowY: "auto", padding: "1rem" }}>
          {/* Home Button */}
          <button
            onClick={() => {
              navigate("/projects");
              onClose();
            }}
            style={{
              width: "100%",
              padding: "0.75rem 1rem",
              background: location.pathname === "/projects" ? "#eff6ff" : "transparent",
              border: "none",
              borderRadius: "8px",
              cursor: "pointer",
              display: "flex",
              alignItems: "center",
              gap: "0.75rem",
              marginBottom: "1rem",
              transition: "all 0.2s ease",
              color: location.pathname === "/projects" ? "#3b82f6" : "#374151",
              fontWeight: location.pathname === "/projects" ? 600 : 500,
            }}
            onMouseEnter={(e) => {
              if (location.pathname !== "/projects") {
                e.currentTarget.style.background = "#f9fafb";
              }
            }}
            onMouseLeave={(e) => {
              if (location.pathname !== "/projects") {
                e.currentTarget.style.background = "transparent";
              }
            }}
          >
            <Home style={{ width: "1.125rem", height: "1.125rem" }} />
            <span>All Projects</span>
          </button>

          {/* Projects List */}
          <div style={{ marginBottom: "1rem" }}>
            <div style={{
              fontSize: "0.75rem",
              fontWeight: 600,
              color: "#6b7280",
              textTransform: "uppercase",
              letterSpacing: "0.05em",
              marginBottom: "0.75rem",
              paddingLeft: "0.5rem",
            }}>
              Projects
            </div>

            {loadingProjects ? (
              <div style={{
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                padding: "2rem",
                color: "#9ca3af",
              }}>
                <Loader2 style={{ width: "1.25rem", height: "1.25rem", animation: "spin 1s linear infinite" }} />
              </div>
            ) : projects.length === 0 ? (
              <div style={{
                padding: "1.5rem",
                textAlign: "center",
                color: "#9ca3af",
                fontSize: "0.875rem",
              }}>
                No projects yet
              </div>
            ) : (
              <div style={{ display: "flex", flexDirection: "column", gap: "0.25rem" }}>
                {projects.map((project) => {
                  const isExpanded = expandedProjects.has(project.id);
                  const isActive = isProjectActive(project.id);
                  const meetings = meetingsByProject[project.id] || [];
                  const isLoadingMeetings = loadingMeetings.has(project.id);

                  return (
                    <div key={project.id} style={{ display: "flex", flexDirection: "column" }}>
                      {/* Project Item */}
                      <div
                        style={{
                          display: "flex",
                          alignItems: "center",
                          gap: "0.5rem",
                          padding: "0.625rem 0.75rem",
                          borderRadius: "6px",
                          cursor: "pointer",
                          background: isActive ? "#eff6ff" : "transparent",
                          transition: "all 0.2s ease",
                        }}
                        onMouseEnter={(e) => {
                          if (!isActive) {
                            e.currentTarget.style.background = "#f9fafb";
                          }
                        }}
                        onMouseLeave={(e) => {
                          if (!isActive) {
                            e.currentTarget.style.background = "transparent";
                          }
                        }}
                      >
                        <button
                          onClick={() => toggleProject(project.id)}
                          style={{
                            padding: "0.25rem",
                            background: "transparent",
                            border: "none",
                            cursor: "pointer",
                            display: "flex",
                            alignItems: "center",
                            justifyContent: "center",
                            color: "#6b7280",
                          }}
                        >
                          {isExpanded ? (
                            <ChevronDown style={{ width: "1rem", height: "1rem" }} />
                          ) : (
                            <ChevronRight style={{ width: "1rem", height: "1rem" }} />
                          )}
                        </button>
                        <FolderOpen style={{
                          width: "1rem",
                          height: "1rem",
                          color: isActive ? "#3b82f6" : "#6b7280",
                          flexShrink: 0,
                        }} />
                        <div
                          onClick={() => {
                            navigate(`/projects/${project.id}`);
                            onClose();
                          }}
                          style={{
                            flex: 1,
                            fontSize: "0.875rem",
                            fontWeight: isActive ? 600 : 500,
                            color: isActive ? "#3b82f6" : "#374151",
                            overflow: "hidden",
                            textOverflow: "ellipsis",
                            whiteSpace: "nowrap",
                          }}
                        >
                          {project.name}
                        </div>
                        {project.meetings_count !== undefined && (
                          <div style={{
                            fontSize: "0.75rem",
                            color: "#9ca3af",
                            padding: "0.125rem 0.5rem",
                            background: "#f3f4f6",
                            borderRadius: "12px",
                          }}>
                            {project.meetings_count}
                          </div>
                        )}
                      </div>

                      {/* Meetings List */}
                      {isExpanded && (
                        <div style={{
                          marginLeft: "1.5rem",
                          marginTop: "0.25rem",
                          paddingLeft: "0.75rem",
                          borderLeft: "2px solid #e5e7eb",
                          display: "flex",
                          flexDirection: "column",
                          gap: "0.125rem",
                        }}>
                          {isLoadingMeetings ? (
                            <div style={{
                              padding: "0.75rem",
                              display: "flex",
                              alignItems: "center",
                              gap: "0.5rem",
                              color: "#9ca3af",
                              fontSize: "0.75rem",
                            }}>
                              <Loader2 style={{ width: "0.875rem", height: "0.875rem", animation: "spin 1s linear infinite" }} />
                              <span>Loading meetings...</span>
                            </div>
                          ) : meetings.length === 0 ? (
                            <div style={{
                              padding: "0.75rem",
                              fontSize: "0.75rem",
                              color: "#9ca3af",
                            }}>
                              No meetings
                            </div>
                          ) : (
                            meetings.map((meeting) => {
                              const meetingActive = isMeetingActive(meeting.id);
                              return (
                                <div
                                  key={meeting.id}
                                  onClick={() => {
                                    if (meeting.has_insights) {
                                      navigate(`/insights/${meeting.id}`);
                                      onClose();
                                    }
                                  }}
                                  style={{
                                    padding: "0.5rem 0.75rem",
                                    borderRadius: "6px",
                                    cursor: meeting.has_insights ? "pointer" : "not-allowed",
                                    background: meetingActive ? "#eff6ff" : "transparent",
                                    opacity: meeting.has_insights ? 1 : 0.6,
                                    transition: "all 0.2s ease",
                                    display: "flex",
                                    alignItems: "center",
                                    gap: "0.5rem",
                                  }}
                                  onMouseEnter={(e) => {
                                    if (meeting.has_insights && !meetingActive) {
                                      e.currentTarget.style.background = "#f9fafb";
                                    }
                                  }}
                                  onMouseLeave={(e) => {
                                    if (meeting.has_insights && !meetingActive) {
                                      e.currentTarget.style.background = "transparent";
                                    }
                                  }}
                                >
                                  <FileVideo style={{
                                    width: "0.875rem",
                                    height: "0.875rem",
                                    color: meetingActive ? "#3b82f6" : "#9ca3af",
                                    flexShrink: 0,
                                  }} />
                                  <div style={{
                                    flex: 1,
                                    fontSize: "0.8125rem",
                                    fontWeight: meetingActive ? 600 : 400,
                                    color: meetingActive ? "#3b82f6" : "#6b7280",
                                    overflow: "hidden",
                                    textOverflow: "ellipsis",
                                    whiteSpace: "nowrap",
                                  }}>
                                    {meeting.meeting_name}
                                  </div>
                                  {meeting.has_insights && (
                                    <div style={{
                                      width: "0.375rem",
                                      height: "0.375rem",
                                      borderRadius: "50%",
                                      background: "#10b981",
                                    }} />
                                  )}
                                </div>
                              );
                            })
                          )}
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        </div>
      </aside>
    </>
  );
}

