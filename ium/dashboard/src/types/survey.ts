// src/types/survey.ts
// 설문지 통합 관리 시스템 공유 타입

export interface ChoiceOption {
  id: string;
  label: string;
  value: string;
  icon_hint?: string;
  is_other?: boolean;
  mbti_axis?: "EI" | "SN" | "TF" | "JP";
  mbti_pole?: "E" | "I" | "S" | "N" | "T" | "F" | "J" | "P";
}

export interface QuestionItem {
  id: string;
  type: "choice" | "narrative";
  text: string;
  target_age?: "elderly" | "youth" | "both";
  allow_multiple?: boolean;
  max_selections?: number;
  has_other?: boolean;
  options?: ChoiceOption[];
  guidelines?: string[];
  placeholder?: string;
  min_length_hint?: string;
  suggested_duration_seconds?: number;
}

export interface QuestionSet {
  schema_version: "1.0";
  question_type: "choice" | "narrative" | "mixed";
  questions: QuestionItem[];
}

export interface WeeklyTopic {
  topic_id: string;
  title: string;
  question_type: string;
  region: string;
  is_customized: boolean;
  created_at?: string;
  active_week?: string;
}

export interface OptionStat {
  label: string;
  count: number;
  percent: number;
}

export interface AnalyticsQuestion {
  question_id: string;
  type: "choice" | "narrative";
  text: string;
  options_stats?: OptionStat[];
  response_count?: number;
  sample_responses?: string[];
}

export interface MbtiAxis {
  axis: string;
  left: string;
  right: string;
  left_label: string;
  right_label: string;
  left_count: number;
  right_count: number;
  dominant: string | null;
  strength: number;
}

export interface MbtiSummary {
  type: string;
  is_complete: boolean;
  axes: MbtiAxis[];
  total_signals: number;
}

export interface RespondentMbti {
  user_id: string;
  nickname: string;
  type: string;
  is_complete: boolean;
  survey_count: number;
  total_signals: number;
}

export interface AnalyticsData {
  topic_id: string;
  total_respondents: number;
  questions: AnalyticsQuestion[];
  mbti_distribution?: MbtiSummary;
  respondent_mbti?: RespondentMbti[];
}

export interface SurveyTemplateItem {
  id: string;
  name: string;
  created_at?: string;
}

export interface DistributedUser {
  user_id: string;
  nickname: string;
  user_type: string;
  acknowledged?: boolean;
  acknowledged_at?: string;
}

export interface PublishResult {
  topic_id: string;
  title: string;
  region: string;
  question_type: string;
  published_at?: string;
  distributed_users?: DistributedUser[];
}

export interface DistributionSummary {
  total_distributed: number;
  acknowledged_count: number;
  pending_count: number;
  users: {
    user_id: string;
    topic_id: string;
    acknowledged: boolean;
    acknowledged_at: string | null;
  }[];
}
