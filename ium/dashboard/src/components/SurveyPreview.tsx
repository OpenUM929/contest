// src/components/SurveyPreview.tsx
import React, { useState } from "react";
import { QuestionSet, QuestionItem } from "../types/survey";

interface Props {
  questionSet: QuestionSet | null;
  candidate?: {
    title: string;
    description?: string;
    text_content?: string;
    media_url?: string;
    media_type: string;
    source: string;
    image_analysis?: {
      artifact_summary: { era: string; type: string; features: string[] };
      mood: { atmosphere: string; associations: string[] };
      topic_candidates: { title: string; description: string; age_suitability: string }[];
    };
  } | null;
}

export default function SurveyPreview({ questionSet, candidate }: Props) {
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
      {/* 주제 정보 */}
      {candidate && (
        <div style={{
          background: "#FFF8F6", borderRadius: 10, padding: "14px 16px",
          border: "1px solid #FEE2E2", marginBottom: 4,
        }}>
          {candidate.media_url && candidate.media_type === "image" && (
            <div style={{ width: "100%", maxHeight: 200, overflow: "hidden", borderRadius: 8, marginBottom: 10 }}>
              <img src={candidate.media_url} alt={candidate.title}
                style={{ width: "100%", height: "auto", display: "block" }} />
            </div>
          )}
          {candidate.media_url && candidate.media_type === "audio" && (
            <audio controls src={candidate.media_url} style={{ width: "100%", marginBottom: 10 }} />
          )}
          {(!candidate.media_url && candidate.media_type === "image") && (
            <div style={{
              width: "100%", height: 80, background: "#F1F5F9", borderRadius: 8,
              display: "flex", alignItems: "center", justifyContent: "center",
              fontSize: 13, color: "#94A3B8", marginBottom: 8,
            }}>🖼 이미지 없음</div>
          )}
          <div style={{ fontSize: 15, fontWeight: "bold", color: "#222", marginBottom: 2 }}>{candidate.title}</div>
          <div style={{ fontSize: 12, color: "#888", marginBottom: 4 }}>
            [{candidate.source}] · {candidate.media_type === "image" ? "사진" : candidate.media_type === "audio" ? "음원" : "텍스트"}
          </div>
          {candidate.description ? (
            <div style={{ fontSize: 13, color: "#555", lineHeight: 1.5, marginBottom: 4 }}>{candidate.description}</div>
          ) : (
            <div style={{ fontSize: 13, color: "#999", fontStyle: "italic", lineHeight: 1.5, marginBottom: 4 }}>설명 정보가 없습니다</div>
          )}
          {candidate.media_type === "text" && candidate.text_content && (
            <div style={{
              background: "#FAFAFA", borderRadius: 6, padding: "10px 12px",
              border: "1px solid #E5E5E5", fontSize: 13, color: "#444",
              lineHeight: 1.6, marginBottom: 8, maxHeight: 200, overflowY: "auto",
            }}>
              {candidate.text_content}
            </div>
          )}
          {candidate.image_analysis && (
            <div style={{
              background: "#F8FAFC", borderRadius: 6, padding: "8px 10px",
              border: "1px solid #E2E8F0", fontSize: 12, color: "#475569",
            }}>
              <div>🏺 {candidate.image_analysis.artifact_summary.era} · {candidate.image_analysis.artifact_summary.type}
                {candidate.image_analysis.artifact_summary.features?.length > 0 && (
                  <span> · {candidate.image_analysis.artifact_summary.features.join(", ")}</span>
                )}
              </div>
              <div>🎨 {candidate.image_analysis.mood.atmosphere}</div>
              {candidate.image_analysis.topic_candidates.length > 0 && (
                <div style={{ display: "flex", flexWrap: "wrap", gap: 6, marginTop: 6 }}>
                  {candidate.image_analysis.topic_candidates.map((tc, ti) => (
                    <span key={ti} style={{
                      fontSize: 11, background: "#E0F2FE", color: "#0369A1",
                      padding: "2px 6px", borderRadius: 12, fontWeight: 600,
                    }}>💡 {tc.title}</span>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* AI 생성 질문 구분선 */}
      <div style={{
        display: "flex", alignItems: "center", gap: 8,
        margin: "8px 0 4px",
      }}>
        <div style={{ flex: 1, height: 1, background: "#DDD" }} />
        <span style={{ fontSize: 13, fontWeight: "bold", color: "#888", whiteSpace: "nowrap" }}>
          🤖 AI 생성 질문
        </span>
        <div style={{ flex: 1, height: 1, background: "#DDD" }} />
        <div style={{ display: "flex", gap: 6 }}>
          <button
            onClick={() => setMode("elder")}
            style={{
              padding: "4px 10px",
              borderRadius: 6,
              border: "none",
              background: mode === "elder" ? "#E8572A" : "#E0E0E0",
              color: mode === "elder" ? "#FFF" : "#333",
              fontSize: 11,
              fontWeight: "bold",
              cursor: "pointer",
            }}
          >
            노인용
          </button>
          <button
            onClick={() => setMode("youth")}
            style={{
              padding: "4px 10px",
              borderRadius: 6,
              border: "none",
              background: mode === "youth" ? "#7B7BFF" : "#E0E0E0",
              color: mode === "youth" ? "#FFF" : "#333",
              fontSize: 11,
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
