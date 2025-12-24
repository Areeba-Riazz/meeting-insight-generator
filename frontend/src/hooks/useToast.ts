import { useState, useCallback } from "react";
import { Toast, ToastType } from "../components/Toast";

let toastIdCounter = 0;

export function useToast() {
  const [toasts, setToasts] = useState<Toast[]>([]);

  const showToast = useCallback((message: string, type: ToastType = "info") => {
    const id = `toast-${++toastIdCounter}`;
    const newToast: Toast = { id, message, type };
    setToasts((prev) => [...prev, newToast]);
  }, []);

  const dismissToast = useCallback((id: string) => {
    setToasts((prev) => prev.filter((toast) => toast.id !== id));
  }, []);

  const showError = useCallback((message: string) => {
    showToast(message, "error");
  }, [showToast]);

  const showSuccess = useCallback((message: string) => {
    showToast(message, "success");
  }, [showToast]);

  const showInfo = useCallback((message: string) => {
    showToast(message, "info");
  }, [showToast]);

  return {
    toasts,
    showToast,
    dismissToast,
    showError,
    showSuccess,
    showInfo,
  };
}
