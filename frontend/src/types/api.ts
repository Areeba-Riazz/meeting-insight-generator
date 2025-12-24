export type UploadResponse = {
  meeting_id: string;
  status: string;
};

export type StatusResponse = {
  meeting_id: string;
  status: string;
};

export type InsightsResponse = {
  meeting_id: string;
  insights: Record<string, any>;
};
export type UploadResponse = {
  meeting_id: string
  status: string
}

export type StatusResponse = {
  meeting_id: string
  status: string
}

export type TranscriptSegment = {
  text: string
  start: number
  end: number
  speaker?: string | null
}

export type Transcript = {
  text: string
  segments: TranscriptSegment[]
  model: string
}

export type InsightsPayload = {
  transcript?: Transcript
  topics?: Array<{ topic?: string; start?: number; end?: number; summary?: string }>
  decisions?: Array<{ decision?: string; participants?: string[]; rationale?: string; evidence?: string }>
  action_items?: Array<{ action?: string; assignee?: string | null; due?: string | null; evidence?: string }>
  sentiments?: Array<{ sentiment?: string; rationale?: string; start?: number; end?: number; text?: string }>
  summary?: string
}

export type InsightsResponse = {
  meeting_id: string
  insights: InsightsPayload
}

