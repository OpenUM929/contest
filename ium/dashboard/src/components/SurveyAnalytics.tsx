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
import { AnalyticsData, AnalyticsQuestion, MbtiSummary, RespondentMbti } from "../types/survey";
import { fetchAnalytics } from "../api/survey";

interface Props {
  topicId: string;
  welfareId?: string;
}

const COLORS = ["#E8572A", "#7B7BFF", "#44BB44", "#FFA500", "#8884D8", "#82CA9D"];

export default function SurveyAnalytics({ topicId, welfareId }: Props) {
  const [data, setData] = useState<AnalyticsData | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!topicId) return;
    loadAnalytics();
  }, [topicId, welfareId]);

  const loadAnalytics = async () => {
    setLoading(true);
    try {
      const res = await fetchAnalytics(topicId, welfareId || undefined);
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

      {data.mbti_distribution && data.mbti_distribution.total_signals > 0 && (
        <MbtiDistribution summary={data.mbti_distribution} />
      )}

      {data.respondent_mbti && data.respondent_mbti.length > 0 && (
        <RespondentMbtiList respondents={data.respondent_mbti} />
      )}

      {data.questions.map((q) => (
        <QuestionAnalytics key={q.question_id} question={q} />
      ))}
    </div>
  );
}

function MbtiDistribution({ summary }: { summary: MbtiSummary }) {
  return (
    <div style={{ background: "#FFF", borderRadius: 12, padding: 18, border: "1px solid #EEE" }}>
      <div style={{ display: "flex", alignItems: "baseline", gap: 10, marginBottom: 14 }}>
        <div style={{ fontWeight: "bold", fontSize: 14, color: "#333" }}>응답자 성향 분포 (MBTI 추정)</div>
        <div style={{ fontSize: 12, color: "#888" }}>
          이 설문 종합: <strong style={{ color: "#7B7BFF" }}>{summary.type}</strong>
          {!summary.is_complete && " (일부 축만 추정)"}
        </div>
      </div>
      <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
        {summary.axes.map((ax) => {
          const total = ax.left_count + ax.right_count;
          const leftPct = total ? Math.round((ax.left_count * 100) / total) : 0;
          const rightPct = total ? 100 - leftPct : 0;
          const noData = total === 0;
          return (
            <div key={ax.axis}>
              <div style={{ display: "flex", justifyContent: "space-between", fontSize: 12, color: "#666", marginBottom: 4 }}>
                <span style={{ fontWeight: ax.dominant === ax.left ? 700 : 400, color: ax.dominant === ax.left ? "#E8572A" : "#666" }}>
                  {ax.left_label} {ax.left_count}
                </span>
                <span style={{ fontWeight: ax.dominant === ax.right ? 700 : 400, color: ax.dominant === ax.right ? "#7B7BFF" : "#666" }}>
                  {ax.right_count} {ax.right_label}
                </span>
              </div>
              <div style={{ display: "flex", height: 12, borderRadius: 6, overflow: "hidden", background: "#EEE" }}>
                {noData ? (
                  <div style={{ flex: 1, background: "#F0F0F0" }} />
                ) : (
                  <>
                    <div style={{ width: `${leftPct}%`, background: "#E8572A" }} />
                    <div style={{ width: `${rightPct}%`, background: "#7B7BFF" }} />
                  </>
                )}
              </div>
            </div>
          );
        })}
      </div>
      <div style={{ fontSize: 11, color: "#AAA", marginTop: 12, lineHeight: 1.5 }}>
        선택형 보기에 태깅된 성향을 합산한 추정치입니다. 응답이 쌓일수록 정확해집니다.
      </div>
    </div>
  );
}

function RespondentMbtiList({ respondents }: { respondents: RespondentMbti[] }) {
  return (
    <div style={{ background: "#FFF", borderRadius: 12, padding: 18, border: "1px solid #EEE" }}>
      <div style={{ fontWeight: "bold", fontSize: 14, color: "#333", marginBottom: 4 }}>
        응답자별 누적 성향
      </div>
      <div style={{ fontSize: 12, color: "#888", marginBottom: 12 }}>
        각 응답자가 참여한 모든 설문을 누적한 MBTI 추정입니다.
      </div>
      <div style={{ display: "flex", flexWrap: "wrap", gap: 10 }}>
        {respondents.map((r) => {
          const hasSignal = r.total_signals > 0;
          return (
            <div
              key={r.user_id}
              style={{
                display: "flex", flexDirection: "column", gap: 2,
                background: "#F8F8F8", borderRadius: 10, padding: "10px 14px",
                minWidth: 120, border: "1px solid #EEE",
              }}
            >
              <span style={{ fontSize: 13, fontWeight: 600, color: "#333" }}>{r.nickname}</span>
              <span style={{ fontSize: 18, fontWeight: 800, color: hasSignal ? "#7B7BFF" : "#CCC", letterSpacing: 1 }}>
                {hasSignal ? r.type : "미집계"}
              </span>
              <span style={{ fontSize: 11, color: "#999" }}>
                설문 {r.survey_count}회 · 신호 {r.total_signals}
                {hasSignal && !r.is_complete && " · 일부 축"}
              </span>
            </div>
          );
        })}
      </div>
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
