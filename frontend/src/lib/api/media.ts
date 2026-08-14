import type { Game, ImageKey, VideoKey } from '@/lib/domain/types';
import { fetchJson } from './client';

export function uploadMedia(gameId: string, key: ImageKey | VideoKey, file: File) {
  const body = new FormData();
  body.append('file', file);
  return fetchJson<Game>(`/games/${gameId}/media/${key}`, { method: 'PUT', body });
}
