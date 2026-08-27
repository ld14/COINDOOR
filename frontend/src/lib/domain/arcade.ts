import arcadeSystems from './arcade-systems.json';

/** ¿Los juegos de este sistema son romsets MAME? Sólo esos existen en ArcadeDB.
 *
 * El criterio es el nombre del sistema, que lo elige el usuario: si nombra uno
 * fuera de `arcade-systems.json` la precarga no se ofrece y la ficha queda
 * manual. Agregar el marcador ahí lo habilita en backend y frontend a la vez.
 */
export function soportaArcadeDb(systemId: string): boolean {
  const nombre = systemId.toLowerCase();
  return arcadeSystems.markers.some((marker) => nombre.includes(marker));
}
