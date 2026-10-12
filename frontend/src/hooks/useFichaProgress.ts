import { useMemo } from 'react';
import type { PendingItem, StepNavItem, StepStatus } from '@/components/dos';
import { missingRequired } from '@/lib/domain/completeness';
import { FIELDDEFS } from '@/lib/domain/types';
import type { Game } from '@/lib/domain/types';

/**
 * Qué falta en una ficha y en qué orden conviene atenderlo.
 *
 * Es lo único que decide los números de la cabecera (porcentaje, píldoras "Para exportar
 * falta:"), el estado de cada paso del StepNav, la cola de "Siguiente pendiente" y el
 * contador de la ActionBar. Combina tres fuentes que ya existen y no inventa reglas:
 *  - `missingRequired()` (lib/domain/completeness): los obligatorios vacíos del contrato.
 *  - `game.guiaChecklist`: lo que el backend marca como requerido en «Cómo se juega».
 *  - los campos con `status: 'suggested'`: lo que el sistema propuso y nadie revisó.
 */

export type SeccionClave =
  | 'identidad'
  | 'imagenes'
  | 'video'
  | 'textos'
  | 'guia'
  | 'trucos'
  | 'presentacion'
  | 'galeria'
  | 'resena'
  | 'manual';

export interface SeccionDef {
  clave: SeccionClave;
  /** Rótulo corto del paso en el StepNav. */
  label: string;
}

/** Orden y numeración de DESIGN_SPEC §5.1, con Presentación en 2.º lugar por pedido posterior (el Gabinete vive en la columna lateral y no es un paso). */
export const FICHA_SECCIONES: readonly SeccionDef[] = [
  { clave: 'identidad', label: 'Identidad' },
  { clave: 'presentacion', label: 'Presentación' },
  { clave: 'imagenes', label: 'Imágenes' },
  { clave: 'galeria', label: 'Galería' },
  { clave: 'video', label: 'Video' },
  { clave: 'textos', label: 'Textos' },
  { clave: 'resena', label: 'Reseña' },
  { clave: 'guia', label: 'Cómo se juega' },
  { clave: 'trucos', label: 'Trucos' },
  { clave: 'manual', label: 'Manual y revistas' },
];

/** `id` del contenedor de cada sección en el DOM. Es el ancla estable que usan StepNav, píldoras y atajos. */
export const anclaSeccion = (clave: string) => `seccion-${clave}`;

export interface PendienteFicha extends PendingItem {
  /** Sección donde se atiende. */
  seccion: SeccionClave;
  /** Clave del campo: la sección la expone como `data-campo="<clave>"` para que el scroll caiga en el control. */
  campo?: string;
  /** Rótulos accesibles con los que buscar el control si la sección todavía no expone `data-campo`. */
  etiquetas: string[];
  /** Clave de API para aceptar la sugerencia (`POST /games/{id}/fields/{clave}/accept`). Solo en sugerencias. */
  aceptarClave?: string;
}

export interface SeccionProgreso {
  clave: SeccionClave;
  label: string;
  numero: number;
  status: StepStatus;
  /** "2 obligatorios" / "5 sugeridos"; vacío si no hay nada pendiente. */
  hint?: string;
  obligatorios: PendienteFicha[];
  sugeridos: PendienteFicha[];
}

export interface FichaProgress {
  /** Obligatorios cubiertos sobre el total, 0–100. 100 = lista para exportar (salvo errores de formato). */
  percent: number;
  totalObligatorios: number;
  /** Obligatorios que bloquean la exportación, en el orden de las secciones. */
  faltantes: PendienteFicha[];
  /** Sugerencias esperando revisión. */
  sugerencias: PendienteFicha[];
  /** Cola de "siguiente pendiente": obligatorios (rojo) primero, después revisiones. */
  cola: PendienteFicha[];
  secciones: SeccionProgreso[];
}

const VACIO: FichaProgress = {
  percent: 0,
  totalObligatorios: 0,
  faltantes: [],
  sugerencias: [],
  cola: [],
  secciones: FICHA_SECCIONES.map((s, i) => ({ ...s, numero: i + 1, status: 'current', obligatorios: [], sugeridos: [] })),
};

type Destino = Pick<PendienteFicha, 'seccion' | 'campo' | 'etiquetas'>;

/** Cada cadena que puede devolver `missingRequired()` → dónde se corrige. Se arma desde fielddefs.json. */
function destinosDeFaltantes(): Map<string, Destino> {
  const mapa = new Map<string, Destino>();
  for (const f of FIELDDEFS.identity) mapa.set(`Identidad: ${f.label}`, { seccion: 'identidad', campo: f.key, etiquetas: [f.label] });
  for (const f of FIELDDEFS.images) mapa.set(f.label, { seccion: 'imagenes', campo: f.key, etiquetas: [f.label, `Cargar ${f.label}`] });
  for (const f of FIELDDEFS.videos) mapa.set(f.label, { seccion: 'video', campo: f.key, etiquetas: [f.label, `Cargar ${f.label}`] });
  for (const f of FIELDDEFS.texts) mapa.set(f.label, { seccion: 'textos', campo: f.key, etiquetas: [f.label] });
  for (const f of FIELDDEFS.rich) {
    if (f.key === 'accent') mapa.set(`Presentación: ${f.label}`, { seccion: 'presentacion', campo: 'accent', etiquetas: [f.label] });
  }
  return mapa;
}
const DESTINOS_FALTANTES = destinosDeFaltantes();

const GUIA_KEYS = new Set<string>(['objetivo', 'primerosPasos', 'reglasEsenciales', 'modo']);

function sinParentesis(label: string): string {
  return label.replace(/\s*\(.*\)\s*$/, '');
}

function obligatoriosDe(game: Game): PendienteFicha[] {
  const items: PendienteFicha[] = missingRequired(game).map((texto) => {
    const destino = DESTINOS_FALTANTES.get(texto) ?? { seccion: 'identidad' as const, etiquetas: [] };
    return { id: `req:${texto}`, label: texto, severity: 'required' as const, ...destino };
  });
  for (const item of game.guiaChecklist ?? []) {
    if (!item.requerido || item.estado !== 'falta') continue;
    const campo = GUIA_KEYS.has(item.key) ? item.key : undefined;
    items.push({
      id: `req:guia:${item.key}`,
      label: `Cómo se juega: ${sinParentesis(item.label)}`,
      severity: 'required',
      seccion: 'guia',
      campo,
      etiquetas: [item.label, sinParentesis(item.label)],
    });
  }
  return items;
}

function totalObligatorios(game: Game): number {
  const contrato = FIELDDEFS.identity.filter((f) => f.required).length
    + FIELDDEFS.images.filter((f) => f.required).length
    + FIELDDEFS.videos.filter((f) => f.required).length
    + FIELDDEFS.texts.filter((f) => f.required).length
    + FIELDDEFS.rich.filter((f) => f.key === 'accent' && f.required).length;
  const guia = (game.guiaChecklist ?? []).filter((item) => item.requerido).length;
  return contrato + guia;
}

function sugerenciasDe(game: Game): PendienteFicha[] {
  const items: PendienteFicha[] = [];
  const sumar = (seccion: SeccionClave, campo: string, label: string, aceptarClave: string, etiquetas: string[] = [label]) => {
    items.push({ id: `sug:${aceptarClave}`, label: `${label} sugerida`, severity: 'review', seccion, campo, etiquetas, aceptarClave });
  };
  for (const f of FIELDDEFS.images) {
    // Una imagen cargada cuenta como aceptada: no queda pendiente de revisión.
    const img = game.images[f.key];
    if (img?.status === 'suggested' && !img.url) sumar('imagenes', f.key, f.label, f.key, [f.label, `Cargar ${f.label}`]);
  }
  for (const f of FIELDDEFS.videos) {
    if (game.video[f.key]?.status === 'suggested') sumar('video', f.key, f.label, f.key, [f.label, `Cargar ${f.label}`]);
  }
  for (const f of FIELDDEFS.texts) {
    if (game.texts[f.key]?.status === 'suggested') sumar(GUIA_KEYS.has(f.key) ? 'guia' : 'textos', f.key, sinParentesis(f.label), f.key);
  }
  if (game.cheats.status === 'suggested') sumar('trucos', 'cheats', 'Trucos', 'cheats');
  if (game.accent === 'suggested') sumar('presentacion', 'accent', 'Color de acento', 'accent', ['Color de acento primario']);
  if (game.review.status === 'suggested') sumar('resena', 'review', 'Reseña', 'review', ['Puntaje de reseña']);
  return items;
}

/** Con la sección ya sin obligatorios faltantes: ¿alcanza para darla por completa? */
function tieneContenido(game: Game, clave: SeccionClave): boolean {
  switch (clave) {
    case 'identidad':
    case 'imagenes':
    case 'textos':
    case 'presentacion':
      return true; // su contenido es obligatorio: sin faltantes está completa
    case 'guia':
      return (game.guiaChecklist?.length ?? 0) > 0;
    case 'video':
      return Object.values(game.video).some((v) => v && v.status !== 'empty');
    case 'galeria':
      return (game.gallery?.length ?? 0) > 0;
    case 'trucos':
      return game.cheats.status !== 'empty';
    case 'resena':
      return game.review.status !== 'empty';
    case 'manual':
      return game.manuals.length > 0 || game.magazine === 'linked';
  }
}

const plural = (n: number, uno: string, varios: string) => `${n} ${n === 1 ? uno : varios}`;

export function computeFichaProgress(game: Game | undefined): FichaProgress {
  if (!game) return VACIO;
  const faltantes = obligatoriosDe(game);
  const sugerencias = sugerenciasDe(game);
  const total = totalObligatorios(game);
  const percent = total === 0 ? 100 : Math.round(((total - Math.min(total, faltantes.length)) / total) * 100);

  const secciones: SeccionProgreso[] = FICHA_SECCIONES.map((def, i) => {
    const obligatorios = faltantes.filter((p) => p.seccion === def.clave);
    const sugeridos = sugerencias.filter((p) => p.seccion === def.clave);
    let status: StepStatus = 'current';
    let hint: string | undefined;
    if (obligatorios.length > 0) {
      status = 'blocking';
      hint = plural(obligatorios.length, 'obligatorio', 'obligatorios');
    } else if (sugeridos.length > 0) {
      status = 'review';
      hint = plural(sugeridos.length, 'sugerido', 'sugeridos');
    } else if (tieneContenido(game, def.clave)) {
      status = 'complete';
    }
    return { ...def, numero: i + 1, status, hint, obligatorios, sugeridos };
  });
  const numeroDe = (clave: SeccionClave) => secciones.findIndex((s) => s.clave === clave) + 1;
  const conPaso = (items: PendienteFicha[]) => items.map((p) => ({ ...p, step: numeroDe(p.seccion) }));

  const faltantesOrdenados = conPaso(faltantes).sort((a, b) => (a.step ?? 0) - (b.step ?? 0));
  const sugerenciasOrdenadas = conPaso(sugerencias).sort((a, b) => (a.step ?? 0) - (b.step ?? 0));
  return {
    percent,
    totalObligatorios: total,
    faltantes: faltantesOrdenados,
    sugerencias: sugerenciasOrdenadas,
    cola: [...faltantesOrdenados, ...sugerenciasOrdenadas],
    secciones,
  };
}

export function useFichaProgress(game: Game | undefined): FichaProgress {
  return useMemo(() => computeFichaProgress(game), [game]);
}

/** Pasos para el StepNav a partir del progreso. */
export function stepsDe(progress: FichaProgress): StepNavItem[] {
  return progress.secciones.map((s) => ({ id: s.clave, label: s.label, status: s.status, hint: s.hint }));
}
