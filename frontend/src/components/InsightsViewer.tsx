import React, { useState } from "react";
import { FileText, MessageSquare, Lightbulb, CheckSquare, TrendingUp, BarChart3 } from "lucide-react";

type Transcript = {
  text: string;
  segments?: any[];
  model?: string;
};

type InsightsPayload = {
  transcript?: Transcript;
  topics?: any[];
  decisions?: any[];
  action_items?: any[];
  sentiments?: any[];
  summary?: string;
  [key: string]: any;
};

type Props = {
  insights: InsightsPayload | null;
};

type TabId = "transcript" | "summary" | "topics" | "decisions" | "actions" | "sentiment";

// Helper function to assign consistent colors to speakers
const getSpeakerColor = (speaker: string): string => {
  const colors = [
    "#3b82f6", // blue
    "#8b5cf6", // purple
    "#10b981", // green
    "#f59e0b", // amber
    "#ec4899", // pink
    "#06b6d4", // cyan
    "#ef4444", // red
    "#6366f1", // indigo
  ];

  // Hash the speaker name to get a consistent color
  let hash = 0;
  for (let i = 0; i < speaker.length; i++) {
    hash = speaker.charCodeAt(i) + ((hash << 5) - hash);
  }
  return colors[Math.abs(hash) % colors.length];
};

// Helper function to format time in MM:SS
const formatTime = (seconds: number): string => {
  const mins = Math.floor(seconds / 60);
  const secs = Math.floor(seconds % 60);
  return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
};

export function InsightsViewer({ insights }: Props) {
  const [activeTab, setActiveTab] = useState<TabId>("transcript");

  if (!insights) return null;

  const { transcript, topics, decisions, action_items, sentiments, summary } = insights;

  const tabs: Array<{ id: TabId; label: string; icon: React.ReactNode; count?: number }> = [
    { id: "transcript", label: "Transcript", icon: <FileText style={{ width: "1rem", height: "1rem" }} /> },
    { id: "summary", label: "Summary", icon: <MessageSquare style={{ width: "1rem", height: "1rem" }} /> },
    { id: "topics", label: "Topics", icon: <Lightbulb style={{ width: "1rem", height: "1rem" }} />, count: topics?.length },
    { id: "decisions", label: "Decisions", icon: <CheckSquare style={{ width: "1rem", height: "1rem" }} />, count: decisions?.length },
    { id: "actions", label: "Action Items", icon: <TrendingUp style={{ width: "1rem", height: "1rem" }} />, count: action_items?.length },
    { id: "sentiment", label: "Sentiment", icon: <BarChart3 style={{ width: "1rem", height: "1rem" }} />, count: sentiments?.length },
  ];

  return (
    <div>
      {/* Tab Navigation */}
      <div style={{
        display: "flex",
        gap: "0.5rem",
        borderBottom: "2px solid #e5e7eb",
        marginBottom: "1.5rem",
        overflowX: "auto",
        paddingBottom: "0.5rem"
      }}>
        {tabs.map((tab) => (
          <button
            key={tab.id}
            type="button"
            onClick={() => setActiveTab(tab.id)}
            style={{
              display: "flex",
              alignItems: "center",
              gap: "0.5rem",
              padding: "0.75rem 1.25rem",
              background: activeTab === tab.id ? "#eff6ff" : "transparent",
              color: activeTab === tab.id ? "#1e40af" : "#6b7280",
              border: "none",
              borderBottom: activeTab === tab.id ? "2px solid #3b82f6" : "2px solid transparent",
              borderRadius: "6px 6px 0 0",
              fontSize: "0.875rem",
              fontWeight: activeTab === tab.id ? 600 : 500,
              cursor: "pointer",
              transition: "all 0.2s ease",
              whiteSpace: "nowrap",
              marginBottom: "-0.5rem"
            }}
            onMouseEnter={(e) => {
              if (activeTab !== tab.id) {
                e.currentTarget.style.background = "#f9fafb";
                e.currentTarget.style.color = "#374151";
              }
            }}
            onMouseLeave={(e) => {
              if (activeTab !== tab.id) {
                e.currentTarget.style.background = "transparent";
                e.currentTarget.style.color = "#6b7280";
              }
            }}
          >
            {tab.icon}
            <span>{tab.label}</span>
            {tab.count !== undefined && tab.count > 0 && (
              <span style={{
                padding: "0.125rem 0.5rem",
                background: activeTab === tab.id ? "#3b82f6" : "#e5e7eb",
                color: activeTab === tab.id ? "white" : "#6b7280",
                borderRadius: "999px",
                fontSize: "0.75rem",
                fontWeight: 600
              }}>
                {tab.count}
              </span>
            )}
          </button>
        ))}
      </div>

      {/* Tab Content */}
      <div style={{ animation: "fadeIn 0.3s ease-out" }}>
        {activeTab === "transcript" && transcript && (
          <div>
            <h3 style={{ fontSize: "1.125rem", fontWeight: 600, color: "#111827", marginBottom: "1rem", display: "flex", alignItems: "center", gap: "0.5rem" }}>
              <FileText style={{ width: "1.25rem", height: "1.25rem", color: "#3b82f6" }} />
              Diarized Transcript
            </h3>

            {/* Show segments with speaker labels */}
            {transcript.segments && transcript.segments.length > 0 ? (
              <div style={{
                padding: "1.5rem",
                background: "#f9fafb",
                border: "1px solid #e5e7eb",
                borderRadius: "10px",
                maxHeight: "600px",
                overflowY: "auto"
              }}>
                {transcript.segments.map((seg: any, idx: number) => {
                  const speaker = seg.speaker || "Unknown Speaker";
                  const speakerColor = getSpeakerColor(speaker);
                  const prevSpeaker = idx > 0 ? (transcript.segments?.[idx - 1]?.speaker || "Unknown Speaker") : null;
                  const showSpeakerHeader = speaker !== prevSpeaker;

                  return (
                    <div key={idx} style={{ marginBottom: "0.75rem" }}>
                      {showSpeakerHeader && (
                        <div style={{
                          display: "flex",
                          alignItems: "center",
                          gap: "0.75rem",
                          marginBottom: "0.5rem",
                          paddingTop: idx > 0 ? "1rem" : "0",
                          borderTop: idx > 0 ? "1px solid #e5e7eb" : "none"
                        }}>
                          <div style={{
                            padding: "0.375rem 0.875rem",
                            background: speakerColor,
                            color: "white",
                            borderRadius: "6px",
                            fontSize: "0.875rem",
                            fontWeight: 600,
                            display: "flex",
                            alignItems: "center",
                            gap: "0.375rem"
                          }}>
                            <span>👤</span>
                            {speaker}
                          </div>
                        </div>
                      )}
                      <div style={{
                        display: "flex",
                        gap: "0.75rem",
                        paddingLeft: showSpeakerHeader ? "0rem" : "1rem"
                      }}>
                        <div style={{
                          fontSize: "0.7rem",
                          color: "#9ca3af",
                          fontFamily: "monospace",
                          fontWeight: 500,
                          minWidth: "80px",
                          paddingTop: "0.25rem",
                          flexShrink: 0
                        }}>
                          [{formatTime(seg.start)}]
                        </div>
                        <div style={{
                          fontSize: "0.95rem",
                          lineHeight: 1.7,
                          color: "#374151",
                          flex: 1
                        }}>
                          {seg.text}
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            ) : (
              <div style={{
                padding: "1.5rem",
                background: "#f9fafb",
                border: "1px solid #e5e7eb",
                borderRadius: "10px",
                maxHeight: "500px",
                overflowY: "auto"
              }}>
                <pre style={{
                  whiteSpace: "pre-wrap",
                  fontFamily: "system-ui, -apple-system, sans-serif",
                  fontSize: "0.95rem",
                  lineHeight: 1.7,
                  color: "#374151",
                  margin: 0
                }}>
                  {transcript.text}
                </pre>
              </div>
            )}

            {transcript.model && (
              <div style={{ marginTop: "0.75rem", fontSize: "0.8rem", color: "#9ca3af" }}>
                Model: {transcript.model}
              </div>
            )}
          </div>
        )}

        {activeTab === "summary" && (
          <div>
            <h3 style={{ fontSize: "1.125rem", fontWeight: 600, color: "#111827", marginBottom: "1rem", display: "flex", alignItems: "center", gap: "0.5rem" }}>
              <MessageSquare style={{ width: "1.25rem", height: "1.25rem", color: "#8b5cf6" }} />
              Meeting Summary
            </h3>
            {summary ? (
              <div style={{
                padding: "1.5rem",
                background: "#faf5ff",
                border: "1px solid #e9d5ff",
                borderRadius: "10px"
              }}>
                <p style={{
                  fontSize: "0.95rem",
                  lineHeight: 1.7,
                  color: "#374151",
                  margin: 0,
                  whiteSpace: "pre-wrap"
                }}>
                  {summary}
                </p>
              </div>
            ) : (
              <div style={{
                padding: "2rem",
                textAlign: "center",
                background: "#f9fafb",
                border: "1px dashed #e5e7eb",
                borderRadius: "10px",
                color: "#9ca3af"
              }}>
                No summary available
              </div>
            )}
          </div>
        )}

        {activeTab === "topics" && (
          <div>
            <h3 style={{ fontSize: "1.125rem", fontWeight: 600, color: "#111827", marginBottom: "1rem", display: "flex", alignItems: "center", gap: "0.5rem" }}>
              <Lightbulb style={{ width: "1.25rem", height: "1.25rem", color: "#f59e0b" }} />
              Key Topics
            </h3>
            {topics && topics.length > 0 ? (
              <div style={{ display: "flex", flexDirection: "column", gap: "0.75rem" }}>
                {topics.map((t, i) => (
                  <div key={i} style={{
                    padding: "1.25rem",
                    background: "#fffbeb",
                    border: "1px solid #fde68a",
                    borderRadius: "10px"
                  }}>
                    <div style={{ display: "flex", alignItems: "start", gap: "0.75rem" }}>
                      <div style={{
                        width: "2rem",
                        height: "2rem",
                        background: "#f59e0b",
                        borderRadius: "6px",
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "center",
                        fontSize: "0.875rem",
                        fontWeight: 600,
                        color: "white",
                        flexShrink: 0
                      }}>
                        {i + 1}
                      </div>
                      <div style={{ flex: 1 }}>
                        <div style={{ fontSize: "1rem", fontWeight: 600, color: "#92400e", marginBottom: "0.5rem" }}>
                          {t.topic || "Topic"}
                        </div>
                        <div style={{ fontSize: "0.875rem", color: "#78350f", marginBottom: "0.5rem" }}>
                          {t.summary}
                        </div>
                        {(t.start !== undefined || t.end !== undefined) && (
                          <div style={{ fontSize: "0.75rem", color: "#a16207", fontWeight: 500 }}>
                            ⏱️ {t.start ?? "?"}s - {t.end ?? "?"}s
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div style={{
                padding: "2rem",
                textAlign: "center",
                background: "#f9fafb",
                border: "1px dashed #e5e7eb",
                borderRadius: "10px",
                color: "#9ca3af"
              }}>
                No topics identified
              </div>
            )}
          </div>
        )}

        {activeTab === "decisions" && (
          <div>
            <h3 style={{ fontSize: "1.125rem", fontWeight: 600, color: "#111827", marginBottom: "1rem", display: "flex", alignItems: "center", gap: "0.5rem" }}>
              <CheckSquare style={{ width: "1.25rem", height: "1.25rem", color: "#10b981" }} />
              Decisions Made
            </h3>
            {decisions && decisions.length > 0 ? (
              <div style={{ display: "flex", flexDirection: "column", gap: "0.75rem" }}>
                {decisions.map((d, i) => (
                  <div key={i} style={{
                    padding: "1.25rem",
                    background: "#f0fdf4",
                    border: "1px solid #bbf7d0",
                    borderRadius: "10px"
                  }}>
                    <div style={{ display: "flex", alignItems: "start", gap: "0.75rem" }}>
                      <div style={{
                        width: "2rem",
                        height: "2rem",
                        background: "#10b981",
                        borderRadius: "6px",
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "center",
                        flexShrink: 0
                      }}>
                        <CheckSquare style={{ width: "1rem", height: "1rem", color: "white" }} />
                      </div>
                      <div style={{ flex: 1 }}>
                        <div style={{ fontSize: "1rem", fontWeight: 600, color: "#065f46", marginBottom: "0.5rem" }}>
                          {d.decision}
                        </div>
                        {d.participants && d.participants.length > 0 && (
                          <div style={{ fontSize: "0.875rem", color: "#047857", marginBottom: "0.25rem" }}>
                            👥 Participants: {d.participants.join(", ")}
                          </div>
                        )}
                        {d.evidence && (
                          <div style={{ fontSize: "0.875rem", color: "#059669", fontStyle: "italic" }}>
                            💬 "{d.evidence}"
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div style={{
                padding: "2rem",
                textAlign: "center",
                background: "#f9fafb",
                border: "1px dashed #e5e7eb",
                borderRadius: "10px",
                color: "#9ca3af"
              }}>
                No decisions recorded
              </div>
            )}
          </div>
        )}

        {activeTab === "actions" && (
          <div>
            <h3 style={{ fontSize: "1.125rem", fontWeight: 600, color: "#111827", marginBottom: "1rem", display: "flex", alignItems: "center", gap: "0.5rem" }}>
              <TrendingUp style={{ width: "1.25rem", height: "1.25rem", color: "#3b82f6" }} />
              Action Items
            </h3>
            {action_items && action_items.length > 0 ? (
              <div style={{ display: "flex", flexDirection: "column", gap: "0.75rem" }}>
                {action_items.map((a, i) => (
                  <div key={i} style={{
                    padding: "1.25rem",
                    background: "#eff6ff",
                    border: "1px solid #bfdbfe",
                    borderRadius: "10px"
                  }}>
                    <div style={{ display: "flex", alignItems: "start", gap: "0.75rem" }}>
                      <div style={{
                        width: "2rem",
                        height: "2rem",
                        background: "#3b82f6",
                        borderRadius: "6px",
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "center",
                        fontSize: "0.875rem",
                        fontWeight: 600,
                        color: "white",
                        flexShrink: 0
                      }}>
                        {i + 1}
                      </div>
                      <div style={{ flex: 1 }}>
                        <div style={{ fontSize: "1rem", fontWeight: 600, color: "#1e40af", marginBottom: "0.5rem" }}>
                          {a.action}
                        </div>
                        <div style={{ display: "flex", flexWrap: "wrap", gap: "0.75rem", fontSize: "0.875rem" }}>
                          {a.assignee && (
                            <div style={{ color: "#1e3a8a" }}>
                              👤 <strong>Assignee:</strong> {a.assignee}
                            </div>
                          )}
                          {a.due && (
                            <div style={{ color: "#1e3a8a" }}>
                              📅 <strong>Due:</strong> {a.due}
                            </div>
                          )}
                        </div>
                        {a.evidence && (
                          <div style={{ fontSize: "0.875rem", color: "#2563eb", fontStyle: "italic", marginTop: "0.5rem" }}>
                            💬 "{a.evidence}"
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div style={{
                padding: "2rem",
                textAlign: "center",
                background: "#f9fafb",
                border: "1px dashed #e5e7eb",
                borderRadius: "10px",
                color: "#9ca3af"
              }}>
                No action items identified
              </div>
            )}
          </div>
        )}

        {activeTab === "sentiment" && (
          <div>
            <h3 style={{ fontSize: "1.125rem", fontWeight: 600, color: "#111827", marginBottom: "1rem", display: "flex", alignItems: "center", gap: "0.5rem" }}>
              <BarChart3 style={{ width: "1.25rem", height: "1.25rem", color: "#ec4899" }} />
              Sentiment Analysis
            </h3>
            {sentiments && sentiments.length > 0 ? (
              <div style={{ display: "flex", flexDirection: "column", gap: "0.75rem" }}>
                {sentiments.map((s, i) => (
                  <div key={i} style={{
                    padding: "1.25rem",
                    background: "#fdf2f8",
                    border: "1px solid #fbcfe8",
                    borderRadius: "10px"
                  }}>
                    <div style={{ display: "flex", alignItems: "start", gap: "0.75rem" }}>
                      <div style={{
                        padding: "0.5rem 0.75rem",
                        background: "#ec4899",
                        borderRadius: "6px",
                        fontSize: "0.875rem",
                        fontWeight: 600,
                        color: "white",
                        flexShrink: 0
                      }}>
                        {s.sentiment}
                      </div>
                      <div style={{ flex: 1 }}>
                        <div style={{ fontSize: "0.95rem", color: "#831843", marginBottom: "0.5rem" }}>
                          {s.text}
                        </div>
                        {(s.start !== undefined || s.end !== undefined) && (
                          <div style={{ fontSize: "0.75rem", color: "#9f1239", fontWeight: 500 }}>
                            ⏱️ {s.start ?? "?"}s - {s.end ?? "?"}s
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div style={{
                padding: "2rem",
                textAlign: "center",
                background: "#f9fafb",
                border: "1px dashed #e5e7eb",
                borderRadius: "10px",
                color: "#9ca3af"
              }}>
                No sentiment data available
              </div>
            )}
          </div>
        )}
      </div>

      <style>{`
        @keyframes fadeIn {
          from { opacity: 0; transform: translateY(10px); }
          to { opacity: 1; transform: translateY(0); }
        }
      `}</style>
    </div>
  );
}