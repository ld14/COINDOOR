import type { CheatsField, Game, ReviewField, TextKey } from '@/lib/domain/types';
import { fetchJson } from './client';

export function setTextField(gameId: string, key: TextKey, value: string) {
  return fetchJson<Game>(`/games/${gameId}/fields/${key}`, {
    method: 'PUT',
    body: JSON.stringify({ value }),
  });
}

export function deleteField(gameId: string, key: string) {
  return fetchJson<Game>(`/games/${gameId}/fields/${key}`, { method: 'DELETE' });
}

export function setReview(gameId: string, review: Pick<ReviewField, 'score' | 'cats'>) {
  return fetchJson<Game>(`/games/${gameId}/fields/review`, {
    method: 'PUT',
    body: JSON.stringify(review),
  });
}

export function setCheats(gameId: string, cheats: Pick<CheatsField, 'groups'>) {
  return fetchJson<Game>(`/games/${gameId}/fields/cheats`, {
    method: 'PUT',
    body: JSON.stringify(cheats),
  });
}
