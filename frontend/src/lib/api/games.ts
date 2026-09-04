import type { Game, GameStatus, Identity, RomSource } from '@/lib/domain/types';
import { fetchJson } from './client';

export interface GamesQuery {
  q?: string;
  systemId?: string;
  status?: GameStatus | '';
  page?: number;
  perPage?: number;
}

export interface GameSummary {
  id: string;
  title: string;
  year: string;
  systemName: string;
  identitySource: Game['identitySource'];
  status: GameStatus;
  coverThumbUrl?: string | null;
}

export interface GamesPage {
  items: GameSummary[];
  page: number;
  perPage: number;
  total: number;
}

export function listGames(query: GamesQuery = {}) {
  const params = new URLSearchParams();
  if (query.q) params.set('q', query.q);
  if (query.systemId) params.set('systemId', query.systemId);
  if (query.status) params.set('status', query.status);
  if (query.page) params.set('page', String(query.page));
  if (query.perPage) params.set('perPage', String(query.perPage));
  const suffix = params.toString() ? `?${params}` : '';
  return fetchJson<GamesPage>(`/games${suffix}`);
}

export interface CreateGamePayload {
  systemId: string;
  romSource: RomSource;
  romRef: string;
  file_format: string;
  tratamiento: string;
  identity: Identity;
}

export function getGame(id: string) {
  return fetchJson<Game>(`/games/${id}`);
}

export function createGame(payload: CreateGamePayload) {
  return fetchJson<Game>('/games', { method: 'POST', body: JSON.stringify(payload) });
}

export function patchGame(id: string, payload: Partial<Pick<Game, 'systemId' | 'identity' | 'romRef' | 'file_format' | 'tratamiento' | 'accent' | 'accentValue' | 'accent2Value'>>) {
  return fetchJson<Game>(`/games/${id}`, { method: 'PATCH', body: JSON.stringify(payload) });
}

export function markReady(id: string) {
  return fetchJson<Game>(`/games/${id}/mark-ready`, { method: 'POST' });
}

export function uploadRom(id: string, file: File) {
  const formData = new FormData();
  formData.append('file', file);
  return fetchJson<Game>(`/games/${id}/rom`, { method: 'POST', body: formData });
}

export interface PrecargaResult {
  jobId: string;
}

export function startPrecarga(id: string, force: boolean = false) {
  const params = force ? '?force=true' : '';
  return fetchJson<PrecargaResult>(`/games/${id}/arcadedb${params}`, { method: 'POST' });
}

export function startPrecargaMsdos(id: string, force: boolean = false) {
  const params = force ? '?force=true' : '';
  return fetchJson<PrecargaResult>(`/games/${id}/msdos${params}`, { method: 'POST' });
}
