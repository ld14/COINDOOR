import { FIELDDEFS } from '@/lib/domain/types';
import type { FieldStatus, Game } from '@/lib/domain/types';

/** Lo que trajo una precarga, para el banner "ArcadeDB trajo N datos · X aplicados · Y esperan revisión". */
export interface ResumenPrecarga {
  /** Datos que vinieron de una fuente externa (aplicados o sugeridos). */
  traidos: number;
  /** Los que ya quedaron firmes (`manual` con fuente externa, o identidad de catálogo). */
  aplicados: number;
  /** Los que esperan revisión (`suggested`). */
  pendientes: number;
  /** Fuentes distintas, en el orden en que aparecen. */
  fuentes: string[];
}

interface Dato {
  status: FieldStatus;
  source?: string;
}

const esExterna = (source?: string) => !!source && source.trim() !== '' && source.trim().toLowerCase() !== 'manual';

export function resumenPrecarga(game: Game): ResumenPrecarga {
  const datos: Dato[] = [
    ...FIELDDEFS.images.map((f) => game.images[f.key]),
    ...FIELDDEFS.videos.map((f) => game.video[f.key]),
    ...FIELDDEFS.texts.map((f) => game.texts[f.key]),
    game.review,
    game.cheats,
    { status: game.accent },
  ].filter((d): d is Dato => d !== undefined);

  let aplicados = 0;
  let pendientes = 0;
  const fuentes: string[] = [];
  const anotar = (source?: string) => {
    const nombre = source?.trim();
    if (nombre && esExterna(nombre) && !fuentes.includes(nombre)) fuentes.push(nombre);
  };

  for (const dato of datos) {
    if (dato.status === 'suggested') {
      pendientes += 1;
      anotar(dato.source);
    } else if (dato.status === 'manual' && esExterna(dato.source)) {
      aplicados += 1;
      anotar(dato.source);
    }
  }
  // La identidad de catálogo (MAME, ScreenScraper) entra firme: cada campo con valor es un dato aplicado.
  if (game.identitySource !== 'manual') {
    aplicados += FIELDDEFS.identity.filter((f) => game.identity[f.key].trim() !== '').length;
    anotar(game.identitySource);
  }
  return { traidos: aplicados + pendientes, aplicados, pendientes, fuentes };
}
