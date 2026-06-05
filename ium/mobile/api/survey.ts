// mobile/api/survey.ts
import axios from "axios";

const API_BASE = process.env.EXPO_PUBLIC_API_URL || "http://localhost:8000";

export interface TopicResponse {
  id: string | null;
  title: string;
  description?: string | null;
  media_url?: string | null;
  media_type?: string;
  source?: string;
  source_url?: string;
  ai_question?: string;
  text_content?: string | null;
  question_type?: string;
  choices?: any;
  active_week?: string | null;
  region?: string;
}

export async function fetchTopic(userId: string): Promise<TopicResponse> {
  const { data } = await axios.get(`${API_BASE}/chat/topic`, {
    params: { user_id: userId },
  });
  return data;
}

export interface ChatSubmitPayload {
  user_id: string;
  message: string;
  question_id?: string;
  selected_option_id?: string;
  selected_option_label?: string;
}

export async function submitChat(payload: ChatSubmitPayload): Promise<Response> {
  return fetch(`${API_BASE}/chat/message`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

// ── 내 설문 누적 보기 ──
export interface MySurveyResponse {
  topic_id: string;
  topic_title: string;
  active_week: string | null;
  responses: {
    question_id: string;
    question_type: string;
    selected_option_id: string | null;
    selected_option_label: string | null;
    narrative_text: string | null;
    responded_at: string;
  }[];
}

export async function fetchMySurveys(userId: string): Promise<{
  user_id: string;
  nickname: string | null;
  topics: MySurveyResponse[];
}> {
  const { data } = await axios.get(`${API_BASE}/chat/users/${userId}/my-surveys`);
  return data;
}

// ── 수필 아카이브 ──
export interface EssayArchiveItem {
  essay_id: string;
  topic_id: string | null;
  topic_title: string;
  active_week: string | null;
  contributor_cnt: number;
  published_at: string;
}

export async function fetchEssayArchive(): Promise<EssayArchiveItem[]> {
  const { data } = await axios.get(`${API_BASE}/essay/archive`);
  return data;
}

export async function fetchEssayDetail(essayId: string): Promise<{
  essay_id: string;
  topic_title: string;
  title: string;
  content: string;
  contributor_cnt: number;
  published_at: string;
}> {
  const { data } = await axios.get(`${API_BASE}/essay/${essayId}`);
  return data;
}

// ── 주제 아카이브 + 통계 ──
export interface TopicArchiveItem {
  topic_id: string;
  title: string;
  active_week: string | null;
  question_type: string;
  respondents: number;
  has_essay: boolean;
  essay_id: string | null;
}

export async function fetchTopicArchive(): Promise<{ topics: TopicArchiveItem[] }> {
  const { data } = await axios.get(`${API_BASE}/welfare/topics/archive`);
  return data;
}
