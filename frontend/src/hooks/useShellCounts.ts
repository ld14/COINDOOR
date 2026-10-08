import type { RailCounts } from '@/components/dos';
import { useGames } from '@/hooks/useGames';
import { useRomCandidates } from '@/hooks/useRomCandidates';
import { useSystems } from '@/hooks/useSystems';

/** Contadores del Rail. Cada uno queda `undefined` hasta que su pedido responde, así
 * el Rail no muestra un "0" que en realidad es "todavía no sé".
 */
export function useShellCounts(): RailCounts {
  const games = useGames({ perPage: 1 });
  const pending = useGames({ status: 'ready', exportStatus: 'pending', perPage: 1 });
  const systems = useSystems();
  const roms = useRomCandidates();
  return {
    games: games.data?.total,
    pendingExport: pending.data?.total,
    systems: systems.data?.length,
    romsWithoutSheet: roms.data?.length,
  };
}
