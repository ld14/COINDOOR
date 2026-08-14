import { useQuery } from '@tanstack/react-query';
import { getGame } from '@/lib/api/games';

export function useGame(id: string) {
  return useQuery({ queryKey: ['game', id], queryFn: () => getGame(id), retry: false });
}
