import { useState, useEffect } from "react";
import Dashboard from "./pages/Dashboard";
import TopicManager from "./pages/TopicManager";
import SurveyManagerPage from "./pages/SurveyManagerPage";
import TempAccountPage from "./pages/TempAccountPage";
import AdminLayout from "./pages/admin/AdminLayout";

type Tab = "dashboard" | "topics" | "surveys" | "accounts" | "admin";

export default function App() {
  const [tab, setTab] = useState<Tab>("dashboard");

  useEffect(() => {
    if (!localStorage.getItem('temp_user_id')) {
      window.location.href = '/login';
    }
  }, []);

  const userType = localStorage.getItem('temp_user_type');
  const isAdmin = userType === 'admin';
  if (userType === 'elder' || userType === 'youth') {
    return (
      <div style={{
        display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center",
        height: "100vh", fontFamily: "sans-serif", background: "#FFFDF7", color: "#4A3728",
      }}>
        <h1 style={{ fontSize: 28, marginBottom: 12 }}>접근 권한이 없습니다</h1>
        <p style={{ fontSize: 16, color: "#888", marginBottom: 24 }}>
          이 페이지는 복지사/관리자 전용입니다.
        </p>
        <p style={{ fontSize: 14, color: "#aaa", marginBottom: 32 }}>
          노인/청년 회원은 모바일 앱을 이용해 주세요.
        </p>
        <button onClick={() => {
          localStorage.removeItem('temp_user_id');
          localStorage.removeItem('temp_user_type');
          localStorage.removeItem('temp_nickname');
          window.location.href = '/login';
        }} style={{
          padding: "12px 32px", fontSize: 16, border: "none", borderRadius: 10,
          background: "#E8572A", color: "#FFF", cursor: "pointer", fontWeight: "bold",
        }}>
          로그인 페이지로 이동
        </button>
      </div>
    );
  }

  const handleLogout = () => {
    localStorage.removeItem('temp_user_id');
    localStorage.removeItem('temp_user_type');
    localStorage.removeItem('temp_nickname');
    window.location.href = '/login';
  };

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
          ["accounts", "🔑 계정 관리"],
          ...(isAdmin ? [["admin", "🛠 관리자"] as [Tab, string]] : []),
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
        <div style={{ flex: 1 }} />
        <button onClick={handleLogout} style={{
          background: "none", border: "none",
          color: "#E8572A", cursor: "pointer", fontSize: 14,
          padding: "16px 24px", fontWeight: "bold",
        }}>
          로그아웃
        </button>
      </nav>

      {tab === "dashboard" && <Dashboard onGoTopics={() => setTab("topics")} />}
      {tab === "topics" && <TopicManager />}
      {tab === "surveys" && <SurveyManagerPage onGoPublish={() => setTab("topics")} />}
      {tab === "accounts" && <TempAccountPage />}
      {tab === "admin" && <AdminLayout />}
    </div>
  );
}
