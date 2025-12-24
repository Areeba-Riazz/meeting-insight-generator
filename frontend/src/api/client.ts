import type { UploadResponse, StatusResponse, InsightsResponse } from "../types/api";

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:3000";

export async function uploadMeeting(file: File): Promise<UploadResponse> {
  const formData = new FormData();
  formData.append("file", file);

  let res: Response;
  try {
    res = await fetch(`${API_BASE}/api/v1/upload`, {
      method: "POST",
      body: formData,
    });
  } catch (error: any) {
    // Network error - backend not connected
    // Check for various network error patterns
    const isNetworkError =
      error.name === "TypeError" ||
      error.message?.includes("Failed to fetch") ||
      error.message?.includes("NetworkError") ||
      error.message?.includes("Network request failed") ||
      error.code === "ERR_NETWORK" ||
      error.code === "ECONNREFUSED";

    if (isNetworkError) {
      throw new Error("CONNECTION_ERROR: Backend server is not connected. Please check if the server is running.");
    }
    throw error;
  }

  if (!res.ok) {
    let errorMessage = `Upload failed: ${res.statusText}`;
    try {
      const errorData = await res.json();
      if (errorData.detail) {
        errorMessage = errorData.detail;
      }
    } catch {
      // If response is not JSON, use default message
    }
    throw new Error(errorMessage);
  }
  return res.json();
}

export async function getStatus(meetingId: string): Promise<StatusResponse> {
  const res = await fetch(`${API_BASE}/api/v1/status/${meetingId}`);
  if (!res.ok) {
    throw new Error(`Status fetch failed: ${res.statusText}`);
  }
  return res.json();
}

export async function getInsights(meetingId: string): Promise<InsightsResponse> {
  const res = await fetch(`${API_BASE}/api/v1/insights/${meetingId}`);
  if (!res.ok) {
    throw new Error(`Insights fetch failed: ${res.statusText}`);
  }
  return res.json();
}

