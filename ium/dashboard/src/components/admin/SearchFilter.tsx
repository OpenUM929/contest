import { inputStyle, btn } from "./ui";

export interface FilterDef {
  key: string;
  label: string;
  options: { value: string; label: string }[];
}

interface Props {
  searchValue: string;
  onSearchChange: (v: string) => void;
  searchPlaceholder?: string;
  filters?: FilterDef[];
  filterValues: Record<string, string>;
  onFilterChange: (key: string, value: string) => void;
  onSubmit: () => void;
  rightSlot?: React.ReactNode;
  hideSearch?: boolean;
}

export default function SearchFilter({
  searchValue,
  onSearchChange,
  searchPlaceholder = "검색...",
  filters = [],
  filterValues,
  onFilterChange,
  onSubmit,
  rightSlot,
  hideSearch = false,
}: Props) {
  return (
    <div style={{
      display: "flex", flexWrap: "wrap", gap: 8, alignItems: "center",
      marginBottom: 16, padding: 16, background: "#fff", borderRadius: 12,
    }}>
      {!hideSearch && (
        <input
          style={{ ...inputStyle, flex: 1, minWidth: 200 }}
          value={searchValue}
          placeholder={searchPlaceholder}
          onChange={(e) => onSearchChange(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && onSubmit()}
        />
      )}
      {filters.map((f) => (
        <select
          key={f.key}
          style={inputStyle}
          value={filterValues[f.key] || ""}
          onChange={(e) => onFilterChange(f.key, e.target.value)}
        >
          <option value="">{f.label} 전체</option>
          {f.options.map((o) => (
            <option key={o.value} value={o.value}>{o.label}</option>
          ))}
        </select>
      ))}
      <button style={btn("primary")} onClick={onSubmit}>검색</button>
      {rightSlot}
    </div>
  );
}
