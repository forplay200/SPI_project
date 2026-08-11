import type {
  Analysis,
  Approval,
  Draft,
  EDL,
  EvidenceItem,
  Job,
  Project,
  SyncReport,
} from "./types";

const API_ROOT = import.meta.env.VITE_API_ROOT ?? "/api";

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API_ROOT}${path}`, {
    ...options,
    headers: { "Content-Type": "application/json", ...options?.headers },
  });
  if (!response.ok) {
    const body = await response
      .json()
      .catch(() => ({ detail: response.statusText }));
    throw new Error(body.detail ?? `Request failed (${response.status})`);
  }
  if (response.status === 204) return undefined as T;
  return response.json() as Promise<T>;
}

export const api = {
  health: () => request<{ status: string; local_only: boolean }>("/health"),
  createProject: (payload: Record<string, unknown>) =>
    request<Project>("/projects", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  getProject: (id: string) => request<Project>(`/projects/${id}`),
  updateProject: (id: string, payload: Partial<Project>) =>
    request<Project>(`/projects/${id}`, {
      method: "PUT",
      body: JSON.stringify(payload),
    }),
  startAnalysis: (id: string) =>
    request<Job>(`/projects/${id}/analysis`, { method: "POST" }),
  getAnalysis: (id: string) => request<Analysis>(`/projects/${id}/analysis`),
  selectCameras: (
    id: string,
    camera_ids: string[],
    master_camera: string,
    continue_with_human_verification = false,
  ) =>
    request<Record<string, unknown>>(`/projects/${id}/camera-group`, {
      method: "PUT",
      body: JSON.stringify({
        camera_ids,
        master_camera,
        continue_with_human_verification,
      }),
    }),
  startSync: (id: string) =>
    request<Job>(`/projects/${id}/sync/detect`, { method: "POST" }),
  getSync: (id: string) => request<SyncReport>(`/projects/${id}/sync`),
  confirmSync: (
    id: string,
    camera_id: string,
    timestamp_seconds: number,
    acknowledge_sync_risk = false,
  ) =>
    request<SyncReport>(`/projects/${id}/sync/confirm`, {
      method: "POST",
      body: JSON.stringify({
        camera_id,
        timestamp_seconds,
        acknowledge_sync_risk,
      }),
    }),
  rejectSync: (
    id: string,
    camera_id: string,
    timestamp_seconds: number | undefined,
    reason: string,
  ) =>
    request<SyncReport>(`/projects/${id}/sync/reject`, {
      method: "POST",
      body: JSON.stringify({
        camera_id,
        timestamp_seconds,
        reason,
      }),
    }),
  startEdl: (id: string) =>
    request<Job>(`/projects/${id}/edl/generate`, { method: "POST" }),
  getEdl: (id: string) => request<EDL>(`/projects/${id}/edl`),
  updateEdl: (id: string, edl: EDL) =>
    request<{ valid: boolean; errors: string[]; edl: EDL }>(
      `/projects/${id}/edl`,
      { method: "PUT", body: JSON.stringify(edl) },
    ),
  validateEdl: (id: string) =>
    request<{ valid: boolean; errors: string[] }>(
      `/projects/${id}/edl/validate`,
      { method: "POST" },
    ),
  startRender: (id: string) =>
    request<Job>(`/projects/${id}/render`, { method: "POST" }),
  getDraft: (id: string) => request<Draft>(`/projects/${id}/draft`),
  getJob: (id: string) => request<Job>(`/jobs/${id}`),
  cancelJob: (id: string) =>
    request<Job>(`/jobs/${id}/cancel`, { method: "POST" }),
  submitReview: (id: string, payload: Record<string, unknown>) =>
    request<Record<string, unknown>>(`/projects/${id}/review`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  getReview: (id: string) =>
    request<Record<string, unknown>>(`/projects/${id}/review`),
  getApproval: (id: string) => request<Approval>(`/projects/${id}/approval`),
  approve: (id: string) =>
    request<Record<string, unknown>>(`/projects/${id}/approve`, {
      method: "POST",
    }),
  listEvidence: (id: string) =>
    request<EvidenceItem[]>(`/projects/${id}/evidence`),
  getEvidence: (id: string, evidenceId: string) =>
    request<Record<string, unknown>>(`/projects/${id}/evidence/${evidenceId}`),
  mediaUrl: (id: string) => `${API_ROOT}/projects/${id}/draft/media`,
  cueUrl: (id: string, cameraId: string) =>
    `${API_ROOT}/projects/${id}/sync/preview/${cameraId}`,
  downloadUrl: (id: string, fileId: string) =>
    `${API_ROOT}/projects/${id}/files/${fileId}`,
};
