import { useEffect, useState } from "react";
import axios from "axios";
import { QuestionSet } from "../types/survey";
import SurveyPreview from "../components/SurveyPreview";
import SurveyRefineChat from "../components/SurveyRefineChat";
import SurveyEditor from "../components/SurveyEditor";

const API = import.meta.env.VITE_API_URL || "http://localhost:8000";

const KEYWORD_CHIPS = [
  "전통 시장", "명절", "민요", "설화", "농촌",
  "학교", "동네", "가족", "장터", "고향",
];

type MediaType = "image" | "audio" | "text";
type QuestionType = "narrative" | "choice" | "mixed";

interface Candidate {
  title: string;
  description?: string;
  media_url?: string;
  media_type: MediaType;
  source: string;
  source_url?: string;
  ai_question?: string;
  text_content?: string;
}

interface Topic {
  id?: string;
  title: string;
  description?: string;
  media_url?: string;
  media_type?: string;
  source?: string;
  ai_question?: string;
  question_type?: string;
  region?: string;
  active_week?: string;
}

interface PendingWorker {
  welfare_id: string;
  name: string;
  region: string;
}

export default function TopicManager() {
  const [step, setStep] = useState<1 | 2 | 3>(1);

  // Step 1
  const [defaultTopic, setDefaultTopic] = useState<Topic | null>(null);
  const [pendingInfo, setPendingInfo] = useState<{
    total_workers: number;
    published_count: number;
    pending_workers: PendingWorker[];
  } | null>(null);

  // Step 2
  const [mediaType, setMediaType] = useState<MediaType>("image");
  const [keyword, setKeyword] = useState("");
  const [quantity, setQuantity] = useState(3);
  const [candidates, setCandidates] = useState<Candidate[]>([]);
  const [searching, setSearching] = useState(false);
  const [searchError, setSearchError] = useState("");

  // Step 3 — 발행
  const [selected, setSelected] = useState<Candidate | null>(null);
  const [questionType, setQuestionType] = useState<QuestionType>("narrative");
  const [customQuestion, setCustomQuestion] = useState("");
  const [publishing, setPublishing] = useState(false);
  const [publishResult, setPublishResult] = useState<{
    topic_id: string; title: string; region: string;
  } | null>(null);

  // Step 3 — 설문지 생성/편집
  const [questionCount, setQuestionCount] = useState(1);
  const [narrativeCount, setNarrativeCount] = useState(1);
  const [choiceCount, setChoiceCount] = useState(1);

  const [questionSet, setQuestionSet] = useState<QuestionSet | null>(null);
  const [isGenerating, setIsGenerating] = useState(false);
  const [needsRegenerate, setNeedsRegenerate] = useState(false);
  const [showRefineChat, setShowRefineChat] = useState(false);
  const [showEditor, setShowEditor] = useState(false);

  useEffect(() => {
    fetchDefaultTopic();
    fetchPending();
  }, []);

  const fetchDefaultTopic = async () => {
    try {
      const { data } = await axios.get(`${API}/welfare/topics/default`);
      setDefaultTopic(data);
    } catch {
      setDefaultTopic(null);
    }
  };

  const fetchPending = async () => {
    try {
      const { data } = await axios.get(`${API}/welfare/topics/pending`);
      setPendingInfo(data);
    } catch {
      setPendingInfo(null);
    }
  };

  const handleSearch = async () => {
    setSearching(true);
    setSearchError("");
    setCandidates([]);
    try {
      const { data } = await axios.post(`${API}/welfare/topics/search`, {
        media_type: mediaType,
        keyword,
        quantity,
      });
      setCandidates(data.candidates);
      setStep(2);
    } catch (e: any) {
      setSearchError(e.response?.data?.detail ?? "검색 실패. API 키를 확인하거나 다시 시도해주세요.");
    } finally {
      setSearching(false);
    }
  };

  const generateSurveyQuestions = async (qType: QuestionType, candidate: Candidate) => {
    setIsGenerating(true);
    setNeedsRegenerate(false);
    try {
      const payload: any = {
        title: candidate.title,
        description: candidate.description ?? "",
        media_type: candidate.media_type,
        target_age: "elderly",
        question_type: qType,
      };
      if (qType === "mixed") {
        payload.narrative_count = narrativeCount;
        payload.choice_count = choiceCount;
      } else {
        payload.question_count = questionCount;
      }
      const { data } = await axios.post(`${API}/welfare/topics/generate-questions`, payload);
      setQuestionSet(data);
    } catch {
      setQuestionSet(null);
    } finally {
      setIsGenerating(false);
    }
  };

  const handleSelect = (c: Candidate) => {
    setSelected(c);
    setCustomQuestion(c.ai_question ?? "");
    setQuestionSet(null);
    setNeedsRegenerate(false);
    setStep(3);
  };

  const handleQuestionTypeChange = (t: QuestionType) => {
    setQuestionType(t);
    if (selected) setNeedsRegenerate(true);
  };

  const handlePublishWithQS = async (qs?: QuestionSet) => {
    if (!selected) return;
    const finalQS = qs ?? questionSet;
    if (qs) setQuestionSet(qs);
    setPublishing(true);
    setShowRefineChat(false);
    try {
      const { data } = await axios.post(`${API}/welfare/topics/publish`, {
        title: selected.title,
        description: selected.description ?? "",
        media_url: selected.media_url ?? null,
        media_type: selected.media_type,
        source: selected.source,
        source_url: selected.source_url ?? "",
        ai_question: customQuestion,
        text_content: selected.text_content ?? null,
        question_type: questionType,
        is_customized: true,
        choices: finalQS ?? null,
      });
      setPublishResult(data);
      fetchDefaultTopic();
      fetchPending();
    } catch (e: any) {
      alert("발행 실패: " + (e.response?.data?.detail ?? e.message));
    } finally {
      setPublishing(false);
    }
  };

  const reset = () => {
    setStep(1);
    setCandidates([]);
    setSelected(null);
    setPublishResult(null);
    setCustomQuestion("");
    setQuestionSet(null);
    setNeedsRegenerate(false);
    setShowRefineChat(false);
    setShowEditor(false);
    setQuestionCount(1);
    setNarrativeCount(1);
    setChoiceCount(1);
  };

  return (
    <div style={s.container}>
      <h2 style={s.title}>📋 주간 주제 관리</h2>

      {/* 현황 카드 */}
      <div style={s.statusRow}>
        <div style={s.statusCard}>
          <div style={s.statusLabel}>이번 주 기본 주제</div>
          {defaultTopic ? (
            <>
              <div style={s.statusValue}>{defaultTopic.title}</div>
              <div style={s.statusMeta}>
                [{defaultTopic.source}] · {defaultTopic.media_type} · {defaultTopic.active_week}
              </div>
              <div style={s.statusMeta}>{defaultTopic.ai_question}</div>
            </>
          ) : (
            <div style={{ color: "#aaa" }}>아직 발행 전</div>
          )}
        </div>
        <div style={s.statusCard}>
          <div style={s.statusLabel}>발행 현황</div>
          {pendingInfo ? (
            <>
              <div style={s.statusValue}>
                {pendingInfo.published_count} / {pendingInfo.total_workers} 완료
              </div>
              {pendingInfo.pending_workers.length > 0 && (
                <div style={{ marginTop: 8 }}>
                  {pendingInfo.pending_workers.map((w) => (
                    <div key={w.welfare_id} style={s.pendingBadge}>
                      ⏳ {w.name} ({w.region})
                    </div>
                  ))}
                </div>
              )}
            </>
          ) : (
            <div style={{ color: "#aaa" }}>조회 중...</div>
          )}
        </div>
      </div>

      {/* 스텝 인디케이터 */}
      <div style={s.stepRow}>
        {(["1. 검색", "2. 후보 선택", "3. 발행"] as const).map((label, i) => (
          <div key={label} style={{
            ...s.stepItem,
            background: step === i + 1 ? "#E8572A" : step > i + 1 ? "#4CAF50" : "#ddd",
            color: step >= i + 1 ? "#fff" : "#888",
          }}>
            {step > i + 1 ? "✓ " : ""}{label}
          </div>
        ))}
      </div>

      {/* Step 1 — 검색 폼 */}
      {step === 1 && !publishResult && (
        <div style={s.card}>
          <h3 style={s.cardTitle}>공공데이터 후보 검색</h3>
          <div style={s.formRow}>
            <label style={s.label}>미디어 타입</label>
            <div style={s.btnGroup}>
              {(["image", "audio", "text"] as MediaType[]).map((t) => (
                <button
                  key={t}
                  style={{ ...s.typeBtn, ...(mediaType === t ? s.typeBtnActive : {}) }}
                  onClick={() => setMediaType(t)}
                >
                  {t === "image" ? "🖼 사진" : t === "audio" ? "🎵 음원" : "📖 기록"}
                </button>
              ))}
            </div>
          </div>
          <div style={s.formRow}>
            <label style={s.label}>키워드 (선택)</label>
            <input
              style={s.input}
              value={keyword}
              onChange={(e) => setKeyword(e.target.value)}
              placeholder="예: 전통 시장, 명절, 민요 (빈칸이면 랜덤)"
              onKeyDown={(e) => e.key === "Enter" && handleSearch()}
            />
            <div style={{ display: "flex", flexWrap: "wrap", gap: 8, marginTop: 10 }}>
              {KEYWORD_CHIPS.map((chip) => (
                <button
                  key={chip}
                  onClick={() => setKeyword(chip)}
                  style={{
                    padding: "6px 14px",
                    borderRadius: 20,
                    border: keyword === chip ? "2px solid #E8572A" : "1px solid #ddd",
                    background: keyword === chip ? "#FFF0EB" : "#fff",
                    color: keyword === chip ? "#E8572A" : "#555",
                    fontSize: 13,
                    fontWeight: 600,
                    cursor: "pointer",
                  }}
                >
                  {chip}
                </button>
              ))}
            </div>
          </div>
          <div style={s.formRow}>
            <label style={s.label}>후보 수</label>
            <div style={s.btnGroup}>
              {[1, 2, 3].map((n) => (
                <button
                  key={n}
                  style={{ ...s.typeBtn, ...(quantity === n ? s.typeBtnActive : {}) }}
                  onClick={() => setQuantity(n)}
                >
                  {n}개
                </button>
              ))}
            </div>
          </div>
          {searchError && <div style={s.error}>{searchError}</div>}
          <button style={s.primaryBtn} onClick={handleSearch} disabled={searching}>
            {searching ? "검색 중..." : "🔍 후보 검색"}
          </button>
        </div>
      )}

      {/* Step 2 — 후보 카드 목록 */}
      {step === 2 && (
        <div style={s.card}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <h3 style={s.cardTitle}>후보 선택 ({candidates.length}개)</h3>
            <button style={s.ghostBtn} onClick={() => setStep(1)}>← 다시 검색</button>
          </div>
          <div style={s.candidateGrid}>
            {candidates.map((c, i) => (
              <div key={i} style={s.candidateCard}>
                {c.media_url && c.media_type === "image" && (
                  <img src={c.media_url} alt={c.title} style={s.candidateImg} />
                )}
                {c.media_url && c.media_type === "audio" && (
                  <audio controls src={c.media_url} style={{ width: "100%", marginBottom: 8 }} />
                )}
                {!c.media_url && (
                  <div style={s.mediaPlaceholder}>
                    {c.media_type === "image" ? "🖼" : c.media_type === "audio" ? "🎵" : "📖"}
                  </div>
                )}
                <div style={s.candidateTitle}>{c.title}</div>
                <div style={s.candidateSource}>[{c.source}] · {c.media_type}</div>
                {c.description && (
                  <div style={s.candidateDesc}>{c.description.slice(0, 80)}{c.description.length > 80 ? "..." : ""}</div>
                )}
                {c.ai_question && (
                  <div style={s.aiQuestion}>💬 {c.ai_question}</div>
                )}
                <button style={s.selectBtn} onClick={() => handleSelect(c)}>
                  이 주제 선택 →
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Step 3 — 발행 확인 */}
      {step === 3 && selected && !publishResult && (
        <div style={s.card}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <h3 style={s.cardTitle}>발행 확인</h3>
            <button style={s.ghostBtn} onClick={() => setStep(2)}>← 후보 다시 보기</button>
          </div>

          <div style={s.selectedPreview}>
            <div style={s.selectedTitle}>{selected.title}</div>
            <div style={s.candidateSource}>[{selected.source}] · {selected.media_type}</div>
          </div>

          <div style={s.formRow}>
            <label style={s.label}>질문 유형</label>
            <div style={{ display: "flex", gap: 8, flexWrap: "wrap", alignItems: "center" }}>
              {([
                ["narrative", "📝 서술형"],
                ["choice", "☑ 선택형"],
                ["mixed", "🔀 혼합형"],
              ] as [QuestionType, string][]).map(([t, label]) => (
                <button
                  key={t}
                  style={{ ...s.typeBtn, ...(questionType === t ? s.typeBtnActive : {}) }}
                  onClick={() => handleQuestionTypeChange(t)}
                >
                  {label}
                </button>
              ))}
              {needsRegenerate && (
                <button
                  style={s.regenBtn}
                  onClick={() => selected && generateSurveyQuestions(questionType, selected)}
                  disabled={isGenerating}
                >
                  {isGenerating ? "생성 중..." : "🔄 재생성"}
                </button>
              )}
            </div>
          </div>

          {/* 질문 수량 설정 */}
          <div style={s.formRow}>
            <label style={s.label}>질문 수량</label>
            {questionType === "narrative" && (
              <div style={s.btnGroup}>
                {[1, 2, 3, 4, 5].map((n) => (
                  <button
                    key={n}
                    style={{ ...s.typeBtn, ...(questionCount === n ? s.typeBtnActive : {}) }}
                    onClick={() => { setQuestionCount(n); if (selected) setNeedsRegenerate(true); }}
                  >
                    {n}개
                  </button>
                ))}
              </div>
            )}
            {questionType === "choice" && (
              <div style={s.btnGroup}>
                {[1, 2, 3, 4, 5, 6, 7, 8, 9, 10].map((n) => (
                  <button
                    key={n}
                    style={{ ...s.typeBtn, ...(questionCount === n ? s.typeBtnActive : {}) }}
                    onClick={() => { setQuestionCount(n); if (selected) setNeedsRegenerate(true); }}
                  >
                    {n}개
                  </button>
                ))}
              </div>
            )}
            {questionType === "mixed" && (
              <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
                <div>
                  <div style={{ fontSize: 13, color: "#555", marginBottom: 6, fontWeight: 600 }}>선택형 질문 수</div>
                  <div style={s.btnGroup}>
                    {[1, 2, 3, 4, 5, 6].map((n) => (
                      <button
                        key={n}
                        style={{ ...s.typeBtn, ...(choiceCount === n ? s.typeBtnActive : {}) }}
                        onClick={() => { setChoiceCount(n); if (selected) setNeedsRegenerate(true); }}
                      >
                        {n}개
                      </button>
                    ))}
                  </div>
                </div>
                <div>
                  <div style={{ fontSize: 13, color: "#555", marginBottom: 6, fontWeight: 600 }}>서술형 질문 수</div>
                  <div style={s.btnGroup}>
                    {[1, 2].map((n) => (
                      <button
                        key={n}
                        style={{ ...s.typeBtn, ...(narrativeCount === n ? s.typeBtnActive : {}) }}
                        onClick={() => { setNarrativeCount(n); if (selected) setNeedsRegenerate(true); }}
                      >
                        {n}개
                      </button>
                    ))}
                  </div>
                </div>
              </div>
            )}
          </div>

          <div style={s.formRow}>
            <label style={s.label}>AI 생성 질문 (수정 가능)</label>
            <textarea
              style={s.textarea}
              value={customQuestion}
              onChange={(e) => setCustomQuestion(e.target.value)}
              rows={3}
            />
          </div>

          {/* 미리보기 생성 버튼 */}
          <div style={s.formRow}>
            <button
              style={{ ...s.primaryBtn, background: "#1A1A2E", marginTop: 0 }}
              onClick={() => selected && generateSurveyQuestions(questionType, selected)}
              disabled={isGenerating}
            >
              {isGenerating ? "⏳ 생성 중..." : "🔍 미리보기 생성"}
            </button>
          </div>

          {/* 설문지 미리보기 */}
          <div style={s.formRow}>
            <label style={s.label}>설문지 미리보기</label>
            {isGenerating ? (
              <div style={s.generatingBox}>⏳ 설문지 질문 생성 중...</div>
            ) : questionSet ? (
              <>
                <SurveyPreview questionSet={questionSet} title={selected.title} />
                <div style={{ display: "flex", gap: 8, marginTop: 12 }}>
                  <button style={s.secondaryBtn} onClick={() => setShowRefineChat(true)}>
                    💬 AI와 협의
                  </button>
                  <button style={s.secondaryBtn} onClick={() => setShowEditor(true)}>
                    ✏️ 직접 수정
                  </button>
                </div>
              </>
            ) : (
              <div style={s.generatingBox}>
                질문 유형과 수량을 선택한 후 "미리보기 생성" 버튼을 눌러주세요.
              </div>
            )}
          </div>

          <button
            style={s.primaryBtn}
            onClick={() => handlePublishWithQS()}
            disabled={publishing || isGenerating}
          >
            {publishing ? "발행 중..." : "🚀 이번 주 주제로 발행"}
          </button>
        </div>
      )}

      {/* 발행 완료 */}
      {publishResult && (
        <div style={{ ...s.card, textAlign: "center" }}>
          <div style={{ fontSize: 48, marginBottom: 16 }}>✅</div>
          <h3 style={{ color: "#4CAF50", marginBottom: 8 }}>발행 완료</h3>
          <div style={s.selectedTitle}>{publishResult.title}</div>
          <div style={{ color: "#888", marginTop: 4 }}>지역: {publishResult.region}</div>
          <div style={{ color: "#888" }}>ID: {publishResult.topic_id}</div>
          <button style={{ ...s.primaryBtn, marginTop: 24 }} onClick={reset}>
            새 주제 발행하기
          </button>
        </div>
      )}

      {/* AI 협의 모달 */}
      {showRefineChat && selected && questionSet && (
        <div style={s.modalOverlay} onClick={() => setShowRefineChat(false)}>
          <div style={s.modalContent} onClick={(e) => e.stopPropagation()}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
              <h3 style={{ margin: 0 }}>AI와 협의</h3>
              <button style={s.closeBtn} onClick={() => setShowRefineChat(false)}>✕</button>
            </div>
            <SurveyRefineChat
              topicTitle={selected.title}
              initialQuestionSet={questionSet}
              onDirectEdit={(qs) => {
                setQuestionSet(qs);
                setShowRefineChat(false);
                setShowEditor(true);
              }}
              onPublish={(qs) => handlePublishWithQS(qs)}
            />
          </div>
        </div>
      )}

      {/* 직접 수정 모달 */}
      {showEditor && selected && questionSet && (
        <div style={s.modalOverlay} onClick={() => setShowEditor(false)}>
          <div style={s.modalContent} onClick={(e) => e.stopPropagation()}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
              <h3 style={{ margin: 0 }}>설문지 직접 수정</h3>
              <button style={s.closeBtn} onClick={() => setShowEditor(false)}>✕</button>
            </div>
            <SurveyEditor
              initialQuestionSet={questionSet}
              onChange={(qs) => setQuestionSet(qs)}
              onPublish={() => { setShowEditor(false); handlePublishWithQS(); }}
            />
          </div>
        </div>
      )}
    </div>
  );
}

const s: Record<string, React.CSSProperties> = {
  container: { padding: 32, background: "#F5F7FA", minHeight: "100vh", fontFamily: "sans-serif" },
  title: { fontSize: 22, fontWeight: "bold", color: "#1A1A2E", marginBottom: 24 },
  statusRow: { display: "flex", gap: 16, marginBottom: 24, flexWrap: "wrap" },
  statusCard: {
    flex: 1, minWidth: 280, background: "#fff", borderRadius: 12,
    padding: "20px 24px", boxShadow: "0 2px 8px rgba(0,0,0,0.06)",
  },
  statusLabel: { fontSize: 12, color: "#888", marginBottom: 8, textTransform: "uppercase", letterSpacing: 1 },
  statusValue: { fontSize: 18, fontWeight: "bold", color: "#222", marginBottom: 4 },
  statusMeta: { fontSize: 13, color: "#888", marginTop: 2 },
  pendingBadge: { fontSize: 13, color: "#E8572A", marginTop: 4 },
  stepRow: { display: "flex", gap: 8, marginBottom: 24 },
  stepItem: {
    flex: 1, textAlign: "center", padding: "10px 0", borderRadius: 8,
    fontSize: 13, fontWeight: "bold", transition: "background 0.2s",
  },
  card: {
    background: "#fff", borderRadius: 12, padding: "24px 28px",
    boxShadow: "0 2px 8px rgba(0,0,0,0.06)", marginBottom: 24,
  },
  cardTitle: { fontSize: 17, fontWeight: "bold", color: "#222", marginBottom: 20, marginTop: 0 },
  formRow: { marginBottom: 18 },
  label: { display: "block", fontSize: 13, color: "#555", marginBottom: 8, fontWeight: 600 },
  btnGroup: { display: "flex", gap: 8, flexWrap: "wrap" },
  typeBtn: {
    padding: "8px 18px", borderRadius: 8, border: "2px solid #ddd",
    background: "#fff", cursor: "pointer", fontSize: 14, fontWeight: 600, color: "#555",
  },
  typeBtnActive: { border: "2px solid #E8572A", background: "#FFF0EB", color: "#E8572A" },
  regenBtn: {
    padding: "8px 18px", borderRadius: 8, border: "2px solid #FF9800",
    background: "#FFF8E1", cursor: "pointer", fontSize: 14, fontWeight: 600, color: "#E65100",
  },
  input: {
    width: "100%", padding: "10px 14px", borderRadius: 8, border: "1px solid #ddd",
    fontSize: 14, boxSizing: "border-box",
  },
  textarea: {
    width: "100%", padding: "10px 14px", borderRadius: 8, border: "1px solid #ddd",
    fontSize: 14, boxSizing: "border-box", resize: "vertical",
  },
  error: { color: "#E8572A", fontSize: 13, marginBottom: 12 },
  primaryBtn: {
    background: "#E8572A", color: "#fff", border: "none", borderRadius: 10,
    padding: "14px 28px", fontSize: 15, fontWeight: "bold", cursor: "pointer",
    marginTop: 8, width: "100%",
  },
  secondaryBtn: {
    padding: "8px 18px", borderRadius: 8, border: "2px solid #1A1A2E",
    background: "#fff", cursor: "pointer", fontSize: 14, fontWeight: 600, color: "#1A1A2E",
  },
  ghostBtn: {
    background: "none", border: "1px solid #ddd", borderRadius: 8,
    padding: "6px 14px", fontSize: 13, cursor: "pointer", color: "#555",
  },
  candidateGrid: { display: "flex", gap: 16, flexWrap: "wrap" },
  candidateCard: {
    flex: "1 1 260px", background: "#FAFAFA", borderRadius: 12, padding: 16,
    border: "2px solid #eee",
  },
  candidateImg: { width: "100%", height: 160, objectFit: "cover", borderRadius: 8, marginBottom: 10 },
  mediaPlaceholder: {
    width: "100%", height: 100, background: "#eee", borderRadius: 8,
    display: "flex", alignItems: "center", justifyContent: "center",
    fontSize: 36, marginBottom: 10,
  },
  candidateTitle: { fontSize: 15, fontWeight: "bold", color: "#222", marginBottom: 4 },
  candidateSource: { fontSize: 12, color: "#888", marginBottom: 6 },
  candidateDesc: { fontSize: 13, color: "#555", marginBottom: 8, lineHeight: 1.5 },
  aiQuestion: {
    fontSize: 13, color: "#4CAF50", background: "#F0FFF4",
    borderRadius: 6, padding: "6px 10px", marginBottom: 10,
  },
  selectBtn: {
    background: "#1A1A2E", color: "#fff", border: "none", borderRadius: 8,
    padding: "10px 0", width: "100%", fontSize: 14, fontWeight: "bold", cursor: "pointer",
  },
  selectedPreview: {
    background: "#FFF8F6", borderRadius: 10, padding: "16px 20px",
    borderLeft: "4px solid #E8572A", marginBottom: 20,
  },
  selectedTitle: { fontSize: 17, fontWeight: "bold", color: "#222" },
  generatingBox: {
    background: "#F5F7FA", borderRadius: 8, padding: "16px 20px",
    color: "#888", fontSize: 14, textAlign: "center",
  },
  modalOverlay: {
    position: "fixed", top: 0, left: 0, right: 0, bottom: 0,
    background: "rgba(0,0,0,0.5)", zIndex: 1000,
    display: "flex", alignItems: "center", justifyContent: "center",
    padding: 24,
  },
  modalContent: {
    background: "#fff", borderRadius: 16, padding: 28,
    width: "100%", maxWidth: 900, maxHeight: "90vh",
    overflow: "auto", boxShadow: "0 8px 32px rgba(0,0,0,0.2)",
  },
  closeBtn: {
    background: "none", border: "none", fontSize: 18,
    cursor: "pointer", color: "#888", padding: "0 4px",
  },
};
