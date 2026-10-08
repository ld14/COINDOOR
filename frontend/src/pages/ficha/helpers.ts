import { FIELDDEFS } from '@/lib/domain/types';
import type { Game, IdentityKey, ImageKey, TextKey } from '@/lib/domain/types';

export const MANUAL_DELETE_CONFIRM = 'Este campo fue cargado a mano. ¿Borrarlo de todas formas?';

export function confirmManualDelete(status: string, action: () => void) {
  if (status === 'manual' && !window.confirm(MANUAL_DELETE_CONFIRM)) return;
  action();
}

export const SUGGESTABLE_LABELS: Record<string, string> = {
  ...Object.fromEntries(FIELDDEFS.identity.map((field) => [field.key, field.label])),
  ...Object.fromEntries(FIELDDEFS.images.map((field) => [field.key, field.label])),
  sinopsis: 'Sinopsis',
  objetivo: 'Objetivo',
  primerosPasos: 'Primeros pasos',
  reglasEsenciales: 'Reglas esenciales',
  modo: 'Modo multijugador',
  review: 'Reseña',
  cheats: 'Trucos',
  video: 'Video de gameplay',
};

export function isIdentityKey(key: string): key is IdentityKey {
  return FIELDDEFS.identity.some((field) => field.key === key);
}

export interface SuggestionCurrent {
  hasContent: boolean;
  isManual: boolean;
  previewUrl?: string | null;
  value?: string | null;
}

export function suggestionStatus(game: Game, key: string): SuggestionCurrent {
  if (isIdentityKey(key)) {
    const value = game.identity[key];
    return { hasContent: value !== '', isManual: game.identitySource === 'manual', value };
  }
  if (FIELDDEFS.images.some((f) => f.key === key)) {
    const img = game.images[key as ImageKey];
    return { hasContent: img?.status !== 'empty', isManual: img?.status === 'manual', previewUrl: img?.url };
  }
  if (FIELDDEFS.texts.some((field) => field.key === key)) {
    const t = game.texts[key as TextKey] ?? { status: 'empty', value: '' };
    return { hasContent: t.value !== '', isManual: t.status === 'manual', value: t.value };
  }
  if (key === 'review') {
    return { hasContent: game.review.status !== 'empty', isManual: game.review.status === 'manual' };
  }
  if (key === 'cheats') {
    const c = game.cheats;
    const value = c.groups.length > 0 ? JSON.stringify({ groups: c.groups.map(g => ({ name: g.name, entries: g.entries })) }) : '';
    return { hasContent: c.status !== 'empty', isManual: c.status === 'manual', value };
  }
  const v = game.video.video;
  return { hasContent: v.status !== 'empty', isManual: v.status === 'manual', previewUrl: v.url };
}

export function summary(game: Game, missing: string[]) {
  if (game.errors.length) return `${game.errors.length} error(es) de formato`;
  if (missing.length) return `${missing.length} campo(s) faltante(s)`;
  return 'Completo';
}
