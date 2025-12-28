import type { 
  UploadResponse, 
  StatusResponse, 
  InsightsResponse, 
  SearchRequest, 
  SearchResponse, 
  SearchStats,
  Project,
  ProjectMeeting,
  CreateProjectRequest,
  UpdateProjectRequest,
  ProjectListResponse,
  ProjectMeetingsResponse,
} from "../types/api";

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:3000";

export async function uploadMeeting(
  file: File,
  projectId?: string,
  onProgress?: (progress: number) => void
): Promise<UploadResponse> {
  const formData = new FormData();
  formData.append("file", file);

  // Build URL with optional project_id
  let url = `${API_BASE}/api/v1/upload`;
  if (projectId) {
    url += `?project_id=${encodeURIComponent(projectId)}`;
  }

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
    xhr.open("POST", url);
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

// Project management functions
export async function createProject(request: CreateProjectRequest): Promise<Project> {
  const res = await fetch(`${API_BASE}/api/v1/projects`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(request),
  });
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(errorData.detail || `Failed to create project: ${res.statusText}`);
  }
  return res.json();
}

export async function getProject(projectId: string): Promise<Project> {
  const res = await fetch(`${API_BASE}/api/v1/projects/${projectId}`);
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(errorData.detail || `Failed to fetch project: ${res.statusText}`);
  }
  return res.json();
}

export async function listProjects(skip = 0, limit = 100): Promise<ProjectListResponse> {
  const res = await fetch(`${API_BASE}/api/v1/projects?skip=${skip}&limit=${limit}`);
  if (!res.ok) {
    throw new Error(`Failed to fetch projects: ${res.statusText}`);
  }
  return res.json();
}

export async function updateProject(
  projectId: string,
  request: UpdateProjectRequest
): Promise<Project> {
  const res = await fetch(`${API_BASE}/api/v1/projects/${projectId}`, {
    method: "PUT",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(request),
  });
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(errorData.detail || `Failed to update project: ${res.statusText}`);
  }
  return res.json();
}

export async function deleteProject(projectId: string): Promise<{ success: boolean }> {
  const res = await fetch(`${API_BASE}/api/v1/projects/${projectId}`, {
    method: "DELETE",
  });
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(errorData.detail || `Failed to delete project: ${res.statusText}`);
  }
  return { success: true };
}

// Project meetings functions
export async function getProjectMeetings(
  projectId: string,
  skip = 0,
  limit = 100
): Promise<ProjectMeetingsResponse> {
  const res = await fetch(
    `${API_BASE}/api/v1/projects/${projectId}/meetings?skip=${skip}&limit=${limit}`
  );
  if (!res.ok) {
    throw new Error(`Failed to fetch project meetings: ${res.statusText}`);
  }
  return res.json();
}

export async function getProjectMeeting(
  projectId: string,
  meetingId: string
): Promise<ProjectMeeting> {
  const res = await fetch(
    `${API_BASE}/api/v1/projects/${projectId}/meetings/${meetingId}`
  );
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(errorData.detail || `Failed to fetch meeting: ${res.statusText}`);
  }
  return res.json();
}

export async function deleteProjectMeeting(
  projectId: string,
  meetingId: string
): Promise<{ success: boolean }> {
  const res = await fetch(
    `${API_BASE}/api/v1/projects/${projectId}/meetings/${meetingId}`,
    {
      method: "DELETE",
    }
  );
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(errorData.detail || `Failed to delete meeting: ${res.statusText}`);
  }
  return { success: true };
}

// Chat functions
export interface ChatRequest {
  message: string;
  context?: string;
  project_id?: string;
}

export interface ChatResponse {
  response: string;
  sources?: Array<{
    meeting_id: string;
    segment_type: string;
    text: string;
    similarity?: number;
  }>;
  used_rag?: boolean;
}

export async function sendChatMessage(
  message: string,
  context?: string,
  project_id?: string
): Promise<ChatResponse> {
  const res = await fetch(`${API_BASE}/api/v1/chat`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ message, context, project_id }),
  });
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(errorData.detail || `Chat failed: ${res.statusText}`);
  }
  return res.json();
}

