import React, { useEffect } from "react";

export type ToastType = "error" | "success" | "info";

export interface Toast {
  id: string;
  message: string;
  type: ToastType;
}

interface ToastProps {
  toast: Toast;
  onDismiss: (id: string) => void;
}

export function ToastItem({ toast, onDismiss }: ToastProps) {
  useEffect(() => {
    const timer = setTimeout(() => {
      onDismiss(toast.id);
    }, 5000);

    return () => clearTimeout(timer);
  }, [toast.id, onDismiss]);

  const bgColor =
    toast.type === "error"
      ? "#fef2f2"
      : toast.type === "success"
      ? "#f0fdf4"
      : "#eff6ff";

  const borderColor =
    toast.type === "error"
      ? "#fecaca"
      : toast.type === "success"
      ? "#bbf7d0"
      : "#bfdbfe";

  const textColor =
    toast.type === "error"
      ? "#b91c1c"
      : toast.type === "success"
      ? "#16a34a"
      : "#1e40af";

  return (
    <div
      style={{
        background: bgColor,
        border: `1px solid ${borderColor}`,
        borderRadius: 8,
        padding: "12px 16px",
        marginBottom: 8,
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        boxShadow: "0 4px 6px -1px rgba(0, 0, 0, 0.1)",
        minWidth: 300,
        maxWidth: 500,
      }}
    >
      <div style={{ color: textColor, fontWeight: 500, flex: 1 }}>{toast.message}</div>
      <button
        onClick={() => onDismiss(toast.id)}
        style={{
          background: "none",
          border: "none",
          color: textColor,
          cursor: "pointer",
          fontSize: 20,
          lineHeight: 1,
          padding: 0,
          marginLeft: 12,
          opacity: 0.7,
        }}
      >
        ×
      </button>
    </div>
  );
}

interface ToastContainerProps {
  toasts: Toast[];
  onDismiss: (id: string) => void;
}

export function ToastContainer({ toasts, onDismiss }: ToastContainerProps) {
  if (toasts.length === 0) return null;

  return (
    <div
      style={{
        position: "fixed",
        top: 20,
        right: 20,
        zIndex: 10000,
        display: "flex",
        flexDirection: "column",
        alignItems: "flex-end",
      }}
    >
      {toasts.map((toast) => (
        <ToastItem key={toast.id} toast={toast} onDismiss={onDismiss} />
      ))}
    </div>
  );
}
