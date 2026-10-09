import type { ExportOption, ExportOptions, JobOut } from '@/lib/api/export';
import { getExportStatus } from '@/lib/api/export';

export type GrupoId = 'siempre' | 'guia' | 'media' | 'extras';

export interface GrupoDef {
  id: GrupoId;
  titulo: string;
  banda: string;
  ayuda?: string;
}

export const GRUPOS: readonly GrupoDef[] = [
  { id: 'siempre', titulo: 'Siempre incluido', banda: 'var(--accent-3)', ayuda: 'obligatorio para ATTRACT' },
  { id: 'guia', titulo: 'Guía “Cómo se juega”', banda: 'var(--accent)' },
  { id: 'media', titulo: 'Media opcional', banda: 'var(--accent-2)' },
  { id: 'extras', titulo: 'Extras', banda: 'var(--warn)' },
];

const CLAVES_GUIA = new Set(['objetivo', 'primerosPasos', 'reglasEsenciales', 'modo']);
const CLAVES_MEDIA = new Set(['caratula', 'marquesina', 'poster', 'logo', 'captura', 'video', 'galeria']);

/** Lo opcional se reparte por clave; lo que no se conoce cae en Extras. */
export function grupoDe(opt: ExportOption): GrupoId {
  if (opt.required) return 'siempre';
  if (CLAVES_GUIA.has(opt.key)) return 'guia';
  if (CLAVES_MEDIA.has(opt.key)) return 'media';
  return 'extras';
}

export function todas(options: ExportOptions): ExportOption[] {
  return [...options.obligatorio, ...options.opcional];
}

/** Lo obligatorio y lo opcional que tiene datos viene tildado; lo vacío, no. */
export function seleccionInicial(options: ExportOptions): Set<string> {
  return new Set([
    ...options.obligatorio.map((o) => o.key),
    ...options.opcional.filter((o) => o.disponible).map((o) => o.key),
  ]);
}

/** Claves opcionales con datos: lo que se manda como `incluir`. */
export function opcionalesDisponibles(options: ExportOptions): string[] {
  return options.opcional.filter((o) => o.disponible).map((o) => o.key);
}

export function motivoNoDisponible(opt: ExportOption): string {
  if (opt.motivo) return opt.motivo;
  if (opt.required) return 'falta el archivo';
  return opt.key === 'cheats' ? 'no hay trucos' : 'sin cargar';
}

export function resumen(items: ExportOption[], selected: ReadonlySet<string>) {
  const elegidos = items.filter((o) => selected.has(o.key));
  return { elegidos: elegidos.length, total: items.length, bytes: elegidos.reduce((sum, o) => sum + o.bytes, 0) };
}

export function formatBytes(bytes: number): string {
  if (bytes === 0) return '0 B';
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export type Etapa = 'armando' | 'verificando' | 'resultado';

/** El backend avanza 20 al armar, 50 al verificar y 80 al empaquetar. */
export function etapaDe(progress: number): Etapa {
  if (progress >= 80) return 'resultado';
  if (progress >= 50) return 'verificando';
  return 'armando';
}

/** Espera a que termine un export; rechaza con el motivo si falla. */
export async function esperarExport(
  runId: string,
  onProgress?: (progress: number) => void,
  pausaMs = 500,
  cancelado: () => boolean = () => false,
): Promise<NonNullable<JobOut['result']>> {
  while (!cancelado()) {
    const job = await getExportStatus(runId);
    if (cancelado()) break;
    onProgress?.(job.progress);
    if (job.status === 'succeeded') {
      if (!job.result) throw new Error('El export terminó sin resultado');
      return job.result;
    }
    if (job.status === 'failed') throw new Error(job.error || 'Error desconocido');
    await new Promise((resolve) => setTimeout(resolve, pausaMs));
  }
  throw new Error('Export cancelado');
}
