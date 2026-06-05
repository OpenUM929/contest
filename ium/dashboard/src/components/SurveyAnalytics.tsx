// src/components/SurveyAnalytics.tsx
import React, { useEffect, useState } from "react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from "recharts";
import { AnalyticsData, AnalyticsQuestion } from "../types/survey";
import { fetchAnalytics } from "../api/survey";

interface Props {
  topicId: string;
}

const COLORS = ["#E8572A", "#7B7BFF", "#44BB44", "#FFA500", "#8884D8", "#82CA9D"];

export default function SurveyAnalytics({ topicId }: Props) {
  const [data, setData] = useState<AnalyticsData | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!topicId) return;
    loadAnalytics();
  }, [topicId]);

  const loadAnalytics = async () => {
    setLoading(true);
    try {
      const res = await fetchAnalytics(topicId);
      setData(res.data);
    } catch (e) {
      alert("집계 데이터 조회 실패");
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <div style={{ textAlign: "center", padding: 40, color: "#888" }}>집계 중...</div>;
  }

  if (!data) {
    return <div style={{ textAlign: "center", padding: 40, color: "#888" }}>데이터가 없습니다.</div>;
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 24 }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <h3 style={{ margin: 0, fontSize: 16, color: "#1A1A2E" }}>응답 집계</h3>
        <span style={{ fontSize: 13, color: "#888" }}>총 응답자: <strong>{data.total_respondents}</strong>명</span>
      </div>

      {data.questions.map((q) => (
        <QuestionAnalytics key={q.question_id} question={q} />
      ))}
    </div>
  );
}

function QuestionAnalytics({ question }: { question: AnalyticsQuestion }) {
  if (question.type === "choice" && question.options_stats && question.options_stats.length > 0) {
    const chartData = question.options_stats.map((s) => ({
      name: s.label.length > 8 ? s.label.slice(0, 8) + "..." : s.label,
      fullLabel: s.label,
      count: s.count,
      percent: s.percent,
    }));

    return (
      <div
        style={{
          background: "#FFF",
          borderRadius: 12,
          padding: 18,
          border: "1px solid #EEE",
        }}
      >
        <div style={{ fontWeight: "bold", fontSize: 14, color: "#333", marginBottom: 12 }}>
          {question.text}
        </div>
        <div style={{ width: "100%", height: 220 }}>
          <ResponsiveContainer>
            <BarChart data={chartData} margin={{ top: 5, right: 5, left: -20, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#EEE" />
              <XAxis dataKey="name" tick={{ fontSize: 11 }} />
              <YAxis allowDecimals={false} tick={{ fontSize: 11 }} />
              <Tooltip
                formatter={(value: any, name: any, props: any) => {
                  const item = props.payload;
                  return [`${item.count}명 (${item.percent}%)`, item.fullLabel];
                }}
              />
              <Bar dataKey="count" radius={[6, 6, 0, 0]}>
                {chartData.map((_, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    );
  }

  if (question.type === "narrative") {
    return (
      <div
        style={{
          background: "#FFF",
          borderRadius: 12,
          padding: 18,
          border: "1px solid #EEE",
        }}
      >
        <div style={{ fontWeight: "bold", fontSize: 14, color: "#333", marginBottom: 8 }}>
          {question.text}
        </div>
        <div style={{ fontSize: 12, color: "#888", marginBottom: 12 }}>
          응답 {question.response_count || 0}건
        </div>
        {question.sample_responses && question.sample_responses.length > 0 ? (
          <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
            {question.sample_responses.map((resp, i) => (
              <div
                key={i}
                style={{
                  background: "#F8F8F8",
                  borderRadius: 8,
                  padding: "10px 14px",
                  fontSize: 13,
                  color: "#444",
                  lineHeight: 1.5,
                }}
              >
                {resp}
              </div>
            ))}
          </div>
        ) : (
          <div style={{ fontSize: 13, color: "#AAA", textAlign: "center", padding: 20 }}>
            아직 서술형 응답이 없습니다.
          </div>
        )}
      </div>
    );
  }

  return null;
}
