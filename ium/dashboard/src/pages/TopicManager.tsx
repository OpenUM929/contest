import { useEffect, useState } from "react";
import axios from "axios";
import { QuestionSet, PublishResult } from "../types/survey";
import SurveyPreview from "../components/SurveyPreview";
import SurveyRefineChat from "../components/SurveyRefineChat";
import SurveyEditor from "../components/SurveyEditor";
import ManualPreviewPanel from "../components/ManualPreviewPanel";
import { buildGeneratePrompt } from "../api/survey";

const API = import.meta.env.VITE_API_URL || "http://localhost:8000";

interface KeywordItem {
  keyword: string;
  count: number;
}

type MediaType = "image" | "audio" | "text" | "story";
type QuestionType = "narrative" | "choice" | "mixed";

interface Candidate {
  title: string;
  description?: string;
  media_url?: string;
  media_type: MediaType;
  media_subtype?: string;
  refined_keywords?: string;
  source: string;
  source_url?: string;
  ai_question?: string;
  text_content?: string;
  ingredient?: string;
  sizing?: string;
  region?: string;
  sub_region?: string;
  keywords?: string;
  theme?: string;
  sub_theme?: string;
  image_analysis?: {
    artifact_summary: { era: string; type: string; features: string[] };
    context: { historical: string | null; social: string | null };
    mood: { atmosphere: string; associations: string[] };
    topic_candidates: { title: string; description: string; age_suitability: string }[];
  };
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

interface WorkerItem {
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
    pending_workers: WorkerItem[];
  } | null>(null);

  // 복지사 선택
  const [workers, setWorkers] = useState<WorkerItem[]>([]);
  const [selectedWelfareId, setSelectedWelfareId] = useState<string>("");

  // Step 2
  const [mediaType, setMediaType] = useState<MediaType>("image");
  const [mediaSubtype, setMediaSubtype] = useState("");
  const [keyword, setKeyword] = useState("");
  const [region, setRegion] = useState("");
  const [quantity, setQuantity] = useState(20);
  const [candidates, setCandidates] = useState<Candidate[]>([]);
  const [searching, setSearching] = useState(false);
  const [searchError, setSearchError] = useState("");
  const [keywordChips, setKeywordChips] = useState<KeywordItem[]>([]);
  const [keywordFiltered, setKeywordFiltered] = useState(false);
  const [keywordMatched, setKeywordMatched] = useState(0);
  const [searchMessage, setSearchMessage] = useState("");
  const [allCandidates, setAllCandidates] = useState<Candidate[]>([]);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [totalCount, setTotalCount] = useState(0);
  const [boardView, setBoardView] = useState(false);

  // Step 3 — 발행
  const [selected, setSelected] = useState<Candidate | null>(null);
  const [questionType, setQuestionType] = useState<QuestionType>("narrative");
  const [customQuestion, setCustomQuestion] = useState("");
  const [publishing, setPublishing] = useState(false);
  const [publishResult, setPublishResult] = useState<PublishResult | null>(null);

  // 이미지 분석 상세 토글 + lazy loading
  const [expandedAnalysis, setExpandedAnalysis] = useState<number | null>(null);
  const [analyzingIdx, setAnalyzingIdx] = useState<number | null>(null);

  // Step 3 — 설문지 생성/편집
  const [questionCount, setQuestionCount] = useState(1);
  const [narrativeCount, setNarrativeCount] = useState(1);
  const [choiceCount, setChoiceCount] = useState(1);

  const [questionSet, setQuestionSet] = useState<QuestionSet | null>(null);
  const [draftStatus, setDraftStatus] = useState<"ai_draft" | "editing" | "published" | null>(null);
  const [warnings, setWarnings] = useState<string[]>([]);
  const [isGenerating, setIsGenerating] = useState(false);
  const [genError, setGenError] = useState("");
  const [needsRegenerate, setNeedsRegenerate] = useState(false);
  const [showRefineChat, setShowRefineChat] = useState(false);
  const [showEditor, setShowEditor] = useState(false);

  // 미리보기 모드 — auto: AI 자동 호출 / manual: 프롬프트 출력 후 외부 AI 답변 붙여넣기
  const [previewMode, setPreviewMode] = useState<"auto" | "manual">("auto");
  const [manualPrompt, setManualPrompt] = useState("");
  const [promptLoading, setPromptLoading] = useState(false);

  // Step 3 — 배포 대상 선택
  const [targetUsers, setTargetUsers] = useState<{ user_id: string; nickname: string; user_type: string }[]>([]);
  const [targetUserIds, setTargetUserIds] = useState<string[]>([]);

  useEffect(() => {
    fetchDefaultTopic();
    fetchPending();
    fetchKeywords();
    fetchWorkers();
  }, []);

  useEffect(() => {
    if (step === 3 && selectedWelfareId) {
      (async () => {
        try {
          const { data } = await axios.get(`${API}/api/welfare/workers/${selectedWelfareId}/users`);
          setTargetUsers(data.users ?? []);
          setTargetUserIds([]);
        } catch {
          setTargetUsers([]);
        }
      })();
    }
  }, [step, selectedWelfareId]);

  const fetchKeywords = async () => {
    try {
      const { data } = await axios.get(`${API}/api/welfare/topics/keywords`);
      setKeywordChips(data.keywords ?? []);
    } catch {
      // API 실패 시 빈 상태 유지
    }
  };

  const fetchDefaultTopic = async () => {
    try {
      const { data } = await axios.get(`${API}/api/welfare/topics/default`);
      setDefaultTopic(data);
    } catch {
      setDefaultTopic(null);
    }
  };

  const fetchWorkers = async () => {
    try {
      const { data } = await axios.get(`${API}/api/welfare/workers`);
      setWorkers(data.workers ?? []);
      if (data.workers?.length > 0 && !selectedWelfareId) {
        setSelectedWelfareId(data.workers[0].welfare_id);
      }
    } catch {
      // 복지사 목록 조회 실패 시 무시
    }
  };

  const fetchPending = async () => {
    try {
      const { data } = await axios.get(`${API}/api/welfare/topics/pending`);
      setPendingInfo(data);
    } catch {
      setPendingInfo(null);
    }
  };

  const handleSearch = async (p?: number) => {
    setSearching(true);
    setSearchError("");
    setSearchMessage("");
    setCandidates([]);
    setAllCandidates([]);
    const targetPage = p ?? 1;
    // media type mapping: image/image, story/text+story, text/text
    let apiMediaType: string = mediaType;
    let apiMediaSubtype: string = "";
    if (mediaType === "story") {
      apiMediaType = "text";
      apiMediaSubtype = "story";
    } else if (mediaType === "text") {
      apiMediaType = "text";
      apiMediaSubtype = "text";
    } else {
      apiMediaSubtype = "image";
    }
    try {
      const { data } = await axios.post(`${API}/api/welfare/topics/search`, {
        media_type: apiMediaType,
        media_subtype: apiMediaSubtype,
        keyword: keyword.trim(),
        region: region.trim(),
        quantity,
        page: targetPage,
      });
      setCandidates(data.candidates ?? []);
      setAllCandidates(data.all_candidates ?? []);
      setKeywordFiltered(data.keyword_filtered ?? false);
      setKeywordMatched(data.keyword_matched ?? 0);
      setSearchMessage(data.message ?? "");
      setPage(data.page ?? 1);
      setTotalPages(data.total_pages ?? 1);
      setTotalCount(data.total_count ?? 0);
      setBoardView(data.keyword_filtered && data.keyword_matched === 0);
      setStep(2);
    } catch (e: any) {
      setSearchError(e.response?.data?.detail ?? "검색 실패. API 키를 확인하거나 다시 시도해주세요.");
    } finally {
      setSearching(false);
    }
  };

  // 자동/수동 미리보기가 동일한 프롬프트를 쓰도록 payload 조립을 공유한다.
  const buildQuestionPayload = (qType: QuestionType, candidate: Candidate) => {
    const payload: any = {
      title: candidate.title,
      description: candidate.description ?? "",
      media_type: candidate.media_type,
      target_age: "elderly",
      question_type: qType,
      welfare_id: selectedWelfareId || undefined,
    };
    if (qType === "mixed") {
      payload.narrative_count = narrativeCount;
      payload.choice_count = choiceCount;
    } else {
      payload.question_count = questionCount;
    }
    return payload;
  };

  const generateSurveyQuestions = async (qType: QuestionType, candidate: Candidate) => {
    setIsGenerating(true);
    setNeedsRegenerate(false);
    setGenError("");
    try {
      const payload = buildQuestionPayload(qType, candidate);
      const { data } = await axios.post(`${API}/api/welfare/topics/generate-questions`, payload);
      const { warnings: w = [], ...qset } = data;
      setQuestionSet(qset);
      setWarnings(w);
      setDraftStatus("ai_draft");
    } catch (e: any) {
      setQuestionSet(null);
      setGenError(e?.response?.data?.detail || e?.message || "질문 생성에 실패했습니다. 서버 또는 API 키를 확인해주세요.");
    } finally {
      setIsGenerating(false);
    }
  };

  // 수동 미리보기: AI에게 보낼 프롬프트 원문을 받아온다 (AI 호출 안 함).
  const generateManualPrompt = async () => {
    if (!selected) return;
    setPromptLoading(true);
    setGenError("");
    try {
      const payload = buildQuestionPayload(questionType, selected);
      const { data } = await buildGeneratePrompt(payload);
      setManualPrompt(data.prompt || "");
    } catch (e: any) {
      setGenError(e?.response?.data?.detail || e?.message || "프롬프트 생성에 실패했습니다.");
    } finally {
      setPromptLoading(false);
    }
  };

  // 수동 미리보기: 붙여넣은 AI 답변을 파싱해 미리보기에 반영한다.
  const applyManualResult = (qs: QuestionSet, w: string[]) => {
    setQuestionSet(qs);
    setWarnings(w);
    setDraftStatus("ai_draft");
    setNeedsRegenerate(false);
  };

  const handleSelect = async (c: Candidate, idx: number) => {
    // lazy loading: image 타입이고 분석 결과가 없으면 클릭 시 분석
    if (c.media_type === "image" && !c.image_analysis) {
      setAnalyzingIdx(idx);
      try {
        const { data } = await axios.post(`${API}/api/welfare/topics/analyze`, {
          title: c.title,
          description: c.description ?? "",
          ingredient: c.ingredient ?? "",
          sizing: c.sizing ?? "",
          source: c.source,
          welfare_id: selectedWelfareId || undefined,
        });
        const updated = { ...c, image_analysis: data };
        setCandidates((prev) =>
          prev.map((item, i) => (i === idx ? updated : item))
        );
        setSelected(updated);
      } catch {
        // 분석 실패 시에도 선택은 진행
        setSelected(c);
      } finally {
        setAnalyzingIdx(null);
      }
    } else {
      setSelected(c);
    }
    setCustomQuestion(c.ai_question ?? "");
    setQuestionSet(null);
    setGenError("");
    setNeedsRegenerate(false);
    setStep(3);
  };

  const handleQuestionTypeChange = (t: QuestionType) => {
    setQuestionType(t);
    if (selected) setNeedsRegenerate(true);
  };

  const handlePublishWithQS = async (qs?: QuestionSet) => {
    if (!selected) return;
    if (!selectedWelfareId) {
      alert("먼저 복지사를 선택해주세요.");
      return;
    }
    const finalQS = qs ?? questionSet;
    if (qs) setQuestionSet(qs);
    setPublishing(true);
    setShowRefineChat(false);
    try {
      const { data } = await axios.post(`${API}/api/welfare/topics/publish`, {
        title: selected.title,
        description: selected.description ?? "",
        media_url: selected.media_url ?? null,
        media_type: selected.media_type,
        source: selected.source,
        source_url: selected.source_url ?? "",
        ai_question: customQuestion,
        text_content: selected.text_content ?? null,
        question_type: questionType,
        welfare_id: selectedWelfareId,
        is_customized: true,
        choices: finalQS ?? null,
        target_user_ids: targetUserIds.length > 0 ? targetUserIds : [],
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
    setAllCandidates([]);
    setSelected(null);
    setPublishResult(null);
    setCustomQuestion("");
    setQuestionSet(null);
    setDraftStatus(null);
    setWarnings([]);
    setNeedsRegenerate(false);
    setShowRefineChat(false);
    setShowEditor(false);
    setTargetUsers([]);
    setTargetUserIds([]);
    setQuestionCount(1);
    setNarrativeCount(1);
    setChoiceCount(1);
    setKeywordFiltered(false);
    setKeywordMatched(0);
    setSearchMessage("");
    setBoardView(false);
    setPage(1);
    setTotalPages(1);
    setTotalCount(0);
  };

  return (
    <div style={s.container}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
        <h2 style={s.title}>📋 주간 주제 관리</h2>
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <label style={{ fontSize: 13, color: "#666", fontWeight: "bold" }}>복지사</label>
          <select
            value={selectedWelfareId}
            onChange={(e) => setSelectedWelfareId(e.target.value)}
            style={{
              padding: "8px 12px", borderRadius: 8, border: "1px solid #DDD",
              fontSize: 14, background: "#FFF", minWidth: 150,
            }}
          >
            {workers.length === 0 && <option value="">로딩 중...</option>}
            {workers.map((w) => (
              <option key={w.welfare_id} value={w.welfare_id}>
                {w.name} ({w.region || "기본"})
              </option>
            ))}
          </select>
        </div>
      </div>

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
              {([["image", "🖼 이미지"], ["story", "📖 이야기"], ["text", "📄 텍스트"]] as const).map(([val, label]) => (
                <button
                  key={val}
                  style={{ ...s.typeBtn, ...(mediaType === val ? s.typeBtnActive : {}) }}
                  onClick={() => setMediaType(val)}
                >
                  {label}
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
              placeholder="예: 설화, 전설, 지명유래 (빈칸이면 전체 목록)"
              onKeyDown={(e) => e.key === "Enter" && handleSearch()}
            />
            <div style={{ display: "flex", flexWrap: "wrap", gap: 8, marginTop: 10 }}>
              {keywordChips.map((chip) => (
                <button
                  key={chip.keyword}
                  onClick={() => setKeyword(chip.keyword)}
                  style={{
                    padding: "6px 14px",
                    borderRadius: 20,
                    border: keyword === chip.keyword ? "2px solid #E8572A" : "1px solid #ddd",
                    background: keyword === chip.keyword ? "#FFF0EB" : "#fff",
                    color: keyword === chip.keyword ? "#E8572A" : "#555",
                    fontSize: 13,
                    fontWeight: 600,
                    cursor: "pointer",
                  }}
                >
                  {chip.keyword}
                </button>
              ))}
            </div>
          </div>
          <div style={s.formRow}>
            <label style={s.label}>지역 (선택)</label>
            <input
              style={s.input}
              value={region}
              onChange={(e) => setRegion(e.target.value)}
              placeholder="예: 경상남도, 충청남도, 서울특별시..."
              onKeyDown={(e) => e.key === "Enter" && handleSearch()}
            />
          </div>
          <div style={s.formRow}>
            <label style={s.label}>페이지 당 개수</label>
            <div style={s.btnGroup}>
              {[10, 20, 50].map((n) => (
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
          <button style={s.primaryBtn} onClick={() => handleSearch()} disabled={searching}>
            {searching ? "검색 중..." : "🔍 검색"}
          </button>
        </div>
      )}

      {/* Step 2 — 후보 카드 목록 + 게시판 */}
      {step === 2 && (
        <div style={s.card}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <h3 style={s.cardTitle}>
              {boardView ? `전체 데이터 (${totalCount}개)` : `후보 선택 (${candidates.length}개)`}
              {keyword && <span style={{ fontSize: 13, color: "#888", marginLeft: 8 }}>키워드: {keyword}</span>}
              {region && <span style={{ fontSize: 13, color: "#888", marginLeft: 8 }}>지역: {region}</span>}
            </h3>
            <button style={s.ghostBtn} onClick={() => setStep(1)}>← 다시 검색</button>
          </div>

          {/* 키워드 검색 결과 없음 메시지 */}
          {boardView && searchMessage && (
            <div style={{
              background: "#FFF3CD", border: "1px solid #FFEAA7", borderRadius: 8,
              padding: "12px 16px", marginBottom: 16, fontSize: 13, color: "#856404",
            }}>
              {searchMessage}
            </div>
          )}

          {/* 키워드 매칭된 후보 */}
          {!boardView && keywordFiltered && keywordMatched > 0 && (
            <div style={s.candidateGrid}>
              {candidates.map((c, i) => (
                <div key={i} style={s.candidateCard}>
                  {c.media_url && c.media_type === "image" && (
                    <img src={c.media_url} alt={c.title} style={s.candidateImg} />
                  )}
                  {!c.media_url && (
                    <div style={s.mediaPlaceholder}>
                      📖
                    </div>
                  )}
                  <div style={s.candidateTitle}>{c.title}</div>
                  <div style={s.candidateSource}>
                    [{c.source}] · {c.media_type}
                    {(c as any).media_subtype && <span> · {(c as any).media_subtype === "story" ? "이야기" : (c as any).media_subtype === "image" ? "이미지" : "텍스트"}</span>}
                    {c.region && <span> · {c.region}{c.sub_region ? ` ${c.sub_region}` : ""}</span>}
                  </div>
                  {c.description && (
                    <div style={s.candidateDesc}>{c.description.slice(0, 80)}{c.description.length > 80 ? "..." : ""}</div>
                  )}
                  {c.ai_question && (
                    <div style={s.aiQuestion}>💬 {c.ai_question}</div>
                  )}
                  <button
                    style={s.selectBtn}
                    onClick={() => handleSelect(c, i)}
                    disabled={analyzingIdx === i}
                  >
                    {analyzingIdx === i ? "🔍 분석 중..." : "이 주제 선택 →"}
                  </button>
                </div>
              ))}
            </div>
          )}

          {/* 전체 게시판 (키워드 미지정 or 결과 없음) */}
          <div style={{ marginTop: boardView ? 0 : 24 }}>
            {!boardView && !keywordFiltered && (
              <h4 style={{ fontSize: 14, fontWeight: 600, color: "#555", marginBottom: 12 }}>
                전체 목록 ({totalCount}개) · {page}/{totalPages} 페이지
              </h4>
            )}
            <div style={s.candidateGrid}>
              {allCandidates.map((c, i) => (
                <div key={i} style={s.candidateCard}>
                  {c.media_url && c.media_type === "image" && (
                    <img src={c.media_url} alt={c.title} style={s.candidateImg} />
                  )}
                  {!c.media_url && (
                    <div style={s.mediaPlaceholder}>
                      📖
                    </div>
                  )}
                  <div style={s.candidateTitle}>{c.title}</div>
                  <div style={s.candidateSource}>
                    [{c.source}] · {c.media_type}
                    {(c as any).media_subtype && <span> · {(c as any).media_subtype === "story" ? "이야기" : (c as any).media_subtype === "image" ? "이미지" : "텍스트"}</span>}
                    {c.region && <span> · {c.region}{c.sub_region ? ` ${c.sub_region}` : ""}</span>}
                  </div>
                  {c.description && (
                    <div style={s.candidateDesc}>{c.description.slice(0, 80)}{c.description.length > 80 ? "..." : ""}</div>
                  )}
                  {(c.keywords || (c as any).refined_keywords) && (
                    <div style={{ display: "flex", flexWrap: "wrap", gap: 4, marginBottom: 8 }}>
                      {((c as any).refined_keywords || c.keywords || "").toString().split(";").slice(0, 3).map((kw: string, ki: number) => (
                        <span key={ki} style={s.topicChip}>{kw.trim()}</span>
                      ))}
                    </div>
                  )}
                  <button
                    style={s.selectBtn}
                    onClick={() => handleSelect(
                      c,
                      // find index in candidates or use a negative temporary index
                      candidates.findIndex(cand => cand.title === c.title && cand.source === c.source) >= 0
                        ? candidates.findIndex(cand => cand.title === c.title && cand.source === c.source)
                        : -1
                    )}
                  >
                    이 주제 선택 →
                  </button>
                </div>
              ))}
            </div>
          </div>

          {/* 페이지네이션 */}
          <div style={{
            display: "flex", justifyContent: "center", alignItems: "center",
            gap: 8, marginTop: 20,
          }}>
            <button
              style={s.ghostBtn}
              disabled={page <= 1}
              onClick={() => handleSearch(page - 1)}
            >
              ← 이전
            </button>
            {Array.from({ length: totalPages }, (_, i) => i + 1).map((p) => (
              <button
                key={p}
                style={{
                  ...s.ghostBtn,
                  background: p === page ? "#E8572A" : "#fff",
                  color: p === page ? "#fff" : "#555",
                  fontWeight: p === page ? "bold" : "normal",
                }}
                onClick={() => handleSearch(p)}
              >
                {p}
              </button>
            ))}
            <button
              style={s.ghostBtn}
              disabled={page >= totalPages}
              onClick={() => handleSearch(page + 1)}
            >
              다음 →
            </button>
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

          {/* 배포 대상 선택 */}
          {targetUsers.length > 0 && (
            <div style={s.formRow}>
              <label style={s.label}>📬 배포 대상 ({targetUserIds.length}명 선택)</label>
              <div style={{ display: "flex", gap: 8, marginBottom: 10 }}>
                <button
                  style={s.ghostBtn}
                  onClick={() => setTargetUserIds(targetUsers.map((u) => u.user_id))}
                >
                  전체 선택
                </button>
                <button
                  style={s.ghostBtn}
                  onClick={() => setTargetUserIds([])}
                >
                  전체 해제
                </button>
              </div>
              <div style={{ maxHeight: 200, overflow: "auto", border: "1px solid #eee", borderRadius: 8, padding: 8 }}>
                {targetUsers.map((u) => (
                  <label
                    key={u.user_id}
                    style={{ display: "flex", alignItems: "center", gap: 8, padding: "6px 8px", cursor: "pointer", borderRadius: 6, fontSize: 14 }}
                  >
                    <input
                      type="checkbox"
                      checked={targetUserIds.includes(u.user_id)}
                      onChange={() => {
                        setTargetUserIds((prev) =>
                          prev.includes(u.user_id)
                            ? prev.filter((id) => id !== u.user_id)
                            : [...prev, u.user_id]
                        );
                      }}
                    />
                    <span>{u.nickname}</span>
                    <span style={{
                      fontSize: 11, padding: "2px 8px", borderRadius: 10,
                      background: u.user_type === "elder" ? "#FFF0E0" : "#E0E0FF",
                      color: u.user_type === "elder" ? "#E8572A" : "#7B7BFF",
                    }}>
                      {u.user_type === "elder" ? "노인" : "청년"}
                    </span>
                  </label>
                ))}
              </div>
              {targetUserIds.length === 0 && (
                <div style={{ fontSize: 12, color: "#888", marginTop: 4 }}>
                  ※ 배포 대상 없이 주제만 발행됩니다
                </div>
              )}
            </div>
          )}

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

          {/* 미리보기 모드 토글 (자동 / 수동) */}
          <div style={s.formRow}>
            <label style={s.label}>미리보기 방식</label>
            <div style={{ display: "flex", gap: 0, border: "1px solid #DDD", borderRadius: 8, overflow: "hidden", width: "fit-content" }}>
              {([
                ["auto", "🤖 자동 (AI 연결)"],
                ["manual", "✍️ 수동 (프롬프트 직접)"],
              ] as ["auto" | "manual", string][]).map(([key, label]) => (
                <button
                  key={key}
                  onClick={() => setPreviewMode(key)}
                  style={{
                    padding: "8px 16px",
                    border: "none",
                    background: previewMode === key ? "#1A1A2E" : "#FFF",
                    color: previewMode === key ? "#FFF" : "#555",
                    fontSize: 13,
                    fontWeight: previewMode === key ? "bold" : "normal",
                    cursor: "pointer",
                  }}
                >
                  {label}
                </button>
              ))}
            </div>
            <div style={{ fontSize: 12, color: "#888", marginTop: 6 }}>
              {previewMode === "auto"
                ? "등록된 AI 키로 시스템이 자동 생성합니다."
                : "AI 키 없이, 프롬프트를 직접 외부 AI에 물어보고 답변을 붙여넣습니다."}
            </div>
          </div>

          {/* 미리보기 생성 — 자동 모드 */}
          {previewMode === "auto" && (
            <div style={s.formRow}>
              <button
                style={{ ...s.primaryBtn, background: "#1A1A2E", marginTop: 0 }}
                onClick={() => selected && generateSurveyQuestions(questionType, selected)}
                disabled={isGenerating}
              >
                {isGenerating ? "⏳ 생성 중..." : "🔍 미리보기 생성"}
              </button>
            </div>
          )}

          {/* 미리보기 생성 — 수동 모드 */}
          {previewMode === "manual" && (
            <div style={s.formRow}>
              <ManualPreviewPanel
                prompt={manualPrompt}
                generating={promptLoading}
                onGeneratePrompt={generateManualPrompt}
                onApply={applyManualResult}
              />
            </div>
          )}

          {/* 설문지 미리보기 */}
          <div style={s.formRow}>
            <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 8 }}>
              <label style={s.label}>설문지 미리보기</label>
              {draftStatus === "ai_draft" && (
                <span style={s.draftBadge}>🤖 AI 초안</span>
              )}
              {draftStatus === "editing" && (
                <span style={{ ...s.draftBadge, background: "#FFF3CD", color: "#856404" }}>✏️ 수정 중</span>
              )}
              {draftStatus === "published" && (
                <span style={{ ...s.draftBadge, background: "#D4EDDA", color: "#155724" }}>✅ 발행 완료</span>
              )}
            </div>
            {draftStatus === "ai_draft" && (
              <div style={s.draftNotice}>
                💡 AI가 생성한 초안입니다. 복지사가 직접 검토·수정한 뒤 발행하세요.
              </div>
            )}
            {warnings.length > 0 && (
              <div style={s.warningBox}>
                {warnings.map((w, i) => (
                  <div key={i} style={{ display: "flex", alignItems: "flex-start", gap: 6 }}>
                    <span>⚠️</span>
                    <span>{w}</span>
                  </div>
                ))}
              </div>
            )}
            {genError && (
              <div style={{
                background: "#FEF2F2", border: "1px solid #FECACA", borderRadius: 8,
                padding: "10px 14px", fontSize: 13, color: "#B91C1C", marginBottom: 10,
              }}>
                ❌ {genError}
              </div>
            )}
            {isGenerating ? (
              <div style={s.generatingBox}>⏳ 설문지 질문 생성 중...</div>
            ) : questionSet ? (
              <>
                <SurveyPreview questionSet={questionSet} candidate={selected} />
                <div style={{ display: "flex", gap: 8, marginTop: 12 }}>
                  <button style={s.secondaryBtn} onClick={() => { setShowRefineChat(true); setDraftStatus("editing"); }}>
                    💬 AI와 협의
                  </button>
                  <button style={s.secondaryBtn} onClick={() => { setShowEditor(true); setDraftStatus("editing"); }}>
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
          {publishResult.distributed_users && publishResult.distributed_users.length > 0 && (
            <div style={{ marginTop: 16, textAlign: "left", background: "#F8FFF8", borderRadius: 8, padding: 16 }}>
              <div style={{ fontWeight: "bold", fontSize: 14, color: "#2E7D32", marginBottom: 8 }}>
                📬 배포 대상 ({publishResult.distributed_users.length}명)
              </div>
              {publishResult.distributed_users.map((u) => (
                <div key={u.user_id} style={{ fontSize: 13, color: "#555", padding: "4px 0", borderBottom: "1px solid #E8F5E9" }}>
                  {u.nickname}
                  <span style={{
                    marginLeft: 8, fontSize: 11, padding: "2px 8px", borderRadius: 10,
                    background: u.user_type === "elder" ? "#FFF0E0" : "#E0E0FF",
                    color: u.user_type === "elder" ? "#E8572A" : "#7B7BFF",
                  }}>
                    {u.user_type === "elder" ? "노인" : "청년"}
                  </span>
                </div>
              ))}
            </div>
          )}
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
              welfareId={selectedWelfareId}
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
  selectedTitle: { fontSize: 17, fontWeight: "bold", color: "#222" },
  generatingBox: {
    background: "#F5F7FA", borderRadius: 8, padding: "16px 20px",
    color: "#888", fontSize: 14, textAlign: "center",
  },
  draftBadge: {
    display: "inline-block", padding: "2px 10px", borderRadius: 12,
    fontSize: 12, fontWeight: 600, background: "#E3F0FF", color: "#1A56DB",
  },
  draftNotice: {
    background: "#EFF6FF", border: "1px solid #BFDBFE", borderRadius: 8,
    padding: "8px 12px", fontSize: 13, color: "#1E40AF", marginBottom: 10,
  },
  warningBox: {
    background: "#FFFBEB", border: "1px solid #FCD34D", borderRadius: 8,
    padding: "10px 14px", fontSize: 13, color: "#92400E",
    display: "flex", flexDirection: "column", gap: 4, marginBottom: 10,
  },
  analysisSummary: {
    background: "#F8FAFC", borderRadius: 8, padding: "10px 12px",
    marginBottom: 10, border: "1px solid #E2E8F0",
  },
  analysisLine: {
    fontSize: 12, color: "#475569", marginBottom: 3,
  },
  topicChip: {
    fontSize: 11, background: "#E0F2FE", color: "#0369A1",
    padding: "3px 8px", borderRadius: 12, fontWeight: 600,
  },
  analysisDetail: {
    background: "#FAFAFA", borderRadius: 8, padding: "12px 14px",
    marginBottom: 10, border: "1px solid #E5E5E5",
  },
  detailSection: {
    marginBottom: 12,
  },
  detailLabel: {
    fontSize: 12, fontWeight: "bold", color: "#334155", marginBottom: 6,
  },
  detailText: {
    fontSize: 12, color: "#555", lineHeight: 1.5, marginBottom: 4,
  },
  estimationNote: {
    fontSize: 11, color: "#B45309", background: "#FFFBEB",
    padding: "4px 8px", borderRadius: 4, marginTop: 4,
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
