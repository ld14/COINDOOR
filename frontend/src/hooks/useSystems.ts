import { useQuery } from '@tanstack/react-query';
import { listSystems } from '@/lib/api/systems';

export function useSystems() {
  return useQuery({ queryKey: ['systems'], queryFn: listSystems });
}
