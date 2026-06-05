// src/components/SurveyEditor.tsx
import React, { useState, useEffect } from "react";
import { QuestionSet, QuestionItem, ChoiceOption } from "../types/survey";
import { validateQuestions } from "../api/survey";
import SurveyPreview from "./SurveyPreview";

interface Props {
  initialQuestionSet: QuestionSet;
  onChange: (qs: QuestionSet) => void;
  onPublish?: () => void;
  onSaveDraft?: () => void;
}

export default function SurveyEditor({ initialQuestionSet, onChange, onPublish, onSaveDraft }: Props) {
  const [qs, setQs] = useState<QuestionSet>(initialQuestionSet);
  const [errors, setErrors] = useState<string[]>([]);
  const [showPreview, setShowPreview] = useState(false);

  useEffect(() => {
    setQs(initialQuestionSet);
  }, [initialQuestionSet]);

  useEffect(() => {
    onChange(qs);
    validate(qs);
  }, [qs]);

  const validate = async (data: QuestionSet) => {
    try {
      const res = await validateQuestions({ question_set: data });
      setErrors(res.data.errors || []);
    } catch (e) {
      setErrors(["검증 요청 실패"]);
    }
  };

  const updateQuestion = (idx: number, patch: Partial<QuestionItem>) => {
    const next = { ...qs, questions: qs.questions.map((q, i) => (i === idx ? { ...q, ...patch } : q)) };
    setQs(next as QuestionSet);
  };

  const updateOption = (qIdx: number, oIdx: number, patch: Partial<ChoiceOption>) => {
    const q = qs.questions[qIdx];
    if (!q.options) return;
    const nextOptions = q.options.map((o, i) => (i === oIdx ? { ...o, ...patch } : o));
    updateQuestion(qIdx, { options: nextOptions });
  };

  const addOption = (qIdx: number) => {
    const q = qs.questions[qIdx];
    const options = q.options ? [...q.options] : [];
    // is_other가 있으면 그 앞에 삽입
    const otherIdx = options.findIndex((o) => o.is_other);
    const newOpt: ChoiceOption = {
      id: `opt_${Date.now()}`,
      label: "새 보기",
      value: `new_${Date.now()}`,
    };
    if (otherIdx >= 0) {
      options.splice(otherIdx, 0, newOpt);
    } else {
      options.push(newOpt);
    }
    updateQuestion(qIdx, { options });
  };

  const removeOption = (qIdx: number, oIdx: number) => {
    const q = qs.questions[qIdx];
    if (!q.options) return;
    if (q.options.length <= 2) {
      alert("선택형 보기는 최소 2개 필요합니다.");
      return;
    }
    const nextOptions = q.options.filter((_, i) => i !== oIdx);
    updateQuestion(qIdx, { options: nextOptions });
  };

  const moveOption = (qIdx: number, oIdx: number, dir: -1 | 1) => {
    const q = qs.questions[qIdx];
    if (!q.options) return;
    const newIdx = oIdx + dir;
    if (newIdx < 0 || newIdx >= q.options.length) return;
    const nextOptions = [...q.options];
    const [moved] = nextOptions.splice(oIdx, 1);
    nextOptions.splice(newIdx, 0, moved);
    updateQuestion(qIdx, { options: nextOptions });
  };

  const addGuideline = (qIdx: number) => {
    const q = qs.questions[qIdx];
    const guidelines = [...(q.guidelines || []), ""];
    updateQuestion(qIdx, { guidelines });
  };

  const updateGuideline = (qIdx: number, gIdx: number, value: string) => {
    const q = qs.questions[qIdx];
    const guidelines = [...(q.guidelines || [])];
    guidelines[gIdx] = value;
    updateQuestion(qIdx, { guidelines });
  };

  const removeGuideline = (qIdx: number, gIdx: number) => {
    const q = qs.questions[qIdx];
    const guidelines = (q.guidelines || []).filter((_, i) => i !== gIdx);
    updateQuestion(qIdx, { guidelines });
  };

  const toggleHasOther = (qIdx: number) => {
    const q = qs.questions[qIdx];
    const hasOther = !q.has_other;
    let options = q.options ? [...q.options] : [];
    if (hasOther) {
      if (!options.some((o) => o.is_other)) {
        options.push({ id: "opt_other", label: "기타 (직접 말씀해 주세요)", value: "OTHER", is_other: true });
      }
    } else {
      options = options.filter((o) => !o.is_other);
    }
    updateQuestion(qIdx, { has_other: hasOther, options });
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
      {/* 상단 툴바 */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: 8 }}>
        <div style={{ display: "flex", gap: 8 }}>
          <button
            onClick={() => setShowPreview(!showPreview)}
            style={{ ...btnStyle, background: "#555", color: "#FFF" }}
          >
            {showPreview ? "미리보기 닫기" : "미리보기"}
          </button>
        </div>
        <div style={{ display: "flex", gap: 8 }}>
          <button onClick={onSaveDraft} style={{ ...btnStyle, background: "#E0E0E0", color: "#333" }}>
            임시 저장
          </button>
          <button onClick={onPublish} style={{ ...btnStyle, background: "#E8572A", color: "#FFF" }}>
            발행하기
          </button>
        </div>
      </div>

      {/* 유효성 오류 */}
      {errors.length > 0 && (
        <div style={{ background: "#FFF0F0", border: "1px solid #FF4444", borderRadius: 8, padding: 12, color: "#FF4444", fontSize: 13 }}>
          {errors.map((e, i) => (
            <div key={i}>• {e}</div>
          ))}
        </div>
      )}

      <div style={{ display: "flex", gap: 16, alignItems: "flex-start" }}>
        {/* 편집 영역 */}
        <div style={{ flex: 1, display: "flex", flexDirection: "column", gap: 16 }}>
          {qs.questions.map((q, qIdx) => (
            <div
              key={q.id}
              style={{
                background: "#FFF",
                borderRadius: 12,
                padding: 18,
                border: "1px solid #EEE",
              }}
            >
              <div style={{ fontWeight: "bold", fontSize: 13, color: "#888", marginBottom: 8 }}>
                질문 {qIdx + 1} ({q.type === "choice" ? "선택형" : "서술형"})
              </div>

              {/* 질문 문구 */}
              <div style={{ marginBottom: 12 }}>
                <label style={{ fontSize: 12, color: "#666", display: "block", marginBottom: 4 }}>질문 문구</label>
                <input
                  type="text"
                  value={q.text}
                  onChange={(e) => updateQuestion(qIdx, { text: e.target.value })}
                  style={{
                    width: "100%",
                    padding: "10px 12px",
                    borderRadius: 8,
                    border: "1px solid #DDD",
                    fontSize: 14,
                    boxSizing: "border-box",
                  }}
                />
              </div>

              {/* 선택형 보기 */}
              {q.type === "choice" && (
                <div style={{ marginBottom: 12 }}>
                  <label style={{ fontSize: 12, color: "#666", display: "block", marginBottom: 6 }}>
                    보기 목록 (☰ 드래그 대신 ↑↓ 버튼으로 순서 변경)
                  </label>
                  <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
                    {q.options?.map((opt, oIdx) => (
                      <div
                        key={opt.id}
                        style={{
                          display: "flex",
                          alignItems: "center",
                          gap: 6,
                          background: opt.is_other ? "#FFF8EE" : "#F8F8F8",
                          borderRadius: 8,
                          padding: "6px 10px",
                        }}
                      >
                        <span style={{ fontSize: 12, color: "#AAA", minWidth: 20 }}>{oIdx + 1}</span>
                        <input
                          type="text"
                          value={opt.label}
                          onChange={(e) => updateOption(qIdx, oIdx, { label: e.target.value })}
                          style={{
                            flex: 1,
                            padding: "8px 10px",
                            borderRadius: 6,
                            border: "1px solid #DDD",
                            fontSize: 13,
                          }}
                          disabled={opt.is_other}
                        />
                        <button
                          onClick={() => moveOption(qIdx, oIdx, -1)}
                          disabled={oIdx === 0}
                          style={{ ...smallBtnStyle, opacity: oIdx === 0 ? 0.3 : 1 }}
                        >
                          ↑
                        </button>
                        <button
                          onClick={() => moveOption(qIdx, oIdx, 1)}
                          disabled={oIdx === (q.options?.length || 0) - 1}
                          style={{ ...smallBtnStyle, opacity: oIdx === (q.options?.length || 0) - 1 ? 0.3 : 1 }}
                        >
                          ↓
                        </button>
                        <button
                          onClick={() => removeOption(qIdx, oIdx)}
                          style={{ ...smallBtnStyle, color: "#FF4444" }}
                          disabled={opt.is_other}
                        >
                          삭제
                        </button>
                      </div>
                    ))}
                  </div>
                  <button
                    onClick={() => addOption(qIdx)}
                    style={{ ...btnStyle, marginTop: 8, background: "#F0F0F0", color: "#333", fontSize: 12 }}
                  >
                    + 보기 추가
                  </button>

                  <div style={{ display: "flex", gap: 16, marginTop: 12, fontSize: 12 }}>
                    <label style={{ display: "flex", alignItems: "center", gap: 6, cursor: "pointer" }}>
                      <input
                        type="checkbox"
                        checked={q.allow_multiple || false}
                        onChange={(e) => updateQuestion(qIdx, { allow_multiple: e.target.checked })}
                      />
                      다중 선택 허용
                    </label>
                    <label style={{ display: "flex", alignItems: "center", gap: 6, cursor: "pointer" }}>
                      <input
                        type="checkbox"
                        checked={q.has_other || false}
                        onChange={() => toggleHasOther(qIdx)}
                      />
                      기타 보기 포함
                    </label>
                  </div>
                </div>
              )}

              {/* 서술형 설정 */}
              {q.type === "narrative" && (
                <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
                  <div>
                    <label style={{ fontSize: 12, color: "#666", display: "block", marginBottom: 4 }}>플레이스홀더</label>
                    <input
                      type="text"
                      value={q.placeholder || ""}
                      onChange={(e) => updateQuestion(qIdx, { placeholder: e.target.value })}
                      style={{
                        width: "100%",
                        padding: "8px 10px",
                        borderRadius: 6,
                        border: "1px solid #DDD",
                        fontSize: 13,
                        boxSizing: "border-box",
                      }}
                    />
                  </div>
                  <div>
                    <label style={{ fontSize: 12, color: "#666", display: "block", marginBottom: 4 }}>가이드라인</label>
                    <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
                      {(q.guidelines || []).map((g, gIdx) => (
                        <div key={gIdx} style={{ display: "flex", gap: 6, alignItems: "center" }}>
                          <input
                            type="text"
                            value={g}
                            onChange={(e) => updateGuideline(qIdx, gIdx, e.target.value)}
                            style={{
                              flex: 1,
                              padding: "8px 10px",
                              borderRadius: 6,
                              border: "1px solid #DDD",
                              fontSize: 13,
                            }}
                          />
                          <button
                            onClick={() => removeGuideline(qIdx, gIdx)}
                            style={{ ...smallBtnStyle, color: "#FF4444" }}
                          >
                            삭제
                          </button>
                        </div>
                      ))}
                    </div>
                    <button
                      onClick={() => addGuideline(qIdx)}
                      style={{ ...btnStyle, marginTop: 6, background: "#F0F0F0", color: "#333", fontSize: 12 }}
                    >
                      + 가이드라인 추가
                    </button>
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>

        {/* 미리보기 */}
        {showPreview && (
          <div style={{ width: 340, flexShrink: 0 }}>
            <SurveyPreview questionSet={qs} />
          </div>
        )}
      </div>
    </div>
  );
}

const btnStyle: React.CSSProperties = {
  padding: "8px 16px",
  borderRadius: 6,
  border: "none",
  fontWeight: "bold",
  fontSize: 13,
  cursor: "pointer",
};

const smallBtnStyle: React.CSSProperties = {
  padding: "4px 8px",
  borderRadius: 4,
  border: "1px solid #DDD",
  background: "#FFF",
  fontSize: 11,
  cursor: "pointer",
};
