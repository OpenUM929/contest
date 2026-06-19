import { btn, COLORS } from "./ui";

interface Props {
  title: string;
  message: string;
  confirmLabel?: string;
  danger?: boolean;
  onConfirm: () => void;
  onCancel: () => void;
}

export default function ConfirmDialog({
  title,
  message,
  confirmLabel = "확인",
  danger = false,
  onConfirm,
  onCancel,
}: Props) {
  return (
    <div style={overlay} onClick={onCancel}>
      <div style={box} onClick={(e) => e.stopPropagation()}>
        <h3 style={{ color: COLORS.brown, margin: "0 0 12px" }}>{title}</h3>
        <p style={{ color: "#555", fontSize: 14, lineHeight: 1.6, marginBottom: 24 }}>{message}</p>
        <div style={{ display: "flex", justifyContent: "flex-end", gap: 8 }}>
          <button style={btn("ghost")} onClick={onCancel}>취소</button>
          <button style={btn(danger ? "danger" : "primary")} onClick={onConfirm}>{confirmLabel}</button>
        </div>
      </div>
    </div>
  );
}

const overlay: React.CSSProperties = {
  position: "fixed", inset: 0, background: "rgba(0,0,0,0.4)",
  display: "flex", alignItems: "center", justifyContent: "center", zIndex: 1000,
};

const box: React.CSSProperties = {
  background: "#fff", borderRadius: 14, padding: 28,
  width: 400, maxWidth: "90vw", boxShadow: "0 10px 40px rgba(0,0,0,0.2)",
};
