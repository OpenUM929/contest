// src/components/ManualPreviewPanel.tsx
// 수동 미리보기 패널.
// 1) AI에게 보낼 프롬프트 원문을 출력하고(복사 가능),
// 2) 복지사가 외부 웹 AI에서 받은 답변 원문을 붙여넣으면,
// 3) 백엔드 parse-questions로 파싱해 QuestionSet으로 변환한다. (AI 키 불필요)
import React, { useState } from "react";
import { QuestionSet } from "../types/survey";
import { parseQuestions } from "../api/survey";

interface Props {
  prompt: string; // 생성된 프롬프트("" 이면 아직 생성 전)
  generating: boolean; // 프롬프트 생성 중
  onGeneratePrompt: () => void; // "프롬프트 생성" 클릭
  onApply: (qs: QuestionSet, warnings: string[]) => void; // 파싱 성공 시
}

export default function ManualPreviewPanel({ prompt, generating, onGeneratePrompt, onApply }: Props) {
  const [pastedAnswer, setPastedAnswer] = useState("");
  const [parsing, setParsing] = useState(false);
  const [parseError, setParseError] = useState("");
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(prompt);
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    } catch {
      setParseError("클립보드 복사에 실패했습니다. 프롬프트를 직접 선택해 복사해 주세요.");
    }
  };

  const handleApply = async () => {
    if (!pastedAnswer.trim() || parsing) return;
    setParsing(true);
    setParseError("");
    try {
      const { data } = await parseQuestions({ raw_text: pastedAnswer });
      if (data.valid) {
        const { warnings = [], valid: _valid, ...qset } = data;
        onApply(qset as QuestionSet, warnings);
      } else {
        setParseError(data.error || "AI 답변을 해석하지 못했습니다.");
      }
    } catch (e: any) {
      setParseError(e?.response?.data?.detail || e?.message || "답변 파싱에 실패했습니다.");
    } finally {
      setParsing(false);
    }
  };

  return (
    <div style={s.panel}>
      {/* 1단계: 프롬프트 생성 */}
      <button
        style={{ ...s.primaryBtn, background: "#1A1A2E" }}
        onClick={onGeneratePrompt}
        disabled={generating}
      >
        {generating ? "⏳ 프롬프트 준비 중..." : prompt ? "🔄 프롬프트 다시 생성" : "📝 프롬프트 생성"}
      </button>

      {prompt && (
        <>
          {/* 2단계: 프롬프트 원문 + 복사 */}
          <div style={s.stepBox}>
            <div style={s.stepHeader}>
              <span style={s.stepLabel}>① 아래 프롬프트를 ChatGPT·Claude 등에 붙여넣으세요</span>
              <button style={s.copyBtn} onClick={handleCopy}>
                {copied ? "✅ 복사됨" : "📋 복사"}
              </button>
            </div>
            <textarea style={{ ...s.textarea, background: "#F8F8FB" }} value={prompt} readOnly rows={8} />
          </div>

          {/* 3단계: 답변 붙여넣기 */}
          <div style={s.stepBox}>
            <div style={s.stepLabel}>② AI가 준 답변 전체를 그대로 아래에 붙여넣으세요</div>
            <textarea
              style={s.textarea}
              value={pastedAnswer}
              onChange={(e) => setPastedAnswer(e.target.value)}
              placeholder='예: {"schema_version":"1.0", "question_type":"narrative", "questions":[ ... ]}  (코드블록/설명이 섞여 있어도 됩니다)'
              rows={8}
            />
          </div>

          {parseError && <div style={s.errorBox}>❌ {parseError}</div>}

          {/* 4단계: 결과 적용 */}
          <button
            style={{ ...s.primaryBtn, background: "#E8572A", opacity: !pastedAnswer.trim() || parsing ? 0.6 : 1 }}
            onClick={handleApply}
            disabled={!pastedAnswer.trim() || parsing}
          >
            {parsing ? "⏳ 해석 중..." : "✅ 결과 적용 (미리보기 채우기)"}
          </button>
        </>
      )}
    </div>
  );
}

const s: Record<string, React.CSSProperties> = {
  panel: { display: "flex", flexDirection: "column", gap: 12 },
  primaryBtn: {
    width: "100%",
    padding: "12px",
    borderRadius: 8,
    border: "none",
    color: "#FFF",
    fontWeight: "bold",
    fontSize: 14,
    cursor: "pointer",
  },
  stepBox: {
    display: "flex",
    flexDirection: "column",
    gap: 6,
    background: "#FFF",
    border: "1px solid #EEE",
    borderRadius: 8,
    padding: 12,
  },
  stepHeader: { display: "flex", justifyContent: "space-between", alignItems: "center" },
  stepLabel: { fontSize: 13, fontWeight: "bold", color: "#333" },
  copyBtn: {
    padding: "4px 12px",
    borderRadius: 6,
    border: "1px solid #DDD",
    background: "#FFF",
    color: "#333",
    fontSize: 12,
    cursor: "pointer",
  },
  textarea: {
    width: "100%",
    padding: "10px 12px",
    borderRadius: 8,
    border: "1px solid #DDD",
    fontSize: 13,
    fontFamily: "monospace",
    lineHeight: 1.5,
    resize: "vertical",
    boxSizing: "border-box",
  },
  errorBox: {
    background: "#FEF2F2",
    border: "1px solid #FECACA",
    borderRadius: 8,
    padding: "10px 14px",
    fontSize: 13,
    color: "#B91C1C",
  },
};
