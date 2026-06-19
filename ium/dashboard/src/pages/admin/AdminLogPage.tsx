import { useEffect, useState, useCallback } from "react";
import { listLogs, type AdminLog, type Paged } from "../../api/admin";
import SearchFilter from "../../components/admin/SearchFilter";
import DataTable, { type Column } from "../../components/admin/DataTable";
import { COLORS, ACTION_LABELS, formatDate } from "../../components/admin/ui";

const EMPTY: Paged<AdminLog> = { items: [], total: 0, page: 1, page_size: 30, total_pages: 1 };

export default function AdminLogPage() {
  const [data, setData] = useState<Paged<AdminLog>>(EMPTY);
  const [loading, setLoading] = useState(false);
  const [page, setPage] = useState(1);
  const [filters, setFilters] = useState<Record<string, string>>({});

  const load = useCallback(async (targetPage = page) => {
    setLoading(true);
    try {
      const res = await listLogs({
        action: filters.action || undefined,
        target_type: filters.target_type || undefined,
        page: targetPage,
        page_size: 30,
      });
      setData(res.data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  }, [filters, page]);

  useEffect(() => { load(page); /* eslint-disable-next-line */ }, [page]);

  const doSearch = () => { setPage(1); load(1); };

  const columns: Column<AdminLog>[] = [
    { key: "created_at", label: "시간", render: (l) => formatDate(l.created_at), width: 180 },
    { key: "admin_id", label: "관리자" },
    { key: "action", label: "작업", render: (l) => ACTION_LABELS[l.action] || l.action },
    { key: "target_type", label: "대상", render: (l) => (l.target_type === "user" ? "회원" : "복지사") },
    { key: "target_id", label: "대상 ID", render: (l) => <code style={{ fontSize: 11, color: "#AAA" }}>{l.target_id}</code> },
    {
      key: "payload", label: "변경 내용",
      render: (l) => (
        <code style={{ fontSize: 11, color: "#777", whiteSpace: "pre-wrap", wordBreak: "break-all" }}>
          {l.payload ? JSON.stringify(l.payload) : "-"}
        </code>
      ),
    },
  ];

  return (
    <div style={{ padding: 24 }}>
      <h2 style={{ color: COLORS.brown, marginBottom: 16 }}>📜 관리자 작업 로그</h2>

      <SearchFilter
        hideSearch
        searchValue=""
        onSearchChange={() => {}}
        filters={[
          {
            key: "action", label: "작업",
            options: Object.entries(ACTION_LABELS).map(([value, label]) => ({ value, label })),
          },
          { key: "target_type", label: "대상", options: [{ value: "user", label: "회원" }, { value: "worker", label: "복지사" }] },
        ]}
        filterValues={filters}
        onFilterChange={(k, v) => setFilters((f) => ({ ...f, [k]: v }))}
        onSubmit={doSearch}
      />

      <DataTable
        columns={columns}
        rows={data.items}
        rowKey={(l) => l.id}
        page={data.page}
        totalPages={data.total_pages}
        total={data.total}
        loading={loading}
        onPageChange={setPage}
        emptyText="작업 로그가 없습니다."
      />
    </div>
  );
}
