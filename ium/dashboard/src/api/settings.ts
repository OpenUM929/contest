// src/api/settings.ts
import axios from "axios";

const API = import.meta.env.VITE_API_URL || "http://localhost:8000";

export type Provider = "claude" | "openai" | "gemini";

export interface ApiKeysResponse {
  claude: string; // 마스킹된 값 (예: "***************abcd") 또는 ""
  openai: string;
  gemini: string;
  active_provider: string;
}

export interface ApiKeysSaveRequest {
  welfare_id: string;
  claude: string;
  openai: string;
  gemini: string;
  active_provider: string;
}

export const getApiKeys = (welfareId: string) =>
  axios.get<ApiKeysResponse>(`${API}/api/welfare/api-keys`, {
    params: { welfare_id: welfareId },
  });

export const saveApiKeys = (data: ApiKeysSaveRequest) =>
  axios.put<{ status: string; active_provider: string }>(`${API}/api/welfare/api-keys`, data);
