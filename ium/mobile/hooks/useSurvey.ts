// mobile/hooks/useSurvey.ts
import { useState, useEffect, useCallback, useRef } from "react";
import { Topic, QuestionItem, SurveyAnswer } from "../types/survey";
import { submitChat } from "../api/survey";

export interface UseSurveyReturn {
  questions: QuestionItem[];
  currentQuestion: QuestionItem | undefined;
  currentIndex: number;
  answers: Record<string, SurveyAnswer>;
  isSubmitting: boolean;
  completed: boolean;
  setAnswer: (qid: string, answer: SurveyAnswer) => void;
  nextQuestion: () => void;
  submitAnswers: (
    userId: string,
    onSendStart?: () => void,
    onAiResponse?: (text: string) => void,
    onCrisis?: (level: string) => void
  ) => Promise<void>;
}

export function useSurvey(topic: Topic | null): UseSurveyReturn {
  const [questions, setQuestions] = useState<QuestionItem[]>([]);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [answers, setAnswers] = useState<Record<string, SurveyAnswer>>({});
  const answersRef = useRef<Record<string, SurveyAnswer>>({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [completed, setCompleted] = useState(false);

  useEffect(() => {
    if (!topic) {
      setQuestions([]);
      setCurrentIndex(0);
      answersRef.current = {};
      setAnswers({});
      setCompleted(false);
      return;
    }

    let qs: QuestionItem[] = [];
    if (
      topic.choices &&
      typeof topic.choices === "object" &&
      !Array.isArray(topic.choices)
    ) {
      qs = topic.choices.questions || [];
    } else if (Array.isArray(topic.choices)) {
      qs = [
        {
          id: "q1",
          type: "choice",
          text: topic.ai_question || "질문입니다.",
          options: topic.choices.map((c, i) => ({
            id: `opt_${i}`,
            label: c,
            value: c,
          })),
        },
      ];
    } else if (topic.ai_question) {
      qs = [{ id: "q1", type: "narrative", text: topic.ai_question }];
    }

    setQuestions(qs);
    setCurrentIndex(0);
    answersRef.current = {};
    setAnswers({});
    setCompleted(false);
  }, [topic]);

  const setAnswer = useCallback((qid: string, answer: SurveyAnswer) => {
    answersRef.current = { ...answersRef.current, [qid]: answer };
    setAnswers(answersRef.current);
  }, []);

  const nextQuestion = useCallback(() => {
    setCurrentIndex((idx) => Math.min(idx + 1, questions.length));
  }, [questions.length]);

  const submitAnswers = useCallback(
    async (
      userId: string,
      onSendStart?: () => void,
      onAiResponse?: (text: string) => void,
      onCrisis?: (level: string) => void
    ) => {
      setIsSubmitting(true);
      if (onSendStart) onSendStart();

      const answeredQuestions = questions.filter((q) => answersRef.current[q.id]);
      if (answeredQuestions.length === 0) {
        setIsSubmitting(false);
        return;
      }

      try {
        for (let i = 0; i < answeredQuestions.length; i++) {
          const q = answeredQuestions[i];
          const ans = answersRef.current[q.id];
          const isLast = i === answeredQuestions.length - 1;

          let message = "";
          let selectedOptionId: string | undefined;
          let selectedOptionLabel: string | undefined;

          if (q.type === "choice" && ans.selectedOptionId) {
            message = ans.selectedOptionLabel?.replace(/\|\|\|/g, ", ") || ans.selectedOptionId;
            selectedOptionId = ans.selectedOptionId;
            selectedOptionLabel = ans.selectedOptionLabel;
          } else if (q.type === "narrative" && ans.narrativeText) {
            message = ans.narrativeText;
          }

          if (!message) continue;

          const response = await submitChat({
            user_id: userId,
            message,
            question_id: q.id,
            selected_option_id: selectedOptionId,
            selected_option_label: selectedOptionLabel,
          });

          // 위기 감지 헤더 확인
          const crisisLevel = response.headers.get("x-crisis-level");

          const reader = response.body!.getReader();
          const decoder = new TextDecoder();
          let full = "";
          while (true) {
            const { done, value } = await reader.read();
            if (done) break;
            full += decoder.decode(value);
          }

          if (isLast && onAiResponse) {
            onAiResponse(full);
          }

          if (crisisLevel && onCrisis) {
            onCrisis(crisisLevel);
          }
        }
        setCompleted(true);
      } catch (e) {
        console.error("submitAnswers failed", e);
      } finally {
        setIsSubmitting(false);
      }
    },
    [questions]
  );

  return {
    questions,
    currentQuestion: questions[currentIndex],
    currentIndex,
    answers,
    isSubmitting,
    completed,
    setAnswer,
    nextQuestion,
    submitAnswers,
  };
}
