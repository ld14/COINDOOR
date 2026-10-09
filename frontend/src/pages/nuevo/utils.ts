import type { System, Tratamiento } from '@/lib/domain/types';
import { soportaArcadeDb } from '@/lib/domain/arcade';

const UNIDADES = ['B', 'KB', 'MB', 'GB'];

/** `21 MB`, `4,0 KB`…; vacío si no hay tamaño conocido. */
export function tamano(bytes: number): string {
  if (bytes <= 0) return '';
  let valor = bytes;
  let unidad = 0;
  while (valor >= 1024 && unidad < UNIDADES.length - 1) {
    valor /= 1024;
    unidad += 1;
  }
  const redondeado = valor < 10 && unidad > 0 ? valor.toFixed(1) : String(Math.round(valor));
  return `${redondeado} ${UNIDADES[unidad]}`;
}

const CARPETAS_MSDOS = new Set(['msdos', 'ms-dos', 'dos', 'pc', 'windows']);

export interface Deteccion {
  /** Carpeta que disparó la propuesta (`mame`, `ms-dos`…). */
  carpeta: string;
  systemId: string;
  tratamiento: Tratamiento;
}

/**
 * Propone sistema y tratamiento mirando las carpetas de la ruta:
 * `mame/` → Arcade + Copiar (romset), `ms-dos/` → MS-DOS + Descomprimir.
 * Sólo propone sistemas que existen en `sistemas.json`; si no, devuelve null.
 */
export function detectarPorCarpeta(ruta: string, sistemas: System[]): Deteccion | null {
  const carpetas = ruta.split(/[\\/]+/).slice(0, -1).map((parte) => parte.trim().toLowerCase()).filter(Boolean);
  for (const carpeta of [...carpetas].reverse()) {
    if (soportaArcadeDb(carpeta)) {
      const sistema = sistemas.find((s) => soportaArcadeDb(s.id));
      if (sistema) return { carpeta, systemId: sistema.id, tratamiento: 'copiar' };
    }
    if (CARPETAS_MSDOS.has(carpeta)) {
      const sistema = sistemas.find((s) => CARPETAS_MSDOS.has(s.id.toLowerCase()));
      if (sistema) return { carpeta, systemId: sistema.id, tratamiento: 'descomprimir' };
    }
  }
  return null;
}
