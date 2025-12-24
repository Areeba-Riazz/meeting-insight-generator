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
};
