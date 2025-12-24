import React, { useState } from "react";
import { Upload, X, File as FileIcon } from "lucide-react";

type Props = {
  onUpload: (file: File) => Promise<void>;
  isUploading: boolean;
};

const ACCEPT = "audio/*,video/mp4,video/x-matroska,video/quicktime";

export function UploadForm({ onUpload, isUploading }: Props) {
  const [file, setFile] = useState<File | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [dragging, setDragging] = useState(false);

  const reset = () => {
    setFile(null);
    setError(null);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file) {
      setError("Please select a file");
      return;
    }
    setError(null);
    await onUpload(file);
  };

  const handleFiles = (files: FileList | null) => {
    if (!files || files.length === 0) {
      setFile(null);
      return;
    }
    const selected = files[0];
    setFile(selected);
    setError(null);
  };

  const onDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragging(false);
    handleFiles(e.dataTransfer.files);
  };

  const onDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragging(true);
  };

  const onDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragging(false);
  };

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "1.25rem" }}>
      <style>{`
        @keyframes shimmer {
          0% { background-position: -200% 0; }
          100% { background-position: 200% 0; }
        }
        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
      `}</style>

      {/* Drop Zone */}
      <div
        onDrop={onDrop}
        onDragOver={onDragOver}
        onDragLeave={onDragLeave}
        style={{
          border: `2px dashed ${dragging ? "#171717" : file ? "#16a34a" : "#d4d4d4"}`,
          borderRadius: "10px",
          padding: file ? "1.5rem" : "3rem 1.5rem",
          background: dragging ? "#fafafa" : file ? "#f0fdf4" : "#ffffff",
          transition: "all 0.2s ease",
          cursor: file ? "default" : "pointer",
          position: "relative"
        }}
      >
        {!file ? (
          <div style={{ textAlign: "center" }}>
            <div style={{ 
              width: "3rem", 
              height: "3rem", 
              background: dragging ? "#171717" : "#fafafa",
              border: "1px solid #e5e5e5",
              borderRadius: "8px",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              margin: "0 auto 1.25rem",
              transition: "all 0.2s ease"
            }}>
              <Upload style={{ width: "1.5rem", height: "1.5rem", color: dragging ? "white" : "#171717" }} />
            </div>

            <div style={{ fontSize: "1rem", fontWeight: 600, color: "#171717", marginBottom: "0.5rem" }}>
              {dragging ? "Drop your file here" : "Drag and drop your file"}
            </div>

            <div style={{ fontSize: "0.875rem", color: "#737373", marginBottom: "1.5rem" }}>
              or click to browse
            </div>

            <label style={{
              display: "inline-flex",
              alignItems: "center",
              gap: "0.5rem",
              padding: "0.625rem 1.25rem",
              background: "#171717",
              color: "white",
              borderRadius: "6px",
              fontSize: "0.875rem",
              fontWeight: 600,
              cursor: "pointer",
              border: "none",
              transition: "background 0.2s ease"
            }}
            onMouseEnter={(e) => e.currentTarget.style.background = "#0a0a0a"}
            onMouseLeave={(e) => e.currentTarget.style.background = "#171717"}
            >
              <FileIcon style={{ width: "0.875rem", height: "0.875rem" }} />
              Choose File
              <input
                type="file"
                accept={ACCEPT}
                onChange={(e) => handleFiles(e.target.files)}
                disabled={isUploading}
                style={{ display: "none" }}
              />
            </label>
          </div>
        ) : (
          <div style={{ display: "flex", alignItems: "center", gap: "1rem" }}>
            <div style={{
              width: "2.5rem",
              height: "2.5rem",
              background: "#16a34a",
              borderRadius: "6px",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              flexShrink: 0
            }}>
              <FileIcon style={{ width: "1.25rem", height: "1.25rem", color: "white" }} />
            </div>
            <div style={{ flex: 1, minWidth: 0 }}>
              <div style={{
                fontSize: "0.95rem",
                fontWeight: 600,
                color: "#171717",
                marginBottom: "0.25rem",
                overflow: "hidden",
                textOverflow: "ellipsis",
                whiteSpace: "nowrap"
              }}>
                {file.name}
              </div>
              <div style={{ fontSize: "0.8rem", color: "#737373" }}>
                {formatFileSize(file.size)}
              </div>
            </div>
            {!isUploading && (
              <button
                onClick={reset}
                style={{
                  width: "2rem",
                  height: "2rem",
                  background: "white",
                  border: "1px solid #e5e5e5",
                  borderRadius: "6px",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  cursor: "pointer",
                  flexShrink: 0,
                  transition: "all 0.2s ease"
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.background = "#fef2f2";
                  e.currentTarget.style.borderColor = "#fca5a5";
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.background = "white";
                  e.currentTarget.style.borderColor = "#e5e5e5";
                }}
              >
                <X style={{ width: "1rem", height: "1rem", color: "#737373" }} />
              </button>
            )}
          </div>
        )}
      </div>

      {/* Upload Button */}
      {file && (
        <button
          onClick={handleSubmit}
          disabled={isUploading || !file}
          style={{
            width: "100%",
            padding: "0.875rem",
            background: isUploading || !file ? "#e5e5e5" : "#171717",
            color: isUploading || !file ? "#a3a3a3" : "white",
            border: "none",
            borderRadius: "8px",
            fontSize: "0.95rem",
            fontWeight: 600,
            cursor: isUploading || !file ? "not-allowed" : "pointer",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            gap: "0.5rem",
            transition: "background 0.2s ease"
          }}
          onMouseEnter={(e) => {
            if (!isUploading && file) e.currentTarget.style.background = "#0a0a0a";
          }}
          onMouseLeave={(e) => {
            if (!isUploading && file) e.currentTarget.style.background = "#171717";
          }}
        >
          {isUploading ? (
            <>
              <div style={{
                width: "1rem",
                height: "1rem",
                border: "2px solid currentColor",
                borderTopColor: "transparent",
                borderRadius: "50%",
                animation: "spin 1s linear infinite"
              }} />
              Uploading...
            </>
          ) : (
            <>
              <Upload style={{ width: "1rem", height: "1rem" }} />
              Upload & Process
            </>
          )}
        </button>
      )}

      {/* Upload Progress Bar */}
      {isUploading && (
        <div style={{ 
          background: "#f5f5f5", 
          height: "6px", 
          borderRadius: "999px",
          overflow: "hidden"
        }}>
          <div style={{
            width: "100%",
            height: "100%",
            background: "linear-gradient(90deg, #171717 0%, #525252 50%, #171717 100%)",
            backgroundSize: "200% 100%",
            animation: "shimmer 1.5s ease-in-out infinite"
          }} />
        </div>
      )}

      {/* Error Message */}
      {error && (
        <div style={{ 
          padding: "0.875rem",
          background: "#fef2f2",
          border: "1px solid #fca5a5",
          borderRadius: "6px",
          fontSize: "0.875rem",
          color: "#dc2626"
        }}>
          {error}
        </div>
      )}
    </div>
  );
}