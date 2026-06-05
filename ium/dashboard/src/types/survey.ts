// src/types/survey.ts
// 설문지 통합 관리 시스템 공유 타입

export interface ChoiceOption {
  id: string;
  label: string;
  value: string;
  icon_hint?: string;
  is_other?: boolean;
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

export interface AnalyticsData {
  topic_id: string;
  total_respondents: number;
  questions: AnalyticsQuestion[];
}

export interface SurveyTemplateItem {
  id: string;
  name: string;
  created_at?: string;
}
