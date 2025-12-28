import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Menu } from "lucide-react";
import { Sidebar } from "./Sidebar";

export function Header() {
  const navigate = useNavigate();
  const [sidebarOpen, setSidebarOpen] = useState(false);

  return (
    <>
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
          maxWidth: 1400, 
          margin: "0 auto", 
          padding: "1rem 1.5rem",
          display: "flex",
          alignItems: "center",
          gap: "1rem"
        }}>
          {/* Sidebar Button - Left Side */}
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
              transition: "all 0.2s ease",
              flexShrink: 0,
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

          {/* Logo and Title */}
          <div 
            onClick={() => navigate("/projects")}
            style={{ display: "flex", alignItems: "center", gap: "0.75rem", cursor: "pointer", flex: 1 }}
          >
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
              boxShadow: "0 4px 12px rgba(59, 130, 246, 0.3)",
              transition: "transform 0.2s ease, box-shadow 0.2s ease"
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.transform = "scale(1.05)";
              e.currentTarget.style.boxShadow = "0 6px 16px rgba(59, 130, 246, 0.4)";
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.transform = "scale(1)";
              e.currentTarget.style.boxShadow = "0 4px 12px rgba(59, 130, 246, 0.3)";
            }}
            >
              MI
            </div>
            <div>
              <div style={{ fontWeight: 700, fontSize: "1.125rem", color: "#111827", lineHeight: 1.2 }}>
                Meeting Insight
              </div>
              <div style={{ fontSize: "0.75rem", color: "#6b7280" }}>
                AI-Powered Meeting Analysis
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Sidebar */}
      <Sidebar isOpen={sidebarOpen} onClose={() => setSidebarOpen(false)} />
    </>
  );
}
