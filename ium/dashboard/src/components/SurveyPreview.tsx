// src/components/SurveyPreview.tsx
import React, { useState } from "react";
import { QuestionSet, QuestionItem } from "../types/survey";

interface Props {
  questionSet: QuestionSet | null;
  title?: string;
}

export default function SurveyPreview({ questionSet, title = "미리보기" }: Props) {
  const [mode, setMode] = useState<"elder" | "youth">("elder");

  if (!questionSet || !questionSet.questions || questionSet.questions.length === 0) {
    return (
      <div style={{ padding: 20, textAlign: "center", color: "#888" }}>
        미리볼 설문지가 없습니다.
      </div>
    );
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <h4 style={{ margin: 0, fontSize: 15, color: "#1A1A2E" }}>{title}</h4>
        <div style={{ display: "flex", gap: 6 }}>
          <button
            onClick={() => setMode("elder")}
            style={{
              padding: "6px 12px",
              borderRadius: 6,
              border: "none",
              background: mode === "elder" ? "#E8572A" : "#E0E0E0",
              color: mode === "elder" ? "#FFF" : "#333",
              fontSize: 12,
              fontWeight: "bold",
              cursor: "pointer",
            }}
          >
            노인용
          </button>
          <button
            onClick={() => setMode("youth")}
            style={{
              padding: "6px 12px",
              borderRadius: 6,
              border: "none",
              background: mode === "youth" ? "#7B7BFF" : "#E0E0E0",
              color: mode === "youth" ? "#FFF" : "#333",
              fontSize: 12,
              fontWeight: "bold",
              cursor: "pointer",
            }}
          >
            청년용
          </button>
        </div>
      </div>

      {mode === "elder" ? (
        <ElderPreview questions={questionSet.questions} />
      ) : (
        <YouthPreview questions={questionSet.questions} />
      )}
    </div>
  );
}

function ElderPreview({ questions }: { questions: QuestionItem[] }) {
  return (
    <div
      style={{
        background: "#FFFDF7",
        borderRadius: 12,
        padding: 16,
        border: "2px solid #EEE",
      }}
    >
      <div
        style={{
          fontSize: 18,
          fontWeight: "bold",
          textAlign: "center",
          color: "#4A3728",
          marginBottom: 16,
        }}
      >
        이부(以音)
      </div>
      {questions.map((q, idx) => (
        <div key={q.id} style={{ marginBottom: 16 }}>
          <div
            style={{
              fontSize: 15,
              fontWeight: "bold",
              color: "#333",
              marginBottom: 10,
              lineHeight: 1.5,
            }}
          >
            Q{idx + 1}. {q.text}
          </div>
          {q.type === "choice" && q.options && (
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8 }}>
              {q.options.map((opt) => (
                <button
                  key={opt.id}
                  style={{
                    padding: "14px 8px",
                    borderRadius: 10,
                    border: "2px solid #DDD",
                    background: "#FFF",
                    fontSize: 14,
                    fontWeight: "bold",
                    color: "#333",
                    cursor: "pointer",
                    textAlign: "center",
                  }}
                >
                  {opt.icon_hint ? <span style={{ fontSize: 20, display: "block", marginBottom: 4 }}>{opt.icon_hint}</span> : null}
                  {opt.label}
                </button>
              ))}
            </div>
          )}
          {q.type === "narrative" && (
            <>
              {q.guidelines && (
                <div style={{ marginBottom: 8, paddingLeft: 12 }}>
                  {q.guidelines.map((g, i) => (
                    <div key={i} style={{ fontSize: 12, color: "#888", marginBottom: 2 }}>
                      • {g}
                    </div>
                  ))}
                </div>
              )}
              <div
                style={{
                  background: "#E8572A",
                  color: "#FFF",
                  padding: 16,
                  borderRadius: 10,
                  textAlign: "center",
                  fontWeight: "bold",
                  fontSize: 15,
                }}
              >
                누르고 말씀해 주세요
              </div>
            </>
          )}
        </div>
      ))}
    </div>
  );
}

function YouthPreview({ questions }: { questions: QuestionItem[] }) {
  return (
    <div
      style={{
        background: "#1A1A2E",
        borderRadius: 12,
        padding: 16,
        color: "#E8E8FF",
        border: "2px solid #333",
      }}
    >
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          marginBottom: 16,
        }}
      >
        <span style={{ fontWeight: "bold", fontSize: 16 }}>이음</span>
        <span
          style={{
            fontSize: 12,
            background: "#2D2D4A",
            padding: "4px 10px",
            borderRadius: 12,
          }}
        >
          익명
        </span>
      </div>
      {questions.map((q, idx) => (
        <div key={q.id} style={{ marginBottom: 16 }}>
          <div
            style={{
              fontSize: 14,
              fontWeight: "bold",
              color: "#FFF",
              marginBottom: 10,
              lineHeight: 1.5,
            }}
          >
            Q{idx + 1}. {q.text}
          </div>
          {q.type === "choice" && q.options && (
            <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
              {q.options.map((opt) => (
                <span
                  key={opt.id}
                  style={{
                    padding: "8px 14px",
                    borderRadius: 16,
                    background: "#16213E",
                    border: "1px solid #333",
                    fontSize: 13,
                    color: "#CCC",
                  }}
                >
                  {opt.label}
                </span>
              ))}
            </div>
          )}
          {q.type === "narrative" && (
            <>
              {q.guidelines && (
                <div style={{ marginBottom: 8 }}>
                  {q.guidelines.map((g, i) => (
                    <div key={i} style={{ fontSize: 12, color: "#888", marginBottom: 2 }}>
                      • {g}
                    </div>
                  ))}
                </div>
              )}
              <div
                style={{
                  background: "#16213E",
                  borderRadius: 12,
                  padding: 12,
                  minHeight: 60,
                  fontSize: 12,
                  color: "#666",
                  border: "1px solid #333",
                }}
              >
                {q.placeholder || "자유롭게 써주세요 (익명으로 기록됩니다)"}
              </div>
              <div style={{ display: "flex", justifyContent: "flex-end", marginTop: 8 }}>
                <span
                  style={{
                    background: "#7B7BFF",
                    padding: "8px 16px",
                    borderRadius: 8,
                    fontSize: 13,
                    fontWeight: "bold",
                    color: "#FFF",
                  }}
                >
                  전달하기
                </span>
              </div>
            </>
          )}
        </div>
      ))}
    </div>
  );
}
