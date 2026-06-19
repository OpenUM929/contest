// src/api/admin.ts
import axios from "axios";

const API = import.meta.env.VITE_API_URL || "http://localhost:8000";
const base = `${API}/api/admin`;

// ── 타입 ──
export interface AdminUser {
  user_id: string;
  user_type: "elder" | "youth";
  name: string | null;
  nickname: string | null;
  status: "active" | "dormant" | "withdrawn";
  phone: string | null;
  email: string | null;
  region: string | null;
  welfare_id: string | null;
  welfare_name: string | null;
  note: string | null;
  last_seen: string | null;
  created_at: string | null;
  updated_at: string | null;
}

export interface AdminWorker {
  welfare_id: string;
  name: string;
  region: string | null;
  email: string | null;
  phone: string | null;
  role: "admin" | "worker";
  status: "active" | "inactive";
  note: string | null;
  active_user_count: number | null;
  created_at: string | null;
  updated_at: string | null;
}

export interface AdminLog {
  id: string;
  admin_id: string;
  action: string;
  target_type: string;
  target_id: string;
  payload: any;
  created_at: string | null;
}

export interface Paged<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface AdminDashboardData {
  stats: {
    total_users: number;
    elder: number;
    youth: number;
    workers: number;
    unresolved_alerts: number;
  };
  recent_logs: {
    id: string;
    action: string;
    target_type: string;
    target_id: string;
    created_at: string | null;
  }[];
}

// ── 회원 ──
export const listUsers = (params: Record<string, any>) =>
  axios.get<Paged<AdminUser>>(`${base}/users`, { params });
export const createUser = (data: any) => axios.post<AdminUser>(`${base}/users`, data);
export const updateUser = (id: string, data: any) => axios.patch<AdminUser>(`${base}/users/${id}`, data);
export const deleteUser = (id: string) => axios.delete(`${base}/users/${id}`);
export const assignWorker = (id: string, welfareId: string | null) =>
  axios.post(`${base}/users/${id}/assign`, { welfare_id: welfareId });

// ── 복지사 ──
export const listWorkers = (params: Record<string, any>) =>
  axios.get<Paged<AdminWorker>>(`${base}/workers`, { params });
export const createWorker = (data: any) => axios.post<AdminWorker>(`${base}/workers`, data);
export const updateWorker = (id: string, data: any) => axios.patch<AdminWorker>(`${base}/workers/${id}`, data);
export const deleteWorker = (id: string) => axios.delete(`${base}/workers/${id}`);
export const getWorkerUsers = (welfareId: string, params?: Record<string, any>) =>
  axios.get<Paged<AdminUser>>(`${base}/workers/${welfareId}/users`, { params });
export const assignWorkerUsers = (welfareId: string, user_ids: string[]) =>
  axios.post(`${base}/workers/${welfareId}/assign`, { user_ids });
export const unassignWorkerUsers = (welfareId: string, user_ids: string[]) =>
  axios.post(`${base}/workers/${welfareId}/unassign`, { user_ids });

// ── 로그 / 대시보드 ──
export const listLogs = (params: Record<string, any>) =>
  axios.get<Paged<AdminLog>>(`${base}/logs`, { params });
export const fetchAdminDashboard = () => axios.get<AdminDashboardData>(`${base}/dashboard`);
