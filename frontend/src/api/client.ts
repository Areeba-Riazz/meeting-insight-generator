import type { UploadResponse, StatusResponse, InsightsResponse, SearchRequest, SearchResponse, SearchStats } from "../types/api";

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:3000";

export async function uploadMeeting(
  file: File,
  onProgress?: (progress: number) => void
): Promise<UploadResponse> {
  const formData = new FormData();
  formData.append("file", file);

  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();

    // Track upload progress
    xhr.upload.onprogress = (event) => {
      if (event.lengthComputable && onProgress) {
        const percentComplete = Math.round((event.loaded / event.total) * 100);
        onProgress(percentComplete);
      }
    };

    // Handle completion
    xhr.onload = () => {
      if (xhr.status >= 200 && xhr.status < 300) {
        try {
          const response = JSON.parse(xhr.responseText);
          resolve(response);
        } catch (error) {
          reject(new Error("Failed to parse response"));
        }
      } else {
        // Handle error responses
        let errorMessage = `Upload failed: ${xhr.statusText}`;
        try {
          const errorData = JSON.parse(xhr.responseText);
          if (errorData.detail) {
            errorMessage = errorData.detail;
          }
        } catch {
          // If response is not JSON, use default message
        }
        reject(new Error(errorMessage));
      }
    };

    // Handle network errors
    xhr.onerror = () => {
      reject(new Error("CONNECTION_ERROR: Backend server is not connected. Please check if the server is running."));
    };

    // Handle timeout
    xhr.ontimeout = () => {
      reject(new Error("Upload timeout. Please try again."));
    };

    // Open and send request
    xhr.open("POST", `${API_BASE}/api/v1/upload`);
    xhr.send(formData);
  });
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

export interface Meeting {
  meeting_id: string;
  uuid: string;
  meeting_name: string;
  upload_timestamp: string;
  file_info: {
    original_filename: string;
    size_bytes: number;
    content_type: string;
  };
  has_insights: boolean;
  has_transcript: boolean;
}

export async function listMeetings(): Promise<{ meetings: Meeting[] }> {
  const res = await fetch(`${API_BASE}/api/v1/meetings`);
  if (!res.ok) {
    throw new Error(`Failed to fetch meetings: ${res.statusText}`);
  }
  return res.json();
}

export async function searchMeetings(request: SearchRequest): Promise<SearchResponse> {
  const res = await fetch(`${API_BASE}/api/v1/search`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(request),
  });
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(errorData.detail || `Search failed: ${res.statusText}`);
  }
  return res.json();
}

export async function getSearchStats(): Promise<SearchStats> {
  const res = await fetch(`${API_BASE}/api/v1/search/stats`);
  if (!res.ok) {
    throw new Error(`Failed to fetch search stats: ${res.statusText}`);
  }
  return res.json();
}

