import { COLORS } from "./ui";

interface Props {
  label: string;
  value: number | string;
  accent?: string;
  icon?: string;
}

export default function StatCard({ label, value, accent = COLORS.accent, icon }: Props) {
  return (
    <div style={{
      background: "#fff", borderRadius: 14, padding: "20px 24px",
      flex: 1, minWidth: 140, boxShadow: "0 2px 8px rgba(0,0,0,0.05)",
      borderTop: `3px solid ${accent}`,
    }}>
      <div style={{ fontSize: 13, color: COLORS.muted, marginBottom: 8 }}>
        {icon ? `${icon} ` : ""}{label}
      </div>
      <div style={{ fontSize: 30, fontWeight: "bold", color: accent }}>{value}</div>
    </div>
  );
}
