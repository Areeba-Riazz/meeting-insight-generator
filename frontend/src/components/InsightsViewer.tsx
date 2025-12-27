import React, { useState, useRef, useEffect } from "react";
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
  sentiment?: {
    overall?: string;
    score?: number;
    segments?: Array<{
      sentiment: string;
      score: number;
      text: string;
      start?: number;
      end?: number;
    }>;
  };
  summary?: string | {
    combined?: string;
    abstractive?: string | {
      paragraph?: string;
      bullets?: string[];
    };
    extractive?: {
      text?: string;
      excerpts?: Array<{
        text: string;
        timestamp?: number | null;
      }>;
    };
  };
  [key: string]: any;
};

type Props = {
  insights: InsightsPayload | null;
  videoUrl?: string | null;
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

export function InsightsViewer({ insights, videoUrl }: Props) {
  const [activeTab, setActiveTab] = useState<TabId>("transcript");
  const [currentTime, setCurrentTime] = useState(0);
  const [summaryMode, setSummaryMode] = useState<'paragraph' | 'bullets'>('paragraph');
  const videoRef = useRef<HTMLVideoElement>(null);

  useEffect(() => {
    const video = videoRef.current;
    if (!video) return;

    const handleTimeUpdate = () => {
      setCurrentTime(video.currentTime);
    };

    video.addEventListener("timeupdate", handleTimeUpdate);
    return () => video.removeEventListener("timeupdate", handleTimeUpdate);
  }, [videoUrl]);

  const seekToTime = (seconds: number) => {
    if (videoRef.current) {
      videoRef.current.currentTime = seconds;
      videoRef.current.play();
    }
  };

  if (!insights) return null;

  const { transcript, topics, decisions, action_items, sentiment, summary } = insights;

  const tabs: Array<{ id: TabId; label: string; icon: React.ReactNode; count?: number }> = [
    { id: "transcript", label: "Transcript", icon: <FileText style={{ width: "1rem", height: "1rem" }} /> },
    { id: "summary", label: "Summary", icon: <MessageSquare style={{ width: "1rem", height: "1rem" }} /> },
    { id: "topics", label: "Topics", icon: <Lightbulb style={{ width: "1rem", height: "1rem" }} />, count: topics?.length },
    { id: "decisions", label: "Decisions", icon: <CheckSquare style={{ width: "1rem", height: "1rem" }} />, count: decisions?.length },
    { id: "actions", label: "Action Items", icon: <TrendingUp style={{ width: "1rem", height: "1rem" }} />, count: action_items?.length },
    { id: "sentiment", label: "Sentiment", icon: <BarChart3 style={{ width: "1rem", height: "1rem" }} />, count: sentiment?.segments?.length },
  ];

  return (
    <div>
      {/* Video Player */}
      {videoUrl && (
        <div style={{ marginBottom: "2rem", borderRadius: "12px", overflow: "hidden", boxShadow: "0 4px 6px -1px rgba(0, 0, 0, 0.1)" }}>
          <video
            ref={videoRef}
            controls
            style={{ width: "100%", maxHeight: "500px", display: "block", backgroundColor: "#000" }}
            src={videoUrl}
          >
            Your browser does not support the video tag.
          </video>
        </div>
      )}

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
                  const isCurrentSegment = videoUrl && currentTime >= seg.start && currentTime <= seg.end;

                  return (
                    <div 
                      key={idx} 
                      style={{ 
                        marginBottom: "0.75rem",
                        background: isCurrentSegment ? "#fef3c7" : "transparent",
                        padding: isCurrentSegment ? "0.5rem" : "0",
                        borderRadius: "6px",
                        transition: "all 0.3s ease"
                      }}
                    >
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
                        <div 
                          onClick={() => videoUrl && seekToTime(seg.start)}
                          style={{
                            fontSize: "0.7rem",
                            color: videoUrl ? "#3b82f6" : "#9ca3af",
                            fontFamily: "monospace",
                            fontWeight: 500,
                            minWidth: "80px",
                            paddingTop: "0.25rem",
                            flexShrink: 0,
                            cursor: videoUrl ? "pointer" : "default",
                            textDecoration: videoUrl ? "underline" : "none"
                          }}
                          onMouseEnter={(e) => {
                            if (videoUrl) e.currentTarget.style.color = "#2563eb";
                          }}
                          onMouseLeave={(e) => {
                            if (videoUrl) e.currentTarget.style.color = "#3b82f6";
                          }}
                        >
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
            {/* Toggle between paragraph and bullets */}
            <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '1rem' }}>
              <button
                type="button"
                onClick={() => setSummaryMode('paragraph')}
                style={{
                  padding: '0.375rem 0.75rem',
                  borderRadius: '8px',
                  border: summaryMode === 'paragraph' ? '1px solid #8b5cf6' : '1px solid #e5e7eb',
                  background: summaryMode === 'paragraph' ? '#f5f3ff' : 'white',
                  color: summaryMode === 'paragraph' ? '#5b21b6' : '#374151',
                  cursor: 'pointer',
                  fontSize: '0.875rem'
                }}
              >
                Paragraph
              </button>
              <button
                type="button"
                onClick={() => setSummaryMode('bullets')}
                style={{
                  padding: '0.375rem 0.75rem',
                  borderRadius: '8px',
                  border: summaryMode === 'bullets' ? '1px solid #8b5cf6' : '1px solid #e5e7eb',
                  background: summaryMode === 'bullets' ? '#f5f3ff' : 'white',
                  color: summaryMode === 'bullets' ? '#5b21b6' : '#374151',
                  cursor: 'pointer',
                  fontSize: '0.875rem'
                }}
              >
                Bullet Points
              </button>
            </div>
            {summary ? (
              (() => {
                // Parse summary if it's a JSON string
                let parsedSummary = summary;
                if (typeof summary === 'string') {
                  try {
                    const parsed = JSON.parse(summary);
                    if (parsed && typeof parsed === 'object') {
                      parsedSummary = parsed;
                    }
                  } catch (e) {
                    // Not JSON, keep as string
                  }
                }
                
                return (
              <div style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
                {/* If user wants bullets, prefer extractive excerpts, else show paragraph/combined */}
                {summaryMode === 'bullets' ? (
                  (() => {
                    // Prefer explicit excerpts list when available
                    const excerpts = parsedSummary && typeof parsedSummary !== 'string' && parsedSummary.extractive && Array.isArray(parsedSummary.extractive.excerpts)
                      ? parsedSummary.extractive.excerpts
                      : null;

                    if (excerpts && excerpts.length > 0) {
                      return (
                        <div style={{
                          padding: "1.5rem",
                          background: "#eff6ff",
                          border: "1px solid #dbeafe",
                          borderRadius: "10px"
                        }}>
                          <div style={{ fontSize: "0.875rem", fontWeight: 600, color: "#1e40af", marginBottom: "1rem", textTransform: "uppercase", letterSpacing: "0.05em" }}>
                            📌 Key Points
                          </div>
                          <ul style={{ margin: 0, paddingLeft: '1.25rem', color: '#374151', lineHeight: 1.7 }}>
                            {excerpts.map((ex: any, i: number) => (
                              <li key={i} style={{ marginBottom: '0.75rem' }}>
                                {ex.text}
                                {ex.timestamp !== null && ex.timestamp !== undefined && videoUrl && (
                                  <div onClick={() => seekToTime(ex.timestamp)} style={{ fontSize: '0.75rem', color: '#3b82f6', fontFamily: 'monospace', cursor: 'pointer' }}>
                                    🕐 {formatTime(ex.timestamp)}
                                  </div>
                                )}
                              </li>
                            ))}
                          </ul>
                        </div>
                      );
                    }

                    // Check for abstractive.bullets first
                    const abstractiveBullets = parsedSummary && typeof parsedSummary !== 'string' && parsedSummary.abstractive && typeof parsedSummary.abstractive === 'object' && Array.isArray(parsedSummary.abstractive.bullets)
                      ? parsedSummary.abstractive.bullets
                      : null;

                    if (abstractiveBullets && abstractiveBullets.length > 0) {
                      return (
                        <div style={{ padding: '1.5rem', background: '#eff6ff', border: '1px solid #dbeafe', borderRadius: '10px' }}>
                          <div style={{ fontSize: '0.875rem', fontWeight: 600, color: '#1e40af', marginBottom: '1rem', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                            📌 Key Points
                          </div>
                          <ul style={{ margin: 0, paddingLeft: '1.25rem', color: '#374151', lineHeight: 1.7 }}>
                            {abstractiveBullets.map((b: string, i: number) => (
                              <li key={i} style={{ marginBottom: '0.75rem' }} dangerouslySetInnerHTML={{ __html: b }} />
                            ))}
                          </ul>
                        </div>
                      );
                    }

                    // Fallback: try to create bullets from combined/abstractive text
                    const abstractivePara = parsedSummary && typeof parsedSummary !== 'string' && parsedSummary.abstractive 
                      ? (typeof parsedSummary.abstractive === 'string' ? parsedSummary.abstractive : parsedSummary.abstractive.paragraph)
                      : null;
                    const para = typeof parsedSummary === 'string' ? parsedSummary : (parsedSummary.combined || abstractivePara || '');
                    if (!para) return (
                      <div style={{ padding: '1.5rem', background: '#f9fafb', border: '1px dashed #e5e7eb', borderRadius: '10px', color: '#9ca3af' }}>
                        No bullet points available
                      </div>
                    );

                    // Split into sentences/lines for simple bullets
                    const bullets = para.split(/\n+|(?<=\.)\s+/).map((s: string) => s.trim()).filter((s: string) => s.length > 0);
                    return (
                      <div style={{ padding: '1.5rem', background: '#eff6ff', border: '1px solid #dbeafe', borderRadius: '10px' }}>
                        <div style={{ fontSize: '0.875rem', fontWeight: 600, color: '#1e40af', marginBottom: '1rem', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                          📌 Key Points
                        </div>
                        <ul style={{ margin: 0, paddingLeft: '1.25rem', color: '#374151', lineHeight: 1.7 }}>
                          {bullets.map((b: string, i: number) => (
                            <li key={i} style={{ marginBottom: '0.75rem' }}>{b}</li>
                          ))}
                        </ul>
                      </div>
                    );
                  })()
                ) : (
                  // Paragraph mode: reuse existing paragraph rendering logic
                  typeof parsedSummary === 'string' ? (
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
                        {parsedSummary}
                      </p>
                    </div>
                  ) : (
                    <>
                      {/* Show combined summary if available */}
                      {parsedSummary.combined && (
                        <div style={{
                          padding: "1.5rem",
                          background: "#faf5ff",
                          border: "1px solid #e9d5ff",
                          borderRadius: "10px"
                        }}>
                          <div style={{ fontSize: "0.875rem", fontWeight: 600, color: "#7c3aed", marginBottom: "0.75rem", textTransform: "uppercase", letterSpacing: "0.05em" }}>
                            📝 Main Summary
                          </div>
                          <p style={{
                            fontSize: "0.95rem",
                            lineHeight: 1.7,
                            color: "#374151",
                            margin: 0,
                            whiteSpace: "pre-wrap"
                          }}>
                            {parsedSummary.combined}
                          </p>
                        </div>
                      )}
                      {/* Show abstractive paragraph if no combined but abstractive exists */}
                      {!parsedSummary.combined && parsedSummary.abstractive && (
                        (() => {
                          const abstractiveText = typeof parsedSummary.abstractive === 'string' 
                            ? parsedSummary.abstractive 
                            : parsedSummary.abstractive.paragraph;
                          if (!abstractiveText) return null;
                          return (
                            <div style={{
                              padding: "1.5rem",
                              background: "#faf5ff",
                              border: "1px solid #e9d5ff",
                              borderRadius: "10px"
                            }}>
                              <div style={{ fontSize: "0.875rem", fontWeight: 600, color: "#7c3aed", marginBottom: "0.75rem", textTransform: "uppercase", letterSpacing: "0.05em" }}>
                                📝 Main Summary
                              </div>
                              <p style={{
                                fontSize: "0.95rem",
                                lineHeight: 1.7,
                                color: "#374151",
                                margin: 0,
                                whiteSpace: "pre-wrap"
                              }}>
                                {abstractiveText}
                              </p>
                            </div>
                          );
                        })()
                      )}
                      {parsedSummary.extractive && (
                        (() => {
                          const extractiveData = typeof parsedSummary.extractive === 'string' 
                            ? { text: parsedSummary.extractive, excerpts: [] }
                            : parsedSummary.extractive;
                          const hasExcerpts = extractiveData.excerpts && extractiveData.excerpts.length > 0;
                          const shouldShow = hasExcerpts || (extractiveData.text && extractiveData.text !== parsedSummary.combined);
                          if (!shouldShow) return null;
                          return (
                            <div style={{
                              padding: "1.5rem",
                              background: "#eff6ff",
                              border: "1px solid #dbeafe",
                              borderRadius: "10px"
                            }}>
                              <div style={{ fontSize: "0.875rem", fontWeight: 600, color: "#1e40af", marginBottom: "1rem", textTransform: "uppercase", letterSpacing: "0.05em" }}>
                                📋 Key Excerpts
                              </div>
                              {hasExcerpts ? (
                                <div style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
                                  {extractiveData.excerpts && extractiveData.excerpts.map((excerpt: any, idx: number) => (
                                    <div 
                                      key={idx}
                                      style={{
                                        padding: "1rem",
                                        background: "white",
                                        borderLeft: "3px solid #3b82f6",
                                        borderRadius: "6px",
                                        position: "relative"
                                      }}
                                    >
                                      <div style={{
                                        fontSize: "0.95rem",
                                        lineHeight: 1.7,
                                        color: "#374151",
                                        fontStyle: "italic",
                                        marginBottom: "0.5rem"
                                      }}>
                                        "{excerpt.text}"
                                      </div>
                                      {excerpt.timestamp !== null && excerpt.timestamp !== undefined && (
                                        <div 
                                          onClick={() => videoUrl && seekToTime(excerpt.timestamp)}
                                          style={{
                                            fontSize: "0.75rem",
                                            color: videoUrl ? "#3b82f6" : "#9ca3af",
                                            fontFamily: "monospace",
                                            fontWeight: 500,
                                            cursor: videoUrl ? "pointer" : "default",
                                            textDecoration: videoUrl ? "underline" : "none",
                                            display: "flex",
                                            alignItems: "center",
                                            gap: "0.25rem"
                                          }}
                                          onMouseEnter={(e) => {
                                            if (videoUrl) e.currentTarget.style.color = "#2563eb";
                                          }}
                                          onMouseLeave={(e) => {
                                            if (videoUrl) e.currentTarget.style.color = "#3b82f6";
                                          }}
                                        >
                                          🕐 {formatTime(excerpt.timestamp)}
                                        </div>
                                      )}
                                    </div>
                                  ))}
                                </div>
                              ) : (
                                <p style={{
                                  fontSize: "0.95rem",
                                  lineHeight: 1.7,
                                  color: "#374151",
                                  margin: 0,
                                  whiteSpace: "pre-wrap"
                                }}>
                                  {extractiveData.text}
                                </p>
                              )}
                            </div>
                          );
                        })()
                      )}
                    </>
                  )
                )}
              </div>
                );
              })()
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
            {sentiment ? (
              <div style={{ display: "flex", flexDirection: "column", gap: "1.5rem" }}>
                {/* Overall Sentiment */}
                {sentiment.overall && (
                  <div style={{
                    padding: "2rem",
                    background: sentiment.overall.toLowerCase() === "positive" 
                      ? "linear-gradient(135deg, #ecfdf5 0%, #d1fae5 100%)"
                      : sentiment.overall.toLowerCase() === "negative"
                        ? "linear-gradient(135deg, #fef2f2 0%, #fee2e2 100%)"
                        : "linear-gradient(135deg, #f3f4f6 0%, #e5e7eb 100%)",
                    border: `2px solid ${
                      sentiment.overall.toLowerCase() === "positive" 
                        ? "#86efac"
                        : sentiment.overall.toLowerCase() === "negative"
                          ? "#fca5a5"
                          : "#d1d5db"
                    }`,
                    borderRadius: "12px",
                    textAlign: "center"
                  }}>
                    <div style={{ fontSize: "0.875rem", fontWeight: 600, color: "#6b7280", textTransform: "uppercase", letterSpacing: "0.05em", marginBottom: "0.75rem" }}>
                      Overall Meeting Sentiment
                    </div>
                    <div style={{ display: "flex", alignItems: "center", justifyContent: "center", gap: "1rem", marginBottom: "0.5rem" }}>
                      <div style={{ fontSize: "3rem" }}>
                        {sentiment.overall.toLowerCase() === "positive" ? "😊" : 
                         sentiment.overall.toLowerCase() === "negative" ? "😞" : "😐"}
                      </div>
                      <div>
                        <div style={{ 
                          fontSize: "2rem", 
                          fontWeight: 700, 
                          color: sentiment.overall.toLowerCase() === "positive" 
                            ? "#065f46"
                            : sentiment.overall.toLowerCase() === "negative"
                              ? "#991b1b"
                              : "#374151"
                        }}>
                          {sentiment.overall}
                        </div>
                        {sentiment.score !== undefined && (
                          <div style={{ fontSize: "0.875rem", color: "#6b7280", fontWeight: 500 }}>
                            Confidence: {(sentiment.score * 100).toFixed(0)}%
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                )}

                {/* Segment-level Sentiments */}
                {sentiment.segments && sentiment.segments.length > 0 && (
                  <div>
                    <div style={{ fontSize: "0.875rem", fontWeight: 600, color: "#374151", marginBottom: "1rem", textTransform: "uppercase", letterSpacing: "0.05em" }}>
                      Segment Analysis ({sentiment.segments.length} segments)
                    </div>
                    <div style={{ display: "flex", flexDirection: "column", gap: "0.75rem" }}>
                      {sentiment.segments.map((s, i) => {
                        const isPositive = s.sentiment.toLowerCase().includes("positive");
                        const isNegative = s.sentiment.toLowerCase().includes("negative");
                        const bgColor = isPositive ? "#f0fdf4" : isNegative ? "#fef2f2" : "#f9fafb";
                        const borderColor = isPositive ? "#bbf7d0" : isNegative ? "#fecaca" : "#e5e7eb";
                        const textColor = isPositive ? "#065f46" : isNegative ? "#991b1b" : "#374151";
                        const badgeBg = isPositive ? "#10b981" : isNegative ? "#ef4444" : "#6b7280";
                        const emoji = isPositive ? "😊" : isNegative ? "😞" : "😐";

                        return (
                          <div key={i} style={{
                            padding: "1.25rem",
                            background: bgColor,
                            border: `1px solid ${borderColor}`,
                            borderRadius: "10px",
                            transition: "all 0.2s ease"
                          }}>
                            <div style={{ display: "flex", alignItems: "start", gap: "0.75rem" }}>
                              <div style={{
                                padding: "0.5rem 0.75rem",
                                background: badgeBg,
                                borderRadius: "6px",
                                fontSize: "0.875rem",
                                fontWeight: 600,
                                color: "white",
                                flexShrink: 0,
                                display: "flex",
                                alignItems: "center",
                                gap: "0.375rem"
                              }}>
                                <span>{emoji}</span>
                                {s.sentiment}
                              </div>
                              <div style={{ flex: 1 }}>
                                <div style={{ fontSize: "0.95rem", color: textColor, marginBottom: "0.5rem", lineHeight: 1.6 }}>
                                  "{s.text}"
                                </div>
                                <div style={{ display: "flex", alignItems: "center", gap: "1rem", flexWrap: "wrap" }}>
                                  {(s.start !== undefined && s.end !== undefined) && (
                                    <div 
                                      onClick={() => videoUrl && seekToTime(s.start!)}
                                      style={{ 
                                        fontSize: "0.75rem", 
                                        color: videoUrl ? "#3b82f6" : "#9ca3af", 
                                        fontWeight: 500,
                                        fontFamily: "monospace",
                                        cursor: videoUrl ? "pointer" : "default",
                                        textDecoration: videoUrl ? "underline" : "none",
                                        display: "flex",
                                        alignItems: "center",
                                        gap: "0.25rem"
                                      }}
                                      onMouseEnter={(e) => {
                                        if (videoUrl) e.currentTarget.style.color = "#2563eb";
                                      }}
                                      onMouseLeave={(e) => {
                                        if (videoUrl) e.currentTarget.style.color = "#3b82f6";
                                      }}
                                    >
                                      🕐 {formatTime(s.start)} - {formatTime(s.end)}
                                    </div>
                                  )}
                                  {s.score !== undefined && (
                                    <div style={{ fontSize: "0.75rem", color: "#6b7280", fontWeight: 500 }}>
                                      Confidence: {(s.score * 100).toFixed(0)}%
                                    </div>
                                  )}
                                </div>
                              </div>
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                )}
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