import { useQuery } from '@tanstack/react-query';
import { listGames, type GamesQuery } from '@/lib/api/games';

export function useGames(query: GamesQuery) {
  return useQuery({ queryKey: ['games', query], queryFn: () => listGames(query) });
}
