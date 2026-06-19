import React, { useEffect, useState } from "react";
import axios from "axios";
import { DistributionSummary } from "../types/survey";

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

interface WorkerItem {
  welfare_id: string;
  name: string;
  region: string;
}

const LEVEL_COLOR = { red: "#FF4444", yellow: "#FFA500", green: "#44BB44" };
const LEVEL_ICON = { red: "🔴", yellow: "🟡", green: "✅" };
const LEVEL_LABEL = { red: "긴급", yellow: "주의", green: "정상" };

export default function Dashboard({ onGoTopics }: { onGoTopics?: () => void }) {
  const [data, setData] = useState<DashboardData | null>(null);
  const [selectedUser, setSelectedUser] = useState<string | null>(null);
  const [resolving, setResolving] = useState<Record<string, boolean>>({});
  const [modalOpen, setModalOpen] = useState(false);
  const [modalAction, setModalAction] = useState<string | null>(null);
  const [modalNote, setModalNote] = useState("");
  const [modalUserId, setModalUserId] = useState<string | null>(null);

  // 복지사 선택 + 배포 현황
  const [workers, setWorkers] = useState<WorkerItem[]>([]);
  const [selectedWelfareId, setSelectedWelfareId] = useState<string>(localStorage.getItem('temp_welfare_id') || "");
  const [distSummary, setDistSummary] = useState<DistributionSummary | null>(null);

  useEffect(() => {
    fetchDashboard();
    fetchWorkers();
    const interval = setInterval(fetchDashboard, 60_000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    if (selectedWelfareId) {
      fetchDistSummary(selectedWelfareId);
    }
  }, [selectedWelfareId]);

  const fetchDashboard = async () => {
    const res = await axios.get(`${API}/api/welfare/dashboard`);
    setData(res.data);
  };

  const fetchWorkers = async () => {
    try {
      const { data } = await axios.get(`${API}/api/welfare/workers`);
      setWorkers(data.workers ?? []);
      if (data.workers?.length > 0 && !selectedWelfareId) {
        setSelectedWelfareId(data.workers[0].welfare_id);
      }
    } catch { /* ignore */ }
  };

  const fetchDistSummary = async (welfareId: string) => {
    try {
      const { data } = await axios.get(`${API}/api/welfare/topics/distribution-summary`, {
        params: { welfare_id: welfareId },
      });
      setDistSummary(data);
    } catch { /* ignore */ }
  };

  const resolveAlert = async (alertId: string, userId: string) => {
    setResolving((prev) => ({ ...prev, [alertId]: true }));
    // 낙관적 업데이트
    const originalUsers = data?.users;
    setData((prev) => {
      if (!prev) return prev;
      return {
        ...prev,
        users: prev.users.map((u) => {
          if (u.user_id !== userId) return u;
          return {
            ...u,
            active_alerts: u.active_alerts - 1,
            active_alert_ids: u.active_alert_ids.filter((id) => id !== alertId),
          };
        }),
      };
    });
    try {
      await axios.patch(`${API}/api/safety/alerts/${alertId}/resolve`);
    } catch (e) {
      // 실패 시 원복
      if (originalUsers) {
        setData((prev) => {
          if (!prev) return prev;
          return { ...prev, users: originalUsers };
        });
      }
      alert("알림 해결에 실패했습니다. 다시 시도해주세요.");
    } finally {
      setResolving((prev) => ({ ...prev, [alertId]: false }));
    }
  };

  const openModal = (userId: string, action: string) => {
    setModalUserId(userId);
    setModalAction(action);
    setModalNote("");
    setModalOpen(true);
  };

  const closeModal = () => {
    setModalOpen(false);
    setModalUserId(null);
    setModalAction(null);
    setModalNote("");
  };

  const submitModal = async () => {
    if (!modalUserId || !modalAction) return;
    try {
      await axios.post(`${API}/api/welfare/users/${modalUserId}/intervention`, {
        action_type: modalAction,
        note: modalNote || null,
      });
      closeModal();
      alert("개입 이력이 기록되었습니다.");
    } catch (e) {
      alert("기록에 실패했습니다. 다시 시도해주세요.");
    }
  };

  return (
    <div style={styles.container}>
      {/* 상단 안내 */}
      <div style={styles.topBar}>
        <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
          <h2 style={styles.title}>📊 복지사 대시보드</h2>
          <select
            value={selectedWelfareId}
            onChange={(e) => setSelectedWelfareId(e.target.value)}
            style={{
              padding: "6px 10px", borderRadius: 6, border: "1px solid #DDD",
              fontSize: 13, background: "#FFF",
            }}
          >
            {workers.map((w) => (
              <option key={w.welfare_id} value={w.welfare_id}>{w.name} ({w.region || "기본"})</option>
            ))}
          </select>
        </div>
        <button onClick={onGoTopics} style={styles.linkBtn}>
          📋 주간 주제 관리 →
        </button>
      </div>

      {data ? (
        <>
          {/* 배포 확인 현황 */}
          {distSummary && (
            <div style={{ ...styles.summaryCard, borderColor: "#7B7BFF", marginBottom: 12, flexDirection: "row", justifyContent: "space-between", alignItems: "center" }}>
              <div>
                <div style={{ fontSize: 12, color: "#888", marginBottom: 4 }}>📬 이번 주 주제 확인 현황</div>
                <div style={{ fontSize: 22, fontWeight: "bold", color: "#1A1A2E" }}>
                  {distSummary.acknowledged_count}/{distSummary.total_distributed}
                  <span style={{ fontSize: 14, color: "#888", fontWeight: "normal", marginLeft: 6 }}>명 확인</span>
                </div>
              </div>
              <div style={{ display: "flex", gap: 16 }}>
                <div style={{ textAlign: "center" }}>
                  <div style={{ fontSize: 20, fontWeight: "bold", color: "#4CAF50" }}>{distSummary.acknowledged_count}</div>
                  <div style={{ fontSize: 11, color: "#888" }}>확인</div>
                </div>
                <div style={{ textAlign: "center" }}>
                  <div style={{ fontSize: 20, fontWeight: "bold", color: distSummary.pending_count > 0 ? "#E8572A" : "#888" }}>{distSummary.pending_count}</div>
                  <div style={{ fontSize: 11, color: "#888" }}>미확인</div>
                </div>
              </div>
            </div>
          )}

          {/* 요약 카드 */}
          <div style={styles.summaryRow}>
            {(["red", "yellow", "green"] as const).map((level) => (
              <div key={level} style={{ ...styles.summaryCard, borderColor: LEVEL_COLOR[level], position: "relative" }}>
                <span style={styles.summaryIcon}>{LEVEL_ICON[level]}</span>
                <span style={{ ...styles.summaryCount, color: LEVEL_COLOR[level] }}>{data.summary[level]}명</span>
                <span style={styles.summaryLabel}>{LEVEL_LABEL[level]}</span>
                <span
                  style={styles.infoIcon}
                  title={
                    level === "red"
                      ? "총점 6점 이상: 미접속(3점) + 미해결알림(3점) 등"
                      : level === "yellow"
                      ? "총점 3~5점: 미접속 또는 부정감정 지속"
                      : "총점 0~2점: 정상 범위"
                  }
                >ⓘ</span>
              </div>
            ))}
            <div style={{ ...styles.summaryCard, borderColor: "#888" }}>
              <span style={styles.summaryIcon}>📊</span>
              <span style={{ ...styles.summaryCount, color: "#555" }}>{data.weekly_participants}/{data.total_users}</span>
              <span style={styles.summaryLabel}>이번 주 참여</span>
            </div>
          </div>
          {/* 등급 기준 안내 */}
          <details style={styles.ruleBox}>
            <summary style={styles.ruleSummary}>📋 위험도 등급 기준 보기</summary>
            <div style={styles.ruleContent}>
              <div style={styles.ruleRow}>
                <span style={{ ...styles.ruleDot, background: "#FF4444" }} />
                <span><b>긴급</b> (6점 이상) — 미접속(3점) + 미해결알림(3점) 또는 위기키워드 감지</span>
              </div>
              <div style={styles.ruleRow}>
                <span style={{ ...styles.ruleDot, background: "#FFA500" }} />
                <span><b>주의</b> (3~5점) — 3일↑ 미접속 또는 최근 3연속 부정감정</span>
              </div>
              <div style={styles.ruleRow}>
                <span style={{ ...styles.ruleDot, background: "#44BB44" }} />
                <span><b>정상</b> (0~2점) — 정상 접속 중</span>
              </div>
              <div style={{ ...styles.ruleRow, marginTop: 8, fontSize: 12, color: "#888" }}>
                <span>📌 알림 유형: no_contact(3점) / emotion_drop(2점) / crisis(3점) / 미해결알림 1건당 +3점</span>
              </div>
            </div>
          </details>

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
                    <span style={styles.userMeta}>마지막 접속: {user.last_seen ? new Date(user.last_seen).toLocaleDateString("ko-KR") : "없음"}{user.active_alerts > 0 && <span style={styles.alertBadge}> · 알림 {user.active_alerts}건</span>}
                      {distSummary && distSummary.users.find(u => u.user_id === user.user_id)?.acknowledged ? (
                        <span style={{ color: "#4CAF50", fontWeight: "bold", marginLeft: 8 }}>✅ 주제 확인</span>
                      ) : distSummary && distSummary.users.find(u => u.user_id === user.user_id) ? (
                        <span style={{ color: "#E8572A", marginLeft: 8 }}>⏳ 주제 미확인</span>
                      ) : null}
                    </span>
                  </div>
                  <span style={{ ...styles.levelBadge, background: LEVEL_COLOR[user.level] }}>{LEVEL_LABEL[user.level]}</span>
                </div>
                {selectedUser === user.user_id && (
                  <div style={styles.actionRow}>
                    <a
                      href="tel:"
                      style={{ ...styles.actionBtn, background: "#E8572A", textDecoration: "none", display: "inline-block" }}
                      onClick={async (e) => {
                        e.preventDefault();
                        window.open("tel:", "_self");
                        try {
                          await axios.post(`${API}/api/welfare/users/${user.user_id}/intervention`, {
                            action_type: "phone",
                          });
                        } catch (e) {
                          console.error("전화 인텐트 기록 실패", e);
                        }
                      }}
                    >
                      📞 전화하기
                    </a>
                    <button
                      style={{ ...styles.actionBtn, background: "#555" }}
                      onClick={() => openModal(user.user_id, "visit")}
                    >
                      🏠 방문 요청
                    </button>
                    <button
                      style={{ ...styles.actionBtn, background: "#4CAF50" }}
                      onClick={() => openModal(user.user_id, "counseling")}
                    >
                      🔗 상담 연결
                    </button>
                    <button
                      style={{ ...styles.actionBtn, background: "#2196F3" }}
                      onClick={() => {
                        axios.post(`${API}/api/welfare/users/${user.user_id}/intervention`, {
                          action_type: "detail",
                          note: "상세 정보 조회",
                        }).catch((e) => console.error("상세 보기 기록 실패", e));
                      }}
                    >
                      📋 상세 보기
                    </button>
                    {user.active_alert_ids.map((alertId) => (
                      <button
                        key={alertId}
                        style={{ ...styles.actionBtn, background: "#9C27B0" }}
                        disabled={resolving[alertId]}
                        onClick={() => resolveAlert(alertId, user.user_id)}
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

      {/* 모달 — 방문/상담 메모 */}
      {modalOpen && (
        <div style={styles.modalOverlay}>
          <div style={styles.modalContent}>
            <h3 style={{ marginTop: 0, fontSize: 18 }}>
              {modalAction === "visit" ? "방문 요청" : "상담 연결"}
            </h3>
            <textarea
              style={styles.modalTextarea}
              placeholder="상황 메모 (선택)"
              value={modalNote}
              onChange={(e) => setModalNote(e.target.value)}
            />
            <div style={styles.modalActions}>
              <button style={styles.modalBtn} onClick={submitModal}>저장</button>
              <button style={styles.modalBtnCancel} onClick={closeModal}>취소</button>
            </div>
          </div>
        </div>
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
  summaryRow: { display: "flex", gap: 12, marginBottom: 4, flexWrap: "wrap" },
  summaryCard: { flex: 1, minWidth: 100, background: "#FFF", borderRadius: 10, padding: "16px 20px", border: "2px solid", display: "flex", flexDirection: "column", alignItems: "center", gap: 6, boxShadow: "0 2px 6px rgba(0,0,0,0.05)" },
  summaryIcon: { fontSize: 24 },
  summaryCount: { fontSize: 28, fontWeight: "bold" },
  summaryLabel: { fontSize: 12, color: "#888" },
  infoIcon: { position: "absolute", top: 6, right: 8, fontSize: 13, color: "#AAA", cursor: "pointer" },
  ruleBox: { background: "#FFF", borderRadius: 10, padding: "10px 16px", border: "1px solid #EEE", marginBottom: 24, fontSize: 13 },
  ruleSummary: { cursor: "pointer", fontWeight: 600, color: "#555", fontSize: 13 },
  ruleContent: { marginTop: 10, display: "flex", flexDirection: "column", gap: 6 },
  ruleRow: { display: "flex", alignItems: "center", gap: 8, fontSize: 13, color: "#444" },
  ruleDot: { display: "inline-block", width: 10, height: 10, borderRadius: "50%", flexShrink: 0 },
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
  // 모달
  modalOverlay: { position: "fixed", top: 0, left: 0, right: 0, bottom: 0, background: "rgba(0,0,0,0.5)", display: "flex", justifyContent: "center", alignItems: "center", zIndex: 1000 },
  modalContent: { background: "#FFF", borderRadius: 12, padding: 24, width: 400, maxWidth: "90%" },
  modalTextarea: { width: "100%", minHeight: 80, borderRadius: 8, border: "1px solid #DDD", padding: 12, fontSize: 14, marginBottom: 16, boxSizing: "border-box" },
  modalActions: { display: "flex", gap: 8, justifyContent: "flex-end" },
  modalBtn: { background: "#4CAF50", color: "#FFF", border: "none", borderRadius: 6, padding: "8px 16px", fontSize: 14, fontWeight: "bold", cursor: "pointer" },
  modalBtnCancel: { background: "#888", color: "#FFF", border: "none", borderRadius: 6, padding: "8px 16px", fontSize: 14, fontWeight: "bold", cursor: "pointer" },
};
