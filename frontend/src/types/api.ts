export type UploadResponse = {
  meeting_id: string;
  status: string;
};

export type StatusResponse = {
  meeting_id: string;
  status: string;
  progress?: number;  // 0-100
  stage?: string;
  estimated_time_remaining?: number;  // seconds
};

export type TranscriptSegment = {
  text: string;
  start: number;
  end: number;
  speaker?: string | null;
};

export type Transcript = {
  text: string;
  segments: TranscriptSegment[];
  model: string;
};

export type InsightsPayload = {
  transcript?: Transcript;
  topics?: Array<{ topic?: string; start?: number; end?: number; summary?: string }>;
  decisions?: Array<{ decision?: string; participants?: string[]; rationale?: string; evidence?: string }>;
  action_items?: Array<{ action?: string; assignee?: string | null; due?: string | null; evidence?: string }>;
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
  summary?: string;
};

export type InsightsResponse = {
  meeting_id: string;
  insights: InsightsPayload;
  file_path?: string;
  legacy_meeting_id?: string;  // For accessing storage files (legacy format)
  original_filename?: string;
};

export type SearchResult = {
  text: string;
  meeting_id: string;
  segment_type: string;
  timestamp?: number | null;
  segment_index?: number | null;
  similarity_score: number;
  distance: number;
  additional_data?: Record<string, any> | null;
};

export type SearchRequest = {
  query: string;
  top_k?: number;
  segment_types?: string[];
  meeting_ids?: string[];
  project_id?: string;
  min_score?: number;
  page?: number;
  page_size?: number;
};

export type SearchResponse = {
  query: string;
  results: SearchResult[];
  total_results: number;
  page: number;
  page_size: number;
  total_pages: number;
  segment_types_filter?: string[] | null;
  meeting_ids_filter?: string[] | null;
};

export type SearchStats = {
  total_vectors: number;
  embedding_dimension?: number | null;
  meetings: Record<string, number>;
  segment_types: Record<string, number>;
};

// Project types
export type Project = {
  id: string;  // UUID
  name: string;
  description?: string;
  created_at: string;
  updated_at: string;
  meetings_count?: number;
};

export type ProjectMeeting = {
  id: string;  // UUID
  project_id: string;
  meeting_name: string;
  original_filename: string;
  file_size_bytes: number;
  content_type?: string;
  status: string;
  upload_timestamp: string;
  processing_completed_at?: string;
  has_insights?: boolean;
  has_transcript?: boolean;
};

export type CreateProjectRequest = {
  name: string;
  description?: string;
};

export type UpdateProjectRequest = {
  name?: string;
  description?: string;
};

export type ProjectListResponse = {
  projects: Project[];
  total: number;
};

export type ProjectMeetingsResponse = {
  meetings: ProjectMeeting[];
  total: number;
};