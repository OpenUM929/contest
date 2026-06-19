import { useEffect, useState } from "react";

const API = import.meta.env.VITE_API_URL || "http://localhost:8000";

interface TempAccount {
  temp_id: string;
  user_type: string;
  nickname: string;
  user_id: string | null;
  last_seen: string | null;
  created_at: string | null;
}

export default function TempAccountPage() {
  const [accounts, setAccounts] = useState<TempAccount[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchAccounts();
  }, []);

  const fetchAccounts = async () => {
    try {
      const res = await fetch(`${API}/api/auth/temp-accounts`);
      const data = await res.json();
      setAccounts(data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (iso: string | null) => {
    if (!iso) return "-";
    return new Date(iso).toLocaleString("ko-KR");
  };

  return (
    <div style={{ padding: 24 }}>
      <h2 style={{ color: "#4A3728", marginBottom: 8 }}>📋 임시 계정 관리</h2>
      <p style={{ color: "#888", fontSize: 14, marginBottom: 24 }}>
        관리자가 등록한 7개의 임시 계정 목록입니다. 프로토타입 테스트용 계정입니다.
      </p>

      {loading ? (
        <p>로딩 중...</p>
      ) : (
        <table style={{
          width: "100%", borderCollapse: "collapse",
          background: "#FFF", borderRadius: 12, overflow: "hidden",
        }}>
          <thead>
            <tr style={{ background: "#F5F0EB" }}>
              <th style={thStyle}>계정 ID</th>
              <th style={thStyle}>닉네임</th>
              <th style={thStyle}>유형</th>
              <th style={thStyle}>DB 사용자 ID</th>
              <th style={thStyle}>마지막 접속</th>
              <th style={thStyle}>생성일</th>
            </tr>
          </thead>
          <tbody>
            {accounts.map((a) => (
              <tr key={a.temp_id} style={{ borderBottom: "1px solid #EEE" }}>
                <td style={tdStyle}>
                  <code style={{ fontSize: 12, color: "#666" }}>{a.temp_id}</code>
                </td>
                <td style={{ ...tdStyle, fontWeight: "bold" }}>{a.nickname}</td>
                <td style={tdStyle}>
                  <span style={{
                    padding: "4px 10px", borderRadius: 12, fontSize: 12,
                    fontWeight: "bold",
                    ...(() => {
                      switch (a.user_type) {
                        case "admin": return { background: "#E8E0D8", color: "#6B4C2A" };
                        case "elder": return { background: "#FFF0E0", color: "#E8572A" };
                        case "youth": return { background: "#E0E0FF", color: "#7B7BFF" };
                        case "worker": return { background: "#D4EDDA", color: "#155724" };
                        default: return { background: "#EEE", color: "#999" };
                      }
                    })()
                  }}>
                    {a.user_type === "admin" ? "관리자" : a.user_type === "elder" ? "노인" : a.user_type === "youth" ? "청년" : a.user_type === "worker" ? "복지사" : a.user_type}
                  </span>
                </td>
                <td style={tdStyle}>
                  {a.user_id ? (
                    <code style={{ fontSize: 11, color: "#AAA" }}>{a.user_id}</code>
                  ) : (
                    <span style={{ color: "#CCC" }}>미등록</span>
                  )}
                </td>
                <td style={tdStyle}>{formatDate(a.last_seen)}</td>
                <td style={tdStyle}>{formatDate(a.created_at)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      <div style={{ marginTop: 32, padding: 16, background: "#FFF8EE", borderRadius: 12 }}>
        <h4 style={{ color: "#4A3728", marginBottom: 8 }}>🔄 테스트 계정 전환 방법</h4>
        <ol style={{ color: "#666", fontSize: 13, lineHeight: 1.8, paddingLeft: 20 }}>
          <li>모바일 앱에서 "계정 전환" 버튼 탭</li>
          <li>원하는 테스트 계정 선택 후 "시작하기"</li>
          <li><strong>비밀번호 없이</strong> 즉시 로그인 (프로토타입)</li>
        </ol>
      </div>
    </div>
  );
}

const thStyle: React.CSSProperties = {
  padding: "12px 16px",
  textAlign: "left",
  fontSize: 13,
  color: "#666",
  fontWeight: "bold",
};

const tdStyle: React.CSSProperties = {
  padding: "12px 16px",
  fontSize: 14,
  color: "#333",
};
