export interface ApiSuccess<T> {
  success: true;
  requestId: string;
  data: T;
}

export interface ApiError {
  success: false;
  requestId: string;
  error: {
    code: string;
    message: string;
    retryable: boolean;
  };
}

export interface AuditItem {
  requestId: string;
  businessCode: string;
  capabilityCode: string;
  callerSystem: string;
  interfacePath: string;
  requestMode: string;
  model: string;
  status: string;
  httpStatus: number;
  errorCode: string | null;
  retryCount: number;
  upstreamCallCount: number;
  promptTokens: number;
  completionTokens: number;
  totalTokens: number;
  durationMs: number;
  promptVersion: string;
  createdAt: string;
}

export interface DashboardData {
  stats: {
    businessRequests: number;
    upstreamCalls: number;
    totalTokens: number;
    successRate: number;
    retryCount: number;
    averageDurationMs: number;
  };
  usageTrend: Array<{
    date: string;
    requestCount: number;
  }>;
  recentRequests: AuditItem[];
  generatedAt: string;
}

export interface HealthData {
  status: string;
  service: string;
  environment: string;
  database: string;
  llmMode: string;
}

export interface SettingsData {
  environment: string;
  mockMode: boolean;
  apiKeyConfigured: boolean;
  baseUrl: string;
  model: string;
  connectTimeoutSeconds: number;
  readTimeoutSeconds: number;
  streamIdleTimeoutSeconds: number;
  maxRetries: number;
  retryDelaysSeconds: number[];
  auditRetentionDays: number;
  internalAuthEnabled: boolean;
  adminAuthConfigured: boolean;
  configurationSource: "environment" | "database";
  updatedBy: string | null;
  updatedAt: string | null;
}

export interface AdminSessionData {
  username: string;
  accessToken: string;
  expiresAt: string;
}

export interface AdminSessionStatus {
  username: string;
  expiresAt: string;
}

export interface ModelListData {
  baseUrl: string;
  models: string[];
}

export interface AdminOperationAuditItem {
  requestId: string;
  actor: string;
  action: string;
  status: string;
  httpStatus: number;
  errorCode: string | null;
  durationMs: number;
  oldBaseUrl: string | null;
  newBaseUrl: string | null;
  oldModel: string | null;
  newModel: string | null;
  createdAt: string;
}

export interface AdminOperationAuditList {
  items: AdminOperationAuditItem[];
  page: number;
  pageSize: number;
  total: number;
}

export interface ResumeParseResult {
  name: string | null;
  school: string | null;
  major: string | null;
  graduationTime: string | null;
  skills: string[];
  projects: Array<{
    name: string;
    summary: string;
    technologies: string[];
    risks: string[];
  }>;
}

export interface ScreeningResult {
  matchScore: number;
  recommendation: string;
  confidence: number;
  strengths: string[];
  risks: string[];
  interviewFocus: string[];
  finalComment: string;
}

export interface InterviewKitResult {
  questions: Array<{
    type: string;
    question: string;
    purpose: string;
  }>;
}

export interface AuditListData {
  items: AuditItem[];
  page: number;
  pageSize: number;
  total: number;
}
