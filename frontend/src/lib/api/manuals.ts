import type { Game } from '@/lib/domain/types';
import { fetchJson } from './client';

export interface ManualSearchResult {
  title: string;
  url: string;
  source: string;
}

export function uploadManual(gameId: string, file: File): Promise<Game> {
  const body = new FormData();
  body.append('file', file);
  return fetchJson<Game>(`/games/${gameId}/manuals`, { method: 'POST', body });
}

export function deleteManual(gameId: string, manualId: string): Promise<Game> {
  return fetchJson<Game>(`/games/${gameId}/manuals/${manualId}`, { method: 'DELETE' });
}

export function searchManuals(gameId: string): Promise<ManualSearchResult[]> {
  return fetchJson<ManualSearchResult[]>(`/games/${gameId}/manuals/search`);
}
