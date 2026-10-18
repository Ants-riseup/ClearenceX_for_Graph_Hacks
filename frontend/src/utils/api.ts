// frontend/src/utils/api.ts
import axios from 'axios';
import type {
  UploadResponse, ShipmentStatus, DocumentExtraction,
  GraphData, Discrepancy, AuditEntry, KeyFieldResponse, CusdecReadiness,
} from '../types';
const API_BASE = import.meta.env.VITE_API_URL || '/api';
export const api = axios.create({
  baseURL: API_BASE,
  withCredentials: true,
  headers: { 'Content-Type': 'application/json' },
});
let csrfToken: string | null = null;
let csrfRequest: Promise<string> | null = null;
export async function ensureCsrf(): Promise<string> {
  if (csrfToken) return csrfToken;
  if (!csrfRequest) csrfRequest = api.get<{ csrf_token: string }>('/auth/csrf').then(({ data }) => {
    csrfToken = data.csrf_token;
    return data.csrf_token;
  }).finally(() => { csrfRequest = null; });
  return csrfRequest;
}
api.interceptors.request.use(async config => {
  if (config.method && !['get', 'head', 'options'].includes(config.method)) {
    config.headers.set('X-CSRF-Token', await ensureCsrf());
  }
  return config;
});
api.interceptors.response.use(response => response, error => {
  if (error.response?.status === 401 && !error.config?.url?.includes('/auth/login')) {
    csrfToken = null;
    window.dispatchEvent(new Event('clearancex:unauthorized'));
  }
  return Promise.reject(error);
});
export interface AuthUser { id: string; email: string; tenant_id: string; role: 'viewer' | 'reviewer' | 'admin' }
export async function signIn(email: string, password: string): Promise<AuthUser> {
  csrfToken = null;
  const { data } = await api.post('/auth/login', { email, password });
  csrfToken = data.csrf_token;
  return data.user;
}
export async function signOut() {
  await api.post('/auth/logout');
  csrfToken = null;
}
export function apiError(error: unknown, fallback = 'The request could not be completed.'): string {
  if (axios.isAxiosError(error)) {
    const detail = error.response?.data?.detail;
    return typeof detail === 'string' ? detail : fallback;
  }
  return error instanceof Error ? error.message : fallback;
}
export async function uploadShipment(files: File[], signal?: AbortSignal): Promise<UploadResponse> {
  const formData = new FormData();
  files.forEach((file) => formData.append('files', file));
  // Override the default 'application/json' header — let axios auto-generate
  // the correct 'multipart/form-data' boundary for file uploads.
  const uploadHeaders = { headers: { 'Content-Type': undefined }, signal };
  const { data } = await api.post<UploadResponse>('/upload', formData, uploadHeaders);
  return data;
}
export async function getShipmentStatus(id: string): Promise<ShipmentStatus> {
  const { data } = await api.get<ShipmentStatus>(`/shipments/${id}/status`);
  return data;
}
export async function getExtraction(id: string): Promise<{ shipment_id: string; documents: DocumentExtraction[] }> {
  const { data } = await api.get(`/shipments/${id}/extraction`);
  return data;
}
export async function getGraph(id: string, signal?: AbortSignal): Promise<GraphData> {
  const { data } = await api.get<GraphData>(`/shipments/${id}/graph`, { signal });
  return data;
}
export async function getDiscrepancies(id: string): Promise<{ shipment_id: string; total_discrepancies: number; discrepancies: Discrepancy[] }> {
  const { data } = await api.get(`/shipments/${id}/discrepancies`);
  return data;
}
export async function getKeyFields(id: string): Promise<KeyFieldResponse> {
  const { data } = await api.get<KeyFieldResponse>(`/shipments/${id}/key-fields`);
  return data;
}
export async function getAuditTrail(id: string, signal?: AbortSignal): Promise<{ shipment_id: string; total_events: number; entries: AuditEntry[] }> {
  const { data } = await api.get(`/shipments/${id}/audit-trail`, { signal });
  return data;
}
export async function exportAsycuda(id: string): Promise<Blob> {
  const { data: state } = await api.get(`/shipments/${id}/context-status`);
  const { data: artifact } = await api.post(`/shipments/${id}/exports`, { expected_revision: state.source_revision, request_id: crypto.randomUUID() });
  const { data } = await api.get(`/shipments/${id}/exports/${artifact.export_id}/content`, {
    responseType: 'blob',
  });
  return data;
}
export async function getCusdecReadiness(id: string): Promise<CusdecReadiness> {
  const { data } = await api.get<CusdecReadiness>(`/shipments/${id}/cusdec-readiness`);
  return data;
}
export async function saveDeclarationMetadata(id: string, values: Record<string, string>): Promise<CusdecReadiness> {
  const { data } = await api.post(`/shipments/${id}/declaration-metadata`, { values, expected_revision: await waitForSyncedRevision(id) });
  return data.readiness;
}
export async function saveCusdecLineItem(
  id: string,
  item: Omit<import('../types').CusdecLineItem, 'row_index'>,
): Promise<CusdecReadiness> {
  const { data } = await api.post(`/shipments/${id}/cusdec-line-items`, { ...item, expected_revision: await waitForSyncedRevision(id) });
  return data.readiness;
}
export function downloadBlob(blob: Blob, filename: string) {
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url; a.download = filename;
  document.body.appendChild(a);
  a.click(); a.remove();
  window.URL.revokeObjectURL(url);
}
export interface DossierSummary { export_allowed?: boolean; readiness_status?: string; blocker_count?: number; dossier_id: string; title: string; status: string; created_at: string | null; document_count: number; revision: number; graph_revision: number; documents: { document_id: string; original_name: string; document_type: string | null; status: string }[] }
export async function listDossiers(params?: { search?: string; status?: string; offset?: number; limit?: number; sort?: string }, signal?: AbortSignal): Promise<{ dossiers: DossierSummary[]; total: number; offset: number; limit: number; has_more: boolean }> {
  const { data } = await api.get('/dossiers', { params, signal });
  return data;
}

export interface RuleCheck {
  id: string;
  label: string;
  description: string;
  status: string;
}

export async function getActiveRules(): Promise<RuleCheck[]> {
  const { data } = await api.get<RuleCheck[]>('/rules/active');
  return data;
}
export async function saveFieldResolution(
  shipmentId: string,
  resolution: {
    canonical_field_id: string;
    source_assertion_id?: string;
    manual_value?: string;
    reason?: string;
  },
): Promise<{ status: string; field: import('../types').ResolvedKeyField }> {
  const { data: context } = await api.get(`/shipments/${shipmentId}/context-status`);
  const { data } = await api.post(`/shipments/${shipmentId}/field-resolutions`, {
    ...resolution, expected_revision: context.source_revision, request_id: crypto.randomUUID(),
  });
  return data;
}

export async function waitForSyncedRevision(id: string, signal?: AbortSignal): Promise<number> {
  for (let attempt = 0; attempt < 60; attempt++) {
    if (signal?.aborted) throw new DOMException('Request cancelled', 'AbortError');
    const { data } = await api.get(`/shipments/${id}/context-status`, { signal });
    if (data.status === 'synced') return data.source_revision;
    await new Promise<void>(resolve => window.setTimeout(resolve, 300));
  }
  throw new Error('Graph synchronization is still pending. Retry once the dossier is synced.');
}
