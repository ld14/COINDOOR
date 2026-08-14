import type { Game } from '@/lib/domain/types';
import { fetchJson } from './client';

export type CandidateClass = 'aplicable' | 'referencia';
export type CandidateKind = 'identity' | 'media' | 'text';

export interface SuggestionTrace {
  nombre: string;
  tipo: string;
  estado: string;
  urlsProcesadas: unknown[];
  datosObtenidos: string[];
}

export interface SuggestionCandidate {
  id: string;
  key: string;
  kind: CandidateKind;
  nombre: string;
  fuente: string;
  clase: CandidateClass;
  value: string | null;
  previewUrl: string | null;
  mediaUrl: string | null;
  origenUrl: string | null;
  generadoPorIa: boolean;
  meta: Record<string, string>;
  trace: SuggestionTrace | null;
}

export interface SuggestionsResult {
  candidatos: SuggestionCandidate[];
  respondieron: number;
  consultados: number;
  fuentes: SuggestionTrace[];
}

export function createSuggestionJob(gameId: string, key: string, reintentar = false) {
  const suffix = reintentar ? '?reintentar=true' : '';
  return fetchJson<{ jobId: string }>(`/games/${gameId}/fields/${key}/suggestions${suffix}`, {
    method: 'POST',
  });
}

export function applySuggestion(gameId: string, key: string, candidateId: string) {
  return fetchJson<Game>(`/games/${gameId}/fields/${key}/apply-suggestion`, {
    method: 'POST',
    body: JSON.stringify({ candidateId }),
  });
}
