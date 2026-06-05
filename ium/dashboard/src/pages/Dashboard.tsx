import React, { useEffect, useState } from "react";
import axios from "axios";

const API = import.meta.env.VITE_API_URL || "http://localhost:8000";

// ─── 타입 정의 ───
interface UserSummary {
  user_id: string;
  nickname: string;
  level: "red" | "yellow" | "green";
  last_seen: string | null;
  active_alerts: number;
  active_alert_ids: string[];
  latest_emotion: string | null;
  weekly_participated: boolean;
}

interface DashboardData {
  summary: { red: number; yellow: number; green: number };
  users: UserSummary[];
  weekly_participants: number;
  total_users: number;
}

const LEVEL_COLOR = { red: "#FF4444", yellow: "#FFA500", green: "#44BB44" };
const LEVEL_ICON = { red: "🔴", yellow: "🟡", green: "✅" };
const LEVEL_LABEL = { red: "긴급", yellow: "주의", green: "정상" };

export default function Dashboard() {
  const [data, setData] = useState<DashboardData | null>(null);
  const [selectedUser, setSelectedUser] = useState<string | null>(null);
  const [resolving, setResolving] = useState<Record<string, boolean>>({});

  useEffect(() => {
    fetchDashboard();
    const interval = setInterval(fetchDashboard, 60_000);
    return () => clearInterval(interval);
  }, []);

  const fetchDashboard = async () => {
    const res = await axios.get(`${API}/welfare/dashboard`);
    setData(res.data);
  };

  const resolveAlert = async (alertId: string) => {
    setResolving((prev) => ({ ...prev, [alertId]: true }));
    try {
      await axios.patch(`${API}/safety/alerts/${alertId}/resolve`);
      await fetchDashboard();
    } catch (e) {
      alert("알림 해결에 실패했습니다.");
    } finally {
      setResolving((prev) => ({ ...prev, [alertId]: false }));
    }
  };

  const recordIntervention = async (
    userId: string,
    actionType: string,
    note?: string
  ) => {
    try {
      await axios.post(`${API}/welfare/users/${userId}/intervention`, {
        action_type: actionType,
        note: note || "",
      });
    } catch (e) {
      console.error("개입 기록 실패", e);
    }
  };

  return (
    <div style={styles.container}>
      {/* 상단 안내 */}
      <div style={styles.topBar}>
        <h2 style={styles.title}>📊 복지사 대시보드</h2>
        <a href="#/topic" style={styles.linkBtn}>
          📋 주간 주제 관리 →
        </a>
      </div>

      {data ? (
        <>
          {/* 요약 카드 */}
          <div style={styles.summaryRow}>
            {(["red", "yellow", "green"] as const).map((level) => (
              <div key={level} style={{ ...styles.summaryCard, borderColor: LEVEL_COLOR[level] }}>
                <span style={styles.summaryIcon}>{LEVEL_ICON[level]}</span>
                <span style={{ ...styles.summaryCount, color: LEVEL_COLOR[level] }}>{data.summary[level]}명</span>
                <span style={styles.summaryLabel}>{LEVEL_LABEL[level]}</span>
              </div>
            ))}
            <div style={{ ...styles.summaryCard, borderColor: "#888" }}>
              <span style={styles.summaryIcon}>📊</span>
              <span style={{ ...styles.summaryCount, color: "#555" }}>{data.weekly_participants}/{data.total_users}</span>
              <span style={styles.summaryLabel}>이번 주 참여</span>
            </div>
          </div>

          {/* 사용자 목록 */}
          <div style={styles.userList}>
            {data.users.map((user) => (
              <div
                key={user.user_id}
                style={{ ...styles.userCard, borderLeft: `6px solid ${LEVEL_COLOR[user.level]}`, background: selectedUser === user.user_id ? "#F0F4FF" : "#FFF" }}
                onClick={() => setSelectedUser(selectedUser === user.user_id ? null : user.user_id)}
              >
                <div style={styles.userMain}>
                  <span style={styles.userIcon}>{LEVEL_ICON[user.level]}</span>
                  <div style={styles.userInfo}>
                    <span style={styles.userName}>{user.nickname}</span>
                    <span style={styles.userMeta}>마지막 접속: {user.last_seen ? new Date(user.last_seen).toLocaleDateString("ko-KR") : "없음"}{user.active_alerts > 0 && <span style={styles.alertBadge}> · 알림 {user.active_alerts}건</span>}</span>
                  </div>
                  <span style={{ ...styles.levelBadge, background: LEVEL_COLOR[user.level] }}>{LEVEL_LABEL[user.level]}</span>
                </div>
                {selectedUser === user.user_id && (
                  <div style={styles.actionRow}>
                    <a
                      href={`tel:`}
                      style={{ ...styles.actionBtn, background: "#E8572A", textDecoration: "none", display: "inline-block" }}
                      onClick={() => recordIntervention(user.user_id, "phone", "전화 연결 시도")}
                    >
                      📞 전화하기
                    </a>
                    <button
                      style={{ ...styles.actionBtn, background: "#555" }}
                      onClick={() => recordIntervention(user.user_id, "visit", "방문 요청")}
                    >
                      🏠 방문 요청
                    </button>
                    <button
                      style={{ ...styles.actionBtn, background: "#4CAF50" }}
                      onClick={() => recordIntervention(user.user_id, "counseling", "상담 연결")}
                    >
                      🔗 상담 연결
                    </button>
                    <button
                      style={{ ...styles.actionBtn, background: "#2196F3" }}
                      onClick={() => recordIntervention(user.user_id, "detail", "상세 정보 조회")}
                    >
                      📋 상세 보기
                    </button>
                    {user.active_alert_ids.map((alertId) => (
                      <button
                        key={alertId}
                        style={{ ...styles.actionBtn, background: "#9C27B0" }}
                        disabled={resolving[alertId]}
                        onClick={() => resolveAlert(alertId)}
                      >
                        {resolving[alertId] ? "처리 중..." : "🔕 알림 해결"}
                      </button>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        </>
      ) : (
        <div style={styles.loading}>대시보드 불러오는 중...</div>
      )}
    </div>
  );
}

// ═════════════════════════════════════
// 스타일
// ═════════════════════════════════════

const styles: Record<string, React.CSSProperties> = {
  container: { fontFamily: "sans-serif", padding: 24, background: "#F5F7FA", minHeight: "100vh" },
  loading: { display: "flex", justifyContent: "center", alignItems: "center", height: "50vh", fontSize: 18 },

  // 상단
  topBar: { display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 24 },
  title: { fontSize: 22, fontWeight: "bold", color: "#1A1A2E", margin: 0 },
  linkBtn: { background: "#E8572A", color: "#FFF", padding: "10px 18px", borderRadius: 8, textDecoration: "none", fontWeight: "bold", fontSize: 14 },

  // 대시보드
  summaryRow: { display: "flex", gap: 12, marginBottom: 24, flexWrap: "wrap" },
  summaryCard: { flex: 1, minWidth: 100, background: "#FFF", borderRadius: 10, padding: "16px 20px", border: "2px solid", display: "flex", flexDirection: "column", alignItems: "center", gap: 6, boxShadow: "0 2px 6px rgba(0,0,0,0.05)" },
  summaryIcon: { fontSize: 24 },
  summaryCount: { fontSize: 28, fontWeight: "bold" },
  summaryLabel: { fontSize: 12, color: "#888" },
  userList: { display: "flex", flexDirection: "column", gap: 10 },
  userCard: { background: "#FFF", borderRadius: 10, padding: "14px 18px", cursor: "pointer", boxShadow: "0 2px 6px rgba(0,0,0,0.05)" },
  userMain: { display: "flex", alignItems: "center", gap: 12 },
  userIcon: { fontSize: 20, minWidth: 28, textAlign: "center" },
  userInfo: { flex: 1, display: "flex", flexDirection: "column", gap: 3 },
  userName: { fontSize: 15, fontWeight: "bold", color: "#222" },
  userMeta: { fontSize: 12, color: "#888" },
  alertBadge: { color: "#E8572A", fontWeight: "bold" },
  levelBadge: { color: "#FFF", borderRadius: 16, padding: "3px 10px", fontSize: 11, fontWeight: "bold" },
  actionRow: { display: "flex", gap: 8, marginTop: 12, flexWrap: "wrap" },
  actionBtn: { border: "none", borderRadius: 6, padding: "8px 14px", color: "#FFF", fontSize: 12, fontWeight: "bold", cursor: "pointer" },
};
