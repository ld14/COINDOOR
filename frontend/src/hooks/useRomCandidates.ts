import { useQuery } from '@tanstack/react-query';
import { listRomCandidates } from '@/lib/api/roms';

/** Sin `systemId` trae los candidatos de todos los sistemas: elegir uno cambia el
 * sistema del formulario, así que filtrar por el seleccionado escondería opciones.
 */
export function useRomCandidates() {
  return useQuery({ queryKey: ['rom-candidates'], queryFn: () => listRomCandidates() });
}
