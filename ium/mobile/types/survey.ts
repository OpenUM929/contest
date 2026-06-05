// mobile/types/survey.ts
// Phase 3: 모바일 앱 동적 설문지 공유 타입

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

export interface Topic {
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
  choices?: QuestionSet | string[] | null;
  active_week?: string | null;
  region?: string;
}

export interface SurveyAnswer {
  questionId: string;
  selectedOptionId?: string;
  selectedOptionLabel?: string;
  narrativeText?: string;
}
