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
  topic_id?: string;
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
  content_type: string;
  contributor_cnt: number;
  published_at: string;
}

export async function fetchEssayArchive(type?: string): Promise<EssayArchiveItem[]> {
  const params = type ? { type } : {};
  const { data } = await axios.get(`${API_BASE}/essay/archive`, { params });
  return data;
}

export async function fetchEssayDetail(essayId: string): Promise<{
  essay_id: string;
  topic_title: string;
  title: string;
  content: string;
  content_type: string;
  contributor_cnt: number;
  published_at: string;
}> {
  const { data } = await axios.get(`${API_BASE}/essay/${essayId}`);
  return data;
}

// ── 최신 수필 단건 조회 ──
export interface LatestEssayResponse {
  essay_id: string;
  title: string;
  content: string;
  content_type: string;
  contributor_cnt: number;
  published_at: string;
}

export async function fetchLatestEssay(): Promise<LatestEssayResponse | null> {
  try {
    const { data } = await axios.get(`${API_BASE}/essay/latest`);
    return data;
  } catch (e: any) {
    if (e.response?.status === 404) {
      return null;
    }
    throw e;
  }
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

// ── 사용자용 설문 목록 (신규) ──
export interface AvailableSurveyItem {
  topic_id: string;
  title: string;
  active_week: string | null;
  question_type: string;
  media_url: string | null;
  has_responded: boolean;
  responded_at: string | null;
}

export interface AvailableSurveysResponse {
  user_id: string;
  surveys: AvailableSurveyItem[];
}

export async function fetchAvailableSurveys(userId: string): Promise<AvailableSurveysResponse> {
  const { data } = await axios.get(`${API_BASE}/chat/users/${userId}/available-surveys`);
  return data;
}

// ── 주제 상세 조회 (과거 주제 로드용) ──
export async function fetchTopicById(topicId: string): Promise<TopicResponse> {
  const { data } = await axios.get(`${API_BASE}/chat/topics/${topicId}`);
  return data;
}

// ── 내 설문 통계 ──
export interface ChoiceStat {
  label: string;
  count: number;
  percent: number;
}

export interface SurveyAnalyticsQuestion {
  question_id: string;
  question_type: string;
  question_text: string;
  my_answer: string | null;
  statistics?: ChoiceStat[];
  sample_responses?: { text: string; responded_at: string | null }[];
  response_count?: number;
}

export interface SurveyAnalytics {
  topic_id: string;
  topic_title: string;
  total_respondents: number;
  my_responses: SurveyAnalyticsQuestion[];
}

export async function fetchTopicStatistics(topicId: string, userId: string): Promise<SurveyAnalytics> {
  const { data } = await axios.get(`${API_BASE}/chat/surveys/${topicId}/my-analytics`, {
    params: { user_id: userId },
  });
  return data;
}

// ── 결과물 전달 (content_type 필터) ──
export async function fetchDeliverablesArchive(type?: string): Promise<EssayArchiveItem[]> {
  return fetchEssayArchive(type);
}
