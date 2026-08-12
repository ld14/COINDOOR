import fielddefs from './fielddefs.json';
import type { Game, GameStatus } from './types';

export function missingRequired(game: Game): string[] {
  const missing: string[] = [];

  for (const field of fielddefs.identity) {
    if (field.required && !game.identity[field.key].trim()) missing.push(`Identidad: ${field.label}`);
  }

  for (const field of fielddefs.images) {
    if (field.required && game.images[field.key].status === 'empty') missing.push(field.label);
  }

  for (const field of fielddefs.videos) {
    if (field.required && game.video[field.key].status === 'empty') missing.push(field.label);
  }

  for (const field of fielddefs.texts) {
    if (field.required && game.texts[field.key].status === 'empty') missing.push(field.label);
  }

  for (const field of fielddefs.rich) {
    if (field.key === 'accent' && field.required && game.accent === 'empty') missing.push(`Presentación: ${field.label}`);
  }

  return missing;
}

export function computeGameStatus(game: Game): GameStatus {
  if (game.errors.length > 0) return 'error';
  if (missingRequired(game).length > 0) return 'incomplete';
  return 'ready';
}
