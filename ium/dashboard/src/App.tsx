import { useState } from "react";
import Dashboard from "./pages/Dashboard";
import TopicManager from "./pages/TopicManager";
import SurveyManagerPage from "./pages/SurveyManagerPage";

type Tab = "dashboard" | "topics" | "surveys";

export default function App() {
  const [tab, setTab] = useState<Tab>("dashboard");

  return (
    <div style={{ margin: 0, padding: 0, fontFamily: "sans-serif" }}>
      {/* 탭 네비게이션 */}
      <nav style={{
        display: "flex", gap: 0, background: "#1A1A2E",
        padding: "0 32px",
      }}>
        {([
          ["dashboard", "📊 이용자 모니터링"],
          ["topics", "📋 주간 주제 관리"],
          ["surveys", "📋 설문지 통합 관리"],
        ] as [Tab, string][]).map(([key, label]) => (
          <button
            key={key}
            onClick={() => setTab(key)}
            style={{
              background: "none",
              border: "none",
              borderBottom: tab === key ? "3px solid #E8572A" : "3px solid transparent",
              color: tab === key ? "#fff" : "#aaa",
              padding: "16px 24px",
              fontSize: 14,
              fontWeight: tab === key ? "bold" : "normal",
              cursor: "pointer",
            }}
          >
            {label}
          </button>
        ))}
      </nav>

      {tab === "dashboard" && <Dashboard />}
      {tab === "topics" && <TopicManager />}
      {tab === "surveys" && <SurveyManagerPage onGoPublish={() => setTab("topics")} />}
    </div>
  );
}
