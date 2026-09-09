import { fetchJson } from './client';

/** Un juego instalado en `games/juegos/<sistema>/` que todavía no tiene ficha.
 *
 * No es una entidad del store: el backend lo calcula leyendo el disco en cada
 * pedido. Seleccionarlo solo precarga el formulario; nada se escribe hasta el alta.
 */
export interface RomCandidate {
  id: string;
  systemId: string;
  name: string;
  title: string;
  path: string;
  kind: 'file' | 'dir';
  file_format: string;
  tratamiento: string;
  sizeBytes: number;
}

export function listRomCandidates(systemId: string = '') {
  const suffix = systemId ? `?systemId=${encodeURIComponent(systemId)}` : '';
  return fetchJson<RomCandidate[]>(`/roms/candidates${suffix}`);
}
