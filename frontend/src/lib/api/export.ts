import { fetchJson } from './client';

export interface ExportOption {
  key: string;
  label: string;
  required: boolean;
  disponible: boolean;
  bytes: number;
}

export interface ExportOptions {
  obligatorio: ExportOption[];
  opcional: ExportOption[];
}

export interface ExportJob {
  runId: string;
}

export interface ExportResult {
  file: string;
  bytes: number;
  incluye: string[];
  verificado: Record<string, unknown>;
}

export interface JobOut {
  jobId: string;
  status: string;
  progress: number;
  result: ExportResult | null;
  error: string | null;
}

export function getExportOptions(gameId: string) {
  return fetchJson<ExportOptions>(`/games/${gameId}/export-options`);
}

export function createExport(gameId: string, incluir: string[]) {
  return fetchJson<ExportJob>('/export', {
    method: 'POST',
    body: JSON.stringify({ gameId, incluir }),
  });
}

export function getExportStatus(runId: string) {
  return fetchJson<JobOut>(`/export/${runId}`);
}
