import { useState } from "react";
import AdminDashboard from "./AdminDashboard";
import UserManager from "./UserManager";
import WorkerManager from "./WorkerManager";
import AdminLogPage from "./AdminLogPage";

type AdminTab = "dashboard" | "users" | "workers" | "logs";

const TABS: [AdminTab, string][] = [
  ["dashboard", "대시보드"],
  ["users", "회원 관리"],
  ["workers", "복지사 관리"],
  ["logs", "작업 로그"],
];

export default function AdminLayout() {
  const [tab, setTab] = useState<AdminTab>("dashboard");

  return (
    <div style={{ background: "#FAF7F2", minHeight: "calc(100vh - 53px)" }}>
      {/* admin 서브탭 네비게이션 */}
      <div style={{
        display: "flex", gap: 4, padding: "12px 32px 0",
        background: "#2A2A40", borderBottom: "1px solid #3A3A55",
      }}>
        {TABS.map(([key, label]) => (
          <button
            key={key}
            onClick={() => setTab(key)}
            style={{
              background: tab === key ? "#FAF7F2" : "transparent",
              border: "none",
              borderRadius: "8px 8px 0 0",
              color: tab === key ? "#1A1A2E" : "#bbb",
              padding: "10px 20px",
              fontSize: 14,
              fontWeight: tab === key ? "bold" : "normal",
              cursor: "pointer",
            }}
          >
            {label}
          </button>
        ))}
      </div>

      {tab === "dashboard" && <AdminDashboard />}
      {tab === "users" && <UserManager />}
      {tab === "workers" && <WorkerManager />}
      {tab === "logs" && <AdminLogPage />}
    </div>
  );
}
