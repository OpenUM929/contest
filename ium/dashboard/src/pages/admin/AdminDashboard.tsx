import { useEffect, useState } from "react";
import { fetchAdminDashboard, type AdminDashboardData } from "../../api/admin";
import StatCard from "../../components/admin/StatCard";
import { COLORS, ACTION_LABELS, formatDate, thStyle, tdStyle } from "../../components/admin/ui";

export default function AdminDashboard() {
  const [data, setData] = useState<AdminDashboardData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchAdminDashboard()
      .then((r) => setData(r.data))
      .catch((e) => console.error(e))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <p style={{ padding: 24 }}>로딩 중...</p>;
  if (!data) return <p style={{ padding: 24, color: "#D33" }}>대시보드를 불러오지 못했습니다.</p>;

  const s = data.stats;
  return (
    <div style={{ padding: 24 }}>
      <h2 style={{ color: COLORS.brown, marginBottom: 20 }}>🛠 관리자 대시보드</h2>

      <div style={{ display: "flex", gap: 16, flexWrap: "wrap", marginBottom: 32 }}>
        <StatCard label="전체 회원" value={s.total_users} icon="👥" />
        <StatCard label="노인" value={s.elder} accent="#E8572A" icon="🧓" />
        <StatCard label="청년" value={s.youth} accent="#7B7BFF" icon="🧑" />
        <StatCard label="복지사" value={s.workers} accent="#2E9E54" icon="💼" />
        <StatCard label="미해결 알림" value={s.unresolved_alerts} accent="#D33" icon="🚨" />
      </div>

      <h3 style={{ color: COLORS.brown, marginBottom: 12 }}>최근 관리자 활동</h3>
      <table style={{ width: "100%", borderCollapse: "collapse", background: "#fff", borderRadius: 12, overflow: "hidden" }}>
        <thead>
          <tr style={{ background: COLORS.headBg }}>
            <th style={thStyle}>작업</th>
            <th style={thStyle}>대상 유형</th>
            <th style={thStyle}>대상 ID</th>
            <th style={thStyle}>시간</th>
          </tr>
        </thead>
        <tbody>
          {data.recent_logs.length === 0 ? (
            <tr><td style={{ ...tdStyle, textAlign: "center", color: "#AAA" }} colSpan={4}>활동 내역이 없습니다.</td></tr>
          ) : (
            data.recent_logs.map((l) => (
              <tr key={l.id}>
                <td style={tdStyle}>{ACTION_LABELS[l.action] || l.action}</td>
                <td style={tdStyle}>{l.target_type === "user" ? "회원" : "복지사"}</td>
                <td style={tdStyle}><code style={{ fontSize: 11, color: "#AAA" }}>{l.target_id}</code></td>
                <td style={tdStyle}>{formatDate(l.created_at)}</td>
              </tr>
            ))
          )}
        </tbody>
      </table>
    </div>
  );
}
