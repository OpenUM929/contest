// src/components/SurveyRefineChat.tsx
import React, { useState, useRef, useEffect } from "react";
import { QuestionSet } from "../types/survey";
import { refineQuestions } from "../api/survey";
import SurveyPreview from "./SurveyPreview";

interface Props {
  topicTitle: string;
  initialQuestionSet: QuestionSet;
  welfareId?: string;
  onDirectEdit: (qs: QuestionSet) => void;
  onPublish: (qs: QuestionSet) => void;
}

interface ChatMessage {
  role: "ai" | "user";
  text: string;
}

export default function SurveyRefineChat({ topicTitle, initialQuestionSet, welfareId, onDirectEdit, onPublish }: Props) {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      role: "ai",
      text: `${typeLabel(initialQuestionSet.question_type)} ${initialQuestionSet.questions.length}문항을 생성했습니다. 아래 미리보기를 확인하고, 수정할 내용을 알려주세요.`,
    },
  ]);
  const [questionSet, setQuestionSet] = useState<QuestionSet>(initialQuestionSet);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  const handleSend = async () => {
    if (!input.trim() || loading) return;
    const userText = input.trim();
    setInput("");
    setMessages((prev) => [...prev, { role: "user", text: userText }]);
    setLoading(true);

    try {
      const res = await refineQuestions({
        topic_title: topicTitle,
        current_question_set: questionSet,
        instruction: userText,
        welfare_id: welfareId || undefined,
      });
      const nextQs = res.data as QuestionSet;
      setQuestionSet(nextQs);
      setMessages((prev) => [
        ...prev,
        {
          role: "ai",
          text: `수정했습니다. 미리보기를 확인해 보세요.\n\n질문 유형: ${typeLabel(nextQs.question_type)} / 문항 수: ${nextQs.questions.length}개`,
        },
      ]);
    } catch (e) {
      setMessages((prev) => [...prev, { role: "ai", text: "죄송합니다, 수정 중 오류가 발생했습니다. 다시 시도해 주세요." }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ display: "flex", gap: 16, height: "70vh" }}>
      {/* 좌측: 채팅 */}
      <div style={{ flex: 1, display: "flex", flexDirection: "column", minWidth: 300 }}>
        <div
          ref={scrollRef}
          style={{
            flex: 1,
            overflowY: "auto",
            background: "#FFF",
            borderRadius: 12,
            padding: 16,
            border: "1px solid #EEE",
            display: "flex",
            flexDirection: "column",
            gap: 12,
          }}
        >
          {messages.map((m, i) => (
            <div
              key={i}
              style={{
                alignSelf: m.role === "user" ? "flex-end" : "flex-start",
                maxWidth: "80%",
                background: m.role === "user" ? "#E8572A" : "#F0F0F0",
                color: m.role === "user" ? "#FFF" : "#333",
                padding: "10px 14px",
                borderRadius: 12,
                fontSize: 13,
                lineHeight: 1.5,
                whiteSpace: "pre-wrap",
              }}
            >
              {m.text}
            </div>
          ))}
          {loading && (
            <div style={{ alignSelf: "flex-start", fontSize: 12, color: "#888" }}>AI가 수정 중...</div>
          )}
        </div>

        <div style={{ display: "flex", gap: 8, marginTop: 10 }}>
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleSend()}
            placeholder="예: 보기를 더 쉬운 말로 바꿔주세요"
            style={{
              flex: 1,
              padding: "10px 12px",
              borderRadius: 8,
              border: "1px solid #DDD",
              fontSize: 14,
            }}
          />
          <button
            onClick={handleSend}
            disabled={loading}
            style={{
              padding: "10px 18px",
              borderRadius: 8,
              border: "none",
              background: "#E8572A",
              color: "#FFF",
              fontWeight: "bold",
              fontSize: 13,
              cursor: "pointer",
              opacity: loading ? 0.6 : 1,
            }}
          >
            전송
          </button>
        </div>

        <div style={{ display: "flex", gap: 10, marginTop: 12 }}>
          <button
            onClick={() => onDirectEdit(questionSet)}
            style={{
              flex: 1,
              padding: "10px",
              borderRadius: 8,
              border: "1px solid #555",
              background: "#FFF",
              color: "#333",
              fontWeight: "bold",
              fontSize: 13,
              cursor: "pointer",
            }}
          >
            직접 수정 (편집기)
          </button>
          <button
            onClick={() => onPublish(questionSet)}
            style={{
              flex: 1,
              padding: "10px",
              borderRadius: 8,
              border: "none",
              background: "#E8572A",
              color: "#FFF",
              fontWeight: "bold",
              fontSize: 13,
              cursor: "pointer",
            }}
          >
            이대로 발행
          </button>
        </div>
      </div>

      {/* 우측: 실시간 미리보기 */}
      <div style={{ width: 340, flexShrink: 0, overflowY: "auto" }}>
        <SurveyPreview questionSet={questionSet} title="실시간 미리보기" />
      </div>
    </div>
  );
}

function typeLabel(qt: string): string {
  const map: Record<string, string> = { choice: "선택형", narrative: "서술형", mixed: "혼합형" };
  return map[qt] || qt;
}
