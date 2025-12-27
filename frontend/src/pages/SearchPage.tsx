import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { searchMeetings, getSearchStats } from "../api/client";
import { Header } from "../components/Header";
import { Search, Loader2, Filter, X, ChevronLeft, ChevronRight, FileText, MessageSquare, CheckCircle, ListTodo, FileSearch } from "lucide-react";
import type { SearchResponse, SearchResult, SearchStats } from "../types/api";

const SEGMENT_TYPE_LABELS: Record<string, { label: string; icon: React.ReactNode; color: string }> = {
  transcript: { label: "Transcript", icon: <FileText size={16} />, color: "#3b82f6" },
  topic: { label: "Topic", icon: <MessageSquare size={16} />, color: "#8b5cf6" },
  decision: { label: "Decision", icon: <CheckCircle size={16} />, color: "#10b981" },
  action_item: { label: "Action Item", icon: <ListTodo size={16} />, color: "#f59e0b" },
  summary: { label: "Summary", icon: <FileSearch size={16} />, color: "#6366f1" },
};

export default function SearchPage() {
  const navigate = useNavigate();
  const [query, setQuery] = useState("");
  const [searchResults, setSearchResults] = useState<SearchResponse | null>(null);
  const [isSearching, setIsSearching] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [stats, setStats] = useState<SearchStats | null>(null);
  
  // Filters
  const [selectedSegmentTypes, setSelectedSegmentTypes] = useState<string[]>([]);
  const [minScore, setMinScore] = useState(0.0);
  const [showFilters, setShowFilters] = useState(false);
  
  // Pagination
  const [currentPage, setCurrentPage] = useState(1);
  const pageSize = 10;

  useEffect(() => {
    loadStats();
  }, []);

  const loadStats = async () => {
    try {
      const statsData = await getSearchStats();
      setStats(statsData);
    } catch (err: any) {
      console.error("Failed to load stats:", err);
    }
  };

  const handleSearch = async (page: number = 1) => {
    if (!query.trim()) {
      setError("Please enter a search query");
      return;
    }

    setIsSearching(true);
    setError(null);
    setCurrentPage(page);

    try {
      const results = await searchMeetings({
        query: query.trim(),
        top_k: 100, // Get more results for pagination
        segment_types: selectedSegmentTypes.length > 0 ? selectedSegmentTypes : undefined,
        min_score: minScore,
        page: page,
        page_size: pageSize,
      });
      setSearchResults(results);
    } catch (err: any) {
      setError(err.message || "Search failed");
      setSearchResults(null);
    } finally {
      setIsSearching(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !isSearching) {
      handleSearch(1);
    }
  };

  const toggleSegmentType = (type: string) => {
    setSelectedSegmentTypes((prev) =>
      prev.includes(type) ? prev.filter((t) => t !== type) : [...prev, type]
    );
  };

  const formatTimestamp = (seconds?: number | null) => {
    if (!seconds) return null;
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, "0")}`;
  };

  const getSegmentTypeInfo = (type: string) => {
    return SEGMENT_TYPE_LABELS[type] || { label: type, icon: <FileText size={16} />, color: "#6b7280" };
  };

  return (
    <div style={{ minHeight: "100vh", background: "#fafafa", position: "relative", overflow: "hidden" }}>
      <style>{`
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
          animation: float 18s ease-in-out infinite;
        }
        .content-wrapper {
          position: relative;
          z-index: 1;
        }
      `}</style>

      <div className="animated-bg">
        <div className="floating-shape shape-1" />
        <div className="floating-shape shape-2" />
        <div className="floating-shape shape-3" />
      </div>
      <Header />

      <div className="content-wrapper" style={{ maxWidth: 1200, margin: "0 auto", padding: "3rem 1.5rem" }}>
        {/* Hero Section */}
        <div style={{ marginBottom: "2.5rem", animation: "fadeIn 0.4s ease-out" }}>
          <h1 style={{ fontSize: "2.25rem", fontWeight: 700, color: "#111827", marginBottom: "0.5rem" }}>
            Search Meetings
          </h1>
          <p style={{ fontSize: "1rem", color: "#6b7280" }}>
            Search across all meeting transcripts, topics, decisions, and action items
          </p>
        </div>

        {/* Stats Card */}
        {stats && stats.total_vectors > 0 && (
          <div style={{
            background: "white",
            border: "1px solid #e5e7eb",
            borderRadius: "12px",
            padding: "1.25rem",
            marginBottom: "2rem",
            display: "flex",
            gap: "2rem",
            flexWrap: "wrap",
            animation: "fadeIn 0.4s ease-out"
          }}>
            <div>
              <div style={{ fontSize: "0.75rem", fontWeight: 600, color: "#6b7280", textTransform: "uppercase", letterSpacing: "0.05em", marginBottom: "0.25rem" }}>
                Total Vectors
              </div>
              <div style={{ fontSize: "1.5rem", fontWeight: 700, color: "#111827" }}>
                {stats.total_vectors.toLocaleString()}
              </div>
            </div>
            <div>
              <div style={{ fontSize: "0.75rem", fontWeight: 600, color: "#6b7280", textTransform: "uppercase", letterSpacing: "0.05em", marginBottom: "0.25rem" }}>
                Meetings Indexed
              </div>
              <div style={{ fontSize: "1.5rem", fontWeight: 700, color: "#111827" }}>
                {Object.keys(stats.meetings).length}
              </div>
            </div>
          </div>
        )}

        {/* Search Bar */}
        <div style={{
          background: "white",
          border: "1px solid #e5e7eb",
          borderRadius: "16px",
          padding: "2rem",
          boxShadow: "0 4px 6px -1px rgba(0, 0, 0, 0.05)",
          marginBottom: "2rem",
          animation: "fadeIn 0.4s ease-out"
        }}>
          <div style={{ display: "flex", gap: "1rem", marginBottom: "1rem" }}>
            <div style={{ flex: 1, position: "relative" }}>
              <Search style={{ position: "absolute", left: "1rem", top: "50%", transform: "translateY(-50%)", color: "#9ca3af", width: "1.25rem", height: "1.25rem" }} />
              <input
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="Search across all meetings... (e.g., 'budget decisions', 'action items for next week')"
                style={{
                  width: "100%",
                  padding: "0.875rem 1rem 0.875rem 3rem",
                  border: "1px solid #e5e7eb",
                  borderRadius: "10px",
                  fontSize: "1rem",
                  outline: "none",
                  transition: "all 0.2s ease"
                }}
                onFocus={(e) => {
                  e.currentTarget.style.borderColor = "#3b82f6";
                  e.currentTarget.style.boxShadow = "0 0 0 3px rgba(59, 130, 246, 0.1)";
                }}
                onBlur={(e) => {
                  e.currentTarget.style.borderColor = "#e5e7eb";
                  e.currentTarget.style.boxShadow = "none";
                }}
              />
            </div>
            <button
              onClick={() => handleSearch(1)}
              disabled={isSearching || !query.trim()}
              style={{
                padding: "0.875rem 2rem",
                background: isSearching || !query.trim() ? "#d1d5db" : "linear-gradient(135deg, #3b82f6 0%, #2563eb 100%)",
                color: "white",
                border: "none",
                borderRadius: "10px",
                fontSize: "1rem",
                fontWeight: 600,
                cursor: isSearching || !query.trim() ? "not-allowed" : "pointer",
                display: "flex",
                alignItems: "center",
                gap: "0.5rem",
                transition: "all 0.2s ease",
                boxShadow: isSearching || !query.trim() ? "none" : "0 4px 12px rgba(59, 130, 246, 0.3)"
              }}
              onMouseEnter={(e) => {
                if (!isSearching && query.trim()) {
                  e.currentTarget.style.transform = "translateY(-2px)";
                  e.currentTarget.style.boxShadow = "0 6px 16px rgba(59, 130, 246, 0.4)";
                }
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.transform = "translateY(0)";
              }}
            >
              {isSearching ? (
                <>
                  <Loader2 size={18} style={{ animation: "spin 1s linear infinite" }} />
                  Searching...
                </>
              ) : (
                <>
                  <Search size={18} />
                  Search
                </>
              )}
            </button>
            <button
              onClick={() => setShowFilters(!showFilters)}
              style={{
                padding: "0.875rem 1.25rem",
                background: showFilters ? "#eff6ff" : "white",
                color: showFilters ? "#3b82f6" : "#6b7280",
                border: `1px solid ${showFilters ? "#3b82f6" : "#e5e7eb"}`,
                borderRadius: "10px",
                fontSize: "1rem",
                fontWeight: 600,
                cursor: "pointer",
                display: "flex",
                alignItems: "center",
                gap: "0.5rem",
                transition: "all 0.2s ease"
              }}
            >
              <Filter size={18} />
              Filters
            </button>
          </div>

          {/* Filters Panel */}
          {showFilters && (
            <div style={{
              marginTop: "1.5rem",
              padding: "1.5rem",
              background: "#f9fafb",
              border: "1px solid #e5e7eb",
              borderRadius: "12px",
              animation: "fadeIn 0.3s ease-out"
            }}>
              <div style={{ marginBottom: "1.25rem" }}>
                <div style={{ fontSize: "0.875rem", fontWeight: 600, color: "#374151", marginBottom: "0.75rem" }}>
                  Segment Types
                </div>
                <div style={{ display: "flex", flexWrap: "wrap", gap: "0.5rem" }}>
                  {Object.entries(SEGMENT_TYPE_LABELS).map(([type, info]) => (
                    <button
                      key={type}
                      onClick={() => toggleSegmentType(type)}
                      style={{
                        padding: "0.5rem 1rem",
                        background: selectedSegmentTypes.includes(type) ? info.color : "white",
                        color: selectedSegmentTypes.includes(type) ? "white" : "#374151",
                        border: `1px solid ${selectedSegmentTypes.includes(type) ? info.color : "#e5e7eb"}`,
                        borderRadius: "8px",
                        fontSize: "0.875rem",
                        fontWeight: 500,
                        cursor: "pointer",
                        display: "flex",
                        alignItems: "center",
                        gap: "0.375rem",
                        transition: "all 0.2s ease"
                      }}
                    >
                      {info.icon}
                      {info.label}
                    </button>
                  ))}
                </div>
              </div>

              <div>
                <div style={{ fontSize: "0.875rem", fontWeight: 600, color: "#374151", marginBottom: "0.75rem" }}>
                  Minimum Similarity Score: {minScore.toFixed(2)}
                </div>
                <input
                  type="range"
                  min="0"
                  max="1"
                  step="0.1"
                  value={minScore}
                  onChange={(e) => setMinScore(parseFloat(e.target.value))}
                  style={{ width: "100%" }}
                />
              </div>

              {(selectedSegmentTypes.length > 0 || minScore > 0) && (
                <button
                  onClick={() => {
                    setSelectedSegmentTypes([]);
                    setMinScore(0.0);
                  }}
                  style={{
                    marginTop: "1rem",
                    padding: "0.5rem 1rem",
                    background: "white",
                    color: "#6b7280",
                    border: "1px solid #e5e7eb",
                    borderRadius: "8px",
                    fontSize: "0.875rem",
                    fontWeight: 500,
                    cursor: "pointer",
                    display: "flex",
                    alignItems: "center",
                    gap: "0.375rem"
                  }}
                >
                  <X size={14} />
                  Clear Filters
                </button>
              )}
            </div>
          )}
        </div>

        {/* Error Message */}
        {error && (
          <div style={{
            background: "#fef2f2",
            border: "1px solid #fecaca",
            borderRadius: "12px",
            padding: "1.25rem",
            marginBottom: "2rem",
            display: "flex",
            alignItems: "start",
            gap: "0.75rem",
            animation: "fadeIn 0.4s ease-out"
          }}>
            <div style={{ color: "#dc2626", fontSize: "1.25rem" }}>⚠️</div>
            <div>
              <div style={{ fontWeight: 600, color: "#991b1b", marginBottom: "0.25rem" }}>Search Error</div>
              <div style={{ color: "#dc2626", fontSize: "0.875rem" }}>{error}</div>
            </div>
          </div>
        )}

        {/* Search Results */}
        {searchResults && (
          <div style={{ animation: "fadeIn 0.4s ease-out" }}>
            {/* Results Header */}
            <div style={{ marginBottom: "1.5rem", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <div>
                <div style={{ fontSize: "1.125rem", fontWeight: 600, color: "#111827", marginBottom: "0.25rem" }}>
                  {searchResults.total_results} {searchResults.total_results === 1 ? "result" : "results"} found
                </div>
                {query && (
                  <div style={{ fontSize: "0.875rem", color: "#6b7280" }}>
                    for "{query}"
                  </div>
                )}
              </div>
            </div>

            {/* Results List */}
            {searchResults.results.length > 0 ? (
              <>
                <div style={{ display: "flex", flexDirection: "column", gap: "1rem", marginBottom: "2rem" }}>
                  {searchResults.results.map((result: SearchResult, idx: number) => {
                    const typeInfo = getSegmentTypeInfo(result.segment_type);
                    return (
                      <div
                        key={idx}
                        style={{
                          background: "white",
                          border: "1px solid #e5e7eb",
                          borderRadius: "12px",
                          padding: "1.5rem",
                          transition: "all 0.2s ease",
                          cursor: "pointer"
                        }}
                        onMouseEnter={(e) => {
                          e.currentTarget.style.borderColor = "#3b82f6";
                          e.currentTarget.style.boxShadow = "0 4px 12px rgba(59, 130, 246, 0.1)";
                        }}
                        onMouseLeave={(e) => {
                          e.currentTarget.style.borderColor = "#e5e7eb";
                          e.currentTarget.style.boxShadow = "none";
                        }}
                        onClick={() => navigate(`/insights/${result.meeting_id}`)}
                      >
                        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "start", marginBottom: "0.75rem" }}>
                          <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
                            <div style={{
                              padding: "0.375rem 0.75rem",
                              background: `${typeInfo.color}15`,
                              color: typeInfo.color,
                              borderRadius: "6px",
                              fontSize: "0.75rem",
                              fontWeight: 600,
                              display: "flex",
                              alignItems: "center",
                              gap: "0.375rem"
                            }}>
                              {typeInfo.icon}
                              {typeInfo.label}
                            </div>
                            {result.timestamp && (
                              <div style={{ fontSize: "0.75rem", color: "#6b7280" }}>
                                {formatTimestamp(result.timestamp)}
                              </div>
                            )}
                          </div>
                          <div style={{
                            padding: "0.25rem 0.75rem",
                            background: "#f3f4f6",
                            borderRadius: "6px",
                            fontSize: "0.75rem",
                            fontWeight: 600,
                            color: "#374151"
                          }}>
                            {(result.similarity_score * 100).toFixed(0)}% match
                          </div>
                        </div>
                        <div style={{ fontSize: "0.95rem", color: "#111827", lineHeight: 1.6, marginBottom: "0.75rem" }}>
                          {result.text}
                        </div>
                        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                          <div style={{ fontSize: "0.875rem", color: "#6b7280" }}>
                            Meeting: <span style={{ fontWeight: 600, color: "#111827" }}>{result.meeting_id}</span>
                          </div>
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              navigate(`/insights/${result.meeting_id}`);
                            }}
                            style={{
                              padding: "0.5rem 1rem",
                              background: "#f3f4f6",
                              color: "#374151",
                              border: "none",
                              borderRadius: "6px",
                              fontSize: "0.875rem",
                              fontWeight: 500,
                              cursor: "pointer",
                              transition: "all 0.2s ease"
                            }}
                            onMouseEnter={(e) => {
                              e.currentTarget.style.background = "#e5e7eb";
                            }}
                            onMouseLeave={(e) => {
                              e.currentTarget.style.background = "#f3f4f6";
                            }}
                          >
                            View Meeting →
                          </button>
                        </div>
                      </div>
                    );
                  })}
                </div>

                {/* Pagination */}
                {searchResults.total_pages > 1 && (
                  <div style={{
                    display: "flex",
                    justifyContent: "center",
                    alignItems: "center",
                    gap: "0.5rem",
                    marginTop: "2rem"
                  }}>
                    <button
                      onClick={() => handleSearch(currentPage - 1)}
                      disabled={currentPage === 1 || isSearching}
                      style={{
                        padding: "0.5rem 1rem",
                        background: currentPage === 1 ? "#f3f4f6" : "white",
                        color: currentPage === 1 ? "#9ca3af" : "#374151",
                        border: "1px solid #e5e7eb",
                        borderRadius: "8px",
                        fontSize: "0.875rem",
                        fontWeight: 500,
                        cursor: currentPage === 1 ? "not-allowed" : "pointer",
                        display: "flex",
                        alignItems: "center",
                        gap: "0.375rem"
                      }}
                    >
                      <ChevronLeft size={16} />
                      Previous
                    </button>
                    <div style={{
                      padding: "0.5rem 1rem",
                      background: "white",
                      border: "1px solid #e5e7eb",
                      borderRadius: "8px",
                      fontSize: "0.875rem",
                      fontWeight: 600,
                      color: "#111827"
                    }}>
                      Page {currentPage} of {searchResults.total_pages}
                    </div>
                    <button
                      onClick={() => handleSearch(currentPage + 1)}
                      disabled={currentPage === searchResults.total_pages || isSearching}
                      style={{
                        padding: "0.5rem 1rem",
                        background: currentPage === searchResults.total_pages ? "#f3f4f6" : "white",
                        color: currentPage === searchResults.total_pages ? "#9ca3af" : "#374151",
                        border: "1px solid #e5e7eb",
                        borderRadius: "8px",
                        fontSize: "0.875rem",
                        fontWeight: 500,
                        cursor: currentPage === searchResults.total_pages ? "not-allowed" : "pointer",
                        display: "flex",
                        alignItems: "center",
                        gap: "0.375rem"
                      }}
                    >
                      Next
                      <ChevronRight size={16} />
                    </button>
                  </div>
                )}
              </>
            ) : (
              <div style={{
                background: "white",
                border: "1px solid #e5e7eb",
                borderRadius: "12px",
                padding: "3rem",
                textAlign: "center"
              }}>
                <div style={{ fontSize: "3rem", marginBottom: "1rem" }}>🔍</div>
                <div style={{ fontSize: "1.125rem", fontWeight: 600, color: "#111827", marginBottom: "0.5rem" }}>
                  No results found
                </div>
                <div style={{ fontSize: "0.95rem", color: "#6b7280" }}>
                  Try adjusting your search query or filters
                </div>
              </div>
            )}
          </div>
        )}

        {/* Empty State */}
        {!searchResults && !isSearching && (
          <div style={{
            background: "white",
            border: "1px solid #e5e7eb",
            borderRadius: "12px",
            padding: "3rem",
            textAlign: "center",
            animation: "fadeIn 0.4s ease-out"
          }}>
            <div style={{ fontSize: "3rem", marginBottom: "1rem" }}>🔍</div>
            <div style={{ fontSize: "1.125rem", fontWeight: 600, color: "#111827", marginBottom: "0.5rem" }}>
              Search across all meetings
            </div>
            <div style={{ fontSize: "0.95rem", color: "#6b7280", marginBottom: "1.5rem" }}>
              Enter a query above to find relevant content from your meeting history
            </div>
            {stats && stats.total_vectors === 0 && (
              <div style={{
                padding: "1rem",
                background: "#fef3c7",
                border: "1px solid #fde047",
                borderRadius: "8px",
                fontSize: "0.875rem",
                color: "#92400e"
              }}>
                ⚠️ No meetings indexed yet. Upload a meeting first to enable search.
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

