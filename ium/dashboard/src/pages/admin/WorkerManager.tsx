import { useEffect, useState, useCallback } from "react";
import {
  listWorkers, createWorker, updateWorker, deleteWorker,
  getWorkerUsers, assignWorkerUsers, unassignWorkerUsers,
  listUsers,
  type AdminWorker, type AdminUser, type Paged,
} from "../../api/admin";
import SearchFilter from "../../components/admin/SearchFilter";
import DataTable, { type Column } from "../../components/admin/DataTable";
import WorkerFormModal from "../../components/admin/WorkerFormModal";
import ConfirmDialog from "../../components/admin/ConfirmDialog";
import { COLORS, btn, statusBadge } from "../../components/admin/ui";

const EMPTY: Paged<AdminWorker> = { items: [], total: 0, page: 1, page_size: 20, total_pages: 1 };

export default function WorkerManager() {
  const [data, setData] = useState<Paged<AdminWorker>>(EMPTY);
  const [loading, setLoading] = useState(false);
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [filters, setFilters] = useState<Record<string, string>>({});

  const [modal, setModal] = useState<{ mode: "create" | "edit"; worker: AdminWorker | null } | null>(null);
  const [confirm, setConfirm] = useState<AdminWorker | null>(null);
  const [error, setError] = useState("");

  // 담당 회원 관리 모달
  const [assignModal, setAssignModal] = useState<AdminWorker | null>(null);
  const [allUsers, setAllUsers] = useState<AdminUser[]>([]);
  const [assignedUserIds, setAssignedUserIds] = useState<Set<string>>(new Set());
  const [checkedUserIds, setCheckedUserIds] = useState<Set<string>>(new Set());
  const [assignLoading, setAssignLoading] = useState(false);

  const load = useCallback(async (targetPage = page) => {
    setLoading(true);
    try {
      const res = await listWorkers({
        q: search,
        status: filters.status || undefined,
        role: filters.role || undefined,
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

  useEffect(() => { load(page); /* eslint-disable-next-line */ }, [page]);

  const doSearch = () => { setPage(1); load(1); };

  const handleSave = async (payload: any) => {
    if (modal?.mode === "create") await createWorker(payload);
    else if (modal?.worker) await updateWorker(modal.worker.welfare_id, payload);
    setModal(null);
    load(page);
  };

  const openAssignModal = async (worker: AdminWorker) => {
    setAssignLoading(true);
    setAssignModal(worker);
    try {
      const [usersRes, assignedRes] = await Promise.all([
        listUsers({ status: "active", page_size: 999 }),
        getWorkerUsers(worker.welfare_id, { page_size: 999 }),
      ]);
      const users = usersRes.data.items ?? [];
      const assigned = assignedRes.data.items ?? [];
      const assignedSet = new Set(assigned.map((u: AdminUser) => u.user_id));
      setAllUsers(users);
      setAssignedUserIds(assignedSet);
      setCheckedUserIds(new Set(assignedSet));
    } catch {
      setAllUsers([]);
      setAssignedUserIds(new Set());
      setCheckedUserIds(new Set());
    } finally {
      setAssignLoading(false);
    }
  };

  const handleAssignSave = async () => {
    if (!assignModal) return;
    const welfareId = assignModal.welfare_id;
    const toAssign = [...checkedUserIds].filter((id) => !assignedUserIds.has(id));
    const toUnassign = [...assignedUserIds].filter((id) => !checkedUserIds.has(id));

    setAssignLoading(true);
    try {
      if (toAssign.length > 0) await assignWorkerUsers(welfareId, toAssign);
      if (toUnassign.length > 0) await unassignWorkerUsers(welfareId, toUnassign);
      setAssignModal(null);
      load(page);
    } catch (e: any) {
      setError(e?.response?.data?.detail || "저장에 실패했습니다.");
    } finally {
      setAssignLoading(false);
    }
  };

  const handleDelete = async () => {
    if (!confirm) return;
    setError("");
    try {
      await deleteWorker(confirm.welfare_id);
      setConfirm(null);
      load(page);
    } catch (e: any) {
      setError(e?.response?.data?.detail || "삭제에 실패했습니다.");
      setConfirm(null);
    }
  };

  const columns: Column<AdminWorker>[] = [
    { key: "name", label: "이름", render: (w) => <strong>{w.name}</strong> },
    { key: "region", label: "지역", render: (w) => w.region || "-" },
    { key: "phone", label: "연락처", render: (w) => w.phone || "-" },
    { key: "role", label: "역할", render: (w) => (w.role === "admin" ? "상위 관리자" : "현장 복지사") },
    {
      key: "status", label: "상태",
      render: (w) => { const b = statusBadge(w.status); return <span style={b.style}>{b.label}</span>; },
    },
    { key: "active_user_count", label: "담당 회원", render: (w) => `${w.active_user_count ?? 0}명` },
    {
      key: "actions", label: "작업",
      render: (w) => (
        <div style={{ display: "flex", gap: 6 }}>
          <button style={btn("ghost")} onClick={() => openAssignModal(w)}>📋 담당 회원</button>
          <button style={btn("ghost")} onClick={() => setModal({ mode: "edit", worker: w })}>수정</button>
          <button style={btn("danger")} disabled={w.status === "inactive"} onClick={() => setConfirm(w)}>삭제</button>
        </div>
      ),
    },
  ];

  return (
    <div style={{ padding: 24 }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
        <h2 style={{ color: COLORS.brown, margin: 0 }}>💼 복지사 관리</h2>
        <button style={btn("primary")} onClick={() => setModal({ mode: "create", worker: null })}>+ 복지사 등록</button>
      </div>

      {error && <p style={{ color: "#D33", fontSize: 13, marginBottom: 12 }}>{error}</p>}

      <SearchFilter
        searchValue={search}
        onSearchChange={setSearch}
        searchPlaceholder="이름 / 지역 검색"
        filters={[
          { key: "status", label: "상태", options: [{ value: "active", label: "정상" }, { value: "inactive", label: "비활성" }] },
          { key: "role", label: "역할", options: [{ value: "worker", label: "현장 복지사" }, { value: "admin", label: "상위 관리자" }] },
        ]}
        filterValues={filters}
        onFilterChange={(k, v) => setFilters((f) => ({ ...f, [k]: v }))}
        onSubmit={doSearch}
      />

      <DataTable
        columns={columns}
        rows={data.items}
        rowKey={(w) => w.welfare_id}
        page={data.page}
        totalPages={data.total_pages}
        total={data.total}
        loading={loading}
        onPageChange={setPage}
        emptyText="복지사가 없습니다."
      />

      {modal && (
        <WorkerFormModal
          mode={modal.mode}
          initial={modal.worker}
          onSave={handleSave}
          onClose={() => setModal(null)}
        />
      )}
      {confirm && (
        <ConfirmDialog
          title="복지사 비활성 처리"
          message={`'${confirm.name}' 복지사를 비활성 처리합니다. 담당 회원이 있으면 처리되지 않습니다. 계속할까요?`}
          confirmLabel="비활성 처리"
          danger
          onConfirm={handleDelete}
          onCancel={() => setConfirm(null)}
        />
      )}

      {/* 담당 회원 관리 모달 */}
      {assignModal && (
        <div style={{
          position: "fixed", top: 0, left: 0, right: 0, bottom: 0,
          background: "rgba(0,0,0,0.5)", zIndex: 1000,
          display: "flex", alignItems: "center", justifyContent: "center", padding: 24,
        }} onClick={() => setAssignModal(null)}>
          <div style={{
            background: "#fff", borderRadius: 16, padding: 28,
            width: "100%", maxWidth: 600, maxHeight: "80vh",
            overflow: "auto", boxShadow: "0 8px 32px rgba(0,0,0,0.2)",
          }} onClick={(e) => e.stopPropagation()}>
            <h3 style={{ color: COLORS.brown, marginBottom: 16 }}>
              💼 {assignModal.name} 담당 회원 관리
            </h3>

            {assignLoading ? (
              <p style={{ color: "#888" }}>로딩 중...</p>
            ) : (
              <>
                <div style={{ display: "flex", gap: 8, marginBottom: 12 }}>
                  <button style={btn("ghost")} onClick={() => setCheckedUserIds(new Set(allUsers.map((u) => u.user_id)))}>
                    전체 선택
                  </button>
                  <button style={btn("ghost")} onClick={() => setCheckedUserIds(new Set())}>
                    전체 해제
                  </button>
                </div>
                <div style={{ maxHeight: 400, overflow: "auto", border: "1px solid #eee", borderRadius: 8 }}>
                  {allUsers.map((u) => (
                    <label
                      key={u.user_id}
                      style={{
                        display: "flex", alignItems: "center", gap: 8,
                        padding: "8px 12px", cursor: "pointer",
                        borderBottom: "1px solid #f5f5f5",
                        background: checkedUserIds.has(u.user_id) ? "#F0FFF4" : "#fff",
                      }}
                    >
                      <input
                        type="checkbox"
                        checked={checkedUserIds.has(u.user_id)}
                        onChange={() => {
                          setCheckedUserIds((prev) => {
                            const next = new Set(prev);
                            if (next.has(u.user_id)) next.delete(u.user_id);
                            else next.add(u.user_id);
                            return next;
                          });
                        }}
                      />
                      <span style={{ flex: 1, fontSize: 14 }}>{u.nickname || u.name || "-"}</span>
                      <span style={{
                        fontSize: 11, padding: "2px 8px", borderRadius: 10,
                        background: u.user_type === "elder" ? "#FFF0E0" : u.user_type === "youth" ? "#E0E0FF" : "#EEE",
                        color: u.user_type === "elder" ? "#E8572A" : u.user_type === "youth" ? "#7B7BFF" : "#999",
                      }}>
                        {u.user_type === "elder" ? "노인" : u.user_type === "youth" ? "청년" : u.user_type}
                      </span>
                      {u.region && <span style={{ fontSize: 12, color: "#999" }}>{u.region}</span>}
                    </label>
                  ))}
                </div>
                <div style={{ fontSize: 12, color: "#888", marginTop: 8, marginBottom: 16 }}>
                  ※ 체크 = 담당 배정, 체크 해제 = 담당 해제
                </div>
                <div style={{ display: "flex", gap: 8, justifyContent: "flex-end" }}>
                  <button style={btn("ghost")} onClick={() => setAssignModal(null)}>취소</button>
                  <button
                    style={{ ...btn("primary") }}
                    onClick={handleAssignSave}
                    disabled={assignLoading}
                  >
                    {assignLoading ? "저장 중..." : "저장"}
                  </button>
                </div>
              </>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
