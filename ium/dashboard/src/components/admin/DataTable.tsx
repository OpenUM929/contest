import { thStyle, tdStyle, btn, COLORS } from "./ui";

export interface Column<T> {
  key: string;
  label: string;
  render?: (row: T) => React.ReactNode;
  width?: number | string;
}

interface Props<T> {
  columns: Column<T>[];
  rows: T[];
  rowKey: (row: T) => string;
  page: number;
  totalPages: number;
  total: number;
  onPageChange: (page: number) => void;
  loading?: boolean;
  emptyText?: string;
}

export default function DataTable<T>({
  columns, rows, rowKey, page, totalPages, total, onPageChange, loading, emptyText = "데이터가 없습니다.",
}: Props<T>) {
  return (
    <div>
      <table style={{
        width: "100%", borderCollapse: "collapse",
        background: COLORS.card, borderRadius: 12, overflow: "hidden",
      }}>
        <thead>
          <tr style={{ background: COLORS.headBg }}>
            {columns.map((c) => (
              <th key={c.key} style={{ ...thStyle, width: c.width }}>{c.label}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {loading ? (
            <tr><td style={tdStyle} colSpan={columns.length}>로딩 중...</td></tr>
          ) : rows.length === 0 ? (
            <tr><td style={{ ...tdStyle, color: "#AAA", textAlign: "center" }} colSpan={columns.length}>{emptyText}</td></tr>
          ) : (
            rows.map((row) => (
              <tr key={rowKey(row)}>
                {columns.map((c) => (
                  <td key={c.key} style={tdStyle}>
                    {c.render ? c.render(row) : (row as any)[c.key] ?? "-"}
                  </td>
                ))}
              </tr>
            ))
          )}
        </tbody>
      </table>

      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginTop: 16 }}>
        <span style={{ fontSize: 13, color: COLORS.muted }}>총 {total}건</span>
        <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
          <button style={btn("ghost")} disabled={page <= 1} onClick={() => onPageChange(page - 1)}>이전</button>
          <span style={{ fontSize: 13, color: "#555" }}>{page} / {totalPages}</span>
          <button style={btn("ghost")} disabled={page >= totalPages} onClick={() => onPageChange(page + 1)}>다음</button>
        </div>
      </div>
    </div>
  );
}
