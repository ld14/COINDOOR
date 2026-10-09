import fielddefs from '@/lib/domain/fielddefs.json';
import { missingRequired } from '@/lib/domain/completeness';
import type { Game } from '@/lib/domain/types';

/** Cantidad de obligatorios de la política (mismos que cuenta `missingRequired`). */
export const TOTAL_OBLIGATORIOS =
  [...fielddefs.identity, ...fielddefs.images, ...fielddefs.videos, ...fielddefs.texts].filter((field) => field.required).length
  + fielddefs.rich.filter((field) => field.key === 'accent' && field.required).length;

export interface Progreso {
  faltan: number;
  porcentaje: number;
  /** Lo que falta, para el texto de la banda. */
  faltantes: string[];
}

export function progresoDe(game: Game): Progreso {
  const faltantes = missingRequired(game);
  const total = Math.max(TOTAL_OBLIGATORIOS, faltantes.length, 1);
  return { faltan: faltantes.length, porcentaje: Math.round(((total - faltantes.length) / total) * 100), faltantes };
}

export function iniciales(title: string): string {
  return title.split(' ').map((part) => part[0]).join('').slice(0, 3).toUpperCase();
}

/** Color estable derivado del título (tono HSL), para la carátula sin imagen. */
export function colorDeTitulo(title: string): string {
  let hash = 0;
  for (const char of title) hash = (hash * 31 + char.charCodeAt(0)) % 360;
  return `hsl(${hash} 50% 34%)`;
}
