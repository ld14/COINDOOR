import type { Game, ImageKey } from '@/lib/domain/types';
import { fetchJson } from './client';

export interface GalleryCandidate {
  id: string;
  tipo: string | null;
  label: string;
  url: string;
  previewUrl?: string;
  origenUrl?: string;
  delPadre: boolean;
  yaGuardada: boolean;
  source: string;
}

export function listGalleryCandidates(gameId: string, source?: string) {
  const params = source ? `?source=${encodeURIComponent(source)}` : '';
  return fetchJson<GalleryCandidate[]>(`/games/${gameId}/gallery/candidates${params}`);
}

export interface GuardarGaleriaItem {
  tipo?: string | null;
  url?: string | null;
  source?: string;
}

export function saveGallery(gameId: string, items: GuardarGaleriaItem[]) {
  return fetchJson<{ jobId: string }>(`/games/${gameId}/gallery`, {
    method: 'POST',
    body: JSON.stringify({ items }),
  });
}

export function useGalleryImageAs(gameId: string, imageId: string, campo: ImageKey) {
  return fetchJson<Game>(`/games/${gameId}/gallery/${imageId}/use-as/${campo}`, { method: 'POST' });
}

export function deleteGalleryImage(gameId: string, imageId: string) {
  return fetchJson<Game>(`/games/${gameId}/gallery/${imageId}`, { method: 'DELETE' });
}
