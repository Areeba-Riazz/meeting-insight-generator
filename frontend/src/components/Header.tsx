import React, { useState } from "react";
import { Menu, X } from "lucide-react";

export function Header() {
  const [sidebarOpen, setSidebarOpen] = useState(false);

  return (
    <>
      <style>{`
        @keyframes slideIn {
          from { transform: translateX(100%); }
          to { transform: translateX(0); }
        }
        @keyframes fadeIn {
          from { opacity: 0; }
          to { opacity: 1; }
        }
      `}</style>

      {/* Header */}
      <header style={{ 
        background: "rgba(255, 255, 255, 0.95)", 
        backdropFilter: "blur(10px)",
        borderBottom: "1px solid #e5e7eb",
        position: "sticky",
        top: 0,
        zIndex: 50
      }}>
        <div style={{ 
          maxWidth: 1200, 
          margin: "0 auto", 
          padding: "1rem 0rem",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between"
        }}>
          <div style={{ display: "flex", alignItems: "center", gap: "0.75rem" }}>
            <div style={{ 
              width: "2.5rem", 
              height: "2.5rem", 
              background: "linear-gradient(135deg, #3b82f6 0%, #2563eb 100%)",
              borderRadius: "8px",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              fontWeight: 700,
              fontSize: "1rem",
              color: "white",
              boxShadow: "0 4px 12px rgba(59, 130, 246, 0.3)"
            }}>
              MI
            </div>
            <div>
              <div style={{ fontWeight: 700, fontSize: "1.125rem", color: "#111827", lineHeight: 1.2 }}>
                Meeting Insight
              </div>
              <div style={{ fontSize: "0.75rem", color: "#6b7280" }}>
                Audio/Video → Insights
              </div>
            </div>
          </div>

          <button
            onClick={() => setSidebarOpen(!sidebarOpen)}
            style={{
              padding: "0.5rem",
              background: "transparent",
              border: "1px solid #e5e7eb",
              borderRadius: "6px",
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
              e.currentTarget.style.background = "transparent";
              e.currentTarget.style.borderColor = "#e5e7eb";
            }}
          >
            <Menu style={{ width: "1.25rem", height: "1.25rem", color: "#374151" }} />
          </button>
        </div>
      </header>

      {/* Sidebar */}
      <div style={{
        position: "fixed",
        top: 0,
        right: 0,
        width: "320px",
        height: "100vh",
        background: "white",
        boxShadow: sidebarOpen ? "-4px 0 24px rgba(0, 0, 0, 0.15)" : "none",
        transform: sidebarOpen ? "translateX(0)" : "translateX(100%)",
        transition: "transform 0.3s ease, box-shadow 0.3s ease",
        zIndex: 100,
        overflowY: "auto"
      }}>
        <div style={{ padding: "1.5rem" }}>
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "2rem" }}>
            <h3 style={{ fontSize: "1.125rem", fontWeight: 600, color: "#111827", margin: 0 }}>
              Previous Insights
            </h3>
            <button
              onClick={() => setSidebarOpen(false)}
              style={{
                padding: "0.25rem",
                background: "transparent",
                border: "none",
                cursor: "pointer",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                borderRadius: "4px",
                transition: "background 0.2s ease"
              }}
              onMouseEnter={(e) => e.currentTarget.style.background = "#f3f4f6"}
              onMouseLeave={(e) => e.currentTarget.style.background = "transparent"}
            >
              <X style={{ width: "1.25rem", height: "1.25rem", color: "#6b7280" }} />
            </button>
          </div>
          
          {/* Placeholder for previous insights */}
          <div style={{ 
            color: "#9ca3af", 
            fontSize: "0.875rem", 
            textAlign: "center", 
            padding: "3rem 1rem",
            background: "#f9fafb",
            borderRadius: "8px",
            border: "1px dashed #e5e7eb"
          }}>
            <div style={{ fontSize: "2rem", marginBottom: "0.75rem" }}>📝</div>
            <div style={{ fontWeight: 500, color: "#6b7280", marginBottom: "0.25rem" }}>
              No insights yet
            </div>
            <div style={{ fontSize: "0.8rem" }}>
              Upload a meeting to get started
            </div>
          </div>

          {/* Example of what insight items could look like */}
          {/* Uncomment and populate with real data:
          <div style={{ display: "flex", flexDirection: "column", gap: "0.75rem" }}>
            <div style={{
              padding: "1rem",
              background: "#f9fafb",
              border: "1px solid #e5e7eb",
              borderRadius: "8px",
              cursor: "pointer",
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
              <div style={{ fontSize: "0.875rem", fontWeight: 600, color: "#111827", marginBottom: "0.25rem" }}>
                Team Standup - Dec 20
              </div>
              <div style={{ fontSize: "0.75rem", color: "#6b7280" }}>
                mtg_abc123xyz
              </div>
            </div>
          </div>
          */}
        </div>
      </div>

      {/* Overlay */}
      {sidebarOpen && (
        <div 
          onClick={() => setSidebarOpen(false)}
          style={{
            position: "fixed",
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            background: "rgba(0, 0, 0, 0.3)",
            zIndex: 90,
            animation: "fadeIn 0.2s ease"
          }}
        />
      )}
    </>
  );
}