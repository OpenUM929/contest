// src/components/SurveyHistory.tsx
import React, { useEffect, useState } from "react";
import { WeeklyTopic } from "../types/survey";
import { fetchSurveyHistory, cloneSurvey } from "../api/survey";

interface Props {
  onSelect?: (topic: WeeklyTopic) => void;
  onCloneSuccess?: () => void;
}

export default function SurveyHistory({ onSelect, onCloneSuccess }: Props) {
  const [history, setHistory] = useState<WeeklyTopic[]>([]);
  const [loading, setLoading] = useState(false);
  const [weeks, setWeeks] = useState(4);

  useEffect(() => {
    loadHistory();
  }, [weeks]);

  const loadHistory = async () => {
    setLoading(true);
    try {
      const res = await fetchSurveyHistory(weeks);
      setHistory(res.data);
    } catch (e) {
      alert("이력 조회 실패");
    } finally {
      setLoading(false);
    }
  };

  const handleClone = async (topic: WeeklyTopic) => {
    if (!window.confirm(`'${topic.title}'를 복제하여 이번 주 draft를 만드시겠습니까?`)) return;
    try {
      await cloneSurvey(topic.topic_id);
      alert("복제 완료! 이번 주 draft가 생성되었습니다.");
      onCloneSuccess?.();
    } catch (e) {
      alert("복제 실패");
    }
  };

  const formatDate = (iso?: string) => {
    if (!iso) return "-";
    return new Date(iso).toLocaleDateString("ko-KR");
  };

  const typeLabel: Record<string, string> = {
    choice: "선택형",
    narrative: "서술형",
    mixed: "혼합형",
  };

  return (
    <div>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
        <h3 style={{ margin: 0, fontSize: 16, color: "#1A1A2E" }}>최근 발행 이력</h3>
        <select
          value={weeks}
          onChange={(e) => setWeeks(Number(e.target.value))}
          style={{ padding: "6px 10px", borderRadius: 6, border: "1px solid #DDD", fontSize: 13 }}
        >
          <option value={2}>최근 2주</option>
          <option value={4}>최근 4주</option>
          <option value={8}>최근 8주</option>
        </select>
      </div>

      {loading ? (
        <div style={{ textAlign: "center", padding: 40, color: "#888" }}>불러오는 중...</div>
      ) : history.length === 0 ? (
        <div style={{ textAlign: "center", padding: 40, color: "#888" }}>발행 이력이 없습니다.</div>
      ) : (
        <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
          {history.map((topic) => (
            <div
              key={topic.topic_id}
              style={{
                background: "#FFF",
                borderRadius: 10,
                padding: "14px 18px",
                border: "1px solid #EEE",
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
                cursor: onSelect ? "pointer" : "default",
              }}
              onClick={() => onSelect?.(topic)}
            >
              <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
                <span style={{ fontWeight: "bold", fontSize: 14, color: "#222" }}>{topic.title}</span>
                <span style={{ fontSize: 12, color: "#888" }}>
                  {typeLabel[topic.question_type] || topic.question_type} · {topic.region} · {formatDate(topic.active_week)}
                </span>
              </div>
              <div style={{ display: "flex", gap: 8 }}>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    handleClone(topic);
                  }}
                  style={{
                    padding: "6px 12px",
                    borderRadius: 6,
                    border: "1px solid #E8572A",
                    background: "#FFF",
                    color: "#E8572A",
                    fontSize: 12,
                    fontWeight: "bold",
                    cursor: "pointer",
                  }}
                >
                  복제
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
