// Shared types for frontend and backend communication for Selfrag

export interface ChatMessage {
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp?: string;
}

export interface GenerateRequest {
  prompt: string;
  model?: string;
  stream?: boolean;
  temperature?: number;
}

export interface GenerateResponse {
  response: string;
  model: string;
  done: boolean;
}

export interface AskRequest {
  question: string;
  model?: string;
  temperature?: number;
}

export interface AskResponse {
  answer: string;
  model: string;
}

export interface ErrorResponse {
  error: string;
  message: string;
  detail?: string;
  timestamp?: string;
}

export interface ModelInfo {
  name: string;
  size?: number;
  digest?: string;
  details?: Record<string, any>;
}

export interface HealthCheck {
  status: 'healthy' | 'unhealthy' | 'degraded';
  localai_connected: boolean;
  timestamp?: string;
  version?: string;
}
