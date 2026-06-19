// src/components/admin/ui.ts — 관리자 모듈 공용 스타일 상수
import type { CSSProperties } from "react";

export const COLORS = {
  brown: "#4A3728",
  accent: "#E8572A",
  navy: "#1A1A2E",
  muted: "#888",
  border: "#EEE",
  headBg: "#F5F0EB",
  card: "#FFF",
  softBg: "#FFF8EE",
};

export const thStyle: CSSProperties = {
  padding: "12px 16px",
  textAlign: "left",
  fontSize: 13,
  color: "#666",
  fontWeight: "bold",
  whiteSpace: "nowrap",
};

export const tdStyle: CSSProperties = {
  padding: "12px 16px",
  fontSize: 14,
  color: "#333",
  borderBottom: "1px solid #EEE",
};

export const inputStyle: CSSProperties = {
  padding: "8px 12px",
  fontSize: 14,
  border: "1px solid #DDD",
  borderRadius: 8,
  outline: "none",
};

export function btn(variant: "primary" | "ghost" | "danger" = "primary"): CSSProperties {
  const baseStyle: CSSProperties = {
    padding: "8px 16px",
    fontSize: 14,
    borderRadius: 8,
    cursor: "pointer",
    border: "1px solid transparent",
    fontWeight: "bold",
  };
  if (variant === "primary") return { ...baseStyle, background: COLORS.accent, color: "#fff" };
  if (variant === "danger") return { ...baseStyle, background: "#fff", color: "#D33", border: "1px solid #F0C0C0" };
  return { ...baseStyle, background: "#fff", color: "#666", border: "1px solid #DDD", fontWeight: "normal" };
}

const USER_STATUS: Record<string, { label: string; bg: string; color: string }> = {
  active: { label: "정상", bg: "#E3F6E8", color: "#2E9E54" },
  dormant: { label: "휴면", bg: "#FFF4DB", color: "#C79100" },
  withdrawn: { label: "탈퇴", bg: "#F0F0F0", color: "#999" },
  inactive: { label: "비활성", bg: "#F0F0F0", color: "#999" },
};

export function statusBadge(status: string): { label: string; style: CSSProperties } {
  const s = USER_STATUS[status] || { label: status, bg: "#EEE", color: "#666" };
  return {
    label: s.label,
    style: {
      padding: "4px 10px",
      borderRadius: 12,
      fontSize: 12,
      fontWeight: "bold",
      background: s.bg,
      color: s.color,
    },
  };
}

export function formatDate(iso: string | null): string {
  if (!iso) return "-";
  return new Date(iso).toLocaleString("ko-KR");
}

export const ACTION_LABELS: Record<string, string> = {
  create_user: "회원 등록",
  update_user: "회원 수정",
  delete_user: "회원 탈퇴",
  assign_worker: "복지사 배정",
  create_worker: "복지사 등록",
  update_worker: "복지사 수정",
  delete_worker: "복지사 비활성",
};
