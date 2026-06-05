// src/pages/SurveyManagerPage.tsx
import React, { useEffect, useState } from "react";
import { WeeklyTopic, QuestionSet, SurveyTemplateItem } from "../types/survey";
import {
  fetchCurrentSurveys,
  fetchTemplates,
  fetchSurveyForEdit,
  updateSurvey,
  stopSurvey,
  saveTemplate,
} from "../api/survey";
import SurveyHistory from "../components/SurveyHistory";
import SurveyAnalytics from "../components/SurveyAnalytics";
import SurveyEditor from "../components/SurveyEditor";
import SurveyRefineChat from "../components/SurveyRefineChat";
import SurveyPreview from "../components/SurveyPreview";

type SubTab = "current" | "history" | "templates";
type ViewMode = "list" | "edit" | "refine" | "analytics" | "preview";

interface Props {
  welfareId?: string;
  onGoPublish?: () => void;
}

const TYPE_LABEL: Record<string, string> = {
  choice: "선택형",
  narrative: "서술형",
  mixed: "혼합형",
};

export default function SurveyManagerPage({ welfareId = "", onGoPublish }: Props) {
  const [subTab, setSubTab] = useState<SubTab>("current");
  const [currentTopics, setCurrentTopics] = useState<WeeklyTopic[]>([]);
  const [templates, setTemplates] = useState<SurveyTemplateItem[]>([]);
  const [loading, setLoading] = useState(false);

  const [viewMode, setViewMode] = useState<ViewMode>("list");
  const [selectedTopic, setSelectedTopic] = useState<WeeklyTopic | null>(null);
  const [editingQuestionSet, setEditingQuestionSet] = useState<QuestionSet | null>(null);

  // 현재 설문지 조회
  const loadCurrent = async () => {
    setLoading(true);
    try {
      const res = await fetchCurrentSurveys();
      setCurrentTopics(res.data);
    } catch (e) {
      alert("현재 설문지 조회 실패");
    } finally {
      setLoading(false);
    }
  };

  // 템플릿 목록
  const loadTemplates = async () => {
    if (!welfareId) return;
    setLoading(true);
    try {
      const res = await fetchTemplates(welfareId);
      setTemplates(res.data);
    } catch (e) {
      alert("템플릿 조회 실패");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadCurrent();
  }, []);

  useEffect(() => {
    if (subTab === "templates") loadTemplates();
  }, [subTab]);

  // 수정 시작
  const startEdit = async (topic: WeeklyTopic) => {
    try {
      const res = await fetchSurveyForEdit(topic.topic_id);
      const data = res.data;
      if (data.choices) {
        setEditingQuestionSet(data.choices);
        setSelectedTopic(topic);
        setViewMode("edit");
      } else {
        alert("설문지 데이터가 없습니다.");
      }
    } catch (e) {
      alert("편집 데이터 조회 실패");
    }
  };

  // AI 협의 시작
  const startRefine = async (topic: WeeklyTopic) => {
    try {
      const res = await fetchSurveyForEdit(topic.topic_id);
      const data = res.data;
      if (data.choices) {
        setEditingQuestionSet(data.choices);
        setSelectedTopic(topic);
        setViewMode("refine");
      } else {
        alert("설문지 데이터가 없습니다.");
      }
    } catch (e) {
      alert("편집 데이터 조회 실패");
    }
  };

  // 미리보기
  const startPreview = async (topic: WeeklyTopic) => {
    try {
      const res = await fetchSurveyForEdit(topic.topic_id);
      const data = res.data;
      if (data.choices) {
        setEditingQuestionSet(data.choices);
        setSelectedTopic(topic);
        setViewMode("preview");
      } else {
        alert("설문지 데이터가 없습니다.");
      }
    } catch (e) {
      alert("조회 실패");
    }
  };

  // 발행 중지
  const handleStop = async (topic: WeeklyTopic) => {
    if (!window.confirm(`'${topic.title}' 발행을 중지하시겠습니까?`)) return;
    try {
      await stopSurvey(topic.topic_id);
      alert("중지 완료");
      loadCurrent();
    } catch (e) {
      alert("중지 실패");
    }
  };

  // 수정 저장
  const handleEditSave = async () => {
    if (!selectedTopic || !editingQuestionSet) return;
    try {
      await updateSurvey(selectedTopic.topic_id, {
        title: selectedTopic.title,
        choices: editingQuestionSet,
      });
      alert("저장 완료");
      setViewMode("list");
      loadCurrent();
    } catch (e) {
      alert("저장 실패");
    }
  };

  // 템플릿 저장
  const handleSaveTemplate = async () => {
    if (!editingQuestionSet || !welfareId) return;
    const name = window.prompt("템플릿 이름을 입력하세요:");
    if (!name) return;
    try {
      await saveTemplate({ welfare_id: welfareId, name, question_set: editingQuestionSet });
      alert("템플릿 저장 완료");
      if (subTab === "templates") loadTemplates();
    } catch (e) {
      alert("템플릿 저장 실패");
    }
  };

  // 발행 (refine에서)
  const handlePublishFromRefine = async (qs: QuestionSet) => {
    if (!selectedTopic) return;
    try {
      await updateSurvey(selectedTopic.topic_id, {
        title: selectedTopic.title,
        choices: qs,
      });
      alert("발행 완료");
      setViewMode("list");
      loadCurrent();
    } catch (e) {
      alert("발행 실패");
    }
  };

  // 뒤로가기
  const goBack = () => setViewMode("list");

  const today = new Date();
  const monday = new Date(today);
  monday.setDate(today.getDate() - today.getDay());
  const sunday = new Date(monday);
  sunday.setDate(monday.getDate() + 6);

  // ═════════════════════════════════════
  // 상세 뷰 (edit / refine / analytics / preview)
  // ═════════════════════════════════════
  if (viewMode !== "list" && selectedTopic) {
    return (
      <div style={{ padding: 24, background: "#F5F7FA", minHeight: "100vh" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
          <h2 style={{ margin: 0, fontSize: 18, color: "#1A1A2E" }}>
            {viewMode === "edit" && "설문지 편집"}
            {viewMode === "refine" && "AI 협의 편집"}
            {viewMode === "analytics" && "응답 집계"}
            {viewMode === "preview" && "설문지 미리보기"}
            {" > "}{selectedTopic.title}
          </h2>
          <button
            onClick={goBack}
            style={{ padding: "8px 16px", borderRadius: 6, border: "none", background: "#E0E0E0", color: "#333", fontWeight: "bold", fontSize: 13, cursor: "pointer" }}
          >
            ← 뒤로
          </button>
        </div>

        {viewMode === "edit" && editingQuestionSet && (
          <SurveyEditor
            initialQuestionSet={editingQuestionSet}
            onChange={setEditingQuestionSet}
            onPublish={handleEditSave}
            onSaveDraft={handleSaveTemplate}
          />
        )}

        {viewMode === "refine" && editingQuestionSet && (
          <SurveyRefineChat
            topicTitle={selectedTopic.title}
            initialQuestionSet={editingQuestionSet}
            onDirectEdit={(qs) => {
              setEditingQuestionSet(qs);
              setViewMode("edit");
            }}
            onPublish={handlePublishFromRefine}
          />
        )}

        {viewMode === "analytics" && <SurveyAnalytics topicId={selectedTopic.topic_id} />}

        {viewMode === "preview" && editingQuestionSet && (
          <SurveyPreview questionSet={editingQuestionSet} />
        )}
      </div>
    );
  }

  // ═════════════════════════════════════
  // 목록 뷰
  // ═════════════════════════════════════
  return (
    <div style={{ padding: 24, background: "#F5F7FA", minHeight: "100vh" }}>
      <h2 style={{ margin: "0 0 16px", fontSize: 20, color: "#1A1A2E" }}>설문지 통합 관리</h2>

      {/* 서브 탭 */}
      <div style={{ display: "flex", gap: 0, background: "#FFF", borderRadius: "8px 8px 0 0", overflow: "hidden", border: "1px solid #EEE", borderBottom: "none" }}>
        {([
          ["current", "이번 주 설문지"],
          ["history", "발행 이력"],
          ["templates", "내 템플릿"],
        ] as [SubTab, string][]).map(([key, label]) => (
          <button
            key={key}
            onClick={() => setSubTab(key)}
            style={{
              flex: 1,
              padding: "12px 16px",
              border: "none",
              background: subTab === key ? "#1A1A2E" : "#FFF",
              color: subTab === key ? "#FFF" : "#333",
              fontWeight: subTab === key ? "bold" : "normal",
              fontSize: 14,
              cursor: "pointer",
              borderBottom: subTab === key ? "3px solid #E8572A" : "3px solid transparent",
            }}
          >
            {label}
          </button>
        ))}
      </div>

      {/* 탭 콘텐츠 */}
      <div style={{ background: "#FFF", borderRadius: "0 0 8px 8px", padding: 20, border: "1px solid #EEE", minHeight: 400 }}>
        {subTab === "current" && (
          <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
            {loading ? (
              <div style={{ textAlign: "center", padding: 40, color: "#888" }}>불러오는 중...</div>
            ) : currentTopics.length === 0 ? (
              <div style={{ textAlign: "center", padding: 40, color: "#888" }}>
                <div style={{ marginBottom: 12 }}>이번 주 발행된 설문지가 없습니다.</div>
                <button
                  onClick={onGoPublish}
                  style={{ padding: "10px 20px", borderRadius: 8, border: "none", background: "#E8572A", color: "#FFF", fontWeight: "bold", fontSize: 14, cursor: "pointer" }}
                >
                  주제 검색·발행하러 가기 →
                </button>
              </div>
            ) : (
              currentTopics.map((topic) => (
                <div
                  key={topic.topic_id}
                  style={{
                    background: "#F8F8F8",
                    borderRadius: 12,
                    padding: 18,
                    border: "1px solid #EEE",
                  }}
                >
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 10 }}>
                    <div>
                      <div style={{ fontWeight: "bold", fontSize: 16, color: "#222", marginBottom: 4 }}>{topic.title}</div>
                      <div style={{ fontSize: 12, color: "#888" }}>
                        유형: {TYPE_LABEL[topic.question_type] || topic.question_type} · 지역: {topic.region} · 상태: {topic.is_customized ? "발행 완료" : "중지됨"}
                      </div>
                      <div style={{ fontSize: 12, color: "#AAA", marginTop: 2 }}>
                        기간: {monday.toLocaleDateString("ko-KR")} ~ {sunday.toLocaleDateString("ko-KR")}
                      </div>
                    </div>
                  </div>

                  <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
                    <button
                      onClick={() => startPreview(topic)}
                      style={{ ...smallBtn, background: "#FFF", border: "1px solid #DDD" }}
                    >
                      미리보기
                    </button>
                    <button
                      onClick={() => startRefine(topic)}
                      style={{ ...smallBtn, background: "#FFF", border: "1px solid #7B7BFF", color: "#7B7BFF" }}
                    >
                      AI 협의
                    </button>
                    <button
                      onClick={() => startEdit(topic)}
                      style={{ ...smallBtn, background: "#FFF", border: "1px solid #555" }}
                    >
                      직접 수정
                    </button>
                    <button
                      onClick={() => {
                        setSelectedTopic(topic);
                        setViewMode("analytics");
                      }}
                      style={{ ...smallBtn, background: "#FFF", border: "1px solid #44BB44", color: "#44BB44" }}
                    >
                      응답 집계
                    </button>
                    <button
                      onClick={() => handleStop(topic)}
                      style={{ ...smallBtn, background: "#FFF0F0", border: "1px solid #FF4444", color: "#FF4444" }}
                    >
                      사용 중지
                    </button>
                  </div>
                </div>
              ))
            )}

            {/* 빠른 작업 */}
            <div style={{ background: "#FFF", borderRadius: 10, padding: 16, border: "1px dashed #DDD" }}>
              <div style={{ fontWeight: "bold", fontSize: 14, color: "#1A1A2E", marginBottom: 10 }}>빠른 작업</div>
              <div style={{ display: "flex", flexWrap: "wrap", gap: 10 }}>
                <button onClick={onGoPublish} style={{ ...smallBtn, background: "#1A1A2E", color: "#FFF", border: "none" }}>
                  주제 검색·발행
                </button>
                <button
                  onClick={() => setSubTab("history")}
                  style={{ ...smallBtn, background: "#F0F0F0", color: "#333", border: "none" }}
                >
                  지난 주 설문지 복제
                </button>
                <button
                  onClick={() => setSubTab("templates")}
                  style={{ ...smallBtn, background: "#F0F0F0", color: "#333", border: "none" }}
                >
                  템플릿에서 불러오기
                </button>
              </div>
            </div>
          </div>
        )}

        {subTab === "history" && (
          <SurveyHistory
            onCloneSuccess={() => {
              setSubTab("current");
              loadCurrent();
            }}
          />
        )}

        {subTab === "templates" && (
          <div>
            <h3 style={{ margin: "0 0 12px", fontSize: 16, color: "#1A1A2E" }}>저장된 템플릿</h3>
            {templates.length === 0 ? (
              <div style={{ textAlign: "center", padding: 40, color: "#888" }}>저장된 템플릿이 없습니다.</div>
            ) : (
              <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
                {templates.map((t) => (
                  <div
                    key={t.id}
                    style={{
                      background: "#F8F8F8",
                      borderRadius: 10,
                      padding: "12px 16px",
                      display: "flex",
                      justifyContent: "space-between",
                      alignItems: "center",
                    }}
                  >
                    <span style={{ fontWeight: "bold", fontSize: 14 }}>{t.name}</span>
                    <span style={{ fontSize: 12, color: "#888" }}>
                      {t.created_at ? new Date(t.created_at).toLocaleDateString("ko-KR") : ""}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

const smallBtn: React.CSSProperties = {
  padding: "6px 12px",
  borderRadius: 6,
  fontSize: 12,
  fontWeight: "bold",
  cursor: "pointer",
};
