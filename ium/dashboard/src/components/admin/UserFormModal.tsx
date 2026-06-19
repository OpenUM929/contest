import { useState } from "react";
import { inputStyle, btn, COLORS } from "./ui";
import type { AdminUser, AdminWorker } from "../../api/admin";

interface Props {
  mode: "create" | "edit";
  initial?: AdminUser | null;
  workers: AdminWorker[];
  onSave: (data: any) => Promise<void>;
  onClose: () => void;
}

export default function UserFormModal({ mode, initial, workers, onSave, onClose }: Props) {
  const [form, setForm] = useState({
    user_type: initial?.user_type || "elder",
    name: initial?.name || "",
    nickname: initial?.nickname || "",
    phone: initial?.phone || "",
    email: initial?.email || "",
    region: initial?.region || "",
    welfare_id: initial?.welfare_id || "",
    status: initial?.status || "active",
    note: initial?.note || "",
  });
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  const set = (k: string, v: string) => setForm((f) => ({ ...f, [k]: v }));

  const submit = async () => {
    if (!form.name.trim() || !form.nickname.trim()) {
      setError("이름과 닉네임은 필수입니다.");
      return;
    }
    setSaving(true);
    setError("");
    try {
      const payload: any = {
        name: form.name.trim(),
        nickname: form.nickname.trim(),
        phone: form.phone || null,
        email: form.email || null,
        region: form.region || null,
        welfare_id: form.welfare_id || null,
        note: form.note || null,
      };
      if (mode === "create") payload.user_type = form.user_type;
      if (mode === "edit") payload.status = form.status;
      await onSave(payload);
    } catch (e: any) {
      setError(e?.response?.data?.detail || "저장에 실패했습니다.");
    } finally {
      setSaving(false);
    }
  };

  const activeWorkers = workers.filter((w) => w.status === "active");

  return (
    <div style={overlay} onClick={onClose}>
      <div style={box} onClick={(e) => e.stopPropagation()}>
        <h3 style={{ color: COLORS.brown, margin: "0 0 20px" }}>
          {mode === "create" ? "회원 등록" : "회원 수정"}
        </h3>

        <div style={grid}>
          <Field label="유형">
            <select style={inputStyle} value={form.user_type} disabled={mode === "edit"}
              onChange={(e) => set("user_type", e.target.value)}>
              <option value="elder">노인</option>
              <option value="youth">청년</option>
            </select>
          </Field>
          {mode === "edit" && (
            <Field label="상태">
              <select style={inputStyle} value={form.status} onChange={(e) => set("status", e.target.value)}>
                <option value="active">정상</option>
                <option value="dormant">휴면</option>
                <option value="withdrawn">탈퇴</option>
              </select>
            </Field>
          )}
          <Field label="이름 *">
            <input style={inputStyle} value={form.name} onChange={(e) => set("name", e.target.value)} />
          </Field>
          <Field label="닉네임 *">
            <input style={inputStyle} value={form.nickname} onChange={(e) => set("nickname", e.target.value)} />
          </Field>
          <Field label="연락처">
            <input style={inputStyle} value={form.phone} onChange={(e) => set("phone", e.target.value)} />
          </Field>
          <Field label="이메일">
            <input style={inputStyle} value={form.email} onChange={(e) => set("email", e.target.value)} />
          </Field>
          <Field label="지역">
            <input style={inputStyle} value={form.region} onChange={(e) => set("region", e.target.value)} />
          </Field>
          <Field label="담당 복지사">
            <select style={inputStyle} value={form.welfare_id} onChange={(e) => set("welfare_id", e.target.value)}>
              <option value="">미배정</option>
              {activeWorkers.map((w) => (
                <option key={w.welfare_id} value={w.welfare_id}>{w.name} ({w.region || "-"})</option>
              ))}
            </select>
          </Field>
        </div>
        <div style={{ marginTop: 12 }}>
          <Field label="메모">
            <textarea style={{ ...inputStyle, width: "100%", minHeight: 60, resize: "vertical" }}
              value={form.note} onChange={(e) => set("note", e.target.value)} />
          </Field>
        </div>

        {error && <p style={{ color: "#D33", fontSize: 13, marginTop: 12 }}>{error}</p>}

        <div style={{ display: "flex", justifyContent: "flex-end", gap: 8, marginTop: 24 }}>
          <button style={btn("ghost")} onClick={onClose}>취소</button>
          <button style={btn("primary")} disabled={saving} onClick={submit}>
            {saving ? "저장 중..." : "저장"}
          </button>
        </div>
      </div>
    </div>
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <label style={{ display: "flex", flexDirection: "column", gap: 4 }}>
      <span style={{ fontSize: 12, color: "#888", fontWeight: "bold" }}>{label}</span>
      {children}
    </label>
  );
}

const overlay: React.CSSProperties = {
  position: "fixed", inset: 0, background: "rgba(0,0,0,0.4)",
  display: "flex", alignItems: "center", justifyContent: "center", zIndex: 1000,
};
const box: React.CSSProperties = {
  background: "#fff", borderRadius: 14, padding: 28,
  width: 560, maxWidth: "92vw", maxHeight: "90vh", overflowY: "auto",
  boxShadow: "0 10px 40px rgba(0,0,0,0.2)",
};
const grid: React.CSSProperties = {
  display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12,
};
