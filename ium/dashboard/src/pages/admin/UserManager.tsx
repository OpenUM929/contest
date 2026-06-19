import { useEffect, useState, useCallback } from "react";
import {
  listUsers, createUser, updateUser, deleteUser, assignWorker, listWorkers,
  type AdminUser, type AdminWorker, type Paged,
} from "../../api/admin";
import SearchFilter from "../../components/admin/SearchFilter";
import DataTable, { type Column } from "../../components/admin/DataTable";
import UserFormModal from "../../components/admin/UserFormModal";
import ConfirmDialog from "../../components/admin/ConfirmDialog";
import { COLORS, btn, statusBadge, formatDate, inputStyle } from "../../components/admin/ui";

const EMPTY: Paged<AdminUser> = { items: [], total: 0, page: 1, page_size: 20, total_pages: 1 };

export default function UserManager() {
  const [data, setData] = useState<Paged<AdminUser>>(EMPTY);
  const [workers, setWorkers] = useState<AdminWorker[]>([]);
  const [loading, setLoading] = useState(false);
  const [page, setPage] = useState(1);

  const [search, setSearch] = useState("");
  const [filters, setFilters] = useState<Record<string, string>>({});

  const [modal, setModal] = useState<{ mode: "create" | "edit"; user: AdminUser | null } | null>(null);
  const [confirm, setConfirm] = useState<AdminUser | null>(null);

  const load = useCallback(async (targetPage = page) => {
    setLoading(true);
    try {
      const res = await listUsers({
        q: search,
        user_type: filters.user_type || undefined,
        status: filters.status || undefined,
        welfare_id: filters.welfare_id || undefined,
        region: filters.region || undefined,
        page: targetPage,
        page_size: 20,
      });
      setData(res.data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  }, [search, filters, page]);

  useEffect(() => {
    listWorkers({ page_size: 100, status: "active" }).then((r) => setWorkers(r.data.items)).catch(console.error);
  }, []);

  useEffect(() => { load(page); /* eslint-disable-next-line */ }, [page]);

  const doSearch = () => { setPage(1); load(1); };

  const handleSave = async (payload: any) => {
    if (modal?.mode === "create") await createUser(payload);
    else if (modal?.user) await updateUser(modal.user.user_id, payload);
    setModal(null);
    load(page);
  };

  const handleDelete = async () => {
    if (!confirm) return;
    await deleteUser(confirm.user_id);
    setConfirm(null);
    load(page);
  };

  const handleAssign = async (user: AdminUser, welfareId: string) => {
    await assignWorker(user.user_id, welfareId || null);
    load(page);
  };

  const columns: Column<AdminUser>[] = [
    { key: "name", label: "이름", render: (u) => <strong>{u.name || "-"}</strong> },
    { key: "nickname", label: "닉네임" },
    { key: "user_type", label: "유형", render: (u) => (u.user_type === "elder" ? "노인" : "청년") },
    {
      key: "status", label: "상태",
      render: (u) => { const b = statusBadge(u.status); return <span style={b.style}>{b.label}</span>; },
    },
    {
      key: "welfare", label: "담당 복지사",
      render: (u) => (
        <select
          style={{ ...inputStyle, padding: "4px 8px", fontSize: 13 }}
          value={u.welfare_id || ""}
          disabled={u.status === "withdrawn"}
          onChange={(e) => handleAssign(u, e.target.value)}
        >
          <option value="">미배정</option>
          {workers.map((w) => (
            <option key={w.welfare_id} value={w.welfare_id}>{w.name}</option>
          ))}
        </select>
      ),
    },
    { key: "region", label: "지역", render: (u) => u.region || "-" },
    { key: "last_seen", label: "최근 접속", render: (u) => formatDate(u.last_seen) },
    {
      key: "actions", label: "작업",
      render: (u) => (
        <div style={{ display: "flex", gap: 6 }}>
          <button style={btn("ghost")} onClick={() => setModal({ mode: "edit", user: u })}>수정</button>
          <button style={btn("danger")} disabled={u.status === "withdrawn"} onClick={() => setConfirm(u)}>삭제</button>
        </div>
      ),
    },
  ];

  return (
    <div style={{ padding: 24 }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
        <h2 style={{ color: COLORS.brown, margin: 0 }}>👥 회원 관리</h2>
        <button style={btn("primary")} onClick={() => setModal({ mode: "create", user: null })}>+ 회원 등록</button>
      </div>

      <SearchFilter
        searchValue={search}
        onSearchChange={setSearch}
        searchPlaceholder="이름 / 닉네임 / 연락처 검색"
        filters={[
          { key: "user_type", label: "유형", options: [{ value: "elder", label: "노인" }, { value: "youth", label: "청년" }] },
          { key: "status", label: "상태", options: [{ value: "active", label: "정상" }, { value: "dormant", label: "휴면" }, { value: "withdrawn", label: "탈퇴" }] },
          { key: "welfare_id", label: "복지사", options: workers.map((w) => ({ value: w.welfare_id, label: w.name })) },
        ]}
        filterValues={filters}
        onFilterChange={(k, v) => setFilters((f) => ({ ...f, [k]: v }))}
        onSubmit={doSearch}
      />

      <DataTable
        columns={columns}
        rows={data.items}
        rowKey={(u) => u.user_id}
        page={data.page}
        totalPages={data.total_pages}
        total={data.total}
        loading={loading}
        onPageChange={setPage}
        emptyText="회원이 없습니다."
      />

      {modal && (
        <UserFormModal
          mode={modal.mode}
          initial={modal.user}
          workers={workers}
          onSave={handleSave}
          onClose={() => setModal(null)}
        />
      )}
      {confirm && (
        <ConfirmDialog
          title="회원 탈퇴 처리"
          message={`'${confirm.nickname}' 회원을 탈퇴 처리합니다. 연락처가 삭제되고 복구할 수 없습니다. 계속할까요?`}
          confirmLabel="탈퇴 처리"
          danger
          onConfirm={handleDelete}
          onCancel={() => setConfirm(null)}
        />
      )}
    </div>
  );
}
